import pytest
from django.urls import reverse
from django.utils import timezone

from studiopilates.core import models


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
