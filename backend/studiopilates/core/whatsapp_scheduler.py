import json
import logging
import sys
from collections import defaultdict
from datetime import timedelta
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.db import connection
from django.utils import timezone

from . import models
from .whatsapp_service import WhatsappMessageType, WhatsappService

logger = logging.getLogger(__name__)
_scheduler = None
_ADVISORY_LOCK_ID = 91437251
BATCH_THROTTLE_SECONDS = getattr(settings, "WHATSAPP_BATCH_PAUSE_SECONDS", 5.0)
_SKIP_COMMANDS = {
    "check",
    "collectstatic",
    "createsuperuser",
    "dumpdata",
    "loaddata",
    "makemigrations",
    "migrate",
    "shell",
    "test",
}


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _render_template(template: str, **context) -> str:
    text = (template or "").strip()
    if not text:
        return ""
    safe_context = _SafeFormatDict({k: "" if v is None else v for k, v in context.items()})
    try:
        return text.format_map(safe_context)
    except Exception:
        logger.exception("Erro ao renderizar template do WhatsApp.")
        return text


def _send_with_retry(send_fn, *, attempts: int = 3, pause_seconds: float = 1.0):
    last_response = None
    for attempt in range(1, max(int(attempts), 1) + 1):
        last_response = send_fn()
        if isinstance(last_response, dict) and "error" not in last_response:
            return last_response
        retry_after = None
        if isinstance(last_response, dict):
            retry_after = last_response.get("retry_after")
            if retry_after is None and isinstance(last_response.get("response"), dict):
                retry_after = last_response["response"].get("retry_after")
        if retry_after is not None:
            try:
                pause_seconds = max(float(retry_after), pause_seconds)
            except (TypeError, ValueError):
                pass
        if attempt < attempts and pause_seconds > 0:
            time.sleep(pause_seconds)
    return last_response or {"error": "Falha ao enviar mensagem."}


def _is_session_down(resp) -> bool:
    """Detecta resposta da WasenderAPI indicando que a sessao do WhatsApp caiu.
    Nesse caso nao adianta seguir o lote (e martelar a API pode gerar restricao)."""
    if not isinstance(resp, dict):
        return False
    texto = str(resp.get("error") or "")
    inner = resp.get("response")
    if isinstance(inner, dict):
        texto += " " + str(inner.get("message") or "")
    texto = texto.lower()
    return "not connected" in texto or ("session" in texto and "connect" in texto)


def _log_key(prefix: str, unidade_id: int | None, data_referencia, recipient_id: int | None) -> str:
    return f"{prefix}:{unidade_id or 0}:{data_referencia.isoformat()}:{recipient_id or 0}"


def _already_sent(dedupe_key: str) -> bool:
    return models.WhatsappAgendamentoLog.objects.filter(dedupe_key=dedupe_key, status="sent").exists()


def _store_log(*, dedupe_key: str, tipo: str, unidade=None, aluno=None, profissional=None, contrato=None, data_referencia=None, telefone="", mensagem="", status="sent", response_payload=""):
    models.WhatsappAgendamentoLog.objects.create(
        dedupe_key=dedupe_key,
        tipo=tipo,
        unidade=unidade,
        aluno=aluno,
        profissional=profissional,
        contrato=contrato,
        data_referencia=data_referencia or timezone.localdate(),
        telefone=telefone or "",
        mensagem=mensagem or "",
        status=status,
        response_payload=response_payload or "",
    )


def _reservas_por_aluno(reservas):
    groups = defaultdict(list)
    for reserva in reservas:
        groups[reserva.aluno_id].append(reserva)
    return groups


def _reservas_por_professor(reservas):
    groups = defaultdict(list)
    for reserva in reservas:
        prof_id = getattr(reserva.aulaSessao, "profissional_id", None)
        if prof_id:
            groups[prof_id].append(reserva)
    return groups


def _format_aulas(reservas):
    lines = []
    for reserva in reservas:
        sessao = reserva.aulaSessao
        tipo_servico = getattr(sessao.tipoServico, "dsTipoServico", "Aula")
        linhas = f"{sessao.horaInicio.strftime('%H:%M')} - {tipo_servico}"
        if getattr(sessao, "unidade", None):
            linhas += f" - {sessao.unidade.dsUnidade}"
        lines.append(linhas)
    return "\n".join(lines)


def _notify_acompanhamento(service: WhatsappService, config: models.WhatsappConfiguracao, resumo: dict, titulo: str):
    """Envia um resumo do disparo para o WhatsApp do gestor (acompanhamento).
    So envia quando houve algum envio novo, para nao gerar spam nas rodadas do scheduler."""
    if not getattr(config, "acompanhar_envios", False):
        return
    numero = service.clean_phone(getattr(config, "numero_acompanhamento", "") or "")
    if not numero:
        return
    if resumo.get("sent", 0) <= 0:
        return
    enviados = [e["aluno"] for e in resumo.get("entries", []) if e.get("status") == "sent"]
    linhas = "\n".join(f"- {nome}" for nome in enviados)
    mensagem = (
        f"{titulo} - {config.unidade.dsUnidade}\n"
        f"Enviados: {resumo.get('sent', 0)}\n"
        f"Sem telefone: {resumo.get('without_phone', 0)}\n"
        f"Pendentes (limite): {resumo.get('rate_limited', 0)}\n"
        f"Falhas: {resumo.get('failed', 0)}"
    )
    if linhas:
        mensagem += f"\n\nAvisados:\n{linhas}"
    try:
        cliente = service._get_client_for_unidade(config.unidade)
        cliente.send_message(numero, mensagem)
    except Exception:
        logger.exception("Falha ao enviar resumo de acompanhamento da unidade %s", config.unidade_id)


def _send_class_reminders(service: WhatsappService, config: models.WhatsappConfiguracao, target_date, *, force: bool = False):
    reservas = (
        models.Reserva.objects.filter(
            aulaSessao__data=target_date,
            aulaSessao__unidade=config.unidade,
        )
        .exclude(status__in=["CANCELADA", "CONCLUIDA", "FALTOU_AVISOU", "FALTOU_SEM_AVISAR"])
        .select_related("aluno", "aulaSessao", "aulaSessao__tipoServico", "aulaSessao__unidade")
        .prefetch_related("aluno__telefones")
        .order_by("aluno__cdAluno", "aulaSessao__horaInicio")
    )
    aluno_groups = list(_reservas_por_aluno(reservas).items())
    total_alunos = len(aluno_groups)
    resumo = {
        "eligible_students": total_alunos,
        "sent": 0,
        "without_phone": 0,
        "rate_limited": 0,
        "already_sent": 0,
        "failed": 0,
        "entries": [],
    }

    for idx, (_aluno_id, aluno_reservas) in enumerate(aluno_groups, start=1):
        aluno = aluno_reservas[0].aluno
        dedupe_key = _log_key("student_reminder", config.unidade_id, target_date, aluno.id)
        if not force and _already_sent(dedupe_key):
            resumo["already_sent"] += 1
            resumo["entries"].append(
                {
                    "ordem": idx,
                    "total": total_alunos,
                    "aluno": aluno.dsNome,
                    "status": "skipped",
                    "status_label": "Ja enviado",
                    "telefone": "",
                    "mensagem": "",
                }
            )
            continue

        telefone = service.get_aluno_phone(aluno)
        if not telefone:
            resumo["without_phone"] += 1
            resumo["entries"].append(
                {
                    "ordem": idx,
                    "total": total_alunos,
                    "aluno": aluno.dsNome,
                    "status": "without_phone",
                    "status_label": "Sem telefone",
                    "telefone": "",
                    "mensagem": "",
                }
            )
            continue

        aulas = _format_aulas(aluno_reservas)
        primeira = aluno_reservas[0].aulaSessao
        mensagem = _render_template(
            config.template_aviso_aluno
            or "Boa noite {aluno}, amanhã temos aula de {tipo_servico} às {horario}. Podemos confirmar?",
            aluno=aluno.dsNome,
            unidade=config.unidade.dsUnidade,
            data=target_date.strftime("%d/%m/%Y"),
            horario=primeira.horaInicio.strftime("%H:%M"),
            tipo_servico=getattr(primeira.tipoServico, "dsTipoServico", "Pilates"),
            aulas=aulas,
            horarios=aulas,
        )

        resp = None
        try:
            resp = _send_with_retry(
                lambda: service.send(aluno, telefone, mensagem, WhatsappMessageType.AUTOMATED_REMINDER),
                attempts=3,
                pause_seconds=BATCH_THROTTLE_SECONDS,
            )
            is_rate_limited = bool(resp.get("rate_limited") or resp.get("status_code") == 429)
            if is_rate_limited:
                resumo["rate_limited"] += 1
                resumo["entries"].append(
                    {
                        "ordem": idx,
                        "total": total_alunos,
                        "aluno": aluno.dsNome,
                        "status": "rate_limited",
                        "status_label": "Pendente por limite",
                        "telefone": telefone,
                        "mensagem": mensagem,
                        "retry_after": resp.get("retry_after"),
                        "error": resp.get("error"),
                    }
                )
            elif "error" not in resp:
                resumo["sent"] += 1
                resumo["entries"].append(
                    {
                        "ordem": idx,
                        "total": total_alunos,
                        "aluno": aluno.dsNome,
                        "status": "sent",
                        "status_label": "Enviado",
                        "telefone": telefone,
                        "mensagem": mensagem,
                    }
                )
                _store_log(
                    dedupe_key=dedupe_key,
                    tipo=WhatsappMessageType.AUTOMATED_REMINDER,
                    unidade=config.unidade,
                    aluno=aluno,
                    data_referencia=target_date,
                    telefone=telefone,
                    mensagem=mensagem,
                    response_payload=json.dumps(resp, ensure_ascii=False),
                )
            else:
                resumo["failed"] += 1
                resumo["entries"].append(
                    {
                        "ordem": idx,
                        "total": total_alunos,
                        "aluno": aluno.dsNome,
                        "status": "failed",
                        "status_label": "Falhou",
                        "telefone": telefone,
                        "mensagem": mensagem,
                        "error": resp.get("error"),
                    }
                )
        except Exception as exc:
            logger.exception("Falha ao enviar WhatsApp para aluno %s na unidade %s", aluno.id, config.unidade_id)
            resumo["failed"] += 1
            resumo["entries"].append(
                {
                    "ordem": idx,
                    "total": total_alunos,
                    "aluno": aluno.dsNome,
                    "status": "failed",
                    "status_label": "Falhou",
                    "telefone": telefone,
                    "mensagem": mensagem,
                    "error": str(exc),
                }
            )

        if _is_session_down(resp):
            logger.warning(
                "Sessao do WhatsApp desconectada na unidade %s - abortando o lote para nao sobrecarregar a API.",
                config.unidade_id,
            )
            resumo["session_down"] = True
            break

        time.sleep(BATCH_THROTTLE_SECONDS)

    _notify_acompanhamento(service, config, resumo, "Lembretes de aula (amanha)")
    return resumo


def _send_professor_schedule(service: WhatsappService, config: models.WhatsappConfiguracao, target_date, *, force: bool = False):
    reservas = (
        models.Reserva.objects.filter(
            aulaSessao__data=target_date,
            aulaSessao__unidade=config.unidade,
            status="RESERVADA",
            aulaSessao__profissional__isnull=False,
        )
        .select_related("aluno", "aulaSessao", "aulaSessao__profissional", "aulaSessao__unidade", "aulaSessao__tipoServico")
        .order_by("aulaSessao__profissional_id", "aulaSessao__horaInicio")
    )
    sent_count = 0
    for prof_id, prof_reservas in _reservas_por_professor(reservas).items():
        prof = prof_reservas[0].aulaSessao.profissional
        if not prof:
            continue
        telefone = service.clean_phone(getattr(prof, "celular", None))
        if not telefone:
            continue
        dedupe_key = _log_key("professor_schedule", config.unidade_id, target_date, prof.id)
        if not force and _already_sent(dedupe_key):
            continue
        slots = []
        for reserva in prof_reservas:
            sessao = reserva.aulaSessao
            tipo_servico = getattr(sessao.tipoServico, "dsTipoServico", "Aula")
            slots.append(f"{sessao.horaInicio.strftime('%H:%M')} - {reserva.aluno.dsNome} - {tipo_servico}")
        agenda_text = "\n".join(slots)
        mensagem = _render_template(
            config.template_aviso_professor or "Resumo de amanhã: {horario} – {alunos}",
            data=target_date.strftime("%d/%m/%Y"),
            unidade=config.unidade.dsUnidade,
            horario=agenda_text,
            alunos=agenda_text,
        )
        cliente = service._get_client_for_unidade(config.unidade)
        try:
            resp = _send_with_retry(lambda: cliente.send_message(telefone, mensagem), attempts=3, pause_seconds=BATCH_THROTTLE_SECONDS)
            if "error" not in resp:
                sent_count += 1
                _store_log(
                    dedupe_key=dedupe_key,
                    tipo=WhatsappMessageType.PROFESSOR_SCHEDULE,
                    unidade=config.unidade,
                    profissional=prof,
                    data_referencia=target_date,
                    telefone=telefone,
                    mensagem=mensagem,
                    response_payload=json.dumps(resp, ensure_ascii=False),
                )
        except Exception:
            logger.exception("Falha ao enviar agenda para professor %s na unidade %s", prof.id, config.unidade_id)
        if len(prof_reservas) > 0:
            time.sleep(BATCH_THROTTLE_SECONDS)
    return sent_count


def _send_contract_renewals(service: WhatsappService, config: models.WhatsappConfiguracao, reminder_date, *, force: bool = False):
    contratos = (
        models.Contrato.objects.filter(
            cdUnidade=config.unidade,
            dtFimContrato=reminder_date,
            status__in=["ASSINADO", "ASSINADO_DIGITALMENTE"],
        )
        .select_related("cdAluno")
        .order_by("cdContrato")
    )
    sent_count = 0
    for contrato in contratos:
        aluno = contrato.cdAluno
        telefone = service.get_aluno_phone(aluno)
        if not telefone:
            continue
        dedupe_key = _log_key("contract_renewal", config.unidade_id, reminder_date, contrato.id)
        if not force and _already_sent(dedupe_key):
            continue
        mensagem = _render_template(
            config.template_aviso_renovacao
            or "Seu contrato vence em {dias_restantes} dias. Deseja renovar?",
            aluno=aluno.dsNome,
            contrato=contrato.cdContrato,
            unidade=config.unidade.dsUnidade,
            dias_restantes=7,
            vencimento=contrato.dtFimContrato.strftime("%d/%m/%Y"),
        )
        try:
            resp = _send_with_retry(
                lambda: service.send(aluno, telefone, mensagem, WhatsappMessageType.CONTRACT_RENEWAL, contrato=contrato),
                attempts=3,
                pause_seconds=BATCH_THROTTLE_SECONDS,
            )
            if "error" not in resp:
                sent_count += 1
                _store_log(
                    dedupe_key=dedupe_key,
                    tipo=WhatsappMessageType.CONTRACT_RENEWAL,
                    unidade=config.unidade,
                    aluno=aluno,
                    contrato=contrato,
                    data_referencia=reminder_date,
                    telefone=telefone,
                    mensagem=mensagem,
                    response_payload=json.dumps(resp, ensure_ascii=False),
                )
        except Exception:
            logger.exception("Falha ao enviar renovacao de contrato %s na unidade %s", contrato.id, config.unidade_id)
        time.sleep(BATCH_THROTTLE_SECONDS)
    return sent_count


def _fmt_valor(v):
    try:
        return f"{float(v):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        return ""


def _send_aluno_messages(service, config, *, prefix, template, recipients, data_referencia, force=False, tipo=None):
    """Envia uma mensagem simples para uma lista de alunos.
    recipients: lista de dicts {aluno, contrato(opcional), dedup_id, context(opcional)}"""
    tipo = tipo or WhatsappMessageType.MANUAL
    sent = 0
    for rec in recipients:
        aluno = rec["aluno"]
        if not aluno:
            continue
        telefone = service.get_aluno_phone(aluno)
        if not telefone:
            continue
        dedupe_key = _log_key(prefix, config.unidade_id, data_referencia, rec["dedup_id"])
        if not force and _already_sent(dedupe_key):
            continue
        mensagem = _render_template(template, aluno=aluno.dsNome, **rec.get("context", {}))
        if not mensagem:
            continue
        resp = None
        try:
            resp = _send_with_retry(
                lambda: service.send(aluno, telefone, mensagem, tipo, contrato=rec.get("contrato")),
                attempts=3,
                pause_seconds=BATCH_THROTTLE_SECONDS,
            )
            if "error" not in resp:
                sent += 1
                _store_log(
                    dedupe_key=dedupe_key,
                    tipo=tipo,
                    unidade=config.unidade,
                    aluno=aluno,
                    contrato=rec.get("contrato"),
                    data_referencia=data_referencia,
                    telefone=telefone,
                    mensagem=mensagem,
                    response_payload=json.dumps(resp, ensure_ascii=False),
                )
        except Exception:
            logger.exception("Falha ao enviar %s para aluno %s na unidade %s", prefix, aluno.id, config.unidade_id)
        if _is_session_down(resp):
            logger.warning(
                "Sessao do WhatsApp desconectada na unidade %s - abortando lote '%s'.",
                config.unidade_id, prefix,
            )
            break
        time.sleep(BATCH_THROTTLE_SECONDS)
    return sent


def _send_birthdays(service, config, hoje, *, force=False):
    alunos = models.Aluno.objects.filter(
        cdUnidade=config.unidade,
        status="ATIVO",
        dtNascimento__month=hoje.month,
        dtNascimento__day=hoje.day,
    ).prefetch_related("telefones")
    recipients = [{"aluno": a, "dedup_id": a.id} for a in alunos]
    return _send_aluno_messages(
        service, config, prefix="birthday", template=config.template_aniversario,
        recipients=recipients, data_referencia=hoje, force=force,
    )


def _send_payment_due(service, config, hoje, *, force=False):
    alvo = hoje + timedelta(days=1)
    contas = (
        models.ContasReceber.objects.filter(
            contrato__cdUnidade=config.unidade, status="ABERTO", dtVencimento=alvo,
        )
        .select_related("contrato", "contrato__cdAluno")
        .prefetch_related("contrato__cdAluno__telefones")
    )
    recipients = []
    for cr in contas:
        aluno = cr.contrato.cdAluno if cr.contrato_id else None
        recipients.append({
            "aluno": aluno, "contrato": cr.contrato, "dedup_id": cr.id,
            "context": {"valor": _fmt_valor(cr.valor), "data": cr.dtVencimento.strftime("%d/%m/%Y")},
        })
    return _send_aluno_messages(
        service, config, prefix="payment_due", template=config.template_vencimento_proximo,
        recipients=recipients, data_referencia=alvo, force=force,
    )


def _send_payment_overdue(service, config, hoje, *, force=False):
    contas = (
        models.ContasReceber.objects.filter(
            contrato__cdUnidade=config.unidade,
            status__in=["ABERTO", "ATRASADO"],
            dtVencimento__lt=hoje,
        )
        .select_related("contrato", "contrato__cdAluno")
        .prefetch_related("contrato__cdAluno__telefones")
    )
    # dedup semanal: usa a segunda-feira da semana como referencia (1x por semana)
    semana = hoje - timedelta(days=hoje.weekday())
    recipients = []
    for cr in contas:
        aluno = cr.contrato.cdAluno if cr.contrato_id else None
        recipients.append({
            "aluno": aluno, "contrato": cr.contrato, "dedup_id": cr.id,
            "context": {"valor": _fmt_valor(cr.valor), "data": cr.dtVencimento.strftime("%d/%m/%Y")},
        })
    return _send_aluno_messages(
        service, config, prefix="payment_overdue", template=config.template_mensalidade_atraso,
        recipients=recipients, data_referencia=semana, force=force,
    )


def _send_three_months(service, config, hoje, *, force=False):
    alvo = hoje - timedelta(days=90)
    contratos = (
        models.Contrato.objects.filter(
            cdUnidade=config.unidade, dtInicioContrato=alvo,
            status__in=["ASSINADO", "ASSINADO_DIGITALMENTE"],
        )
        .select_related("cdAluno")
        .prefetch_related("cdAluno__telefones")
    )
    recipients = [{"aluno": c.cdAluno, "contrato": c, "dedup_id": c.id} for c in contratos]
    return _send_aluno_messages(
        service, config, prefix="three_months", template=config.template_tres_meses,
        recipients=recipients, data_referencia=alvo, force=force,
    )


def _run_jobs():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [_ADVISORY_LOCK_ID])
        locked = cursor.fetchone()[0]
    if not locked:
        return
    service = WhatsappService()
    now = timezone.localtime(timezone.now())
    today = now.date()
    target_date = today + timedelta(days=1)
    configs = models.WhatsappConfiguracao.objects.select_related("unidade").all()
    try:
        for config in configs:
            try:
                if config.avisar_aluno and now.time() >= config.horario_aviso_aluno:
                    _send_class_reminders(service, config, target_date)
            except Exception:
                logger.exception("Erro ao enviar lembretes diários para a unidade %s", config.unidade_id)
            try:
                if config.avisar_professor and now.time() >= config.horario_aviso_professor:
                    _send_professor_schedule(service, config, target_date)
            except Exception:
                logger.exception("Erro ao enviar agenda para professores da unidade %s", config.unidade_id)
            try:
                if config.avisar_renovacao and now.time() >= config.horario_aviso_renovacao:
                    _send_contract_renewals(service, config, today + timedelta(days=7))
            except Exception:
                logger.exception("Erro ao enviar lembretes de renovacao da unidade %s", config.unidade_id)
            try:
                if config.avisar_aniversario and now.time() >= config.horario_aviso_aniversario:
                    _send_birthdays(service, config, today)
            except Exception:
                logger.exception("Erro ao enviar aniversarios da unidade %s", config.unidade_id)
            try:
                if config.avisar_vencimento and now.time() >= config.horario_aviso_vencimento:
                    _send_payment_due(service, config, today)
            except Exception:
                logger.exception("Erro ao enviar avisos de vencimento da unidade %s", config.unidade_id)
            try:
                if config.avisar_atraso and now.time() >= config.horario_aviso_atraso:
                    _send_payment_overdue(service, config, today)
            except Exception:
                logger.exception("Erro ao enviar avisos de atraso da unidade %s", config.unidade_id)
            try:
                if config.avisar_tres_meses and now.time() >= config.horario_aviso_tres_meses:
                    _send_three_months(service, config, today)
            except Exception:
                logger.exception("Erro ao enviar acompanhamento 3 meses da unidade %s", config.unidade_id)
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [_ADVISORY_LOCK_ID])


def start_scheduler():
    global _scheduler
    if not settings.WHATSAPP_SCHEDULER_ENABLED:
        return
    if _scheduler:
        return
    if len(sys.argv) > 1 and sys.argv[1] in _SKIP_COMMANDS:
        return
    _scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    _scheduler.add_job(
        _run_jobs,
        CronTrigger(minute="*/5", timezone="America/Sao_Paulo"),
        id="whatsapp_sistema_mensagens",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=300,
    )
    _scheduler.start()
