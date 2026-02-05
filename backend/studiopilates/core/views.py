import logging
from datetime import date, datetime, timedelta
import calendar
import json
import re
from io import BytesIO
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, OuterRef, Subquery, Exists
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from . import forms, models, services, totalpass_service
from .signals import ensure_profissional_for_user
from shared.ai.gemini_client import extract_address_from_proof, extract_student_from_document
from .whatsapp_service import WhatsappService, WhatsappMessageType

logger = logging.getLogger(__name__)


def _contrato_assinatura_link(contrato, request=None):
    token = services.gerar_token_contrato(contrato)
    base_url = (settings.SITE_BASE_URL or "").rstrip("/")
    if request and (not base_url or "localhost" in base_url):
        base_url = request.build_absolute_uri("/").rstrip("/")
    return f"{base_url}/contratos/assinar/{token}/"


def _mensagem_contrato_whatsapp(contrato, link, is_new=False):
    aluno = contrato.cdAluno
    plano = contrato.cdPlano
    unidade = contrato.cdUnidade
    prefix = "Seu contrato foi criado com sucesso" if is_new else "Seu contrato foi gerado"
    return (
        f"Oi {aluno.dsNome}!\\n"
        f"{prefix} no Mayris Pilates.\\n\\n"
        f"Contrato: #{contrato.cdContrato}\\n"
        f"Plano: {plano}\\n"
        f"Unidade: {unidade}\\n\\n"
        "Para ler e assinar, clique no link abaixo:\\n"
        f"{link}\\n\\n"
        "Qualquer duvida, estamos a disposicao."
    )


def _shift_month(value, months):
    offset = (value.month - 1) + months
    year = value.year + (offset // 12)
    month = (offset % 12) + 1
    return value.replace(year=year, month=month, day=1)


def _get_profissional_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return models.Profissional.objects.select_related("cdPerfilAcesso").filter(user=user).first()


def _is_professor_user(user):
    profissional = _get_profissional_for_user(user)
    if not profissional or not profissional.cdPerfilAcesso_id:
        return False
    perfil = (profissional.cdPerfilAcesso.dsPerfilAcesso or "").strip().lower()
    return "professor" in perfil


def _enviar_contrato_whatsapp(request, contrato, is_new=False):
    service = WhatsappService()
    telefone = service.get_aluno_phone(contrato.cdAluno)
    if not telefone:
        messages.warning(request, "Aluno sem telefone valido para WhatsApp.")
        return False
    link = _contrato_assinatura_link(contrato, request=request)
    mensagem = _mensagem_contrato_whatsapp(contrato, link, is_new=is_new)
    resp = service.send(contrato.cdAluno, telefone, mensagem, WhatsappMessageType.CONTRACT_LINK, contrato=contrato)
    if resp.get("error"):
        messages.warning(request, "Nao foi possivel enviar o contrato por WhatsApp.")
        return False
    messages.success(request, "Contrato enviado por WhatsApp.")
    return True


def _active_menu(path: str) -> str:
    if path.startswith("/cadastros/alunos") or path.startswith("/cadastros/profissionais"):
        return "pessoas"
    if path.startswith("/agenda"):
        return "agenda"
    if path.startswith("/financeiro"):
        return "financeiro"
    if path.startswith("/configuracoes"):
        return "configuracoes"
    if path.startswith("/evolucoes"):
        return "evolucao"
    if path.startswith("/contratos") or path.startswith("/wizard"):
        return "contratos"
    if path.startswith("/cadastros"):
        return "cadastros"
    return "dashboard"


PHONE_CLEAN_REGEX = re.compile(r"\D+")


def _format_whatsapp_number(telefones):
    for tel in telefones:
        cleaned = PHONE_CLEAN_REGEX.sub("", tel or "")
        if not cleaned:
            continue
        if cleaned.startswith("55"):
            return cleaned
        if len(cleaned) in (10, 11):
            return f"55{cleaned}"
        return cleaned
    return None


def _round_to_next_hour(dt_value):
    if dt_value.minute == 0 and dt_value.second == 0 and dt_value.microsecond == 0:
        return dt_value
    return dt_value.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


AULA_INTERVALO_MINUTOS = 10


def _load_funcionamento(unidade_id, tipo_servico_id=None):
    qs = models.HorarioFuncionamento.objects.filter(unidade_id=unidade_id, ativo=True)
    if tipo_servico_id:
        qs = qs.filter(Q(tipoServico_id=tipo_servico_id) | Q(tipoServico__isnull=True))
    else:
        qs = qs.filter(tipoServico__isnull=True)
    horarios = list(qs.order_by("diaSemana", "horaInicio"))
    by_day = {}
    if tipo_servico_id:
        specific_days = {}
        for item in horarios:
            if item.tipoServico_id == tipo_servico_id:
                specific_days.setdefault(item.diaSemana, []).append(item)
            else:
                by_day.setdefault(item.diaSemana, []).append(item)
        for day, items in specific_days.items():
            by_day[day] = items
    else:
        for item in horarios:
            by_day.setdefault(item.diaSemana, []).append(item)
    return by_day


def _load_bloqueios(unidade_id, tipo_servico_id, profissional_id, start_date, end_date):
    qs = models.BloqueioAgenda.objects.filter(unidade_id=unidade_id, ativo=True)
    if tipo_servico_id:
        qs = qs.filter(Q(tipoServico_id=tipo_servico_id) | Q(tipoServico__isnull=True))
    else:
        qs = qs.filter(tipoServico__isnull=True)
    if profissional_id:
        qs = qs.filter(Q(profissional_id=profissional_id) | Q(profissional__isnull=True))
    else:
        qs = qs.filter(profissional__isnull=True)
    qs = qs.filter(Q(dataInicio__lte=end_date) & (Q(dataFim__isnull=True) | Q(dataFim__gte=start_date)))
    return list(qs)


def _is_slot_blocked(blocks, slot_date, slot_start, slot_end):
    for block in blocks:
        if block.recorrente:
            if block.diaSemana is None or block.diaSemana != slot_date.weekday():
                continue
            if block.dataInicio and slot_date < block.dataInicio:
                continue
            if block.dataFim and slot_date > block.dataFim:
                continue
        else:
            if slot_date < block.dataInicio:
                continue
            if block.dataFim and slot_date > block.dataFim:
                continue
        if slot_start < block.horaFim and slot_end > block.horaInicio:
            return True
    return False


def _generate_slots_for_date(target_date, horario_windows, duracao_minutos):
    slots = []
    for window in horario_windows:
        start_dt = _round_to_next_hour(datetime.combine(target_date, window.horaInicio))
        end_dt = datetime.combine(target_date, window.horaFim)
        while start_dt + timedelta(minutes=duracao_minutos) <= end_dt:
            slot_end = start_dt + timedelta(minutes=duracao_minutos)
            slots.append((start_dt.time(), slot_end.time()))
            start_dt += timedelta(minutes=duracao_minutos + AULA_INTERVALO_MINUTOS)
    return slots


def _build_reserva_slots(reservas, days_ahead=60):
    reservas_list = list(reservas or [])
    if not reservas_list:
        return {}
    today = timezone.now().date()
    end_date = today + timedelta(days=days_ahead)
    slots_map = {}
    for reserva in reservas_list:
        aula_atual = reserva.aulaSessao
        if not aula_atual:
            slots_map[reserva.id] = []
            continue
        unidade = aula_atual.unidade
        if not unidade:
            slots_map[reserva.id] = []
            continue
        start_date = min(today, aula_atual.data)
        duracao = unidade.duracao_aula_minutos or 50
        funcionamento = _load_funcionamento(unidade.id, aula_atual.tipoServico_id)
        if not funcionamento:
            slots_map[reserva.id] = []
            continue
        blocks = _load_bloqueios(unidade.id, aula_atual.tipoServico_id, aula_atual.profissional_id, start_date, end_date)
        existing_aulas = list(
            models.AulaSessao.objects.select_related("unidade", "profissional", "tipoServico")
            .filter(
                data__range=(start_date, end_date),
                unidade_id=unidade.id,
                tipoServico_id=aula_atual.tipoServico_id,
                profissional_id=aula_atual.profissional_id,
            )
            .order_by("data", "horaInicio")
        )
        existing_by_key = {(a.data, a.horaInicio): a for a in existing_aulas}
        current_date = start_date
        while current_date <= end_date:
            windows = funcionamento.get(current_date.weekday(), [])
            if windows:
                for hora_inicio, hora_fim in _generate_slots_for_date(current_date, windows, duracao):
                    if _is_slot_blocked(blocks, current_date, hora_inicio, hora_fim):
                        continue
                    key = (current_date, hora_inicio)
                    if key in existing_by_key:
                        continue
                    aula = models.AulaSessao.objects.create(
                        unidade_id=unidade.id,
                        tipoServico_id=aula_atual.tipoServico_id,
                        profissional_id=aula_atual.profissional_id,
                        data=current_date,
                        horaInicio=hora_inicio,
                        horaFim=hora_fim,
                    )
                    existing_by_key[key] = aula
            current_date += timedelta(days=1)

        aulas = list(existing_by_key.values())
        if aula_atual not in aulas:
            aulas.append(aula_atual)
        aula_ids = [a.id for a in aulas]
        reserva_counts = {
            row["aulaSessao_id"]: row["total"]
            for row in models.Reserva.objects.filter(aulaSessao_id__in=aula_ids, status="RESERVADA")
            .values("aulaSessao_id")
            .annotate(total=Count("id"))
        }
        slots = []
        for aula in sorted(aulas, key=lambda x: (x.data, x.horaInicio)):
            capacidade = aula.capacidade if aula.capacidade is not None else unidade.capacidade
            reservadas = reserva_counts.get(aula.id, 0)
            is_current = aula.id == aula_atual.id
            if not is_current and (capacidade is None or capacidade <= 0 or reservadas >= capacidade):
                continue
            vagas = max((capacidade or 0) - reservadas, 0)
            label = f"{aula.horaInicio.strftime('%H:%M')} - {aula.horaFim.strftime('%H:%M')}"
            if aula.profissional_id:
                label = f"{label} | {aula.profissional}"
            if capacidade and capacidade > 0:
                label = f"{label} ({vagas} vaga(s))"
            slots.append(
                {
                    "id": aula.id,
                    "date": aula.data.strftime("%Y-%m-%d"),
                    "time_start": aula.horaInicio.strftime("%H:%M"),
                    "time_end": aula.horaFim.strftime("%H:%M"),
                    "label": label,
                }
            )
        slots_map[reserva.id] = slots
    return slots_map



def login_view(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user:
            ensure_profissional_for_user(user)
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Login invalido")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def perfil_view(request):
    profissional = models.Profissional.objects.filter(user=request.user).first()
    if not profissional:
        profissional = ensure_profissional_for_user(request.user)
    if not profissional:
        messages.error(request, "Nao foi possivel localizar o seu cadastro.")
        return redirect("dashboard")
    return edit_view(request, models.Profissional, forms.ProfissionalForm, "perfil", profissional.pk)


@login_required
def dashboard(request):
    today = timezone.localdate()
    start_month = _shift_month(today.replace(day=1), -5)
    aniversariantes_mes = (
        models.Aluno.objects.filter(dtNascimento__month=today.month)
        .exclude(dtNascimento__isnull=True)
        .order_by("dtNascimento__day", "dsNome")[:8]
    )
    proximas_aulas = (
        models.Reserva.objects.select_related("aluno", "aulaSessao", "aulaSessao__profissional", "aulaSessao__unidade")
        .filter(aulaSessao__data__gte=today, status__in=["RESERVADA", "PENDENTE"])
        .order_by("aulaSessao__data", "aulaSessao__horaInicio")[:8]
    )
    contas_atrasadas = models.ContasReceber.objects.filter(
        status__in=["ABERTO", "ATRASADO"],
        dtVencimento__lt=today,
    ).count()
    contratos_vencendo = models.Contrato.objects.filter(
        dtFimContrato__gte=today,
        dtFimContrato__lte=today + timedelta(days=7),
    ).count()
    alertas = []
    if contas_atrasadas:
        alertas.append(f"{contas_atrasadas} faturas em atraso")
    if contratos_vencendo:
        alertas.append(f"{contratos_vencendo} contratos vencendo em 7 dias")

    aulas_por_mes_raw = (
        models.Reserva.objects.filter(aulaSessao__data__gte=start_month)
        .annotate(month=TruncMonth("aulaSessao__data"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    aulas_por_mes_map = {item["month"]: item["total"] for item in aulas_por_mes_raw if item["month"]}
    aulas_por_mes = []
    for i in range(0, 6):
        month_start = _shift_month(start_month, i)
        total = aulas_por_mes_map.get(month_start, 0)
        aulas_por_mes.append(
            {
                "label": f"{calendar.month_abbr[month_start.month]}/{str(month_start.year)[-2:]}",
                "total": total,
            }
        )

    aulas_por_professor = (
        models.Reserva.objects.filter(aulaSessao__data__gte=start_month, aulaSessao__profissional__isnull=False)
        .values("aulaSessao__profissional__profissional")
        .annotate(total=Count("id"))
        .order_by("-total")[:6]
    )
    context = {
        "alunos": models.Aluno.objects.count(),
        "contratos": models.Contrato.objects.count(),
        "reservas_hoje": models.Reserva.objects.filter(aulaSessao__data=today).exclude(status="CANCELADA").count(),
        "receber_aberto": models.ContasReceber.objects.filter(status__in=["ABERTO", "ATRASADO"]).count(),
        "aniversariantes_mes": aniversariantes_mes,
        "proximas_aulas": proximas_aulas,
        "alertas": alertas,
        "aulas_por_mes": aulas_por_mes,
        "aulas_por_professor": aulas_por_professor,
        "breadcrumbs": [("Home", "#")],
        "active_menu": "dashboard",
    }
    return render(request, "dashboard.html", context)

@login_required
@login_required
@require_POST
def contrato_whatsapp(request, pk):
    contrato = get_object_or_404(models.Contrato, pk=pk)
    next_url = request.POST.get("next")
    _enviar_contrato_whatsapp(request, contrato, is_new=False)
    if next_url:
        return redirect(next_url)
    return redirect(f"{reverse('alunos_detail', args=[contrato.cdAluno_id])}?tab=contratos")


def aluno_detail(request, pk):
    is_professor = _is_professor_user(request.user)
    aluno = get_object_or_404(models.Aluno, pk=pk)
    endereco = aluno.cdEndereco
    telefones = list(aluno.telefones.values_list("dsTelefone", flat=True))
    whatsapp_number = _format_whatsapp_number(telefones)
    contratos = models.Contrato.objects.filter(cdAluno=aluno).select_related("cdPlano", "cdUnidade")
    contrato_forms = {contrato.id: forms.ContratoForm(instance=contrato) for contrato in contratos}
    reservas = (
        models.Reserva.objects.filter(aluno=aluno)
        .select_related("aulaSessao", "aulaSessao__profissional", "aulaSessao__unidade", "aulaSessao__tipoServico")
        .order_by("aulaSessao__data", "aulaSessao__horaInicio")
    )
    reserva_forms = {reserva.id: forms.ReservaForm(instance=reserva) for reserva in reservas}
    reserva_slots = _build_reserva_slots(reservas)
    evolucoes = (
        models.EvolucaoAluno.objects.filter(reserva__aluno=aluno)
        .select_related("profissional", "reserva")
        .order_by("-dtEvolucao")
    )
    avaliacoes = (
        models.AvaliacaoAluno.objects.filter(reserva__aluno=aluno)
        .select_related("profissional", "reserva")
        .order_by("-dtAvaliacao")
    )
    contas_receber = _filtrar_contas_receber(
        models.ContasReceber.objects.filter(contrato__cdAluno=aluno).select_related("contrato"),
        request,
    )
    planos = models.Plano.objects.select_related("cdTipoServico").all()
    unidades = models.Unidade.objects.all()
    profissionais = models.Profissional.objects.all()
    whatsapp_messages = aluno.whatsapp_messages.select_related("contrato").all()
    whatsapp_form = forms.WhatsappMessageForm()
    context = {
        "aluno": aluno,
        "endereco": endereco,
        "telefones": telefones,
        "whatsapp_number": whatsapp_number,
        "contratos": contratos,
        "contrato_forms": contrato_forms,
        "reservas": reservas,
        "reserva_forms": reserva_forms,
        "reserva_slots": reserva_slots,
        "evolucoes": evolucoes,
        "avaliacoes": avaliacoes,
        "contas_receber": contas_receber,
        "filtros_financeiro": _get_filtros_financeiro(request),
        "today": timezone.now().date().strftime("%Y-%m-%d"),
        "today_date": timezone.now().date(),
        "planos": planos,
        "unidades": unidades,
        "profissionais": profissionais,
        "whatsapp_messages": whatsapp_messages,
        "whatsapp_form": whatsapp_form,
        "edit_form": forms.AlunoForm(instance=aluno),
        "breadcrumbs": [("Home", reverse("dashboard")), ("Alunos", reverse("alunos_list")), ("Ficha", "#")],
        "active_menu": "cadastros",
        "can_view_contratos": not is_professor,
        "can_view_financeiro": not is_professor,
    }
    return render(request, "alunos/detail.html", context)


@login_required
def aluno_whatsapp_message(request, pk):
    aluno = get_object_or_404(models.Aluno, pk=pk)
    if request.method != "POST":
        return redirect("alunos_detail", pk=pk)
    next_url = request.POST.get("next")
    form = forms.WhatsappMessageForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Informe uma mensagem valida para enviar.")
        return redirect(next_url or "alunos_detail", pk=aluno.pk) if not next_url else redirect(next_url)
    service = WhatsappService()
    telefone = service.get_aluno_phone(aluno)
    if not telefone:
        messages.warning(request, "Aluno sem telefone valido cadastrado.")
        return redirect(next_url or "alunos_detail", pk=aluno.pk) if not next_url else redirect(next_url)
    resp = service.send(aluno, telefone, form.cleaned_data["mensagem"], WhatsappMessageType.MANUAL)
    if resp.get("error"):
        messages.warning(request, "Mensagem registrada, mas nao foi possivel enviar via WhatsApp.")
    else:
        messages.success(request, "Mensagem enviada e registrada.")
    return redirect(next_url or "alunos_detail", pk=aluno.pk) if not next_url else redirect(next_url)


@login_required
@require_POST
def aluno_evolucao_create(request, aluno_id):
    aluno = get_object_or_404(models.Aluno, pk=aluno_id)
    reserva_id = request.POST.get("reserva_id")
    profissional_id = request.POST.get("profissional_id")
    texto = (request.POST.get("texto") or "").strip()
    if not texto or not reserva_id or not profissional_id:
        messages.error(request, "Preencha todos os campos da evolucao.")
        return redirect("alunos_detail", pk=aluno.pk)
    reserva = get_object_or_404(models.Reserva, pk=reserva_id, aluno=aluno)
    profissional = get_object_or_404(models.Profissional, pk=profissional_id)
    models.EvolucaoAluno.objects.create(reserva=reserva, profissional=profissional, texto=texto)
    messages.success(request, "Evolucao registrada.")
    return redirect(f"{reverse('alunos_detail', args=[aluno.pk])}?tab=evolucao")


@login_required
@require_POST
def aluno_evolucao_update(request, evolucao_id):
    evolucao = get_object_or_404(models.EvolucaoAluno, pk=evolucao_id)
    texto = (request.POST.get("texto") or "").strip()
    if not texto:
        messages.error(request, "Informe o texto da evolucao.")
        return redirect(f"{reverse('alunos_detail', args=[evolucao.reserva.aluno_id])}?tab=evolucao")
    evolucao.texto = texto
    evolucao.save(update_fields=["texto"])
    messages.success(request, "Evolucao atualizada.")
    return redirect(f"{reverse('alunos_detail', args=[evolucao.reserva.aluno_id])}?tab=evolucao")


@login_required
@require_POST
def aluno_evolucao_delete(request, evolucao_id):
    evolucao = get_object_or_404(models.EvolucaoAluno, pk=evolucao_id)
    aluno_id = evolucao.reserva.aluno_id
    evolucao.delete()
    messages.success(request, "Evolucao removida.")
    return redirect(f"{reverse('alunos_detail', args=[aluno_id])}?tab=evolucao")


@login_required
@require_POST
def aluno_avaliacao_create(request, aluno_id):
    aluno = get_object_or_404(models.Aluno, pk=aluno_id)
    reserva_id = request.POST.get("reserva_id")
    profissional_id = request.POST.get("profissional_id")
    texto = (request.POST.get("texto") or "").strip()
    if not texto or not reserva_id or not profissional_id:
        messages.error(request, "Preencha todos os campos da avaliacao.")
        return redirect("alunos_detail", pk=aluno.pk)
    reserva = get_object_or_404(models.Reserva, pk=reserva_id, aluno=aluno)
    profissional = get_object_or_404(models.Profissional, pk=profissional_id)
    models.AvaliacaoAluno.objects.create(reserva=reserva, profissional=profissional, texto=texto)
    messages.success(request, "Avaliacao registrada.")
    return redirect(f"{reverse('alunos_detail', args=[aluno.pk])}?tab=avaliacao")


@login_required
@require_POST
def aluno_avaliacao_update(request, avaliacao_id):
    avaliacao = get_object_or_404(models.AvaliacaoAluno, pk=avaliacao_id)
    texto = (request.POST.get("texto") or "").strip()
    if not texto:
        messages.error(request, "Informe o texto da avaliacao.")
        return redirect(f"{reverse('alunos_detail', args=[avaliacao.reserva.aluno_id])}?tab=avaliacao")
    avaliacao.texto = texto
    avaliacao.save(update_fields=["texto"])
    messages.success(request, "Avaliacao atualizada.")
    return redirect(f"{reverse('alunos_detail', args=[avaliacao.reserva.aluno_id])}?tab=avaliacao")


@login_required
@require_POST
def aluno_avaliacao_delete(request, avaliacao_id):
    avaliacao = get_object_or_404(models.AvaliacaoAluno, pk=avaliacao_id)
    aluno_id = avaliacao.reserva.aluno_id
    avaliacao.delete()
    messages.success(request, "Avaliacao removida.")
    return redirect(f"{reverse('alunos_detail', args=[aluno_id])}?tab=avaliacao")


def _sync_user_for_profissional(profissional, raw_password=None, old_cd=None):
    User = get_user_model()
    base_username = (profissional.email or "").strip().lower()
    if not base_username:
        base_username = slugify(profissional.profissional) or f"user-{profissional.id}"
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exclude(pk=getattr(profissional.user, "pk", None)).exists():
        counter += 1
        username = f"{base_username}-{counter}"

    if profissional.user_id:
        user = profissional.user
        user.username = username
        user.first_name = profissional.profissional
        if profissional.email:
            user.email = profissional.email
    else:
        user = User(username=username, first_name=profissional.profissional, email=(profissional.email or ""))

    if raw_password:
        user.set_password(raw_password)
    elif not user.has_usable_password():
        user.set_unusable_password()
    user.save()

    if not profissional.user_id:
        profissional.user = user
        profissional.save(update_fields=["user"])


def _inject_cd_value(model, data):
    cd_field = next((f.name for f in model._meta.fields if f.name.startswith("cd")), None)
    if not cd_field:
        return data
    if data.get(cd_field):
        return data
    max_val = model.objects.order_by(f"-{cd_field}").values_list(cd_field, flat=True).first() or 0
    data[cd_field] = max_val + 1
    return data


def _sync_aluno_address(aluno, data):
    fields = {
        "dsLogradouro": data.get("dsLogradouro", "").strip(),
        "dsNumero": data.get("dsNumero", "").strip(),
        "dsCEP": data.get("dsCEP", "").strip(),
        "dsCidade": data.get("dsCidade", "").strip(),
        "dsBairro": data.get("dsBairro", "").strip(),
    }
    if not any(fields.values()):
        return
    endereco = aluno.cdEndereco
    if not endereco:
        max_cd = models.EnderecoAluno.objects.order_by("-cdEndereco").values_list("cdEndereco", flat=True).first() or 0
        endereco = models.EnderecoAluno(cdEndereco=max_cd + 1, cdAluno=aluno)
    for key, value in fields.items():
        setattr(endereco, key, value)
    endereco.save()
    if aluno.cdEndereco_id != endereco.id:
        aluno.cdEndereco = endereco
        aluno.save(update_fields=["cdEndereco"])


def _sync_aluno_phones(aluno, data):
    phones = []
    for key, value in data.items():
        if key.startswith("telefone_"):
            raw = value.strip()
            if raw:
                phones.append(raw)
    if not phones:
        return
    models.TelefoneAluno.objects.filter(cdAluno=aluno).delete()
    max_cd = models.TelefoneAluno.objects.order_by("-cdTelefone").values_list("cdTelefone", flat=True).first() or 0
    for idx, numero in enumerate(phones, start=1):
        models.TelefoneAluno.objects.create(cdTelefone=max_cd + idx, cdAluno=aluno, dsTelefone=numero)


def _to_time(raw_value):
    if not raw_value:
        return None
    if isinstance(raw_value, str):
        try:
            return datetime.strptime(raw_value.strip(), "%H:%M").time()
        except ValueError:
            return None
    return raw_value


def _add_months(base_date, months):
    year = base_date.year + (base_date.month - 1 + months) // 12
    month = (base_date.month - 1 + months) % 12 + 1
    day = min(base_date.day, 28)
    return date(year, month, day)


def _add_years(base_date, years):
    return _add_months(base_date, years * 12)


def _first_last_day_month(ref_date):
    first = ref_date.replace(day=1)
    last_day = calendar.monthrange(ref_date.year, ref_date.month)[1]
    last = ref_date.replace(day=last_day)
    return first, last


@login_required
def gerar_horarios_studio(request):
    if request.method != "POST":
        return redirect("horarios_studio_list")
    unidade_id = request.POST.get("unidade") or ""
    tipo_id = request.POST.get("tipoServico") or ""
    profissional_id = request.POST.get("profissional") or ""
    dias = request.POST.getlist("dias")
    inicio = _to_time(request.POST.get("horaInicio"))
    fim = _to_time(request.POST.get("horaFim"))
    intervalo = int(request.POST.get("intervalo") or 0)
    capacidade = request.POST.get("capacidade") or ""
    try:
        capacidade = int(capacidade) if capacidade else None
    except ValueError:
        capacidade = None
    if not (unidade_id and tipo_id and dias and inicio and fim and intervalo):
        messages.error(request, "Preencha unidade, tipo de servico, dias e horarios.")
        return redirect("horarios_studio_list")
    try:
        unidade_id = int(unidade_id)
        tipo_id = int(tipo_id)
    except ValueError:
        messages.error(request, "Unidade ou tipo de servico invalido.")
        return redirect("horarios_studio_list")
    prof_id = None
    if profissional_id:
        try:
            prof_id = int(profissional_id)
        except ValueError:
            prof_id = None
    start_minutes = inicio.hour * 60 + inicio.minute
    end_minutes = fim.hour * 60 + fim.minute
    if end_minutes <= start_minutes:
        messages.error(request, "Horario final deve ser maior que o inicial.")
        return redirect("horarios_studio_list")
    if intervalo <= 0:
        messages.error(request, "Intervalo invalido.")
        return redirect("horarios_studio_list")
    max_cd = models.HorarioStudio.objects.order_by("-cdHorario").values_list("cdHorario", flat=True).first() or 0
    created = 0
    for dia in dias:
        try:
            dia_int = int(dia)
        except ValueError:
            continue
        current = start_minutes
        while current + intervalo <= end_minutes:
            hora_inicio = datetime.strptime(f"{current // 60:02d}:{current % 60:02d}", "%H:%M").time()
            next_min = current + intervalo
            hora_fim = datetime.strptime(f"{next_min // 60:02d}:{next_min % 60:02d}", "%H:%M").time()
            exists = models.HorarioStudio.objects.filter(
                unidade_id=unidade_id,
                tipoServico_id=tipo_id,
                profissional_id=prof_id,
                diaSemana=dia_int,
                horaInicio=hora_inicio,
                horaFim=hora_fim,
            ).exists()
            if not exists:
                max_cd += 1
                models.HorarioStudio.objects.create(
                    cdHorario=max_cd,
                    unidade_id=unidade_id,
                    tipoServico_id=tipo_id,
                    profissional_id=prof_id,
                    diaSemana=dia_int,
                    horaInicio=hora_inicio,
                    horaFim=hora_fim,
                    capacidade=capacidade,
                )
                created += 1
            current = next_min
    if created:
        messages.success(request, f"{created} horarios criados.")
    else:
        messages.info(request, "Nenhum horario novo criado.")
    return redirect("horarios_studio_list")


@login_required
def gerar_horarios_funcionamento(request):
    if request.method != "POST":
        return redirect("horarios_funcionamento_list")
    unidade_id = request.POST.get("unidade") or ""
    tipo_id = request.POST.get("tipoServico") or ""
    dias = request.POST.getlist("dias")
    inicio = _to_time(request.POST.get("horaInicio"))
    fim = _to_time(request.POST.get("horaFim"))
    ativo = request.POST.get("ativo") in ("1", "on", "true", "True")
    if not (unidade_id and dias and inicio and fim):
        messages.error(request, "Preencha unidade, dias e horarios.")
        return redirect("horarios_funcionamento_list")
    try:
        unidade_id = int(unidade_id)
    except ValueError:
        messages.error(request, "Unidade invalida.")
        return redirect("horarios_funcionamento_list")
    tipo_servico_id = None
    if tipo_id:
        try:
            tipo_servico_id = int(tipo_id)
        except ValueError:
            tipo_servico_id = None
    if fim <= inicio:
        messages.error(request, "Horario final deve ser maior que o inicial.")
        return redirect("horarios_funcionamento_list")
    created = 0
    for dia in dias:
        try:
            dia_int = int(dia)
        except ValueError:
            continue
        exists = models.HorarioFuncionamento.objects.filter(
            unidade_id=unidade_id,
            tipoServico_id=tipo_servico_id,
            diaSemana=dia_int,
            horaInicio=inicio,
            horaFim=fim,
        ).exists()
        if exists:
            continue
        models.HorarioFuncionamento.objects.create(
            unidade_id=unidade_id,
            tipoServico_id=tipo_servico_id,
            diaSemana=dia_int,
            horaInicio=inicio,
            horaFim=fim,
            ativo=ativo,
        )
        created += 1
    if created:
        messages.success(request, f"{created} horarios criados.")
    else:
        messages.info(request, "Nenhum horario novo criado.")
    return redirect("horarios_funcionamento_list")


@login_required
def atualizar_horario_funcionamento(request, pk):
    obj = get_object_or_404(models.HorarioFuncionamento, pk=pk)
    if request.method != "POST":
        return redirect("horarios_funcionamento_list")
    unidade_id = request.POST.get("unidade") or obj.unidade_id
    tipo_id = request.POST.get("tipoServico") or ""
    dias = request.POST.getlist("dias")
    inicio = _to_time(request.POST.get("horaInicio")) or obj.horaInicio
    fim = _to_time(request.POST.get("horaFim")) or obj.horaFim
    ativo = request.POST.get("ativo") in ("1", "on", "true", "True")
    try:
        unidade_id = int(unidade_id)
    except ValueError:
        messages.error(request, "Unidade invalida.")
        return redirect("horarios_funcionamento_list")
    tipo_servico_id = None
    if tipo_id:
        try:
            tipo_servico_id = int(tipo_id)
        except ValueError:
            tipo_servico_id = None
    if fim <= inicio:
        messages.error(request, "Horario final deve ser maior que o inicial.")
        return redirect("horarios_funcionamento_list")
    if not dias:
        dias = [str(obj.diaSemana)]
    dias_int = []
    for dia in dias:
        try:
            dias_int.append(int(dia))
        except ValueError:
            continue
    if not dias_int:
        dias_int = [obj.diaSemana]
    primary_day = dias_int[0]
    obj.unidade_id = unidade_id
    obj.tipoServico_id = tipo_servico_id
    obj.diaSemana = primary_day
    obj.horaInicio = inicio
    obj.horaFim = fim
    obj.ativo = ativo
    obj.save()

    created = 0
    for dia in dias_int[1:]:
        exists = models.HorarioFuncionamento.objects.filter(
            unidade_id=unidade_id,
            tipoServico_id=tipo_servico_id,
            diaSemana=dia,
            horaInicio=inicio,
            horaFim=fim,
        ).exists()
        if exists:
            continue
        models.HorarioFuncionamento.objects.create(
            unidade_id=unidade_id,
            tipoServico_id=tipo_servico_id,
            diaSemana=dia,
            horaInicio=inicio,
            horaFim=fim,
            ativo=ativo,
        )
        created += 1
    if created:
        messages.success(request, f"{created} horario(s) extras criados.")
    else:
        messages.success(request, "Horario atualizado.")
    return redirect("horarios_funcionamento_list")


@login_required
def criar_bloqueio_agenda(request):
    if request.method != "POST":
        return redirect("bloqueios_list")
    unidade_id = request.POST.get("unidade") or ""
    tipo_id = request.POST.get("tipoServico") or ""
    profissional_id = request.POST.get("profissional") or ""
    recorrente = request.POST.get("recorrente") in ("1", "on", "true", "True")
    dias = request.POST.getlist("dias")
    data_inicio = request.POST.get("dataInicio") or ""
    data_fim = request.POST.get("dataFim") or ""
    inicio = _to_time(request.POST.get("horaInicio"))
    fim = _to_time(request.POST.get("horaFim"))
    motivo = request.POST.get("motivo", "").strip()
    ativo = request.POST.get("ativo") in ("1", "on", "true", "True")

    try:
        unidade_id = int(unidade_id)
    except ValueError:
        messages.error(request, "Unidade invalida.")
        return redirect("bloqueios_list")
    tipo_servico_id = None
    if tipo_id:
        try:
            tipo_servico_id = int(tipo_id)
        except ValueError:
            tipo_servico_id = None
    prof_id = None
    if profissional_id:
        try:
            prof_id = int(profissional_id)
        except ValueError:
            prof_id = None
    if not data_inicio:
        messages.error(request, "Informe a data de inicio.")
        return redirect("bloqueios_list")
    try:
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Data de inicio invalida.")
        return redirect("bloqueios_list")
    data_fim_dt = None
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Data final invalida.")
            return redirect("bloqueios_list")
    if not inicio or not fim or fim <= inicio:
        messages.error(request, "Horario final deve ser maior que o inicial.")
        return redirect("bloqueios_list")

    created = 0
    if recorrente:
        if not dias:
            messages.error(request, "Selecione os dias da semana.")
            return redirect("bloqueios_list")
        for dia in dias:
            try:
                dia_int = int(dia)
            except ValueError:
                continue
            models.BloqueioAgenda.objects.create(
                unidade_id=unidade_id,
                tipoServico_id=tipo_servico_id,
                profissional_id=prof_id,
                recorrente=True,
                diaSemana=dia_int,
                dataInicio=data_inicio_dt,
                dataFim=data_fim_dt,
                horaInicio=inicio,
                horaFim=fim,
                motivo=motivo,
                ativo=ativo,
            )
            created += 1
    else:
        models.BloqueioAgenda.objects.create(
            unidade_id=unidade_id,
            tipoServico_id=tipo_servico_id,
            profissional_id=prof_id,
            recorrente=False,
            diaSemana=None,
            dataInicio=data_inicio_dt,
            dataFim=data_fim_dt,
            horaInicio=inicio,
            horaFim=fim,
            motivo=motivo,
            ativo=ativo,
        )
        created = 1
    messages.success(request, f"{created} bloqueio(s) criado(s).")
    return redirect("bloqueios_list")


@login_required
def atualizar_bloqueio_agenda(request, pk):
    obj = get_object_or_404(models.BloqueioAgenda, pk=pk)
    if request.method != "POST":
        return redirect("bloqueios_list")
    unidade_id = request.POST.get("unidade") or obj.unidade_id
    tipo_id = request.POST.get("tipoServico") or ""
    profissional_id = request.POST.get("profissional") or ""
    recorrente = request.POST.get("recorrente") in ("1", "on", "true", "True")
    dias = request.POST.getlist("dias")
    data_inicio = request.POST.get("dataInicio") or obj.dataInicio.strftime("%Y-%m-%d")
    data_fim = request.POST.get("dataFim") or ""
    inicio = _to_time(request.POST.get("horaInicio")) or obj.horaInicio
    fim = _to_time(request.POST.get("horaFim")) or obj.horaFim
    motivo = request.POST.get("motivo", "").strip()
    ativo = request.POST.get("ativo") in ("1", "on", "true", "True")

    try:
        unidade_id = int(unidade_id)
    except ValueError:
        messages.error(request, "Unidade invalida.")
        return redirect("bloqueios_list")
    tipo_servico_id = None
    if tipo_id:
        try:
            tipo_servico_id = int(tipo_id)
        except ValueError:
            tipo_servico_id = None
    prof_id = None
    if profissional_id:
        try:
            prof_id = int(profissional_id)
        except ValueError:
            prof_id = None
    try:
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Data de inicio invalida.")
        return redirect("bloqueios_list")
    data_fim_dt = None
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Data final invalida.")
            return redirect("bloqueios_list")
    if not inicio or not fim or fim <= inicio:
        messages.error(request, "Horario final deve ser maior que o inicial.")
        return redirect("bloqueios_list")

    if recorrente and not dias:
        dias = [str(obj.diaSemana)] if obj.diaSemana is not None else []

    if recorrente and dias:
        dias_int = []
        for dia in dias:
            try:
                dias_int.append(int(dia))
            except ValueError:
                continue
        if not dias_int:
            messages.error(request, "Selecione os dias da semana.")
            return redirect("bloqueios_list")
        primary_day = dias_int[0]
        obj.unidade_id = unidade_id
        obj.tipoServico_id = tipo_servico_id
        obj.profissional_id = prof_id
        obj.recorrente = True
        obj.diaSemana = primary_day
        obj.dataInicio = data_inicio_dt
        obj.dataFim = data_fim_dt
        obj.horaInicio = inicio
        obj.horaFim = fim
        obj.motivo = motivo
        obj.ativo = ativo
        obj.save()
        created = 0
        for dia in dias_int[1:]:
            models.BloqueioAgenda.objects.create(
                unidade_id=unidade_id,
                tipoServico_id=tipo_servico_id,
                profissional_id=prof_id,
                recorrente=True,
                diaSemana=dia,
                dataInicio=data_inicio_dt,
                dataFim=data_fim_dt,
                horaInicio=inicio,
                horaFim=fim,
                motivo=motivo,
                ativo=ativo,
            )
            created += 1
        if created:
            messages.success(request, f"{created} bloqueio(s) extras criados.")
        else:
            messages.success(request, "Bloqueio atualizado.")
        return redirect("bloqueios_list")

    obj.unidade_id = unidade_id
    obj.tipoServico_id = tipo_servico_id
    obj.profissional_id = prof_id
    obj.recorrente = False
    obj.diaSemana = None
    obj.dataInicio = data_inicio_dt
    obj.dataFim = data_fim_dt
    obj.horaInicio = inicio
    obj.horaFim = fim
    obj.motivo = motivo
    obj.ativo = ativo
    obj.save()
    messages.success(request, "Bloqueio atualizado.")
    return redirect("bloqueios_list")


def list_view(request, model, form_class, title, allow_modal=True, extra_context=None):
    if model in (models.Plano, models.Contrato) and _is_professor_user(request.user):
        messages.error(request, "Sem permissao para acessar esta area.")
        return redirect("dashboard")
    query = request.GET.get("q", "").strip()
    order = request.GET.get("order", "id")
    qs = model.objects.all()
    if model is models.ContasReceber:
        qs = qs.select_related("contrato", "contrato__cdAluno")
    if model is models.Contrato:
        qs = qs.select_related("cdAluno", "cdPlano", "cdUnidade")
    if query:
        field_name = model._meta.fields[1].name
        qs = qs.filter(Q(**{f"{field_name}__icontains": query}) | Q(id__icontains=query))
    if order:
        qs = qs.order_by(order)
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page"))
    display_fields = [
        {"name": field.name, "label": str(field.verbose_name)}
        for field in model._meta.fields
        if not field.primary_key and not field.name.startswith("cd")
    ][:3]
    edit_forms = {}
    if allow_modal:
        for obj in page:
            edit_forms[obj.id] = form_class(instance=obj)

    context = {
        "title": title,
        "page": page,
        "form": form_class(),
        "model_name": model._meta.model_name,
        "breadcrumbs": [("Home", reverse("dashboard")), (title, "#")],
        "active_menu": _active_menu(request.path),
        "allow_modal": allow_modal,
        "display_fields": display_fields,
        "edit_forms": edit_forms,
    }
    if model is models.Aluno:
        address_map = {}
        phones_map = {}
        for obj in page:
            address_map[obj.id] = obj.cdEndereco
            phones_map[obj.id] = list(obj.telefones.values_list("dsTelefone", flat=True))
        context.update({"address_map": address_map, "phones_map": phones_map})
    if extra_context:
        context.update(extra_context)
    return render(request, "generic/list.html", context)


@login_required
def horarios_studio_list(request):
    extra_context = {
        "unidades": models.Unidade.objects.all(),
        "tipos_servico": models.TipoServico.objects.all(),
        "profissionais": models.Profissional.objects.all(),
        "dias_semana": models.HorarioStudio.DIAS_SEMANA,
    }
    return list_view(
        request,
        models.HorarioStudio,
        forms.HorarioStudioForm,
        "Horario do Studio",
        extra_context=extra_context,
    )


@login_required
def horarios_funcionamento_list(request):
    extra_context = {
        "unidades": models.Unidade.objects.all(),
        "tipos_servico": models.TipoServico.objects.all(),
        "dias_semana": models.HorarioStudio.DIAS_SEMANA,
    }
    return list_view(
        request,
        models.HorarioFuncionamento,
        forms.HorarioFuncionamentoForm,
        "Horario de Funcionamento",
        extra_context=extra_context,
    )


@login_required
def bloqueios_list(request):
    extra_context = {
        "unidades": models.Unidade.objects.all(),
        "tipos_servico": models.TipoServico.objects.all(),
        "profissionais": models.Profissional.objects.all(),
        "dias_semana": models.HorarioStudio.DIAS_SEMANA,
    }
    return list_view(
        request,
        models.BloqueioAgenda,
        forms.BloqueioAgendaForm,
        "Bloqueios de Agenda",
        extra_context=extra_context,
    )


@login_required
def contas_pagar_list(request):
    today = timezone.now().date()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    status = request.GET.get("status", "").strip()
    fornecedor_id = request.GET.get("fornecedor", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    subcategoria_id = request.GET.get("subcategoria", "").strip()
    if not inicio or not fim:
        first, last = _first_last_day_month(today)
        if not inicio:
            inicio = first.strftime("%Y-%m-%d")
        if not fim:
            fim = last.strftime("%Y-%m-%d")

    qs = models.ContasPagar.objects.select_related("cdFornecedor", "cdCategoria", "cdSubcategoria").all()
    if fornecedor_id:
        qs = qs.filter(cdFornecedor_id=fornecedor_id)
    if categoria_id:
        qs = qs.filter(cdCategoria_id=categoria_id)
    if subcategoria_id:
        qs = qs.filter(cdSubcategoria_id=subcategoria_id)
    if inicio:
        try:
            inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
            qs = qs.filter(dtVencimento__gte=inicio_dt)
        except ValueError:
            pass
    if fim:
        try:
            fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
            qs = qs.filter(dtVencimento__lte=fim_dt)
        except ValueError:
            pass
    if status:
        if status == "ATRASADO":
            qs = qs.filter(dtVencimento__lt=today).exclude(status__in=["PAGO", "CANCELADO"])
        else:
            qs = qs.filter(status=status)

    qs = qs.order_by("dtVencimento", "id")
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page"))
    edit_forms = {obj.id: forms.ContasPagarForm(instance=obj) for obj in page}
    for obj in page:
        if obj.status == "PAGO":
            display_status = "PAGO"
        elif obj.status == "CANCELADO":
            display_status = "CANCELADO"
        elif obj.dtVencimento and obj.dtVencimento < today:
            display_status = "ATRASADO"
        else:
            display_status = "AGENDADO"
        obj.display_status = display_status

    query_params = request.GET.copy()
    if query_params.get("page"):
        query_params.pop("page")
    context = {
        "title": "Contas a Pagar",
        "page": page,
        "form": forms.ContasPagarForm(),
        "edit_forms": edit_forms,
        "fornecedores": models.Fornecedor.objects.all(),
        "categorias": models.Categoria.objects.all(),
        "subcategorias": models.Subcategoria.objects.all(),
        "filtros": {
            "inicio": inicio,
            "fim": fim,
            "status": status,
            "fornecedor": fornecedor_id,
            "categoria": categoria_id,
            "subcategoria": subcategoria_id,
        },
        "today": today.strftime("%Y-%m-%d"),
        "pagination_query": query_params.urlencode(),
        "breadcrumbs": [("Home", reverse("dashboard")), ("Contas a Pagar", "#")],
        "active_menu": "financeiro",
    }
    return render(request, "financeiro/contas_pagar_list.html", context)


def _filtrar_contas_pagar(request):
    today = timezone.now().date()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    status = request.GET.get("status", "").strip()
    fornecedor_id = request.GET.get("fornecedor", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    subcategoria_id = request.GET.get("subcategoria", "").strip()

    qs = models.ContasPagar.objects.select_related("cdFornecedor", "cdCategoria", "cdSubcategoria").all()
    if fornecedor_id:
        qs = qs.filter(cdFornecedor_id=fornecedor_id)
    if categoria_id:
        qs = qs.filter(cdCategoria_id=categoria_id)
    if subcategoria_id:
        qs = qs.filter(cdSubcategoria_id=subcategoria_id)
    if inicio:
        try:
            inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
            qs = qs.filter(dtVencimento__gte=inicio_dt)
        except ValueError:
            pass
    if fim:
        try:
            fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
            qs = qs.filter(dtVencimento__lte=fim_dt)
        except ValueError:
            pass
    if status:
        if status == "ATRASADO":
            qs = qs.filter(dtVencimento__lt=today).exclude(status__in=["PAGO", "CANCELADO"])
        else:
            qs = qs.filter(status=status)
    return qs.order_by("dtVencimento", "id")


@login_required
def conta_bancaria_view(request):
    today = timezone.now().date()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    conta_id = request.GET.get("conta", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    if not inicio or not fim:
        first, last = _first_last_day_month(today)
        if not inicio:
            inicio = first.strftime("%Y-%m-%d")
        if not fim:
            fim = last.strftime("%Y-%m-%d")

    contas = models.ContaBancaria.objects.filter(ativo=True).order_by("banco")
    conta_selecionada = contas.filter(pk=conta_id).first() if conta_id else contas.first()
    movimentos_qs = models.MovimentoConta.objects.select_related("conta").all()
    if conta_selecionada:
        movimentos_qs = movimentos_qs.filter(conta=conta_selecionada)
    if tipo:
        movimentos_qs = movimentos_qs.filter(tipo=tipo)
    if inicio:
        try:
            inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
            movimentos_qs = movimentos_qs.filter(data__gte=inicio_dt)
        except ValueError:
            inicio_dt = None
    else:
        inicio_dt = None
    if fim:
        try:
            fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
            movimentos_qs = movimentos_qs.filter(data__lte=fim_dt)
        except ValueError:
            fim_dt = None
    else:
        fim_dt = None
    movimentos = movimentos_qs.order_by("-data", "-id")
    total_entrada = movimentos_qs.filter(tipo="ENTRADA").aggregate(total=Sum("valor"))["total"] or 0
    total_saida = movimentos_qs.filter(tipo="SAIDA").aggregate(total=Sum("valor"))["total"] or 0
    saldo_inicial = conta_selecionada.saldo_inicial if conta_selecionada else 0
    saldo_atual = saldo_inicial + total_entrada - total_saida

    context = {
        "title": "Conta Bancaria",
        "contas": contas,
        "conta_selecionada": conta_selecionada,
        "movimentos": movimentos,
        "form_conta": forms.ContaBancariaForm(),
        "form_movimento": forms.MovimentoContaForm(),
        "filtros": {"inicio": inicio, "fim": fim, "conta": conta_id, "tipo": tipo},
        "total_entrada": total_entrada,
        "total_saida": total_saida,
        "saldo_inicial": saldo_inicial,
        "saldo_atual": saldo_atual,
        "today": today.strftime("%Y-%m-%d"),
        "breadcrumbs": [("Home", reverse("dashboard")), ("Conta Bancaria", "#")],
        "active_menu": "financeiro",
    }
    return render(request, "financeiro/conta_bancaria.html", context)


@login_required
def criar_conta_bancaria(request):
    if request.method != "POST":
        return redirect("conta_bancaria")
    data = request.POST.copy()
    data = _inject_cd_value(models.ContaBancaria, data)
    form = forms.ContaBancariaForm(data)
    if form.is_valid():
        form.save()
        messages.success(request, "Conta bancaria criada.")
    else:
        messages.error(request, "Verifique os erros.")
    return redirect("conta_bancaria")


@login_required
def criar_movimento_conta(request):
    if request.method != "POST":
        return redirect("conta_bancaria")
    data = request.POST.copy()
    form = forms.MovimentoContaForm(data, files=request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Lancamento registrado.")
    else:
        messages.error(request, "Verifique os erros.")
    return redirect("conta_bancaria")


@login_required
def dre_view(request):
    today = timezone.now().date()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    if not inicio or not fim:
        first, last = _first_last_day_month(today)
        if not inicio:
            inicio = first.strftime("%Y-%m-%d")
        if not fim:
            fim = last.strftime("%Y-%m-%d")
    try:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
    except ValueError:
        inicio_dt = today.replace(day=1)
    try:
        fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
    except ValueError:
        fim_dt = today

    receitas = models.ContasReceber.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))
    despesas = models.ContasPagar.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))
    total_receitas = receitas.aggregate(total=Sum("valor"))["total"] or 0
    total_despesas = despesas.aggregate(total=Sum("valor"))["total"] or 0
    resultado = total_receitas - total_despesas
    status_label = "Lucro" if resultado >= 0 else "Prejuizo"

    context = {
        "title": "DRE",
        "inicio": inicio,
        "fim": fim,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado": resultado,
        "status_label": status_label,
        "receitas": receitas.order_by("-dtPagamento")[:10],
        "despesas": despesas.order_by("-dtPagamento")[:10],
        "breadcrumbs": [("Home", reverse("dashboard")), ("DRE", "#")],
        "active_menu": "financeiro",
    }
    return render(request, "financeiro/dre.html", context)


@login_required
def dre_relatorio(request):
    today = timezone.now().date()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    if not inicio or not fim:
        first, last = _first_last_day_month(today)
        if not inicio:
            inicio = first.strftime("%Y-%m-%d")
        if not fim:
            fim = last.strftime("%Y-%m-%d")
    try:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
    except ValueError:
        inicio_dt = today.replace(day=1)
    try:
        fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
    except ValueError:
        fim_dt = today

    prev_month_last = inicio_dt.replace(day=1) - timedelta(days=1)
    movimentos_prev = models.MovimentoConta.objects.filter(data__lte=prev_month_last)
    saldo_inicial_total = models.ContaBancaria.objects.filter(ativo=True).aggregate(total=Sum("saldo_inicial"))["total"] or 0
    entradas_prev = movimentos_prev.filter(tipo="ENTRADA").aggregate(total=Sum("valor"))["total"] or 0
    saidas_prev = movimentos_prev.filter(tipo="SAIDA").aggregate(total=Sum("valor"))["total"] or 0
    saldo_bancario_anterior = saldo_inicial_total + entradas_prev - saidas_prev

    receitas_qs = models.ContasReceber.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))
    despesas_qs = models.ContasPagar.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))

    receita_bruta = receitas_qs.aggregate(total=Sum("valor"))["total"] or 0
    deducoes = 0
    receita_liquida = receita_bruta - deducoes
    custo_direto = 0
    lucro_bruto = receita_liquida - custo_direto
    despesas_operacionais = despesas_qs.aggregate(total=Sum("valor"))["total"] or 0
    resultado_final = lucro_bruto - despesas_operacionais
    saldo_bancario_final = saldo_bancario_anterior + receita_bruta - despesas_operacionais

    receitas_por_plano = (
        receitas_qs.values("contrato__cdPlano__dsPlano")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    receitas_por_categoria = (
        receitas_qs.values("contrato__cdPlano__categoria_receita__dsCategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    receitas_por_subcategoria = (
        receitas_qs.values("contrato__cdPlano__subcategoria_receita__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_categoria = (
        despesas_qs.values("cdCategoria__dsCategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_subcategoria = (
        despesas_qs.values("cdSubcategoria__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_subcategoria = (
        despesas_qs.values("cdSubcategoria__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_subcategoria = (
        despesas_qs.values("cdSubcategoria__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_subcategoria = (
        despesas_qs.values("cdSubcategoria__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_subcategoria = (
        despesas_qs.values("cdSubcategoria__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_subcategoria = (
        despesas_qs.values("cdSubcategoria__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    receitas_labels = [item["contrato__cdPlano__dsPlano"] or "Sem plano" for item in receitas_por_plano]
    receitas_values = [float(item["total"] or 0) for item in receitas_por_plano]
    receitas_cat_labels = [item["contrato__cdPlano__categoria_receita__dsCategoria"] or "Sem categoria" for item in receitas_por_categoria]
    receitas_cat_values = [float(item["total"] or 0) for item in receitas_por_categoria]
    receitas_sub_labels = [item["contrato__cdPlano__subcategoria_receita__dsSubcategoria"] or "Sem subcategoria" for item in receitas_por_subcategoria]
    receitas_sub_values = [float(item["total"] or 0) for item in receitas_por_subcategoria]
    despesas_labels = [item["cdCategoria__dsCategoria"] or "Sem categoria" for item in despesas_por_categoria]
    despesas_values = [float(item["total"] or 0) for item in despesas_por_categoria]
    despesas_sub_labels = [item["cdSubcategoria__dsSubcategoria"] or "Sem subcategoria" for item in despesas_por_subcategoria]
    despesas_sub_values = [float(item["total"] or 0) for item in despesas_por_subcategoria]

    context = {
        "inicio": inicio,
        "fim": fim,
        "receita_bruta": receita_bruta,
        "deducoes": deducoes,
        "receita_liquida": receita_liquida,
        "custo_direto": custo_direto,
        "lucro_bruto": lucro_bruto,
        "despesas_operacionais": despesas_operacionais,
        "resultado_final": resultado_final,
        "resultado_label": "Lucro" if resultado_final >= 0 else "Prejuizo",
        "saldo_bancario_anterior": saldo_bancario_anterior,
        "saldo_bancario_final": saldo_bancario_final,
        "receitas_por_plano": receitas_por_plano,
        "receitas_por_categoria": receitas_por_categoria,
        "receitas_por_subcategoria": receitas_por_subcategoria,
        "despesas_por_categoria": despesas_por_categoria,
        "despesas_por_subcategoria": despesas_por_subcategoria,
        "chart_receitas_labels": json.dumps(receitas_labels),
        "chart_receitas_values": json.dumps(receitas_values),
        "chart_receitas_cat_labels": json.dumps(receitas_cat_labels),
        "chart_receitas_cat_values": json.dumps(receitas_cat_values),
        "chart_receitas_sub_labels": json.dumps(receitas_sub_labels),
        "chart_receitas_sub_values": json.dumps(receitas_sub_values),
        "chart_despesas_labels": json.dumps(despesas_labels),
        "chart_despesas_values": json.dumps(despesas_values),
        "chart_despesas_sub_labels": json.dumps(despesas_sub_labels),
        "chart_despesas_sub_values": json.dumps(despesas_sub_values),
        "breadcrumbs": [("Home", reverse("dashboard")), ("DRE", reverse("dre_view")), ("Relatorio", "#")],
        "active_menu": "financeiro",
    }
    return render(request, "financeiro/dre_relatorio.html", context)


@login_required
def exportar_dre_excel(request):
    today = timezone.now().date()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    if not inicio or not fim:
        first, last = _first_last_day_month(today)
        if not inicio:
            inicio = first.strftime("%Y-%m-%d")
        if not fim:
            fim = last.strftime("%Y-%m-%d")
    try:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
    except ValueError:
        inicio_dt = today.replace(day=1)
    try:
        fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
    except ValueError:
        fim_dt = today

    receitas_qs = models.ContasReceber.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))
    despesas_qs = models.ContasPagar.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))
    receita_bruta = receitas_qs.aggregate(total=Sum("valor"))["total"] or 0
    deducoes = 0
    receita_liquida = receita_bruta - deducoes
    custo_direto = 0
    lucro_bruto = receita_liquida - custo_direto
    despesas_operacionais = despesas_qs.aggregate(total=Sum("valor"))["total"] or 0
    resultado_final = lucro_bruto - despesas_operacionais

    receitas_por_plano = (
        receitas_qs.values("contrato__cdPlano__dsPlano")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    receitas_por_categoria = (
        receitas_qs.values("contrato__cdPlano__categoria_receita__dsCategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_categoria = (
        despesas_qs.values("cdCategoria__dsCategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo"
    ws.append(["Periodo inicio", inicio])
    ws.append(["Periodo fim", fim])
    ws.append(["Receita bruta", float(receita_bruta)])
    ws.append(["Deducoes", float(deducoes)])
    ws.append(["Receita liquida", float(receita_liquida)])
    ws.append(["Custo direto", float(custo_direto)])
    ws.append(["Lucro bruto", float(lucro_bruto)])
    ws.append(["Despesas operacionais", float(despesas_operacionais)])
    ws.append(["Resultado final", float(resultado_final)])

    ws_receitas = wb.create_sheet("Receitas por plano")
    ws_receitas.append(["Plano", "Total"])
    for item in receitas_por_plano:
        ws_receitas.append([item["contrato__cdPlano__dsPlano"] or "Sem plano", float(item["total"] or 0)])

    ws_receitas_cat = wb.create_sheet("Receitas por categoria")
    ws_receitas_cat.append(["Categoria", "Total"])
    for item in receitas_por_categoria:
        ws_receitas_cat.append([item["contrato__cdPlano__categoria_receita__dsCategoria"] or "Sem categoria", float(item["total"] or 0)])

    ws_receitas_sub = wb.create_sheet("Receitas por subcategoria")
    ws_receitas_sub.append(["Subcategoria", "Total"])
    for item in receitas_por_subcategoria:
        ws_receitas_sub.append([item["contrato__cdPlano__subcategoria_receita__dsSubcategoria"] or "Sem subcategoria", float(item["total"] or 0)])

    ws_despesas = wb.create_sheet("Despesas por categoria")
    ws_despesas.append(["Categoria", "Total"])
    for item in despesas_por_categoria:
        ws_despesas.append([item["cdCategoria__dsCategoria"] or "Sem categoria", float(item["total"] or 0)])

    ws_despesas_sub = wb.create_sheet("Despesas por subcategoria")
    ws_despesas_sub.append(["Subcategoria", "Total"])
    for item in despesas_por_subcategoria:
        ws_despesas_sub.append([item["cdSubcategoria__dsSubcategoria"] or "Sem subcategoria", float(item["total"] or 0)])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="dre-completo.xlsx"'
    return response


@login_required
def exportar_dre_pdf(request):
    today = timezone.now().date()
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    if not inicio or not fim:
        first, last = _first_last_day_month(today)
        if not inicio:
            inicio = first.strftime("%Y-%m-%d")
        if not fim:
            fim = last.strftime("%Y-%m-%d")
    try:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
    except ValueError:
        inicio_dt = today.replace(day=1)
    try:
        fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
    except ValueError:
        fim_dt = today

    receitas_qs = models.ContasReceber.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))
    despesas_qs = models.ContasPagar.objects.filter(status="PAGO", dtPagamento__range=(inicio_dt, fim_dt))
    receita_bruta = receitas_qs.aggregate(total=Sum("valor"))["total"] or 0
    deducoes = 0
    receita_liquida = receita_bruta - deducoes
    custo_direto = 0
    lucro_bruto = receita_liquida - custo_direto
    despesas_operacionais = despesas_qs.aggregate(total=Sum("valor"))["total"] or 0
    resultado_final = lucro_bruto - despesas_operacionais

    receitas_por_plano = (
        receitas_qs.values("contrato__cdPlano__dsPlano")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    receitas_por_categoria = (
        receitas_qs.values("contrato__cdPlano__categoria_receita__dsCategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_categoria = (
        despesas_qs.values("cdCategoria__dsCategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )
    despesas_por_subcategoria = (
        despesas_qs.values("cdSubcategoria__dsSubcategoria")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="DRE Completo")
    styles = getSampleStyleSheet()
    title = Paragraph("DRE Completo", styles["Title"])
    subtitle = Paragraph(f"Periodo {inicio_dt.strftime('%d/%m/%Y')} a {fim_dt.strftime('%d/%m/%Y')}", styles["Normal"])
    resumo = [
        ["Receita bruta", f"R$ {receita_bruta}"],
        ["Deducoes", f"R$ {deducoes}"],
        ["Receita liquida", f"R$ {receita_liquida}"],
        ["Custo direto", f"R$ {custo_direto}"],
        ["Lucro bruto", f"R$ {lucro_bruto}"],
        ["Despesas operacionais", f"R$ {despesas_operacionais}"],
        ["Resultado final", f"R$ {resultado_final}"],
    ]
    resumo_table = Table(resumo, colWidths=[220, 160])
    resumo_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4d4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    receitas_table = [["Plano", "Total"]]
    for item in receitas_por_plano:
        receitas_table.append([item["contrato__cdPlano__dsPlano"] or "Sem plano", f"R$ {item['total']}"])
    receitas_table = Table(receitas_table, colWidths=[260, 120])
    receitas_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    receitas_cat_table = [["Categoria", "Total"]]
    for item in receitas_por_categoria:
        receitas_cat_table.append([item["contrato__cdPlano__categoria_receita__dsCategoria"] or "Sem categoria", f"R$ {item['total']}"])
    receitas_cat_table = Table(receitas_cat_table, colWidths=[260, 120])
    receitas_cat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcfce7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    despesas_table = [["Categoria", "Total"]]
    for item in despesas_por_categoria:
        despesas_table.append([item["cdCategoria__dsCategoria"] or "Sem categoria", f"R$ {item['total']}"])
    despesas_table = Table(despesas_table, colWidths=[260, 120])
    despesas_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    elements = [
        title,
        subtitle,
        Spacer(1, 12),
        resumo_table,
        Spacer(1, 16),
        Paragraph("Receitas por plano", styles["Heading3"]),
        receitas_table,
        Spacer(1, 16),
        Paragraph("Receitas por categoria", styles["Heading3"]),
        receitas_cat_table,
        Spacer(1, 16),
        Paragraph("Receitas por subcategoria", styles["Heading3"]),
        Table(
            [["Subcategoria", "Total"]] + [
                [item["contrato__cdPlano__subcategoria_receita__dsSubcategoria"] or "Sem subcategoria", f"R$ {item['total']}"]
                for item in receitas_por_subcategoria
            ],
            colWidths=[260, 120],
        ),
        Spacer(1, 16),
        Paragraph("Despesas por categoria", styles["Heading3"]),
        despesas_table,
        Spacer(1, 16),
        Paragraph("Despesas por subcategoria", styles["Heading3"]),
        Table(
            [["Subcategoria", "Total"]] + [
                [item["cdSubcategoria__dsSubcategoria"] or "Sem subcategoria", f"R$ {item['total']}"]
                for item in despesas_por_subcategoria
            ],
            colWidths=[260, 120],
        ),
    ]
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="dre-completo.pdf"'
    return response

@login_required
def exportar_contas_pagar_excel(request):
    qs = _filtrar_contas_pagar(request)
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Contas a Pagar"
    ws.append(["Fornecedor", "Categoria", "Subcategoria", "Vencimento", "Pagamento", "Valor", "Status"])
    for f in qs:
        if f.status == "PAGO":
            display_status = "PAGO"
        elif f.status == "CANCELADO":
            display_status = "CANCELADO"
        elif f.dtVencimento and f.dtVencimento < timezone.now().date():
            display_status = "ATRASADO"
        else:
            display_status = "AGENDADO"
        ws.append(
            [
                str(f.cdFornecedor),
                str(f.cdCategoria),
                str(f.cdSubcategoria),
                f.dtVencimento.strftime("%d/%m/%Y") if f.dtVencimento else "",
                f.dtPagamento.strftime("%d/%m/%Y") if f.dtPagamento else "",
                float(f.valor),
                display_status,
            ]
        )
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="contas-a-pagar.xlsx"'
    return response


@login_required
def exportar_contas_pagar_pdf(request):
    qs = _filtrar_contas_pagar(request)
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Contas a Pagar")
    styles = getSampleStyleSheet()
    title = Paragraph("Contas a Pagar", styles["Title"])
    data = [["Fornecedor", "Categoria", "Subcategoria", "Vencimento", "Pagamento", "Valor", "Status"]]
    for f in qs:
        if f.status == "PAGO":
            display_status = "PAGO"
        elif f.status == "CANCELADO":
            display_status = "CANCELADO"
        elif f.dtVencimento and f.dtVencimento < timezone.now().date():
            display_status = "ATRASADO"
        else:
            display_status = "AGENDADO"
        data.append(
            [
                str(f.cdFornecedor),
                str(f.cdCategoria),
                str(f.cdSubcategoria),
                f.dtVencimento.strftime("%d/%m/%Y") if f.dtVencimento else "-",
                f.dtPagamento.strftime("%d/%m/%Y") if f.dtPagamento else "-",
                f"R$ {f.valor}",
                display_status,
            ]
        )
    table = Table(data, repeatRows=1, colWidths=[90, 80, 90, 70, 70, 60, 70])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4d4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fb")]),
            ]
        )
    )
    elements = [title, Spacer(1, 12), table]
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="contas-a-pagar.pdf"'
    return response


@login_required
def aulas_list(request):
    qs = models.AulaSessao.objects.select_related("unidade", "tipoServico", "profissional")
    week_str = request.GET.get("week", "").strip()
    profissional_id = request.GET.get("profissional", "").strip()
    view_mode = request.GET.get("view", "week").strip().lower()
    if view_mode == "list":
        view_mode = "week"
    if view_mode not in {"week", "day", "month"}:
        view_mode = "week"
    try:
        ref_date = datetime.strptime(week_str, "%Y-%m-%d").date() if week_str else date.today()
    except ValueError:
        ref_date = date.today()

    if view_mode == "day":
        week_start = ref_date
        week_end = ref_date
        days = [ref_date]
        columns = 1
    elif view_mode == "month":
        first = ref_date.replace(day=1)
        if first.month == 12:
            last = date(first.year + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(first.year, first.month + 1, 1) - timedelta(days=1)
        week_start = first
        week_end = last
        leading = first.weekday()
        days = [None] * leading + [first + timedelta(days=i) for i in range((last - first).days + 1)]
        columns = 7
    else:
        week_start = ref_date - timedelta(days=ref_date.weekday())
        week_end = week_start + timedelta(days=5)
        days = [week_start + timedelta(days=i) for i in range(6)]
        columns = 6

    qs = qs.filter(data__range=(week_start, week_end))
    if profissional_id:
        qs = qs.filter(profissional_id=profissional_id)

    aulas = list(qs.order_by("data", "horaInicio"))
    aula_ids = [aula.id for aula in aulas]
    reservas = (
        models.Reserva.objects.filter(aulaSessao_id__in=aula_ids)
        .select_related("aluno", "aulaSessao", "aulaSessao__profissional")
        .order_by("aulaSessao__data", "aulaSessao__horaInicio")
    )
    reservas_by_aula = {}
    for reserva in reservas:
        reservas_by_aula.setdefault(reserva.aulaSessao_id, []).append(reserva)

    aulas_by_day = {day: [] for day in days if day}
    for aula in aulas:
        aulas_by_day.setdefault(aula.data, []).append(aula)
    for aulas in aulas_by_day.values():
        aulas.sort(key=lambda x: x.horaInicio)

    weekday_labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    week_cards = []
    for dia in days:
        if not dia:
            week_cards.append({"is_placeholder": True})
            continue
        week_cards.append(
            {
                "date": dia,
                "label": weekday_labels[dia.weekday()],
                "number": dia.day,
                "is_today": dia == date.today(),
                "aulas": aulas_by_day.get(dia, []),
            }
        )

    prof_chips = []
    for prof in models.Profissional.objects.all():
        parts = [p for p in prof.profissional.split() if p]
        initials = "".join([p[0] for p in parts[:2]]).upper()
        prof_chips.append({"name": prof.profissional, "initials": initials})

    meses = [
        "Janeiro",
        "Fevereiro",
        "Marco",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    month_label = f"{meses[week_start.month - 1]} {week_start.year}"

    context = {
        "title": "Aulas",
        "week_cards": week_cards,
        "week_start": week_start,
        "week_end": week_end,
        "prev_week": week_start - timedelta(days=7),
        "next_week": week_start + timedelta(days=7),
        "month_label": month_label,
        "view_mode": view_mode,
        "columns": columns,
        "form": forms.AulaSessaoForm(),
        "profissionais": models.Profissional.objects.all(),
        "unidades": models.Unidade.objects.all(),
        "prof_chips": prof_chips[:5],
        "reservas_by_aula": reservas_by_aula,
        "modelos_evolucao": models.ModeloEvolucao.objects.filter(ativo=True).order_by("titulo"),
        "breadcrumbs": [("Home", reverse("dashboard")), ("Aulas", "#")],
        "active_menu": "agenda",
    }
    return render(request, "agenda/aulas_list.html", context)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _build_period_range(target: date | None, periodo: str | None) -> tuple[date, date]:
    base = target or date.today()
    if periodo == "amanha":
        start = base + timedelta(days=1)
        return start, start
    if periodo == "semana":
        start = base - timedelta(days=base.weekday())
        end = start + timedelta(days=6)
        return start, end
    return base, base


def _map_status(reserva_status: str, inicio: datetime, fim: datetime) -> str:
    status_map = {
        "RESERVADA": "aguardando_chegar",
        "PENDENTE": "aguardando_chegar",
        "CONCLUIDA": "finalizada",
        "FALTOU_AVISOU": "faltou",
        "FALTOU_SEM_AVISAR": "faltou",
        "CANCELADA": "remarcada",
    }
    mapped = status_map.get(reserva_status, "aguardando_chegar")
    if mapped == "aguardando_chegar":
        now = timezone.localtime()
        if inicio <= now <= fim:
            return "em_aula"
    return mapped


@login_required
def aulas_operacao_api(request):
    target = _parse_date(request.GET.get("data", "").strip())
    periodo = request.GET.get("periodo", "hoje").strip()
    start_date, end_date = _build_period_range(target, periodo)

    unidade_id = request.GET.get("unidade_id") or None
    profissional_id = request.GET.get("profissional_id") or None
    status_filter = request.GET.get("status_aula") or None
    query = (request.GET.get("q") or "").strip()

    contrato_qs = (
        models.Contrato.objects.filter(
            cdAluno=OuterRef("aluno_id"),
            dtInicioContrato__lte=OuterRef("aulaSessao__data"),
            dtFimContrato__gte=OuterRef("aulaSessao__data"),
        )
        .order_by("-dtFimContrato", "-id")
    )

    telefone_qs = models.TelefoneAluno.objects.filter(cdAluno=OuterRef("aluno_id")).order_by("-dtCadastro", "-id")
    evolucao_qs = models.EvolucaoAluno.objects.filter(reserva_id=OuterRef("pk")).order_by("-dtEvolucao", "-id")
    cobranca_exists = Exists(
        models.ContasReceber.objects.filter(
            contrato__cdAluno=OuterRef("aluno_id"),
            status="ABERTO",
        )
    )

    reservas = (
        models.Reserva.objects.select_related(
            "aluno",
            "aulaSessao",
            "aulaSessao__unidade",
            "aulaSessao__profissional",
            "aulaSessao__tipoServico",
        )
        .annotate(
            plano_id=Subquery(contrato_qs.values("cdPlano_id")[:1]),
            plano_descricao=Subquery(contrato_qs.values("cdPlano__dsPlano")[:1]),
            aluno_telefone=Subquery(telefone_qs.values("dsTelefone")[:1]),
            ultima_evolucao=Subquery(evolucao_qs.values("texto")[:1]),
            ultima_evolucao_em=Subquery(evolucao_qs.values("dtEvolucao")[:1]),
            cobranca_pendente=cobranca_exists,
        )
        .filter(aulaSessao__data__range=(start_date, end_date))
    )

    if unidade_id:
        reservas = reservas.filter(aulaSessao__unidade_id=unidade_id)
    if profissional_id:
        reservas = reservas.filter(aulaSessao__profissional_id=profissional_id)
    if query:
        reservas = reservas.filter(
            Q(aluno__dsNome__icontains=query)
            | Q(aluno__dsCPF__icontains=query)
            | Q(aluno__telefones__dsTelefone__icontains=query)
        ).distinct()

    items = []
    for reserva in reservas.order_by("aulaSessao__data", "aulaSessao__horaInicio", "aluno__dsNome"):
        inicio = datetime.combine(reserva.aulaSessao.data, reserva.aulaSessao.horaInicio)
        fim = datetime.combine(reserva.aulaSessao.data, reserva.aulaSessao.horaFim)
        inicio = timezone.make_aware(inicio)
        fim = timezone.make_aware(fim)
        status_calc = _map_status(reserva.status, inicio, fim)
        if status_filter and status_calc != status_filter:
            continue
        items.append(
            {
                "id": reserva.id,
                "aula_sessao_id": reserva.aulaSessao_id,
                "dt_inicio": inicio.isoformat(),
                "dt_fim": fim.isoformat(),
                "unidade_id": reserva.aulaSessao.unidade_id if reserva.aulaSessao else None,
                "unidade": reserva.aulaSessao.unidade.dsUnidade if reserva.aulaSessao and reserva.aulaSessao.unidade else None,
                "sala": None,
                "profissional": {
                    "id": reserva.aulaSessao.profissional_id if reserva.aulaSessao else None,
                    "nome": reserva.aulaSessao.profissional.profissional if reserva.aulaSessao and reserva.aulaSessao.profissional else None,
                },
                "aluno": {
                    "id": reserva.aluno_id,
                    "nome": reserva.aluno.dsNome,
                    "telefone": reserva.aluno_telefone,
                    "avatar_url": reserva.aluno.foto.url if reserva.aluno.foto else None,
                    "ficha_url": reverse("alunos_detail", args=[reserva.aluno_id]),
                },
                "plano": {"id": reserva.plano_id, "descricao": reserva.plano_descricao},
                "status_aula": status_calc,
                "confirmacao": reserva.status != "PENDENTE",
                "flags": {
                    "tem_preliminares": bool(reserva.aluno.termo_aceite_em),
                    "cobranca_pendente": bool(reserva.cobranca_pendente),
                    "observacao_importante": False,
                },
                "ultima_evolucao": {
                    "texto": reserva.ultima_evolucao,
                    "dt_evolucao": reserva.ultima_evolucao_em.isoformat() if reserva.ultima_evolucao_em else None,
                },
            }
        )

    return JsonResponse(
        {
            "data_inicio": start_date.isoformat(),
            "data_fim": end_date.isoformat(),
            "total": len(items),
            "items": items,
        }
    )


def _parse_json_body(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    return request.POST


def _normalize_cpf(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 11:
        return digits, ""
    masked = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return digits, masked


def _parse_totalpass_datetime(payload):
    slot = payload.get("slot") or {}
    date_raw = slot.get("date") or slot.get("start_at") or slot.get("startAt") or ""
    time_raw = slot.get("start_time") or slot.get("startTime") or slot.get("time") or ""

    if not date_raw:
        return None, "Data nao informada no payload."

    try:
        if "T" in date_raw:
            base = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
        else:
            base = datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError:
        return None, "Data invalida no payload."

    if time_raw:
        try:
            time_value = datetime.strptime(time_raw, "%H:%M").time()
            base = datetime.combine(base.date(), time_value)
        except ValueError:
            return None, "Hora invalida no payload."
    elif base.time() == datetime.min.time():
        return None, "Horario nao informado no payload."

    if timezone.is_naive(base):
        base = timezone.make_aware(base)
    return base, ""


def _get_totalpass_config(payload):
    place_id = ""
    place = payload.get("place") or {}
    for key in ["place", "id", "place_id", "uuid"]:
        if place.get(key):
            place_id = place.get(key)
            break
    if place_id:
        cfg = models.TotalpassConfiguracao.objects.filter(place_id=place_id).select_related("unidade").first()
        if cfg:
            return cfg
    unidade_id = getattr(settings, "TOTALPASS_UNIDADE_ID", "") or ""
    if unidade_id:
        return models.TotalpassConfiguracao.objects.filter(unidade_id=unidade_id).select_related("unidade").first()
    return models.TotalpassConfiguracao.objects.select_related("unidade").first()


def _resolve_totalpass_unidade(payload):
    cfg = _get_totalpass_config(payload)
    if cfg and cfg.unidade_id:
        return cfg.unidade
    unidade_id = getattr(settings, "TOTALPASS_UNIDADE_ID", "") or ""
    if unidade_id:
        return models.Unidade.objects.filter(pk=unidade_id).first()
    return models.Unidade.objects.filter(dsUnidade__iexact="Matriz").first() or models.Unidade.objects.filter(dsUnidade__icontains="Matriz").first()


def _resolve_totalpass_tipo_servico(title):
    if not title:
        return None
    return (
        models.TipoServico.objects.filter(dsTipoServico__iexact=title).first()
        or models.TipoServico.objects.filter(dsTipoServico__icontains=title).first()
    )


def _build_totalpass_payload_from_slot(slot):
    if not isinstance(slot, dict):
        return {}
    if slot.get("event") or slot.get("user"):
        if slot.get("slot"):
            return slot
        payload = dict(slot)
        payload["slot"] = slot.get("slot") or {}
        return payload
    event_title = slot.get("event_title") or slot.get("eventTitle") or slot.get("title") or ""
    user_name = slot.get("user_name") or slot.get("userName") or ""
    user_email = slot.get("user_email") or slot.get("userEmail") or ""
    user_doc = slot.get("document_number") or slot.get("documentNumber") or slot.get("userDocument") or ""
    user_phone = slot.get("phone") or slot.get("userPhone") or ""
    place_id = slot.get("place_id") or slot.get("placeId") or ""
    return {
        "event": {"id": slot.get("event_id") or slot.get("eventId") or "", "title": event_title},
        "place": {"place": place_id},
        "user": {
            "name": user_name,
            "email": user_email,
            "phone": user_phone,
            "document_number": user_doc,
            "document_type": "cpf",
        },
        "slot": {
            "id": slot.get("slot_id") or slot.get("id") or "",
            "status": slot.get("status") or slot.get("slot_status") or "",
            "date": slot.get("date") or slot.get("start_at") or slot.get("startAt") or "",
            "start_time": slot.get("start_time") or slot.get("startTime") or slot.get("time") or "",
        },
    }


def _process_totalpass_payload(payload, cfg, event_obj=None):
    event_id = (payload.get("event") or {}).get("id") or ""
    slot_id = (payload.get("slot") or {}).get("id") or ""
    user_document = (payload.get("user") or {}).get("document_number") or ""
    slot_status = (payload.get("slot") or {}).get("status") or ""

    if not event_obj:
        event_obj = models.TotalpassWebhookEvent.objects.create(
            event_id=event_id,
            slot_id=slot_id,
            user_document=user_document,
            status=slot_status,
            payload=payload or {},
        )
    else:
        event_obj.event_id = event_id
        event_obj.slot_id = slot_id
        event_obj.user_document = user_document
        event_obj.status = slot_status
        event_obj.payload = payload or {}
        event_obj.save(update_fields=["event_id", "slot_id", "user_document", "status", "payload"])

    dt_inicio, err = _parse_totalpass_datetime(payload)
    if err:
        event_obj.error = err
        event_obj.save(update_fields=["error"])
        return None, err

    if cfg and cfg.somente_dia:
        if dt_inicio.date() != timezone.localdate():
            event_obj.error = "Fora do dia atual."
            event_obj.save(update_fields=["error"])
            return None, "Fora do dia atual."

    unidade = cfg.unidade if cfg and cfg.unidade_id else _resolve_totalpass_unidade(payload)
    if not unidade:
        event_obj.error = "Unidade Matriz nao encontrada."
        event_obj.save(update_fields=["error"])
        return None, event_obj.error

    tipo_servico = _resolve_totalpass_tipo_servico((payload.get("event") or {}).get("title"))
    if not tipo_servico:
        event_obj.error = "Tipo de servico nao encontrado."
        event_obj.save(update_fields=["error"])
        return None, event_obj.error

    cpf_digits, cpf_mask = _normalize_cpf(user_document)
    aluno = (
        models.Aluno.objects.filter(dsCPF=cpf_mask).first()
        or models.Aluno.objects.filter(dsCPF=cpf_digits).first()
    )
    if not aluno and cfg and cfg.criar_aluno_automatico is False:
        event_obj.error = "Aluno nao encontrado pelo CPF."
        event_obj.save(update_fields=["error"])
        return None, event_obj.error
    if not aluno:
        nome = (payload.get("user") or {}).get("name") or "Aluno TotalPass"
        email = (payload.get("user") or {}).get("email") or ""
        telefone = (payload.get("user") or {}).get("phone") or ""
        max_cd = models.Aluno.objects.order_by("-cdAluno").values_list("cdAluno", flat=True).first() or 0
        aluno = models.Aluno.objects.create(
            cdAluno=max_cd + 1,
            dsNome=nome,
            dsCPF=cpf_mask or cpf_digits,
            dsEmail=email,
            cdUnidade=unidade,
        )
        if telefone:
            max_tel = models.TelefoneAluno.objects.order_by("-cdTelefone").values_list("cdTelefone", flat=True).first() or 0
            models.TelefoneAluno.objects.create(cdTelefone=max_tel + 1, cdAluno=aluno, dsTelefone=telefone)

    duracao_min = unidade.duracao_aula_minutos or 50
    hora_fim = (dt_inicio + timedelta(minutes=duracao_min)).time()

    aula, _ = models.AulaSessao.objects.get_or_create(
        unidade=unidade,
        tipoServico=tipo_servico,
        profissional=None,
        data=dt_inicio.date(),
        horaInicio=dt_inicio.time().replace(second=0, microsecond=0),
        horaFim=hora_fim,
        defaults={"capacidade": unidade.capacidade},
    )

    status_lower = str(slot_status).lower()
    if status_lower in ["canceled", "cancelled", "inactive"]:
        reserva = models.Reserva.objects.filter(aluno=aluno, aulaSessao=aula).first()
        if reserva:
            reserva.status = "CANCELADA"
            reserva.save(update_fields=["status"])
        event_obj.processed_at = timezone.now()
        event_obj.save(update_fields=["processed_at"])
        return reserva, ""

    capacidade = aula.capacidade_efetiva()
    total = models.Reserva.objects.filter(aulaSessao=aula, status="RESERVADA").count()
    if capacidade and total >= capacidade:
        event_obj.error = "Capacidade excedida."
        event_obj.save(update_fields=["error"])
        return None, event_obj.error

    reserva, created = models.Reserva.objects.get_or_create(
        aluno=aluno,
        aulaSessao=aula,
        defaults={"status": "RESERVADA"},
    )
    if not created and reserva.status != "RESERVADA":
        reserva.status = "RESERVADA"
        reserva.save(update_fields=["status"])

    event_obj.processed_at = timezone.now()
    event_obj.save(update_fields=["processed_at"])
    return reserva, ""


@login_required
def aula_evolucao_api(request, reserva_id):
    reserva = get_object_or_404(models.Reserva, pk=reserva_id)
    if request.method == "POST":
        payload = _parse_json_body(request)
        texto = (payload.get("texto") or "").strip()
        profissional_id = payload.get("profissional_id")
        finalizar = bool(payload.get("finalizar"))
        if not texto:
            return JsonResponse({"error": "Texto obrigatorio."}, status=400)

        profissional = None
        if profissional_id:
            profissional = models.Profissional.objects.filter(pk=profissional_id).first()
        if not profissional:
            profissional = reserva.aulaSessao.profissional if reserva.aulaSessao else None
        if not profissional:
            return JsonResponse({"error": "Profissional invalido."}, status=400)

        evolucao = models.EvolucaoAluno.objects.create(
            reserva=reserva,
            profissional=profissional,
            texto=texto,
            dtEvolucao=timezone.now(),
        )
        if finalizar:
            reserva.status = "CONCLUIDA"
            reserva.save(update_fields=["status"])
        return JsonResponse(
            {
                "id": evolucao.id,
                "reserva_id": reserva.id,
                "texto": evolucao.texto,
                "dt_evolucao": evolucao.dtEvolucao.isoformat(),
            }
        )

    evolucoes = (
        models.EvolucaoAluno.objects.filter(reserva__aluno=reserva.aluno)
        .select_related("profissional", "reserva", "reserva__aulaSessao")
        .order_by("-dtEvolucao")[:20]
    )
    return JsonResponse(
        {
            "items": [
                {
                    "id": e.id,
                    "texto": e.texto,
                    "dt_evolucao": e.dtEvolucao.isoformat(),
                    "profissional": e.profissional.profissional if e.profissional else None,
                    "reserva_id": e.reserva_id,
                    "data": e.reserva.aulaSessao.data.isoformat() if e.reserva and e.reserva.aulaSessao else None,
                }
                for e in evolucoes
            ]
        }
    )


@login_required
def aula_avaliacoes_api(request, reserva_id):
    reserva = get_object_or_404(models.Reserva, pk=reserva_id)
    if request.method == "POST":
        payload = _parse_json_body(request)
        texto = (payload.get("texto") or "").strip()
        profissional_id = payload.get("profissional_id")
        acao = (payload.get("acao") or "create").lower()
        avaliacao_id = payload.get("avaliacao_id")

        if acao in ["update", "delete"]:
            avaliacao = (
                models.AvaliacaoAluno.objects.filter(
                    pk=avaliacao_id,
                    reserva__aluno=reserva.aluno,
                )
                .select_related("profissional")
                .first()
            )
            if not avaliacao:
                return JsonResponse({"error": "Avaliacao nao encontrada."}, status=404)
            if acao == "delete":
                avaliacao.delete()
                return JsonResponse({"ok": True})
            if not texto:
                return JsonResponse({"error": "Texto obrigatorio."}, status=400)
            avaliacao.texto = texto
            avaliacao.save(update_fields=["texto"])
            return JsonResponse(
                {
                    "id": avaliacao.id,
                    "reserva_id": avaliacao.reserva_id,
                    "texto": avaliacao.texto,
                    "dt_avaliacao": avaliacao.dtAvaliacao.isoformat(),
                    "profissional": avaliacao.profissional.profissional if avaliacao.profissional else None,
                }
            )
        if not texto:
            return JsonResponse({"error": "Texto obrigatorio."}, status=400)

        profissional = None
        if profissional_id:
            profissional = models.Profissional.objects.filter(pk=profissional_id).first()
        if not profissional:
            profissional = reserva.aulaSessao.profissional if reserva.aulaSessao else None
        if not profissional:
            return JsonResponse({"error": "Profissional invalido."}, status=400)

        avaliacao = models.AvaliacaoAluno.objects.create(
            reserva=reserva,
            profissional=profissional,
            texto=texto,
            dtAvaliacao=timezone.now(),
        )
        return JsonResponse(
            {
                "id": avaliacao.id,
                "reserva_id": reserva.id,
                "texto": avaliacao.texto,
                "dt_avaliacao": avaliacao.dtAvaliacao.isoformat(),
            }
        )

    avaliacoes = (
        models.AvaliacaoAluno.objects.filter(reserva__aluno=reserva.aluno)
        .select_related("profissional", "reserva", "reserva__aulaSessao")
        .order_by("-dtAvaliacao")[:20]
    )
    return JsonResponse(
        {
            "items": [
                {
                    "id": a.id,
                    "texto": a.texto,
                    "dt_avaliacao": a.dtAvaliacao.isoformat(),
                    "profissional": a.profissional.profissional if a.profissional else None,
                    "reserva_id": a.reserva_id,
                    "data": a.reserva.aulaSessao.data.isoformat() if a.reserva and a.reserva.aulaSessao else None,
                }
                for a in avaliacoes
            ]
        }
    )


@login_required
def aula_cobranca_api(request, reserva_id):
    reserva = get_object_or_404(models.Reserva, pk=reserva_id)
    contas = (
        models.ContasReceber.objects.filter(contrato__cdAluno=reserva.aluno)
        .select_related("contrato")
        .order_by("-dtVencimento", "-id")
    )
    items = []
    for conta in contas:
        items.append(
            {
                "id": conta.id,
                "competencia": conta.competencia,
                "dt_vencimento": conta.dtVencimento.isoformat() if conta.dtVencimento else None,
                "dt_pagamento": conta.dtPagamento.isoformat() if conta.dtPagamento else None,
                "status": conta.status,
                "valor": float(conta.valor),
                "contrato": conta.contrato.cdContrato if conta.contrato else None,
                "baixar_url": reverse("contas_receber_baixar", args=[conta.id]),
                "recibo_url": reverse("contas_receber_recibo", args=[conta.id]),
                "excluir_url": reverse("contas_receber_excluir", args=[conta.id]),
            }
        )
    return JsonResponse({"items": items})


@login_required
def aula_historico_api(request, reserva_id):
    reserva = get_object_or_404(models.Reserva, pk=reserva_id)
    reservas = (
        models.Reserva.objects.filter(aluno=reserva.aluno)
        .select_related("aulaSessao", "aulaSessao__unidade", "aulaSessao__profissional", "aulaSessao__tipoServico")
        .order_by("-aulaSessao__data", "-aulaSessao__horaInicio")[:20]
    )
    items = []
    for item in reservas:
        aula = item.aulaSessao
        if not aula:
            continue
        inicio = timezone.make_aware(datetime.combine(aula.data, aula.horaInicio))
        fim = timezone.make_aware(datetime.combine(aula.data, aula.horaFim))
        status_calc = _map_status(item.status, inicio, fim)
        items.append(
            {
                "id": item.id,
                "data": aula.data.isoformat(),
                "hora_inicio": aula.horaInicio.strftime("%H:%M"),
                "hora_fim": aula.horaFim.strftime("%H:%M"),
                "unidade": aula.unidade.dsUnidade if aula.unidade else None,
                "profissional": aula.profissional.profissional if aula.profissional else None,
                "servico": aula.tipoServico.dsTipoServico if aula.tipoServico else None,
                "status": status_calc,
            }
        )
    return JsonResponse({"items": items})


@login_required
@require_POST
def aula_status_api(request, reserva_id):
    payload = _parse_json_body(request)
    acao = (payload.get("acao") or "").strip().lower()
    status_map = {
        "chegou": "RESERVADA",
        "iniciar": "RESERVADA",
        "finalizar": "CONCLUIDA",
        "faltou": "FALTOU_SEM_AVISAR",
        "remarcar": "CANCELADA",
    }
    if acao not in status_map:
        return JsonResponse({"error": "Acao invalida."}, status=400)
    reserva = get_object_or_404(models.Reserva, pk=reserva_id)
    reserva.status = status_map[acao]
    reserva.save(update_fields=["status"])
    return JsonResponse({"reserva_id": reserva.id, "status": reserva.status})


@login_required
def aula_remarcar_api(request, reserva_id):
    if request.method != "POST":
        return JsonResponse({"error": "Metodo invalido."}, status=405)
    payload = _parse_json_body(request)
    data_str = (payload.get("data") or "").strip()
    hora_str = (payload.get("hora_inicio") or "").strip()
    profissional_id = payload.get("profissional_id")
    if not data_str or not hora_str:
        return JsonResponse({"error": "Informe data e hora."}, status=400)
    try:
        nova_data = datetime.strptime(data_str, "%Y-%m-%d").date()
        nova_hora_inicio = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        return JsonResponse({"error": "Data ou hora invalida."}, status=400)

    reserva = get_object_or_404(models.Reserva.objects.select_related("aulaSessao", "aulaSessao__unidade", "aulaSessao__tipoServico", "aulaSessao__profissional"), pk=reserva_id)
    aula = reserva.aulaSessao
    if not aula:
        return JsonResponse({"error": "Aula nao encontrada."}, status=404)
    profissional = aula.profissional
    if profissional_id:
        profissional = models.Profissional.objects.filter(pk=profissional_id).first()
        if not profissional:
            return JsonResponse({"error": "Profissional invalido."}, status=400)

    duracao_min = aula.unidade.duracao_aula_minutos if aula.unidade else 50
    if aula.horaFim and aula.horaInicio:
        base_inicio = datetime.combine(date.today(), aula.horaInicio)
        base_fim = datetime.combine(date.today(), aula.horaFim)
        diff_min = int((base_fim - base_inicio).total_seconds() / 60)
        if diff_min > 0:
            duracao_min = diff_min
    hora_fim = (datetime.combine(nova_data, nova_hora_inicio) + timedelta(minutes=duracao_min)).time()

    nova_sessao, _ = models.AulaSessao.objects.get_or_create(
        unidade=aula.unidade,
        tipoServico=aula.tipoServico,
        profissional=profissional,
        data=nova_data,
        horaInicio=nova_hora_inicio,
        horaFim=hora_fim,
        defaults={"capacidade": aula.capacidade},
    )

    capacidade = nova_sessao.capacidade_efetiva()
    total = (
        models.Reserva.objects.filter(aulaSessao=nova_sessao, status="RESERVADA")
        .exclude(pk=reserva.pk)
        .count()
    )
    if capacidade and total >= capacidade:
        return JsonResponse({"error": "Sem capacidade para este horario."}, status=400)

    antiga_sessao = reserva.aulaSessao
    reserva.aulaSessao = nova_sessao
    reserva.status = "RESERVADA"
    reserva.save(update_fields=["aulaSessao", "status"])

    if antiga_sessao and not models.Reserva.objects.filter(aulaSessao=antiga_sessao).exists():
        antiga_sessao.delete()

    inicio_dt = timezone.make_aware(datetime.combine(nova_data, nova_sessao.horaInicio))
    fim_dt = timezone.make_aware(datetime.combine(nova_data, nova_sessao.horaFim))
    return JsonResponse(
          {
              "ok": True,
              "reserva_id": reserva.id,
              "dt_inicio": inicio_dt.isoformat(),
              "dt_fim": fim_dt.isoformat(),
          }
      )


@csrf_exempt
@require_POST
def totalpass_webhook(request):
    payload = _parse_json_body(request)
    cfg = _get_totalpass_config(payload)
    token = ""
    if cfg and cfg.webhook_token:
        token = cfg.webhook_token
    if not token:
        token = getattr(settings, "TOTALPASS_WEBHOOK_TOKEN", "") or ""
    if token:
        header_token = request.headers.get("X-Totalpass-Token") or request.headers.get("x-totalpass-token") or ""
        if header_token != token:
            return JsonResponse({"error": "Token invalido."}, status=403)
    if cfg and cfg.ativo is False:
        return JsonResponse({"ok": True, "warning": "Integracao desativada."}, status=202)
    reserva, err = _process_totalpass_payload(payload, cfg)
    if err:
        return JsonResponse({"error": err}, status=400)
    return JsonResponse({"ok": True, "reserva_id": reserva.id if reserva else None})


def create_view(request, model, form_class, redirect_name):
    if model in (models.Plano, models.Contrato) and _is_professor_user(request.user):
        messages.error(request, "Sem permissao para acessar esta area.")
        return redirect("dashboard")
    if request.method == "POST":
        data = request.POST.copy()
        data = _inject_cd_value(model, data)
        if model is models.AulaSessao and not data.get("horaFim"):
            unidade_id = data.get("unidade")
            hora_inicio = data.get("horaInicio")
            if unidade_id and hora_inicio:
                unidade = models.Unidade.objects.filter(pk=unidade_id).first()
                if unidade and unidade.duracao_aula_minutos:
                    inicio_time = datetime.strptime(hora_inicio, "%H:%M").time()
                    base = datetime.combine(date.today(), inicio_time)
                    fim = base + timedelta(minutes=unidade.duracao_aula_minutos)
                    data["horaFim"] = fim.time().strftime("%H:%M")
        if model is models.Profissional and not data.get("cdPerfilAcesso"):
            perfil, _ = models.PerfilAcesso.objects.get_or_create(
                cdPerfilAcesso=1, defaults={"dsPerfilAcesso": "Padrao"}
            )
            data["cdPerfilAcesso"] = perfil.id
        form = form_class(data, files=request.FILES or None)
        if form.is_valid():
            if model is models.Contrato:
                cleaned = form.cleaned_data
                valor_parcela = cleaned.get("valor_parcela") or float(data.get("valor", "0") or 0)
                valor_total = cleaned.get("valor_total") or 0
                if not valor_total and cleaned.get("cdPlano"):
                    valor_total = float(valor_parcela) * float(cleaned["cdPlano"].duracao_meses or 1)
                contrato_data = {
                    "cdContrato": cleaned["cdContrato"],
                    "cdAluno": cleaned["cdAluno"],
                    "cdPlano": cleaned["cdPlano"],
                    "cdUnidade": cleaned["cdUnidade"],
                    "cdProfissional": cleaned["cdProfissional"],
                    "valor_parcela": valor_parcela,
                    "valor_total": valor_total,
                    "dtInicioContrato": cleaned["dtInicioContrato"],
                    "dtFimContrato": cleaned["dtFimContrato"],
                }
                valor = float(valor_parcela or 0)
                obj = services.criar_contrato_e_contas(contrato_data, valor)
                if services.enviar_contrato_para_assinatura(obj, request.build_absolute_uri("/")):
                    messages.success(request, "Contrato criado e enviado por email. Agende as aulas.")
                else:
                    messages.warning(request, "Contrato criado, mas aluno sem email para assinatura.")
                    messages.success(request, "Contrato criado. Agende as aulas.")
                _enviar_contrato_whatsapp(request, obj, is_new=True)
                return redirect("contratos_agenda", pk=obj.id)
            obj = form.save()
            if model is models.ContasPagar:
                recorrencia = obj.recorrencia
                quantidade = obj.recorrencia_quantidade or 0
                if recorrencia and quantidade < 1:
                    quantidade = 1
                    obj.recorrencia_quantidade = quantidade
                    obj.save(update_fields=["recorrencia_quantidade"])
                if recorrencia and quantidade > 1:
                    max_cd = models.ContasPagar.objects.order_by("-cdContasPagar").values_list("cdContasPagar", flat=True).first() or 0
                    for idx in range(1, quantidade):
                        if recorrencia == "SEMANAL":
                            vencimento = obj.dtVencimento + timedelta(days=7 * idx)
                        elif recorrencia == "ANUAL":
                            vencimento = _add_years(obj.dtVencimento, idx)
                        else:
                            vencimento = _add_months(obj.dtVencimento, idx)
                        max_cd += 1
                        models.ContasPagar.objects.create(
                            cdContasPagar=max_cd,
                            cdFornecedor=obj.cdFornecedor,
                            cdCategoria=obj.cdCategoria,
                            cdSubcategoria=obj.cdSubcategoria,
                            dtVencimento=vencimento,
                            valor=obj.valor,
                            recorrencia=obj.recorrencia,
                            recorrencia_quantidade=obj.recorrencia_quantidade,
                        )
            if model is models.Profissional:
                _sync_user_for_profissional(obj, raw_password=form.cleaned_data.get("password"))
            if model is models.Aluno:
                _sync_aluno_address(obj, request.POST)
                _sync_aluno_phones(obj, request.POST)
            messages.success(request, "Salvo com sucesso")
        else:
            messages.error(request, "Verifique os erros")
        return redirect(redirect_name)
    return render(
        request,
        "generic/form.html",
        {"form": form_class(), "title": "Novo", "model_name": model._meta.model_name, "active_menu": _active_menu(request.path)},
    )


def edit_view(request, model, form_class, redirect_name, pk):
    if model in (models.Plano, models.Contrato) and _is_professor_user(request.user):
        messages.error(request, "Sem permissao para acessar esta area.")
        return redirect("dashboard")
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        next_url = request.POST.get("next", "").strip()
        if next_url and not next_url.startswith("/"):
            next_url = ""
        data = request.POST.copy()
        for field in model._meta.fields:
            if field.name.startswith("cd") and not data.get(field.name):
                data[field.name] = getattr(obj, field.name)
        if model is models.AulaSessao and not data.get("horaFim"):
            unidade_id = data.get("unidade")
            hora_inicio = data.get("horaInicio")
            if unidade_id and hora_inicio:
                unidade = models.Unidade.objects.filter(pk=unidade_id).first()
                if unidade and unidade.duracao_aula_minutos:
                    inicio_time = datetime.strptime(hora_inicio, "%H:%M").time()
                    base = datetime.combine(date.today(), inicio_time)
                    fim = base + timedelta(minutes=unidade.duracao_aula_minutos)
                    data["horaFim"] = fim.time().strftime("%H:%M")
        form = form_class(data, files=request.FILES or None, instance=obj)
        if form.is_valid():
            obj = form.save()
            if model is models.Profissional:
                _sync_user_for_profissional(obj, raw_password=form.cleaned_data.get("password"))
            if model is models.Aluno:
                _sync_aluno_address(obj, request.POST)
                _sync_aluno_phones(obj, request.POST)
            if model is models.Contrato and obj.status == "NAO_ASSINADO":
                if not services.enviar_contrato_para_assinatura(obj, request.build_absolute_uri("/")):
                    messages.warning(request, "Contrato atualizado, mas aluno sem email para assinatura.")
            messages.success(request, "Atualizado com sucesso")
            return redirect(next_url or redirect_name)
        messages.error(request, "Verifique os erros")
        if next_url:
            return redirect(next_url)
    return render(
        request,
        "generic/form.html",
        {"form": form_class(instance=obj), "title": "Editar", "model_name": model._meta.model_name, "active_menu": _active_menu(request.path)},
    )


def delete_view(request, model, redirect_name, pk):
    if model in (models.Plano, models.Contrato) and _is_professor_user(request.user):
        messages.error(request, "Sem permissao para acessar esta area.")
        return redirect("dashboard")
    obj = get_object_or_404(model, pk=pk)
    delete_context = {}
    if model is models.Contrato:
        reservas_qs = models.Reserva.objects.filter(
            aluno=obj.cdAluno,
            aulaSessao__data__range=(obj.dtInicioContrato, obj.dtFimContrato),
            aulaSessao__unidade=obj.cdUnidade,
            aulaSessao__tipoServico=obj.cdPlano.cdTipoServico,
        )
        aula_ids = list(reservas_qs.values_list("aulaSessao_id", flat=True))
        delete_context = {
            "requires_confirm": True,
            "delete_summary": {
                "contas_receber": models.ContasReceber.objects.filter(contrato=obj).count(),
                "reservas": reservas_qs.count(),
                "aulas": len(set(aula_ids)),
            },
        }
    if request.method == "POST":
        next_url = request.POST.get("next", "").strip()
        if next_url and not next_url.startswith("/"):
            next_url = ""
        if model is models.Contrato:
            if request.POST.get("confirm_delete") != "1":
                messages.error(request, "Confirme a exclusao do contrato.")
                return redirect(next_url or redirect_name)
            # Remove contas a receber e reservas do aluno dentro do periodo do contrato.
            models.ContasReceber.objects.filter(contrato=obj).delete()
            reservas_qs = models.Reserva.objects.filter(
                aluno=obj.cdAluno,
                aulaSessao__data__range=(obj.dtInicioContrato, obj.dtFimContrato),
                aulaSessao__unidade=obj.cdUnidade,
                aulaSessao__tipoServico=obj.cdPlano.cdTipoServico,
            )
            aula_ids = list(reservas_qs.values_list("aulaSessao_id", flat=True))
            reservas_qs.delete()
            if aula_ids:
                models.AulaSessao.objects.filter(id__in=aula_ids).annotate(total=Count("reserva")).filter(total=0).delete()
        obj.delete()
        messages.success(request, "Removido")
        return redirect(next_url or redirect_name)
    context = {"object": obj, "title": "Excluir", "active_menu": _active_menu(request.path)}
    context.update(delete_context)
    return render(request, "generic/confirm_delete.html", context)


@login_required
def baixar_conta_receber(request, pk):
    conta = get_object_or_404(models.ContasReceber, pk=pk)
    if request.method == "POST":
        next_url = request.POST.get("next", "").strip()
        if next_url and not next_url.startswith("/"):
            next_url = ""
        data_pagamento = request.POST.get("dtPagamento") or ""
        try:
            pago_em = datetime.strptime(data_pagamento, "%Y-%m-%d").date() if data_pagamento else timezone.now().date()
        except ValueError:
            pago_em = timezone.now().date()
        conta.status = "PAGO"
        conta.dtPagamento = pago_em
        conta.save(update_fields=["status", "dtPagamento"])
        messages.success(request, "Lancamento baixado com sucesso.")
        return redirect(next_url or "contas_receber_list")
    return redirect("contas_receber_list")


@login_required
def efetuar_pagamento_conta_pagar(request, pk):
    conta = get_object_or_404(models.ContasPagar, pk=pk)
    if request.method != "POST":
        return redirect("contas_pagar_list")
    next_url = request.POST.get("next", "").strip()
    if next_url and not next_url.startswith("/"):
        next_url = ""
    data_pagamento = request.POST.get("dtPagamento") or ""
    try:
        pago_em = datetime.strptime(data_pagamento, "%Y-%m-%d").date() if data_pagamento else timezone.now().date()
    except ValueError:
        pago_em = timezone.now().date()
    comprovante = request.FILES.get("comprovante")
    conta.status = "PAGO"
    conta.dtPagamento = pago_em
    if comprovante:
        conta.comprovante = comprovante
    conta.save(update_fields=["status", "dtPagamento", "comprovante"])
    messages.success(request, "Pagamento registrado.")
    return redirect(next_url or "contas_pagar_list")


@login_required
def cancelar_conta_pagar(request, pk):
    conta = get_object_or_404(models.ContasPagar, pk=pk)
    if request.method != "POST":
        return redirect("contas_pagar_list")
    next_url = request.POST.get("next", "").strip()
    if next_url and not next_url.startswith("/"):
        next_url = ""
    motivo = request.POST.get("motivo_cancelamento", "").strip()
    conta.status = "CANCELADO"
    conta.motivo_cancelamento = motivo
    conta.save(update_fields=["status", "motivo_cancelamento"])
    messages.success(request, "Lancamento cancelado.")
    return redirect(next_url or "contas_pagar_list")


@login_required
def evoluir_reserva(request, pk):
    reserva = get_object_or_404(models.Reserva, pk=pk)
    if request.method != "POST":
        return redirect("aulas_list")
    next_url = request.POST.get("next", "").strip()
    if next_url and not next_url.startswith("/"):
        next_url = ""
    status = request.POST.get("status", "").strip()
    texto = request.POST.get("texto", "").strip()
    if status not in {"CONCLUIDA", "FALTOU_AVISOU", "FALTOU_SEM_AVISAR"}:
        messages.error(request, "Status invalido.")
        return redirect(next_url or "aulas_list")
    if not texto:
        messages.error(request, "Preencha a evolucao.")
        return redirect(next_url or "aulas_list")
    if not reserva.aulaSessao.profissional_id:
        messages.error(request, "Defina o profissional da aula antes de registrar a evolucao.")
        return redirect(next_url or "aulas_list")
    models.EvolucaoAluno.objects.create(
        reserva=reserva,
        profissional=reserva.aulaSessao.profissional,
        texto=texto,
    )
    reserva.status = status
    reserva.save(update_fields=["status"])
    messages.success(request, "Evolucao registrada.")
    return redirect(next_url or "aulas_list")


def _get_filtros_financeiro(request):
    return {
        "status": request.GET.get("status", "").strip(),
        "inicio": request.GET.get("inicio", "").strip(),
        "fim": request.GET.get("fim", "").strip(),
    }


def _filtrar_contas_receber(qs, request):
    filtros = _get_filtros_financeiro(request)
    if filtros["status"]:
        qs = qs.filter(status=filtros["status"])
    inicio = filtros["inicio"]
    fim = filtros["fim"]
    if inicio:
        try:
            inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
            qs = qs.filter(dtVencimento__gte=inicio_dt)
        except ValueError:
            pass
    if fim:
        try:
            fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()
            qs = qs.filter(dtVencimento__lte=fim_dt)
        except ValueError:
            pass
    return qs.order_by("dtVencimento", "id")


@login_required
def exportar_contas_receber_excel(request, aluno_id):
    aluno = get_object_or_404(models.Aluno, pk=aluno_id)
    qs = _filtrar_contas_receber(
        models.ContasReceber.objects.filter(contrato__cdAluno=aluno).select_related(
            "contrato",
            "contrato__cdPlano",
            "contrato__cdPlano__subcategoria_receita",
        ),
        request,
    )
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Faturas"
    ws.append(["Competencia", "Vencimento", "Pagamento", "Contrato", "Subcategoria", "Status", "Valor"])
    for f in qs:
        ws.append(
            [
                f.competencia or "",
                f.dtVencimento.strftime("%d/%m/%Y") if f.dtVencimento else "",
                f.dtPagamento.strftime("%d/%m/%Y") if f.dtPagamento else "",
                f.contrato.cdContrato if f.contrato_id else "",
                f.contrato.cdPlano.subcategoria_receita.dsSubcategoria if f.contrato_id and f.contrato.cdPlano and f.contrato.cdPlano.subcategoria_receita else "",
                f.status,
                float(f.valor),
            ]
        )
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="faturas-aluno-{aluno.id}.xlsx"'
    return response


@login_required
def exportar_contas_receber_pdf(request, aluno_id):
    aluno = get_object_or_404(models.Aluno, pk=aluno_id)
    qs = _filtrar_contas_receber(
        models.ContasReceber.objects.filter(contrato__cdAluno=aluno).select_related(
            "contrato",
            "contrato__cdPlano",
            "contrato__cdPlano__subcategoria_receita",
        ),
        request,
    )
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Faturas do Aluno")
    styles = getSampleStyleSheet()
    title = Paragraph(f"Faturas do aluno: {aluno.dsNome}", styles["Title"])
    subtitle = Paragraph("Resumo financeiro", styles["Normal"])
    data = [["Competencia", "Vencimento", "Pagamento", "Contrato", "Subcategoria", "Status", "Valor"]]
    for f in qs:
        data.append(
            [
                f.competencia or "-",
                f.dtVencimento.strftime("%d/%m/%Y") if f.dtVencimento else "-",
                f.dtPagamento.strftime("%d/%m/%Y") if f.dtPagamento else "-",
                str(f.contrato.cdContrato) if f.contrato_id else "-",
                f.contrato.cdPlano.subcategoria_receita.dsSubcategoria if f.contrato_id and f.contrato.cdPlano and f.contrato.cdPlano.subcategoria_receita else "-",
                f.status,
                f"R$ {f.valor}",
            ]
        )
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4d4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fb")]),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    elements = [title, subtitle, Spacer(1, 12), table]
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="faturas-aluno-{aluno.id}.pdf"'
    return response


@login_required
def recibo_conta_receber_pdf(request, pk):
    conta = get_object_or_404(models.ContasReceber, pk=pk)
    aluno = conta.contrato.cdAluno if conta.contrato_id else None
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Recibo")
    styles = getSampleStyleSheet()
    title = Paragraph("Recibo de Pagamento", styles["Title"])
    aluno_nome = aluno.dsNome if aluno else "-"
    pago_em = conta.dtPagamento.strftime("%d/%m/%Y") if conta.dtPagamento else "-"
    data = [
        ["Aluno", aluno_nome],
        ["Contrato", str(conta.contrato.cdContrato) if conta.contrato_id else "-"],
        ["Competencia", conta.competencia or "-"],
        ["Vencimento", conta.dtVencimento.strftime("%d/%m/%Y") if conta.dtVencimento else "-"],
        ["Pagamento", pago_em],
        ["Valor", f"R$ {conta.valor}"],
        ["Status", conta.status],
    ]
    table = Table(data, colWidths=[120, 360])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4d4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fb")]),
            ]
        )
    )
    elements = [title, Spacer(1, 8), table, Spacer(1, 18), Paragraph("Obrigado!", styles["Heading3"])]
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="recibo-{conta.id}.pdf"'
    return response


@login_required
def exportar_evolucoes_excel(request, aluno_id):
    aluno = get_object_or_404(models.Aluno, pk=aluno_id)
    qs = (
        models.EvolucaoAluno.objects.filter(reserva__aluno=aluno)
        .select_related("profissional", "reserva")
        .order_by("-dtEvolucao")
    )
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Evolucoes"
    ws.append(["Data", "Profissional", "Evolucao"])
    for e in qs:
        ws.append(
            [
                e.dtEvolucao.strftime("%d/%m/%Y %H:%M") if e.dtEvolucao else "",
                str(e.profissional),
                e.texto,
            ]
        )
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="evolucoes-aluno-{aluno.id}.xlsx"'
    return response


@login_required
def exportar_evolucoes_pdf(request, aluno_id):
    aluno = get_object_or_404(models.Aluno, pk=aluno_id)
    qs = (
        models.EvolucaoAluno.objects.filter(reserva__aluno=aluno)
        .select_related("profissional", "reserva")
        .order_by("-dtEvolucao")
    )
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Evolucoes do Aluno")
    styles = getSampleStyleSheet()
    title = Paragraph(f"Evolucoes do aluno: {aluno.dsNome}", styles["Title"])
    data = [["Data", "Profissional", "Evolucao"]]
    for e in qs:
        data.append(
            [
                e.dtEvolucao.strftime("%d/%m/%Y %H:%M") if e.dtEvolucao else "-",
                str(e.profissional),
                e.texto,
            ]
        )
    table = Table(data, repeatRows=1, colWidths=[110, 140, 290])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4d4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4ea")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fb")]),
            ]
        )
    )
    elements = [title, Spacer(1, 12), table]
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="evolucoes-aluno-{aluno.id}.pdf"'
    return response


@login_required
def wizard_step1(request):
    if request.method == "POST":
        if request.FILES.get("documento"):
            data = extract_student_from_document(request.FILES["documento"].read(), request.FILES["documento"].name)
            request.session["wizard_student"] = data
            return render(
                request,
                "wizard/step1_documento.html",
                {
                    "student": data,
                    "unidades": models.Unidade.objects.all(),
                    "breadcrumbs": [("Home", reverse("dashboard")), ("Wizard", "#")],
                    "active_menu": "cadastros",
                },
            )
        if request.POST.get("confirm") == "1":
            cpf = request.POST.get("cpf", "")
            if models.Aluno.objects.filter(dsCPF=cpf).exists():
                messages.error(request, "CPF duplicado")
                return redirect("wizard_step1")
            max_cd = models.Aluno.objects.order_by("-cdAluno").values_list("cdAluno", flat=True).first() or 0
            aluno = models.Aluno.objects.create(
                cdAluno=max_cd + 1,
                dsNome=request.POST.get("nome", ""),
                dsCPF=cpf,
                dsRg=request.POST.get("rg", ""),
                cdUnidade_id=int(request.POST.get("cdUnidade")),
            )
            request.session["wizard_aluno_id"] = aluno.id
            return redirect("wizard_step2")
    return render(
        request,
        "wizard/step1_documento.html",
        {"unidades": models.Unidade.objects.all(), "breadcrumbs": [("Home", reverse("dashboard")), ("Wizard", "#")], "active_menu": "cadastros"},
    )


@login_required
def wizard_step2(request):
    if request.method == "POST":
        if request.FILES.get("comprovante"):
            data = extract_address_from_proof(request.FILES["comprovante"].read(), request.FILES["comprovante"].name)
            request.session["wizard_address"] = data
            return render(
                request,
                "wizard/step2_endereco.html",
                {"address": data, "breadcrumbs": [("Home", reverse("dashboard")), ("Wizard", "#")], "active_menu": "cadastros"},
            )
        if request.POST.get("confirm") == "1":
            aluno_id = request.session.get("wizard_aluno_id")
            if not aluno_id:
                messages.error(request, "Aluno nao encontrado")
                return redirect("wizard_step1")
            max_cd = models.EnderecoAluno.objects.order_by("-cdEndereco").values_list("cdEndereco", flat=True).first() or 0
            endereco = models.EnderecoAluno.objects.create(
                cdEndereco=max_cd + 1,
                cdAluno_id=aluno_id,
                dsLogradouro=request.POST.get("logradouro", ""),
                dsNumero=request.POST.get("numero", ""),
                dsCEP=request.POST.get("cep", ""),
                dsCidade=request.POST.get("cidade", ""),
                dsBairro=request.POST.get("bairro", ""),
            )
            models.Aluno.objects.filter(pk=aluno_id).update(cdEndereco=endereco)
            return redirect("wizard_step3")
    return render(
        request,
        "wizard/step2_endereco.html",
        {"breadcrumbs": [("Home", reverse("dashboard")), ("Wizard", "#")], "active_menu": "cadastros"},
    )


@login_required
def wizard_step3(request):
    termos = models.TermoUso.objects.all()
    if request.method == "POST":
        termo_id = request.POST.get("termo")
        aluno_id = request.session.get("wizard_aluno_id")
        if aluno_id and termo_id:
            services.registrar_aceite_termo(models.Aluno.objects.get(pk=aluno_id), models.TermoUso.objects.get(pk=int(termo_id)))
        return redirect("wizard_step4")
    return render(
        request,
        "wizard/step3_termo.html",
        {"termos": termos, "breadcrumbs": [("Home", reverse("dashboard")), ("Wizard", "#")], "active_menu": "cadastros"},
    )


@login_required
def wizard_step4(request):
    if request.method == "POST":
        request.session["wizard_contrato"] = request.POST.dict()
        return redirect("wizard_step5")
    context = {
        "alunos": models.Aluno.objects.all(),
        "aluno_id": request.session.get("wizard_aluno_id"),
        "planos": models.Plano.objects.all(),
        "unidades": models.Unidade.objects.all(),
        "profissionais": models.Profissional.objects.all(),
        "breadcrumbs": [("Home", reverse("dashboard")), ("Wizard", "#")],
        "active_menu": "cadastros",
    }
    return render(request, "wizard/step4_contrato.html", context)


@login_required
def wizard_step5(request):
    if request.method == "POST":
        data = request.session.get("wizard_contrato", {})
        aluno = models.Aluno.objects.get(pk=int(data.get("cdAluno")))
        plano = models.Plano.objects.get(pk=int(data.get("cdPlano")))
        valor_parcela = float(data.get("valor_parcela") or data.get("valor") or 0)
        valor_total = float(data.get("valor_total") or 0)
        if not valor_total and plano:
            valor_total = float(valor_parcela) * float(plano.duracao_meses or 1)
        contrato_data = {
            "cdContrato": int(data.get("cdContrato")),
            "cdAluno": aluno,
            "cdPlano": plano,
            "cdUnidade": models.Unidade.objects.get(pk=int(data.get("cdUnidade"))),
            "cdProfissional": models.Profissional.objects.get(pk=int(data.get("cdProfissional"))),
            "valor_parcela": valor_parcela,
            "valor_total": valor_total,
            "dtInicioContrato": data.get("dtInicioContrato"),
            "dtFimContrato": data.get("dtFimContrato"),
        }
        contrato = services.criar_contrato_e_contas(contrato_data, float(data.get("valor", "0")))
        if services.enviar_contrato_para_assinatura(contrato, request.build_absolute_uri("/")):
            messages.success(request, "Contrato criado e enviado por email. Agende as aulas.")
        else:
            messages.warning(request, "Contrato criado, mas aluno sem email para assinatura.")
            messages.success(request, "Contrato criado. Agende as aulas.")
        _enviar_contrato_whatsapp(request, contrato, is_new=True)
        return redirect("contratos_agenda", pk=contrato.id)
    return render(
        request,
        "wizard/step5_reservas.html",
        {"breadcrumbs": [("Home", reverse("dashboard")), ("Wizard", "#")], "active_menu": "cadastros"},
    )


@login_required
def contrato_agenda(request, pk):
    contrato = get_object_or_404(models.Contrato, pk=pk)
    plano = contrato.cdPlano
    aulas_por_semana = plano.aulas_por_semana or 1
    aulas = models.AulaSessao.objects.filter(
        unidade=contrato.cdUnidade,
        tipoServico=plano.cdTipoServico,
        data__range=(contrato.dtInicioContrato, contrato.dtFimContrato),
    ).select_related("unidade").order_by("data", "horaInicio")

    profissionais = list(models.Profissional.objects.all())
    prof_ids = [prof.id for prof in profissionais]
    duracao = contrato.cdUnidade.duracao_aula_minutos or 50
    funcionamento = _load_funcionamento(contrato.cdUnidade_id, plano.cdTipoServico_id)
    horarios_configurados = bool(funcionamento)

    slots = {}
    aulas_by_key = {(aula.data, aula.horaInicio, aula.horaFim, aula.profissional_id): aula for aula in aulas}
    capacidade_padrao = contrato.cdUnidade.capacidade or 0

    dates_by_weekday = {i: [] for i in range(7)}
    current = contrato.dtInicioContrato
    while current <= contrato.dtFimContrato:
        dates_by_weekday[current.weekday()].append(current)
        current += timedelta(days=1)

    blocks_by_prof = {}
    for prof in profissionais:
        blocks_by_prof[prof.id] = _load_bloqueios(
            contrato.cdUnidade_id,
            plano.cdTipoServico_id,
            prof.id,
            contrato.dtInicioContrato,
            contrato.dtFimContrato,
        )

    for weekday, windows in funcionamento.items():
        if not dates_by_weekday.get(weekday):
            continue
        sample_date = dates_by_weekday[weekday][0]
        time_slots = _generate_slots_for_date(sample_date, windows, duracao)
        for inicio, fim in time_slots:
            allowed_profs = []
            for prof in profissionais:
                prof_ok = True
                blocks = blocks_by_prof.get(prof.id, [])
                for day in dates_by_weekday[weekday]:
                    if _is_slot_blocked(blocks, day, inicio, fim):
                        prof_ok = False
                        break
                    aula = aulas_by_key.get((day, inicio, fim, prof.id))
                    if aula:
                        reservadas = models.Reserva.objects.filter(aulaSessao=aula, status="RESERVADA").count()
                        cap = aula.capacidade_efetiva()
                    else:
                        reservadas = 0
                        cap = capacidade_padrao
                    if reservadas >= (cap or 0):
                        prof_ok = False
                        break
                if prof_ok:
                    allowed_profs.append(prof.id)
            if allowed_profs:
                slots[(weekday, inicio, fim)] = {
                    "weekday": weekday,
                    "inicio": inicio,
                    "fim": fim,
                    "allowed_profs": allowed_profs,
                }

    if not slots and not horarios_configurados:
        slots = {}
        for aula in aulas:
            reservadas = models.Reserva.objects.filter(aulaSessao=aula, status="RESERVADA").count()
            if reservadas >= aula.capacidade_efetiva():
                continue
            key = (aula.data.weekday(), aula.horaInicio, aula.horaFim)
            slots[key] = {"weekday": key[0], "inicio": key[1], "fim": key[2], "allowed_profs": []}

    if request.method == "POST":

        escolhidas = []
        for idx in range(1, aulas_por_semana + 1):
            valor = request.POST.get(f"slot_{idx}") or ""
            dia_raw = request.POST.get(f"slot_day_{idx}") or ""
            if valor:
                escolhidas.append((idx, valor, dia_raw))
        if len(escolhidas) != aulas_por_semana:
            messages.error(request, f"Selecione exatamente {aulas_por_semana} horarios por semana.")
        else:
            conflitos = []
            faltando_prof = False
            usados = set()
            dias_usados = set()
            for idx, slot_value, dia_raw in escolhidas:
                if slot_value in usados:
                    messages.error(request, "Nao repita o mesmo horario.")
                    return redirect("contratos_agenda", pk=contrato.id)
                usados.add(slot_value)
                try:
                    weekday_raw, inicio, fim = slot_value.split("|")
                    weekday = int(weekday_raw)
                except ValueError:
                    messages.error(request, "Horario invalido na selecao.")
                    return redirect("contratos_agenda", pk=contrato.id)
                if dia_raw:
                    try:
                        dia_selected = int(dia_raw)
                    except ValueError:
                        messages.error(request, "Dia da semana invalido.")
                        return redirect("contratos_agenda", pk=contrato.id)
                    if dia_selected != weekday:
                        messages.error(request, "Dia e horario nao conferem.")
                        return redirect("contratos_agenda", pk=contrato.id)
                if weekday in dias_usados:
                    messages.error(request, "Selecione apenas um horario por dia.")
                    return redirect("contratos_agenda", pk=contrato.id)
                dias_usados.add(weekday)
                prof_id = request.POST.get(f"prof_for_{idx}") or ""
                try:
                    prof_id = int(prof_id)
                except ValueError:
                    prof_id = None
                if not prof_id:
                    faltando_prof = True
                    continue
                try:
                    inicio_time = datetime.strptime(inicio, "%H:%M").time()
                    fim_time = datetime.strptime(fim, "%H:%M").time()
                except ValueError:
                    messages.error(request, "Horario invalido na selecao.")
                    return redirect("contratos_agenda", pk=contrato.id)
                horario_key = (weekday, inicio_time, fim_time)
                if horario_key not in slots:
                    messages.error(request, "Horario invalido para o dia selecionado.")
                    return redirect("contratos_agenda", pk=contrato.id)
                slot_payload = slots.get(horario_key, {})
                allowed = set(slot_payload.get("allowed_profs") or [])
                if allowed and prof_id not in allowed:
                    messages.error(request, "Professor invalido para o horario selecionado.")
                    return redirect("contratos_agenda", pk=contrato.id)
                current = contrato.dtInicioContrato
                while current <= contrato.dtFimContrato:
                    if current.weekday() == weekday:
                        blocks = blocks_by_prof.get(prof_id, [])
                        if _is_slot_blocked(blocks, current, inicio_time, fim_time):
                            conflitos.append(f"Bloqueio em {current} {inicio}")
                            current = current + timedelta(days=1)
                            continue
                        aula = models.AulaSessao.objects.filter(
                            unidade=contrato.cdUnidade,
                            tipoServico=plano.cdTipoServico,
                            profissional_id=prof_id,
                            data=current,
                            horaInicio=inicio_time,
                            horaFim=fim_time,
                        ).first()
                        try:
                            if not aula:
                                aula = models.AulaSessao.objects.create(
                                    unidade=contrato.cdUnidade,
                                    tipoServico=plano.cdTipoServico,
                                    profissional_id=prof_id,
                                    data=current,
                                    horaInicio=inicio_time,
                                    horaFim=fim_time,
                                )
                            else:
                                update_fields = ["profissional"]
                                aula.profissional_id = prof_id
                                aula.save(update_fields=update_fields)
                            if models.Reserva.objects.filter(aluno=contrato.cdAluno, aulaSessao=aula).exists():
                                current = current + timedelta(days=1)
                                continue
                            services.create_reserva(contrato.cdAluno, aula, status="RESERVADA")
                        except Exception:
                            conflitos.append(f"Sem vaga em {current} {inicio}")
                    current = current + timedelta(days=1)
            if faltando_prof:
                messages.error(request, "Selecione o professor em todos os horarios.")
                return redirect("contratos_agenda", pk=contrato.id)
            if conflitos:
                messages.warning(request, "Conflitos ao reservar: " + "; ".join(conflitos[:5]))
            else:
                messages.success(request, "Agenda criada com sucesso.")
                return redirect("alunos_detail", pk=contrato.cdAluno_id)

    weekday_labels = {
        0: "Segunda",
        1: "Terca",
        2: "Quarta",
        3: "Quinta",
        4: "Sexta",
        5: "Sabado",
        6: "Domingo",
    }
    slots_by_day = {key: [] for key in weekday_labels}
    seen_slots = set()
    for item in sorted(slots.values(), key=lambda x: (x["weekday"], x["inicio"])):
        key = (item["weekday"], item["inicio"], item["fim"])
        if key in seen_slots:
            continue
        seen_slots.add(key)
        slots_by_day[item["weekday"]].append(
            {
                "label": f'{item["inicio"].strftime("%H:%M")} - {item["fim"].strftime("%H:%M")}',
                "value": f'{item["weekday"]}|{item["inicio"].strftime("%H:%M")}|{item["fim"].strftime("%H:%M")}',
                "allowed_profs": ",".join(
                    [str(pid) for pid in (item.get("allowed_profs") or [])]
                ),
            }
        )

    slot_options = []
    for item in sorted(slots.values(), key=lambda x: (x["weekday"], x["inicio"])):
        slot_options.append(
            {
                "label": f'{weekday_labels[item["weekday"]]} {item["inicio"].strftime("%H:%M")} - {item["fim"].strftime("%H:%M")}',
                "value": f'{item["weekday"]}|{item["inicio"].strftime("%H:%M")}|{item["fim"].strftime("%H:%M")}',
                "allowed_profs": item.get("allowed_profs") or [],
            }
        )

    context = {
        "contrato": contrato,
        "aluno": contrato.cdAluno,
        "aulas_por_semana": aulas_por_semana,
        "slot_indices": list(range(1, aulas_por_semana + 1)),
        "slots_by_day": slots_by_day,
        "weekday_labels": weekday_labels,
        "slot_options": slot_options,
        "profissionais": profissionais,
        "horarios_configurados": horarios_configurados,
        "breadcrumbs": [("Home", reverse("dashboard")), ("Contratos", reverse("contratos_list")), ("Agenda", "#")],
        "active_menu": "cadastros",
    }
    return render(request, "contratos/agenda.html", context)


@login_required
def email_config_view(request):
    cfg = models.EmailConfiguracao.objects.order_by("-dtCadastro").first()
    if request.method == "POST":
        data = request.POST.copy()
        data = _inject_cd_value(models.EmailConfiguracao, data)
        form = forms.EmailConfiguracaoForm(data, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuracao de email salva.")
            return redirect("email_config")
        messages.error(request, "Verifique os erros do formulario.")
    else:
        form = forms.EmailConfiguracaoForm(instance=cfg)
    return render(
        request,
        "configuracoes/email.html",
        {
            "form": form,
            "title": "Configuracao de Email",
            "breadcrumbs": [("Home", reverse("dashboard")), ("Configuracoes", "#"), ("Email", "#")],
            "active_menu": "configuracoes",
        },
    )


@login_required
def whatsapp_config_view(request):
    unidades = models.Unidade.objects.order_by("cdUnidade").all()
    if not unidades:
        messages.warning(request, "Cadastre ao menos uma unidade antes de configurar o WhatsApp.")
        return redirect("dashboard")
    unidade_id = request.GET.get("unidade")
    unidade = unidades.filter(pk=unidade_id).first() if unidade_id else unidades.first()
    if not unidade:
        unidade = unidades.first()
    configuracao = models.WhatsappConfiguracao.objects.filter(unidade=unidade).first()
    if request.method == "POST":
        form = forms.WhatsappConfiguracaoForm(request.POST, instance=configuracao)
        if form.is_valid():
            cfg = form.save(commit=False)
            cfg.unidade = unidade
            cfg.save()
            messages.success(request, "Configuracoes de WhatsApp salvas.")
            return redirect(f"{reverse('whatsapp_config')}?unidade={unidade.id}")
        messages.error(request, "Corrija os erros antes de salvar.")
    else:
        form = forms.WhatsappConfiguracaoForm(instance=configuracao)
    return render(
          request,
          "configuracoes/whatsapp.html",
          {
              "form": form,
              "unidades": unidades,
              "unidade": unidade,
              "title": "Configuracao de WhatsApp",
              "breadcrumbs": [("Home", reverse("dashboard")), ("Configuracoes", "#"), ("WhatsApp", "#")],
              "active_menu": "configuracoes",
          },
      )


def totalpass_config_view(request):
    unidades = models.Unidade.objects.order_by("cdUnidade").all()
    if not unidades:
        messages.warning(request, "Cadastre ao menos uma unidade antes de configurar o TotalPass.")
        return redirect("dashboard")
    unidade_id = request.GET.get("unidade")
    unidade = unidades.filter(pk=unidade_id).first() if unidade_id else unidades.first()
    if not unidade:
        unidade = unidades.first()
    configuracao = models.TotalpassConfiguracao.objects.filter(unidade=unidade).first()
    if request.method == "POST":
        form = forms.TotalpassConfiguracaoForm(request.POST, instance=configuracao)
        if form.is_valid():
            cfg = form.save(commit=False)
            cfg.unidade = unidade
            cfg.save()
            messages.success(request, "Configuracoes do TotalPass salvas.")
            return redirect(f"{reverse('totalpass_config')}?unidade={unidade.id}")
        messages.error(request, "Corrija os erros antes de salvar.")
    else:
        form = forms.TotalpassConfiguracaoForm(instance=configuracao)
    return render(
        request,
        "configuracoes/totalpass.html",
        {
            "form": form,
            "unidades": unidades,
            "unidade": unidade,
            "title": "Configuracao TotalPass",
            "breadcrumbs": [("Home", reverse("dashboard")), ("Configuracoes", "#"), ("TotalPass", "#")],
            "active_menu": "configuracoes",
        },
    )


def contrato_assinar(request, token):
    try:
        contrato_id = services.validar_token_contrato(token)
    except Exception:
        return render(request, "contratos/assinatura.html", {"token_invalido": True})
    contrato = get_object_or_404(models.Contrato, pk=contrato_id)
    if request.method == "POST":
        if contrato.status in ("ASSINADO", "ASSINADO_DIGITALMENTE"):
            return render(
                request,
                "contratos/assinatura_sucesso.html",
                {"contrato": contrato, "ja_assinado": True},
            )
        assinatura_nome = request.POST.get("assinatura_nome", "").strip()
        assinatura_documento = request.POST.get("assinatura_documento", "").strip()
        assinatura_data = request.POST.get("assinatura_data", "").strip()
        assinatura_ip = request.META.get("REMOTE_ADDR")
        if assinatura_nome and assinatura_data.startswith("data:image/"):
            try:
                from django.core.files.base import ContentFile
                import base64

                header, data = assinatura_data.split(",", 1)
                content = ContentFile(base64.b64decode(data), name=f"contrato_{contrato.id}.png")
                contrato.assinatura_imagem = content
            except Exception:
                assinatura_data = ""
        contrato.assinatura_nome = assinatura_nome
        contrato.assinatura_documento = assinatura_documento
        contrato.assinatura_ip = assinatura_ip
        contrato.status = "ASSINADO_DIGITALMENTE"
        contrato.assinado_em = timezone.now()
        contrato.save()
        already_notified = models.AlunoWhatsappMessage.objects.filter(
            contrato=contrato, tipo=WhatsappMessageType.CONTRACT_LINK
        ).exists()
        if not already_notified:
            try:
                service = WhatsappService()
                telefone = service.get_aluno_phone(contrato.cdAluno)
                if telefone:
                    token = services.gerar_token_contrato(contrato)
                    link = request.build_absolute_uri(reverse("contrato_assinar", kwargs={"token": token}))
                    mensagem = (
                        f"Olá {contrato.cdAluno.dsNome}, o contrato #{contrato.cdContrato} foi assinado. "
                        f"Você pode acessá-lo em {link}"
                    )
                    resp = service.send(
                        contrato.cdAluno,
                        telefone,
                        mensagem,
                        WhatsappMessageType.CONTRACT_LINK,
                        contrato=contrato,
                    )
                    if resp.get("error"):
                        messages.warning(request, "Contrato assinado, mas não foi possível enviar o aviso via WhatsApp.")
                else:
                    messages.warning(request, "Contrato assinado, mas o aluno não possui telefone válido.")
            except Exception:
                logger.exception("Erro ao enviar contrato assinado pelo WhatsApp")
        return render(request, "contratos/assinatura_sucesso.html", {"contrato": contrato})
    html = services.render_contrato_html(contrato)
    return render(
        request,
        "contratos/assinatura.html",
        {"contrato": contrato, "contrato_html": html, "token": token},
    )


@login_required
def contrato_enviar_email(request, pk):
    contrato = get_object_or_404(models.Contrato, pk=pk)
    if request.method != "POST":
        return redirect("alunos_detail", pk=contrato.cdAluno_id)
    if not contrato.cdAluno.dsEmail:
        messages.warning(request, "Aluno sem email cadastrado.")
        return redirect("alunos_detail", pk=contrato.cdAluno_id)
    if services.enviar_contrato_para_assinatura(contrato, request.build_absolute_uri("/")):
        messages.success(request, "Contrato enviado para assinatura por email.")
    else:
        messages.warning(request, "Nao foi possivel enviar o email do contrato.")
    return redirect("alunos_detail", pk=contrato.cdAluno_id)


@login_required
def contrato_assinar_local(request, pk):
    contrato = get_object_or_404(models.Contrato, pk=pk)
    token = services.gerar_token_contrato(contrato)
    return redirect("contrato_assinar", token=token)


@login_required
def contrato_assinatura_detalhe(request, pk):
    contrato = get_object_or_404(models.Contrato, pk=pk)
    contrato_html = services.render_contrato_html(contrato)
    return render(
        request,
        "contratos/assinatura_detalhe.html",
        {
            "contrato": contrato,
            "contrato_html": contrato_html,
            "breadcrumbs": [("Home", reverse("dashboard")), ("Alunos", reverse("alunos_list")), ("Assinatura", "#")],
            "active_menu": "cadastros",
        },
    )
