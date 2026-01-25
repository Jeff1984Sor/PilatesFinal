from datetime import date
from django.db import transaction
from . import models


def get_aluno(aluno_id):
    return models.Aluno.objects.get(pk=aluno_id)


def list_alunos():
    return models.Aluno.objects.all()


def list_aulas(start: date, end: date, unidade_id=None, tipo_servico_id=None):
    qs = models.AulaSessao.objects.filter(data__range=(start, end))
    if unidade_id:
        qs = qs.filter(unidade_id=unidade_id)
    if tipo_servico_id:
        qs = qs.filter(tipoServico_id=tipo_servico_id)
    return qs


def create_reserva(aluno, aula, status="RESERVADA"):
    reserva = models.Reserva(aluno=aluno, aulaSessao=aula, status=status)
    reserva.full_clean()
    reserva.save()
    return reserva


def create_contas_receber(contrato, parcelas):
    created = []
    for parcela in parcelas:
        created.append(
            models.ContasReceber.objects.create(
                contrato=contrato,
                valor=parcela["valor"],
                dtVencimento=parcela["vencimento"],
                competencia=parcela.get("competencia", ""),
            )
        )
    return created


def create_contrato(data):
    with transaction.atomic():
        contrato = models.Contrato.objects.create(**data)
    return contrato
