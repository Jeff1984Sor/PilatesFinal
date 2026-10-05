from datetime import date, time

import pytest
from django.urls import get_resolver, URLPattern, URLResolver, reverse

from studiopilates.core import models
from studiopilates.core.middleware import (
    POR_ALUNO,
    POR_AVALIACAO,
    POR_EVOLUCAO,
    POR_RESERVA,
    ROTAS_LIVRES,
)


@pytest.fixture
def cenario(db, django_user_model):
    """Duas professoras, cada uma com um aluno em aula; mais um admin."""
    unidade = models.Unidade.objects.create(cdUnidade=90, dsUnidade="Matriz", capacidade=6, duracao_aula_minutos=50)
    tipo = models.TipoServico.objects.create(cdTipoServico=90, dsTipoServico="Pilates")
    perfil_prof = models.PerfilAcesso.objects.create(cdPerfilAcesso=90, dsPerfilAcesso="Professor")
    perfil_admin = models.PerfilAcesso.objects.create(cdPerfilAcesso=91, dsPerfilAcesso="Administrador")

    def profissional(cd, nome, perfil):
        prof = models.Profissional.objects.create(
            cdProfissional=cd, profissional=nome, email=f"{nome.lower()}@x.com", celular="", cdPerfilAcesso=perfil
        )
        prof.refresh_from_db()
        prof.user.set_password("senha")
        prof.user.save()
        return prof

    natalia = profissional(90, "Natalia", perfil_prof)
    ranieli = profissional(91, "Ranieli", perfil_prof)
    gestora = profissional(92, "Gestora", perfil_admin)

    def aluno_com_aula(cd, nome, prof):
        aluno = models.Aluno.objects.create(
            cdAluno=cd, dsNome=nome, dsCPF=f"9{cd}", dsRg="", dsEmail="", cdUnidade=unidade, cdTermoUso=None
        )
        aula = models.AulaSessao.objects.create(
            unidade=unidade, tipoServico=tipo, profissional=prof, data=date(2026, 10, 5),
            horaInicio=time(9, 0), horaFim=time(9, 50),
        )
        reserva = models.Reserva.objects.create(aluno=aluno, aulaSessao=aula, status="RESERVADA")
        evolucao = models.EvolucaoAluno.objects.create(reserva=reserva, profissional=prof, texto="ok")
        avaliacao = models.AvaliacaoAluno.objects.create(reserva=reserva, profissional=prof, texto="ok")
        return aluno, reserva, evolucao, avaliacao

    return {
        "natalia": natalia,
        "ranieli": ranieli,
        "gestora": gestora,
        "da_natalia": aluno_com_aula(90, "Aluna da Natalia", natalia),
        "da_ranieli": aluno_com_aula(91, "Aluna da Ranieli", ranieli),
    }


def entrar(client, prof):
    assert client.login(username=prof.user.username, password="senha")


ROTAS_PROIBIDAS = [
    "contas_receber_list", "contas_pagar_list", "contas_pagar_exportar_excel", "contas_pagar_exportar_pdf",
    "fluxo_caixa", "fluxo_caixa_exportar_excel", "fluxo_caixa_exportar_pdf", "dre_view", "dre_relatorio",
    "conta_bancaria", "contratos_list", "contratos_gestao", "planos_list", "alunos_list", "profissionais_list",
    "perfis_acesso_list", "unidades_list", "tokens_integracao_list", "email_config", "whatsapp_config",
    "whatsapp_historico", "totalpass_config", "comunicado_geral", "aviso_aluno_config", "modelos_contrato_list",
    "modelos_evolucao_list", "termos_list", "wizard_step1", "mayasec",
]


@pytest.mark.parametrize("nome", ROTAS_PROIBIDAS)
def test_professor_nao_abre_telas_administrativas(client, cenario, nome):
    entrar(client, cenario["natalia"])
    resp = client.get(reverse(nome))
    assert resp.status_code in (302, 403), f"{nome} abriu para professor ({resp.status_code})"
    if resp.status_code == 302:
        assert resp["Location"].rstrip("/").endswith(("/agenda/aulas", "")) or resp["Location"] in ("/", "/agenda/aulas/")


def test_professor_abre_agenda_e_operacao(client, cenario):
    entrar(client, cenario["natalia"])
    for nome in ("aulas_list", "aulas_semana", "aulas_operacao_api", "perfil"):
        assert client.get(reverse(nome)).status_code == 200, nome


def test_professor_so_ve_as_proprias_aulas_na_operacao(client, cenario):
    entrar(client, cenario["natalia"])
    resp = client.get(reverse("aulas_operacao_api"), {"data": "2026-10-05", "periodo": "hoje"})
    nomes = [i["aluno"]["nome"] for i in resp.json()["items"]]
    assert nomes == ["Aluna da Natalia"]


def test_operacao_nao_mostra_cobranca_para_professor(client, cenario):
    aluno, _, _, _ = cenario["da_natalia"]
    plano = models.Plano.objects.create(
        cdPlano=90, dsPlano="P", cdTipoServico=models.TipoServico.objects.get(cdTipoServico=90), valor=100
    )
    contrato = models.Contrato.objects.create(
        cdContrato=90, cdAluno=aluno, cdPlano=plano, cdUnidade=models.Unidade.objects.get(cdUnidade=90),
        cdProfissional=cenario["natalia"], valor_parcela=100, valor_total=100,
        dtInicioContrato=date(2026, 10, 1), dtFimContrato=date(2026, 10, 31), status="ASSINADO",
    )
    models.ContasReceber.objects.create(contrato=contrato, status="ABERTO", valor=100, dtVencimento=date(2026, 10, 5))
    entrar(client, cenario["natalia"])
    item = client.get(reverse("aulas_operacao_api"), {"data": "2026-10-05", "periodo": "hoje"}).json()["items"][0]
    assert item["flags"]["cobranca_pendente"] is False


def test_professor_nao_abre_cobranca_nem_exclusao_de_reserva(client, cenario):
    _, reserva, _, _ = cenario["da_natalia"]
    entrar(client, cenario["natalia"])
    r = client.get(reverse("aulas_cobranca_api", args=[reserva.id]))
    assert r.status_code == 403 and r.json()["error"]
    assert client.post(reverse("aulas_reserva_excluir", args=[reserva.id])).status_code == 403
    assert models.Reserva.objects.filter(pk=reserva.pk).exists()


def test_professor_acessa_evolucao_da_propria_aula(client, cenario):
    _, reserva, _, _ = cenario["da_natalia"]
    entrar(client, cenario["natalia"])
    assert client.get(reverse("aulas_evolucao_api", args=[reserva.id])).status_code == 200
    assert client.get(reverse("aulas_avaliacoes_api", args=[reserva.id])).status_code == 200


def test_professor_nao_acessa_reserva_de_outra_professora(client, cenario):
    _, reserva_alheia, evolucao_alheia, avaliacao_alheia = cenario["da_ranieli"]
    entrar(client, cenario["natalia"])
    for nome in ("aulas_evolucao_api", "aulas_avaliacoes_api", "aulas_historico_api", "aulas_status_api",
                 "aulas_whatsapp_now_api", "aulas_evolucao_enriquecer_api"):
        r = client.get(reverse(nome, args=[reserva_alheia.id]))
        assert r.status_code == 403, f"{nome} deixou ver reserva alheia"
    assert client.get(reverse("reservas_evoluir", args=[reserva_alheia.id])).status_code in (302, 403)
    assert client.post(reverse("alunos_evolucao_update", args=[evolucao_alheia.id])).status_code == 302
    assert client.post(reverse("alunos_avaliacao_delete", args=[avaliacao_alheia.id])).status_code == 302
    assert models.AvaliacaoAluno.objects.filter(pk=avaliacao_alheia.pk).exists()


def test_ficha_so_do_proprio_aluno_e_sem_abas_financeiras(client, cenario):
    meu, _, _, _ = cenario["da_natalia"]
    alheio, _, _, _ = cenario["da_ranieli"]
    entrar(client, cenario["natalia"])

    resp = client.get(reverse("alunos_detail", args=[meu.id]))
    assert resp.status_code == 200
    html = resp.content.decode()
    for aba in ("tab-contratos", "tab-financeiro", "tab-whatsapp", "tab-documentos", "tab-imagem", "tab-agenda"):
        assert f'id="{aba}"' not in html, f"{aba} apareceu para o professor"
    assert 'id="tab-evolucao"' in html and 'id="tab-avaliacao"' in html

    assert client.get(reverse("alunos_detail", args=[alheio.id])).status_code == 302


def test_admin_continua_com_acesso_total(client, cenario):
    entrar(client, cenario["gestora"])
    for nome in ("contas_receber_list", "alunos_list", "email_config", "contratos_gestao", "aulas_list"):
        assert client.get(reverse(nome)).status_code == 200, nome
    meu, _, _, _ = cenario["da_natalia"]
    html = client.get(reverse("alunos_detail", args=[meu.id])).content.decode()
    assert 'id="tab-financeiro"' in html and 'id="tab-whatsapp"' in html


def _todas_as_rotas():
    def andar(patterns):
        for p in patterns:
            if isinstance(p, URLResolver):
                yield from andar(p.url_patterns)
            elif isinstance(p, URLPattern) and p.name:
                yield p.name
    return set(andar(get_resolver().url_patterns))


def test_liberacoes_do_professor_apontam_para_rotas_que_existem():
    """Se alguem renomear uma rota, a liberacao some em silencio; este teste avisa."""
    existentes = _todas_as_rotas()
    liberadas = set(ROTAS_LIVRES) | set(POR_RESERVA) | set(POR_ALUNO) | set(POR_EVOLUCAO) | set(POR_AVALIACAO)
    assert not (liberadas - existentes), f"rotas inexistentes: {liberadas - existentes}"


def test_comando_set_acesso_professor(cenario):
    from io import StringIO

    from django.core.management import call_command
    from django.core.management.base import CommandError

    gestora = cenario["gestora"]
    # simulacao nao grava
    call_command("set_acesso_professor", "Gestora", "--simular", stdout=StringIO())
    gestora.refresh_from_db()
    assert gestora.cdPerfilAcesso.dsPerfilAcesso == "Administrador"

    out = StringIO()
    call_command("set_acesso_professor", "Gestora", stdout=out)
    gestora.refresh_from_db()
    assert gestora.cdPerfilAcesso.dsPerfilAcesso.lower() == "professor"
    assert gestora.user.username in out.getvalue()

    with pytest.raises(CommandError):
        call_command("set_acesso_professor", "NomeQueNaoExiste", stdout=StringIO())
