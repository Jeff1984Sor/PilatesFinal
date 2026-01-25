import pytest
from datetime import date
from studiopilates.core import models, services


@pytest.mark.django_db
def test_geracao_contas_receber_mensal():
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=1, dsPerfilAcesso="Padrao")
    prof = models.Profissional.objects.create(cdProfissional=1, profissional="Prof", cdPerfilAcesso=perfil)
    unidade = models.Unidade.objects.create(cdUnidade=1, dsUnidade="Un1", capacidade=10)
    termo = models.TermoUso.objects.create(cdTermoUso=1, dsTermoUso="Termo")
    aluno = models.Aluno.objects.create(cdAluno=1, dsNome="Aluno", dsCPF="52998224725", dsRg="1", cdUnidade=unidade, cdTermoUso=termo)
    tipo_servico = models.TipoServico.objects.create(cdTipoServico=1, dsTipoServico="Servico")
    plano = models.Plano.objects.create(cdPlano=1, dsPlano="Plano", cdTipoServico=tipo_servico, duracao_meses=1)

    contrato_data = {
        "cdContrato": 1,
        "cdAluno": aluno,
        "cdPlano": plano,
        "cdUnidade": unidade,
        "cdProfissional": prof,
        "dtInicioContrato": date(2024, 1, 1),
        "dtFimContrato": date(2024, 3, 1),
    }
    contrato, _ = services.criar_contrato_e_agenda(contrato_data, 100.0)
    assert models.ContasReceber.objects.filter(contrato=contrato).count() >= 2
