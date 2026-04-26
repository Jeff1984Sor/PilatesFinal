import json
import logging
import sys
from collections import defaultdict
from datetime import timedelta

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


def _send_class_reminders(service: WhatsappService, config: models.WhatsappConfiguracao, target_date):
    reservas = (
        models.Reserva.objects.filter(
            aulaSessao__data=target_date,
            aulaSessao__unidade=config.unidade,
            status__in=["RESERVADA", "PENDENTE"],
        )
        .select_related("aluno", "aulaSessao", "aulaSessao__tipoServico", "aulaSessao__unidade")
        .order_by("aluno__cdAluno", "aulaSessao__horaInicio")
    )
    for aluno_id, aluno_reservas in _reservas_por_aluno(reservas).items():
        aluno = aluno_reservas[0].aluno
        telefone = service.get_aluno_phone(aluno)
        if not telefone:
            continue
        dedupe_key = _log_key("student_reminder", config.unidade_id, target_date, aluno.id)
        if _already_sent(dedupe_key):
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
        resp = service.send(aluno, telefone, mensagem, WhatsappMessageType.AUTOMATED_REMINDER)
        if "error" not in resp:
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


def _send_professor_schedule(service: WhatsappService, config: models.WhatsappConfiguracao, target_date):
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
    for prof_id, prof_reservas in _reservas_por_professor(reservas).items():
        prof = prof_reservas[0].aulaSessao.profissional
        if not prof:
            continue
        telefone = service.clean_phone(getattr(prof, "celular", None))
        if not telefone:
            continue
        dedupe_key = _log_key("professor_schedule", config.unidade_id, target_date, prof.id)
        if _already_sent(dedupe_key):
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
        resp = service._get_client_for_unidade(config.unidade).send_message(telefone, mensagem)
        if "error" not in resp:
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


def _send_contract_renewals(service: WhatsappService, config: models.WhatsappConfiguracao, reminder_date):
    contratos = (
        models.Contrato.objects.filter(
            cdUnidade=config.unidade,
            dtFimContrato=reminder_date,
            status__in=["ASSINADO", "ASSINADO_DIGITALMENTE"],
        )
        .select_related("cdAluno")
        .order_by("cdContrato")
    )
    for contrato in contratos:
        aluno = contrato.cdAluno
        telefone = service.get_aluno_phone(aluno)
        if not telefone:
            continue
        dedupe_key = _log_key("contract_renewal", config.unidade_id, reminder_date, contrato.id)
        if _already_sent(dedupe_key):
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
        resp = service.send(aluno, telefone, mensagem, WhatsappMessageType.CONTRACT_RENEWAL, contrato=contrato)
        if "error" not in resp:
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
