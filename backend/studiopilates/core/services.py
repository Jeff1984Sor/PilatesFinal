from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone
from .repositories import list_aulas, create_reserva, create_contas_receber, create_contrato


def gerar_parcelas(valor, inicio, fim, meses):
    parcelas = []
    months = max(int(meses or 1), 1)
    cursor = inicio
    while cursor <= fim:
        competencia = cursor.strftime("%Y-%m")
        parcelas.append({"valor": valor, "vencimento": cursor, "competencia": competencia})
        month = cursor.month + months
        year = cursor.year + ((month - 1) // 12)
        month = ((month - 1) % 12) + 1
        day = min(cursor.day, 28)
        cursor = date(year, month, day)
    return parcelas


def criar_contrato_e_contas(data_contrato, valor_parcela):
    meses = data_contrato["cdPlano"].duracao_meses
    with transaction.atomic():
        contrato = create_contrato(data_contrato)
        parcelas = gerar_parcelas(
            valor_parcela, data_contrato["dtInicioContrato"], data_contrato["dtFimContrato"], meses
        )
        create_contas_receber(contrato, parcelas)
    return contrato


def reservar_aulas_automaticas(contrato):
    aulas = list_aulas(
        contrato.dtInicioContrato,
        contrato.dtFimContrato,
        contrato.cdUnidade_id,
        contrato.cdPlano.cdTipoServico_id,
    )
    aulas_por_semana = contrato.cdPlano.aulas_por_semana or 1
    conflitos = []
    week_count = {}
    for aula in aulas:
        week_key = aula.data.isocalendar()[:2]
        if week_count.get(week_key, 0) >= aulas_por_semana:
            continue
        try:
            create_reserva(contrato.cdAluno, aula, status="RESERVADA")
            week_count[week_key] = week_count.get(week_key, 0) + 1
        except Exception:
            create_reserva(contrato.cdAluno, aula, status="PENDENTE")
            conflitos.append(aula.id)

    if not aulas.exists():
        conflitos.append("Sem aulas disponiveis")
    return conflitos


def registrar_aceite_termo(aluno, termo):
    aluno.cdTermoUso = termo
    aluno.termo_aceite_em = timezone.now()
    aluno.save(update_fields=["cdTermoUso", "termo_aceite_em"])
