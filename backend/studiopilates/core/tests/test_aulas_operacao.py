from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from studiopilates.core import models
from studiopilates.core import services


def test_gerar_parcelas_usa_quantidade_do_plano():
    parcelas = services.gerar_parcelas(100, date(2026, 1, 25), date(2026, 7, 25), 6)
    assert len(parcelas) == 6
    assert [parcela["vencimento"].isoformat() for parcela in parcelas] == [
        "2026-01-25",
        "2026-02-25",
        "2026-03-25",
        "2026-04-25",
        "2026-05-25",
        "2026-06-25",
    ]


@pytest.mark.django_db
def test_operacao_listagem_filtra_data(client, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="pass")
    client.login(username="user", password="pass")

    unidade = models.Unidade.objects.create(cdUnidade=1, dsUnidade="Unidade Central", capacidade=5, duracao_aula_minutos=50)
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=1, dsPerfilAcesso="Padrao")
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=1, dsTipoServico="Pilates")
    profissional = models.Profissional.objects.create(cdProfissional=1, profissional="Flavia", email="", celular="", cdPerfilAcesso=perfil)
    aluno = models.Aluno.objects.create(cdAluno=1, dsNome="Elena", dsCPF="123", dsRg="", dsEmail="", cdUnidade=unidade, cdTermoUso=None)
    plano = models.Plano.objects.create(cdPlano=1, dsPlano="Pilates 2x", cdTipoServico=tipo_servico, valor=100, aulas_por_semana=2, duracao_meses=1)
    contrato = models.Contrato.objects.create(
        cdContrato=1,
        cdAluno=aluno,
        cdPlano=plano,
        cdUnidade=unidade,
        cdProfissional=profissional,
        valor_parcela=100,
        valor_total=100,
        dtInicioContrato=timezone.now().date(),
        dtFimContrato=timezone.now().date(),
        status="ASSINADO",
    )
    aula = models.AulaSessao.objects.create(
        unidade=unidade,
        tipoServico=tipo_servico,
        profissional=profissional,
        data=timezone.now().date(),
        horaInicio=timezone.now().time().replace(second=0, microsecond=0),
        horaFim=(timezone.now() + timezone.timedelta(minutes=50)).time().replace(second=0, microsecond=0),
        capacidade=5,
    )
    models.Reserva.objects.create(aluno=aluno, aulaSessao=aula, status="RESERVADA")
    models.TelefoneAluno.objects.create(cdTelefone=1, cdAluno=aluno, dsTelefone="11999998888")
    models.ContasReceber.objects.create(contrato=contrato, status="ABERTO", valor=100, dtVencimento=timezone.now().date())

    url = reverse("aulas_operacao_api")
    resp = client.get(url, {"data": timezone.now().date().isoformat(), "periodo": "hoje"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 1
    assert payload["items"][0]["aluno"]["nome"] == "Elena"


@pytest.mark.django_db
def test_operacao_salvar_evolucao_finaliza(client, django_user_model):
    user = django_user_model.objects.create_user(username="user2", password="pass")
    client.login(username="user2", password="pass")

    unidade = models.Unidade.objects.create(cdUnidade=2, dsUnidade="Unidade 2", capacidade=5, duracao_aula_minutos=50)
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=2, dsPerfilAcesso="Padrao")
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=2, dsTipoServico="Pilates")
    profissional = models.Profissional.objects.create(cdProfissional=2, profissional="Prof", email="", celular="", cdPerfilAcesso=perfil)
    aluno = models.Aluno.objects.create(cdAluno=2, dsNome="Aluno", dsCPF="234", dsRg="", dsEmail="", cdUnidade=unidade, cdTermoUso=None)
    aula = models.AulaSessao.objects.create(
        unidade=unidade,
        tipoServico=tipo_servico,
        profissional=profissional,
        data=timezone.now().date(),
        horaInicio=timezone.now().time().replace(second=0, microsecond=0),
        horaFim=(timezone.now() + timezone.timedelta(minutes=50)).time().replace(second=0, microsecond=0),
        capacidade=5,
    )
    reserva = models.Reserva.objects.create(aluno=aluno, aulaSessao=aula, status="RESERVADA")

    url = reverse("aulas_evolucao_api", args=[reserva.id])
    resp = client.post(url, data={"texto": "Boa aula", "profissional_id": profissional.id, "finalizar": True})
    assert resp.status_code == 200
    reserva.refresh_from_db()
    assert reserva.status == "CONCLUIDA"


@pytest.mark.django_db
def test_operacao_salvar_avaliacao(client, django_user_model):
    user = django_user_model.objects.create_user(username="user4", password="pass")
    client.login(username="user4", password="pass")

    unidade = models.Unidade.objects.create(cdUnidade=4, dsUnidade="Unidade 4", capacidade=5, duracao_aula_minutos=50)
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=4, dsPerfilAcesso="Padrao")
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=4, dsTipoServico="Pilates")
    profissional = models.Profissional.objects.create(cdProfissional=4, profissional="Prof", email="", celular="", cdPerfilAcesso=perfil)
    aluno = models.Aluno.objects.create(cdAluno=4, dsNome="Aluno 4", dsCPF="456", dsRg="", dsEmail="", cdUnidade=unidade, cdTermoUso=None)
    aula = models.AulaSessao.objects.create(
        unidade=unidade,
        tipoServico=tipo_servico,
        profissional=profissional,
        data=timezone.now().date(),
        horaInicio=timezone.now().time().replace(second=0, microsecond=0),
        horaFim=(timezone.now() + timezone.timedelta(minutes=50)).time().replace(second=0, microsecond=0),
        capacidade=5,
    )
    reserva = models.Reserva.objects.create(aluno=aluno, aulaSessao=aula, status="RESERVADA")

    url = reverse("aulas_avaliacoes_api", args=[reserva.id])
    resp = client.post(url, data={"texto": "Boa evolucao", "profissional_id": profissional.id})
    assert resp.status_code == 200
    assert models.AvaliacaoAluno.objects.filter(reserva=reserva).count() == 1


@pytest.mark.django_db
def test_operacao_lista_cobranca(client, django_user_model):
    user = django_user_model.objects.create_user(username="user5", password="pass")
    client.login(username="user5", password="pass")

    unidade = models.Unidade.objects.create(cdUnidade=5, dsUnidade="Unidade 5", capacidade=5, duracao_aula_minutos=50)
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=5, dsPerfilAcesso="Padrao")
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=5, dsTipoServico="Pilates")
    profissional = models.Profissional.objects.create(cdProfissional=5, profissional="Prof", email="", celular="", cdPerfilAcesso=perfil)
    aluno = models.Aluno.objects.create(cdAluno=5, dsNome="Aluno 5", dsCPF="567", dsRg="", dsEmail="", cdUnidade=unidade, cdTermoUso=None)
    plano = models.Plano.objects.create(cdPlano=5, dsPlano="Plano", cdTipoServico=tipo_servico, valor=100, aulas_por_semana=2, duracao_meses=1)
    contrato = models.Contrato.objects.create(
        cdContrato=5,
        cdAluno=aluno,
        cdPlano=plano,
        cdUnidade=unidade,
        cdProfissional=profissional,
        valor_parcela=100,
        valor_total=100,
        dtInicioContrato=timezone.now().date(),
        dtFimContrato=timezone.now().date(),
        status="ASSINADO",
    )
    aula = models.AulaSessao.objects.create(
        unidade=unidade,
        tipoServico=tipo_servico,
        profissional=profissional,
        data=timezone.now().date(),
        horaInicio=timezone.now().time().replace(second=0, microsecond=0),
        horaFim=(timezone.now() + timezone.timedelta(minutes=50)).time().replace(second=0, microsecond=0),
        capacidade=5,
    )
    reserva = models.Reserva.objects.create(aluno=aluno, aulaSessao=aula, status="RESERVADA")
    models.ContasReceber.objects.create(contrato=contrato, status="ABERTO", valor=100, dtVencimento=timezone.now().date())

    url = reverse("aulas_cobranca_api", args=[reserva.id])
    resp = client.get(url)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["items"]
@pytest.mark.django_db
def test_operacao_atualiza_status(client, django_user_model):
    user = django_user_model.objects.create_user(username="user3", password="pass")
    client.login(username="user3", password="pass")

    unidade = models.Unidade.objects.create(cdUnidade=3, dsUnidade="Unidade 3", capacidade=5, duracao_aula_minutos=50)
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=3, dsPerfilAcesso="Padrao")
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=3, dsTipoServico="Pilates")
    profissional = models.Profissional.objects.create(cdProfissional=3, profissional="Prof", email="", celular="", cdPerfilAcesso=perfil)
    aluno = models.Aluno.objects.create(cdAluno=3, dsNome="Aluno 3", dsCPF="345", dsRg="", dsEmail="", cdUnidade=unidade, cdTermoUso=None)
    aula = models.AulaSessao.objects.create(
        unidade=unidade,
        tipoServico=tipo_servico,
        profissional=profissional,
        data=timezone.now().date(),
        horaInicio=timezone.now().time().replace(second=0, microsecond=0),
        horaFim=(timezone.now() + timezone.timedelta(minutes=50)).time().replace(second=0, microsecond=0),
        capacidade=5,
    )
    reserva = models.Reserva.objects.create(aluno=aluno, aulaSessao=aula, status="RESERVADA")

    url = reverse("aulas_status_api", args=[reserva.id])
    resp = client.post(url, data={"acao": "faltou"})
    assert resp.status_code == 200
    reserva.refresh_from_db()
    assert reserva.status == "FALTOU_SEM_AVISAR"
