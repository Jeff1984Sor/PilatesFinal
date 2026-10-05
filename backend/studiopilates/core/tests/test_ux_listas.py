from datetime import date, time

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from studiopilates.core import models


@pytest.fixture
def base(db, django_user_model):
    django_user_model.objects.create_user(username="user", password="pass")
    unidade = models.Unidade.objects.create(cdUnidade=1, dsUnidade="Matriz", capacidade=6, duracao_aula_minutos=50)
    tipo = models.TipoServico.objects.create(cdTipoServico=1, dsTipoServico="Pilates")
    return unidade, tipo


def _aluno(unidade, cd, nome, status="ATIVO"):
    return models.Aluno.objects.create(
        cdAluno=cd, dsNome=nome, dsCPF=f"000{cd}", dsRg="", dsEmail="", cdUnidade=unidade, cdTermoUso=None, status=status
    )


def test_lista_de_alunos_tem_chips_e_filtra_por_situacao(client, base):
    unidade, _ = base
    _aluno(unidade, 1, "Ana")
    _aluno(unidade, 2, "Bia")
    _aluno(unidade, 3, "Carla", status="INATIVO")
    client.login(username="user", password="pass")

    resp = client.get(reverse("alunos_list"))
    chips = {c["label"]: c["n"] for c in resp.context["status_chips"]}
    assert chips == {"Ativos": 2, "Inativos": 1, "Todos": 3}
    assert [a.dsNome for a in resp.context["page"]] == ["Ana", "Bia"]

    resp = client.get(reverse("alunos_list"), {"status": "INATIVO"})
    assert [a.dsNome for a in resp.context["page"]] == ["Carla"]
    assert resp.context["status_atual"] == "INATIVO"

    resp = client.get(reverse("alunos_list"), {"status": "TODOS"})
    assert len(resp.context["page"]) == 3


def test_contas_a_receber_chips_somam_valor_por_situacao(client, base):
    client.login(username="user", password="pass")
    hoje = date.today()
    models.ContasReceber.objects.create(status="ABERTO", valor=100, dtVencimento=hoje)
    models.ContasReceber.objects.create(status="ABERTO", valor=50, dtVencimento=hoje)
    models.ContasReceber.objects.create(status="PAGO", valor=30, dtVencimento=hoje)

    resp = client.get(reverse("contas_receber_list"))
    por_rotulo = {c["label"]: c for c in resp.context["status_chips"]}
    assert por_rotulo["Todos"]["n"] == 3
    assert por_rotulo["ABERTO"]["n"] == 2 and por_rotulo["ABERTO"]["soma"] == 150

    resp = client.get(reverse("contas_receber_list"), {"status": "PAGO"})
    assert len(resp.context["page"]) == 1


def test_duplicar_plano_cria_copia_com_novo_codigo(client, base):
    _, tipo = base
    client.login(username="user", password="pass")
    original = models.Plano.objects.create(cdPlano=7, dsPlano="Pilates 2x", cdTipoServico=tipo, valor=300, aulas_por_semana=2)

    resp = client.post(reverse("planos_duplicar", args=[original.id]))
    assert resp.status_code == 302
    copia = models.Plano.objects.exclude(pk=original.pk).get()
    assert copia.dsPlano == "Pilates 2x (copia)"
    assert copia.cdPlano == 8
    assert copia.valor == 300 and copia.aulas_por_semana == 2
    assert models.Plano.objects.count() == 2


def test_duplicar_exige_post(client, base):
    _, tipo = base
    client.login(username="user", password="pass")
    original = models.Plano.objects.create(cdPlano=1, dsPlano="X", cdTipoServico=tipo, valor=1)
    client.get(reverse("planos_duplicar", args=[original.id]))
    assert models.Plano.objects.count() == 1


def test_agenda_semana_mostra_ocupacao_da_aula(client, base):
    unidade, tipo = base
    client.login(username="user", password="pass")
    hoje = date(2026, 10, 5)  # segunda-feira: a grade vai de segunda a sabado
    aula = models.AulaSessao.objects.create(
        unidade=unidade, tipoServico=tipo, data=hoje, horaInicio=time(9, 0), horaFim=time(9, 50)
    )
    for i in range(1, 4):
        models.Reserva.objects.create(aluno=_aluno(unidade, i, f"Aluna {i}"), aulaSessao=aula, status="RESERVADA")

    resp = client.get(reverse("aulas_semana"), {"week": hoje.isoformat()})
    assert resp.status_code == 200
    blocos = [b for d in resp.context["grid_days"] for b in d["blocks"]]
    assert len(blocos) == 3
    assert {b["ocup"] for b in blocos} == {"3/6"}


def test_capacidade_excedida_diz_qual_aula_e_quantas_vagas(base):
    unidade, tipo = base
    aula = models.AulaSessao.objects.create(
        unidade=unidade, tipoServico=tipo, data=date(2026, 10, 5), horaInicio=time(9, 0), horaFim=time(9, 50), capacidade=1
    )
    models.Reserva.objects.create(aluno=_aluno(unidade, 1, "Ana"), aulaSessao=aula, status="RESERVADA")
    segunda = models.Reserva(aluno=_aluno(unidade, 2, "Bia"), aulaSessao=aula, status="RESERVADA")

    with pytest.raises(ValidationError) as exc:
        segunda.clean()
    mensagem = exc.value.messages[0]
    assert "Capacidade excedida" in mensagem
    assert "05/10" in mensagem and "09:00" in mensagem and "1 de 1" in mensagem


def test_ficha_do_aluno_renderiza_atalhos_e_tema(client, base):
    unidade, _ = base
    aluno = _aluno(unidade, 1, "Ana")
    client.login(username="user", password="pass")

    resp = client.get(reverse("alunos_detail", args=[aluno.id]))
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "js-aba-atalho" in html
    assert "/static/css/marsala.css" in html and "/static/js/ux.js" in html


def test_lista_de_profissionais_mostra_login_e_perfil(client, base):
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=70, dsPerfilAcesso="Professor")
    prof = models.Profissional.objects.create(
        cdProfissional=70, profissional="Natalia", email="natalia@x.com", celular="159", cdPerfilAcesso=perfil
    )
    prof.refresh_from_db()
    client.login(username="user", password="pass")

    resp = client.get(reverse("profissionais_list"))
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "<th>Login</th>" in html and "<th>Perfil</th>" in html
    assert prof.user.username in html and "Professor" in html
    assert prof.login == prof.user.username and prof.perfil_acesso_nome == "Professor"
