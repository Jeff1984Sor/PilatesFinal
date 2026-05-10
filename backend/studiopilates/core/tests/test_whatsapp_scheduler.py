from datetime import datetime, time, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from studiopilates.core import whatsapp_scheduler as ws
from studiopilates.core import models


@pytest.mark.django_db
def test_whatsapp_scheduler_uses_unit_config_and_logs(monkeypatch):
    tz = ZoneInfo("America/Sao_Paulo")
    fixed_now = datetime(2026, 4, 26, 20, 0, tzinfo=tz)
    monkeypatch.setattr(ws.timezone, "now", lambda: fixed_now)
    monkeypatch.setattr(ws.timezone, "localtime", lambda value=None: fixed_now)

    unidade = models.Unidade.objects.create(cdUnidade=1, dsUnidade="Matriz", capacidade=20)
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=1, dsPerfilAcesso="Padrao")
    profissional = models.Profissional.objects.create(
        cdProfissional=1,
        profissional="Flavia Barros",
        celular="(11) 99999-8888",
        cdPerfilAcesso=perfil,
    )
    aluno = models.Aluno.objects.create(
        cdAluno=1,
        dsNome="Elena Vianna",
        dsCPF="SEM_CPF_1",
        sem_cpf=True,
        cdUnidade=unidade,
    )
    models.TelefoneAluno.objects.create(cdTelefone=1, cdAluno=aluno, dsTelefone="(11) 98888-7777")
    aluno2 = models.Aluno.objects.create(
        cdAluno=2,
        dsNome="Marina Souza",
        dsCPF="SEM_CPF_2",
        sem_cpf=True,
        cdUnidade=unidade,
    )
    models.TelefoneAluno.objects.create(cdTelefone=2, cdAluno=aluno2, dsTelefone="(11) 97777-6666")
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=1, dsTipoServico="Pilates")
    plano = models.Plano.objects.create(
        cdPlano=1,
        dsPlano="Pilates Mensal",
        cdTipoServico=tipo_servico,
        valor=120,
        aulas_por_semana=2,
        duracao_meses=1,
    )
    contrato = models.Contrato.objects.create(
        cdContrato=1,
        cdAluno=aluno,
        cdPlano=plano,
        cdUnidade=unidade,
        cdProfissional=profissional,
        modo_pagamento="PIX",
        valor_parcela=120,
        valor_total=120,
        dtInicioContrato=fixed_now.date(),
        dtFimContrato=fixed_now.date() + timedelta(days=7),
        status="ASSINADO",
    )
    sessao = models.AulaSessao.objects.create(
        unidade=unidade,
        tipoServico=tipo_servico,
        profissional=profissional,
        data=fixed_now.date() + timedelta(days=1),
        horaInicio=time(8, 0),
        horaFim=time(8, 50),
    )
    models.Reserva.objects.create(aluno=aluno, aulaSessao=sessao, status="RESERVADA")
    models.Reserva.objects.create(aluno=aluno2, aulaSessao=sessao, status="PENDENTE")
    models.WhatsappConfiguracao.objects.create(
        unidade=unidade,
        evolution_url="https://www.wasenderapi.com/api/send-message",
        evolution_senha="token-da-unidade",
        avisar_aluno=True,
        horario_aviso_aluno=time(19, 0),
        template_aviso_aluno="Aluno {aluno} {aulas}",
        avisar_professor=True,
        horario_aviso_professor=time(18, 0),
        template_aviso_professor="Prof {unidade} {horario}",
        avisar_renovacao=True,
        horario_aviso_renovacao=time(10, 0),
        template_aviso_renovacao="Renovacao {aluno} {dias_restantes}",
    )

    aluno_calls = []
    professor_calls = []

    def fake_send(self, aluno_obj, telefone, mensagem, tipo, contrato=None):
        aluno_calls.append(
            {
                "aluno": getattr(aluno_obj, "dsNome", None),
                "telefone": telefone,
                "mensagem": mensagem,
                "tipo": tipo,
                "contrato": contrato.id if contrato else None,
            }
        )
        return {"ok": True}

    class FakeClient:
        def send_message(self, telefone, mensagem):
            professor_calls.append({"telefone": telefone, "mensagem": mensagem})
            return {"ok": True}

    monkeypatch.setattr(ws.WhatsappService, "send", fake_send)
    monkeypatch.setattr(ws.WhatsappService, "_get_client_for_unidade", lambda self, unidade_obj: FakeClient())

    ws._run_jobs()

    assert len(aluno_calls) == 3
    assert {call["aluno"] for call in aluno_calls} == {"Elena Vianna", "Marina Souza"}
    assert professor_calls == [{"telefone": "5511999998888", "mensagem": "Prof Matriz 08:00 - Elena Vianna - Pilates\n08:00 - Marina Souza - Pilates"}]
    assert models.WhatsappAgendamentoLog.objects.count() == 4
    assert models.WhatsappAgendamentoLog.objects.filter(tipo=models.WhatsappMessageType.AUTOMATED_REMINDER).exists()
    assert models.WhatsappAgendamentoLog.objects.filter(tipo=models.WhatsappMessageType.PROFESSOR_SCHEDULE).exists()
    assert models.WhatsappAgendamentoLog.objects.filter(tipo=models.WhatsappMessageType.CONTRACT_RENEWAL).exists()

    ws._run_jobs()
    assert len(aluno_calls) == 3
    assert professor_calls == [{"telefone": "5511999998888", "mensagem": "Prof Matriz 08:00 - Elena Vianna - Pilates\n08:00 - Marina Souza - Pilates"}]
    assert models.WhatsappAgendamentoLog.objects.count() == 4
