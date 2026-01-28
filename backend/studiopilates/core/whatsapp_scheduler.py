import logging
import sys
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.utils import timezone

from . import models
from .whatsapp_service import EvolutionClient, WhatsappMessageType, WhatsappService

logger = logging.getLogger(__name__)
_scheduler = None
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


def _send_class_reminders(service: WhatsappService, target_date):
    reservas = (
        models.Reserva.objects.filter(
            aulaSessao__data=target_date,
            status__in=["RESERVADA", "PENDENTE"],
        )
        .select_related("aluno", "aulaSessao")
        .order_by("aluno__cdAluno")
    )
    sent_alunos = set()
    today = timezone.localdate()
    for reserva in reservas:
        aluno = reserva.aluno
        if aluno.id in sent_alunos:
            continue
        sent_alunos.add(aluno.id)
        telefone = service.get_aluno_phone(aluno)
        if not telefone:
            continue
        already_sent = models.AlunoWhatsappMessage.objects.filter(
            aluno=aluno,
            tipo=WhatsappMessageType.AUTOMATED_REMINDER,
            enviado_em__date=today,
        ).exists()
        if already_sent:
            continue
        mensagem = f"Boa noite {aluno.dsNome}, amanhã temos aula de Pilates. Podemos confirmar a sua aula?"
        service.send(aluno, telefone, mensagem, WhatsappMessageType.AUTOMATED_REMINDER)


def _send_professor_schedule(target_date):
    reservas = (
        models.Reserva.objects.filter(
            aulaSessao__data=target_date,
            status="RESERVADA",
            aulaSessao__profissional__isnull=False,
        )
        .select_related("aluno", "aulaSessao__profissional")
        .order_by("aulaSessao__profissional_id", "aulaSessao__horaInicio")
    )
    schedule = {}
    for reserva in reservas:
        prof = reserva.aulaSessao.profissional
        if not prof:
            continue
        prof_map = schedule.setdefault(prof.id, {"prof": prof, "slots": {}})
        slot_time = reserva.aulaSessao.horaInicio.strftime("%H:%M")
        prof_map["slots"].setdefault(slot_time, []).append(reserva.aluno.dsNome)
    service = WhatsappService()
    client = EvolutionClient()
    for entry in schedule.values():
        prof = entry["prof"]
        telefone = service.clean_phone(getattr(prof, "celular", None))
        if not telefone:
            continue
        lines = [f"Horários de {target_date.strftime('%d/%m/%Y')}:"]
        for slot_time in sorted(entry["slots"]):
            alunos = entry["slots"][slot_time]
            lines.append(f"{slot_time} - {', '.join(alunos)}")
        message = "\n".join(lines)
        client.send_message(telefone, message)


def _send_contract_renewals(service: WhatsappService):
    reminder_date = timezone.localdate() + timedelta(days=7)
    contratos = (
        models.Contrato.objects.filter(
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
        already_sent = models.AlunoWhatsappMessage.objects.filter(
            contrato=contrato,
            tipo=WhatsappMessageType.CONTRACT_RENEWAL,
        ).exists()
        if already_sent:
            continue
        mensagem = (
            f"Olá {aluno.dsNome}, seu contrato #{contrato.cdContrato} vence em 7 dias "
            f"({contrato.dtFimContrato.strftime('%d/%m/%Y')}). Deseja renovar?"
        )
        service.send(aluno, telefone, mensagem, WhatsappMessageType.CONTRACT_RENEWAL, contrato=contrato)


def _run_jobs():
    service = WhatsappService()
    target_date = timezone.localdate() + timedelta(days=1)
    try:
        _send_class_reminders(service, target_date)
    except Exception:
        logger.exception("Erro ao enviar lembretes diários")
    try:
        _send_professor_schedule(target_date)
    except Exception:
        logger.exception("Erro ao enviar agenda para professores")
    try:
        _send_contract_renewals(service)
    except Exception:
        logger.exception("Erro ao enviar lembretes de renovação")


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
        CronTrigger(hour=19, minute=0, timezone="America/Sao_Paulo"),
        id="whatsapp_sistema_mensagens",
        replace_existing=True,
    )
    _scheduler.start()
