from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.urls import reverse

from studiopilates.core import models, receita_saude

CPF_PROFISSIONAL = "52998224725"  # CPFs de teste com digito verificador valido
CPF_ALUNO = "11144477735"
CPF_PAI = "39053344705"


def _config(**extra):
    base = dict(cpf_profissional=CPF_PROFISSIONAL, registro_profissional="79013-F", codigo_ocupacao="231",
                descricao_padrao="Aulas de Pilates")
    base.update(extra)
    return SimpleNamespace(**base)


def _aluno(cpf=CPF_ALUNO, pagador="", sem_cpf=False):
    return SimpleNamespace(dsCPF=cpf, sem_cpf=sem_cpf, cpf_pagador_recibo=pagador)


def _conta(valor="150.00", pago=date(2026, 10, 5), status="PAGO", descricao="", competencia="2026-10"):
    return SimpleNamespace(status=status, dtPagamento=pago, valor=Decimal(valor), descricao=descricao,
                           competencia=competencia, dtVencimento=date(2026, 10, 5))


def test_cpf_valido():
    assert receita_saude.cpf_valido("529.982.247-25")
    assert receita_saude.cpf_valido(CPF_ALUNO)
    assert not receita_saude.cpf_valido("111.111.111-11")
    assert not receita_saude.cpf_valido("529.982.247-24")
    assert not receita_saude.cpf_valido("123")
    assert not receita_saude.cpf_valido("")


def test_linha_segue_o_layout_oficial_coluna_a_coluna():
    conteudo, erros = receita_saude.gerar_arquivo([(_conta("1234.5"), _aluno())], _config())
    assert erros == []
    assert conteudo.endswith("\r\n")
    colunas = conteudo.rstrip("\r\n").split(";")
    assert len(colunas) == 16
    assert colunas == [
        "05/10/2026",        # 1 data do pagamento
        "R01.001.001",       # 2 codigo do rendimento (fixo)
        "231",               # 3 ocupacao: fisioterapeuta
        "1234,50",           # 4 valor, virgula decimal, sem milhar
        "",                  # 5 deducao: vazio
        "Aulas de Pilates - competencia 2026-10",  # 6 descricao
        "PF",                # 7 recebido de
        CPF_ALUNO,           # 8 cpf do pagador
        CPF_ALUNO,           # 9 cpf do beneficiario
        "", "", "", "",      # 10-13 vazios
        "S",                 # 14 indicador de recibo
        CPF_PROFISSIONAL,    # 15 cpf do profissional
        "79013-F",           # 16 registro profissional
    ]


def test_pagador_diferente_do_aluno_vai_na_coluna_do_pagador():
    conteudo, erros = receita_saude.gerar_arquivo([(_conta(), _aluno(pagador="390.533.447-05"))], _config())
    colunas = conteudo.rstrip("\r\n").split(";")
    assert erros == [] and colunas[7] == CPF_PAI and colunas[8] == CPF_ALUNO


def test_descricao_sem_acento_sem_ponto_e_virgula_e_ate_255():
    conta = _conta(descricao="Sessão; fisioterapia\ncom acentuação " + "x" * 400, competencia="")
    linha = receita_saude.montar_linha(conta, _aluno(), _config())
    descricao = linha[5]
    assert ";" not in descricao and "\n" not in descricao
    assert descricao.startswith("Sessao, fisioterapia com acentuacao")
    assert len(descricao) == 255


@pytest.mark.parametrize(
    "conta,aluno,trecho",
    [
        (_conta(status="ABERTO"), _aluno(), "nao esta paga"),
        (_conta(pago=None), _aluno(), "Sem data de pagamento"),
        (_conta(valor="0"), _aluno(), "maior que zero"),
        (_conta(), _aluno(cpf=""), "sem CPF"),
        (_conta(), _aluno(sem_cpf=True), "sem CPF"),
        (_conta(), _aluno(cpf="12345678900"), "CPF do aluno invalido"),
        (_conta(), _aluno(pagador="11111111111"), "CPF do pagador invalido"),
    ],
)
def test_nao_gera_arquivo_com_pagamento_problematico(conta, aluno, trecho):
    conteudo, erros = receita_saude.gerar_arquivo([(conta, aluno)], _config())
    assert conteudo is None
    assert any(trecho.lower() in erro.lower() for erro in erros), erros


def test_nao_mistura_anos_nem_passa_de_1000_linhas():
    itens = [(_conta(pago=date(2025, 12, 30)), _aluno()), (_conta(pago=date(2026, 1, 2)), _aluno())]
    conteudo, erros = receita_saude.gerar_arquivo(itens, _config())
    assert conteudo is None and any("mesmo ano" in e for e in erros)

    muitos = [(_conta(), _aluno())] * 1001
    conteudo, erros = receita_saude.gerar_arquivo(muitos, _config())
    assert conteudo is None and any("1000" in e for e in erros)

    ok, erros = receita_saude.gerar_arquivo([(_conta(), _aluno())] * 1000, _config())
    assert erros == [] and ok.count("\r\n") == 1000


def test_exige_configuracao_valida_e_ao_menos_um_pagamento():
    _, erros = receita_saude.gerar_arquivo([(_conta(), _aluno())], None)
    assert any("Configure" in e for e in erros)
    _, erros = receita_saude.gerar_arquivo([(_conta(), _aluno())], _config(cpf_profissional="123"))
    assert any("CPF do profissional" in e for e in erros)
    _, erros = receita_saude.gerar_arquivo([(_conta(), _aluno())], _config(codigo_ocupacao="999"))
    assert any("ocupacao" in e.lower() for e in erros)
    _, erros = receita_saude.gerar_arquivo([], _config())
    assert any("ao menos um" in e for e in erros)


# ---------------------------------------------------------------- telas

@pytest.fixture
def cenario(db, django_user_model):
    django_user_model.objects.create_superuser(username="admin", password="pass")
    unidade = models.Unidade.objects.create(cdUnidade=60, dsUnidade="Matriz", capacidade=6, duracao_aula_minutos=50)
    aluno = models.Aluno.objects.create(cdAluno=60, dsNome="Ana Souza", dsCPF=CPF_ALUNO, dsRg="", dsEmail="", cdUnidade=unidade)
    outro = models.Aluno.objects.create(cdAluno=61, dsNome="Bia Lima", dsCPF=CPF_PAI, dsRg="", dsEmail="", cdUnidade=unidade)
    models.ReceitaSaudeConfig.objects.create(cpf_profissional=CPF_PROFISSIONAL, registro_profissional="79013-F")

    def conta(al, valor, pago):
        return models.ContasReceber.objects.create(
            aluno=al, status="PAGO", valor=valor, dtVencimento=pago, dtPagamento=pago, descricao="Mensalidade"
        )

    return {
        "aluno": aluno,
        "outro": outro,
        "c1": conta(aluno, 150, date(2026, 10, 5)),
        "c2": conta(aluno, 200, date(2026, 10, 20)),
        "alheia": conta(outro, 99, date(2026, 10, 6)),
    }


def test_gerar_arquivo_baixa_csv_e_marca_como_gerado(client, cenario):
    client.login(username="admin", password="pass")
    url = reverse("aluno_receita_saude_arquivo", args=[cenario["aluno"].id])

    resp = client.post(url, {"acao": "gerar", "contas": [cenario["c1"].id, cenario["c2"].id]})
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/csv")
    assert "receita-saude-ana-souza" in resp["Content-Disposition"]
    linhas = resp.content.decode().strip().split("\r\n")
    assert [l.split(";")[0] for l in linhas] == ["05/10/2026", "20/10/2026"]
    assert [l.split(";")[3] for l in linhas] == ["150,00", "200,00"]
    cenario["c1"].refresh_from_db()
    assert cenario["c1"].recibo_saude_gerado_em is not None

    # segunda vez: bloqueia para nao emitir o recibo em duplicidade
    resp = client.post(url, {"acao": "gerar", "contas": [cenario["c1"].id]})
    assert resp.status_code == 302 and "text/csv" not in resp.get("Content-Type", "")

    # liberar permite gerar de novo
    client.post(url, {"acao": "liberar", "contas": [cenario["c1"].id]})
    cenario["c1"].refresh_from_db()
    assert cenario["c1"].recibo_saude_gerado_em is None
    assert client.post(url, {"acao": "gerar", "contas": [cenario["c1"].id]}).status_code == 200


def test_pagamento_de_outro_aluno_e_ignorado(client, cenario):
    client.login(username="admin", password="pass")
    url = reverse("aluno_receita_saude_arquivo", args=[cenario["aluno"].id])
    resp = client.post(url, {"acao": "gerar", "contas": [cenario["alheia"].id]})
    assert resp.status_code == 302
    cenario["alheia"].refresh_from_db()
    assert cenario["alheia"].recibo_saude_gerado_em is None


def test_sem_configuracao_nao_gera(client, cenario):
    models.ReceitaSaudeConfig.objects.all().delete()
    client.login(username="admin", password="pass")
    url = reverse("aluno_receita_saude_arquivo", args=[cenario["aluno"].id])
    resp = client.post(url, {"acao": "gerar", "contas": [cenario["c1"].id]})
    assert resp.status_code == 302
    cenario["c1"].refresh_from_db()
    assert cenario["c1"].recibo_saude_gerado_em is None


def test_ficha_mostra_pagamentos_prontos_e_avisos(client, cenario):
    client.login(username="admin", password="pass")
    html = client.get(reverse("alunos_detail", args=[cenario["aluno"].id])).content.decode()
    assert "Recibos do Receita Saude" in html
    assert html.count('name="contas"') == 2 and "Pronto" in html

    models.ReceitaSaudeConfig.objects.all().delete()
    html = client.get(reverse("alunos_detail", args=[cenario["aluno"].id])).content.decode()
    assert "Configure o CPF do profissional" in html


def test_salvar_cpf_do_pagador(client, cenario):
    client.login(username="admin", password="pass")
    url = reverse("aluno_receita_saude_pagador", args=[cenario["aluno"].id])
    client.post(url, {"cpf_pagador": "390.533.447-05"})
    cenario["aluno"].refresh_from_db()
    assert cenario["aluno"].cpf_pagador_recibo == CPF_PAI
    client.post(url, {"cpf_pagador": "111.111.111-11"})  # invalido: nao grava
    cenario["aluno"].refresh_from_db()
    assert cenario["aluno"].cpf_pagador_recibo == CPF_PAI


def test_tela_de_configuracao_valida_cpf(client, cenario):
    client.login(username="admin", password="pass")
    url = reverse("receita_saude_config")
    assert client.get(url).status_code == 200
    resp = client.post(url, {"cpf_profissional": "123", "codigo_ocupacao": "231", "descricao_padrao": "x"})
    assert resp.status_code == 200 and "CPF invalido" in resp.content.decode()
    resp = client.post(url, {"cpf_profissional": "529.982.247-25", "registro_profissional": "1-F",
                             "codigo_ocupacao": "231", "descricao_padrao": "Aulas"})
    assert resp.status_code == 302
    assert models.ReceitaSaudeConfig.objects.order_by("-id").first().cpf_profissional == CPF_PROFISSIONAL


def test_professor_nao_acessa_nada_do_receita_saude(client, cenario):
    perfil = models.PerfilAcesso.objects.create(cdPerfilAcesso=61, dsPerfilAcesso="Professor")
    prof = models.Profissional.objects.create(
        cdProfissional=61, profissional="Natalia", email="n@x.com", celular="", cdPerfilAcesso=perfil
    )
    prof.refresh_from_db()
    prof.user.set_password("p")
    prof.user.save()
    client.login(username=prof.user.username, password="p")
    aluno_id = cenario["aluno"].id
    assert client.get(reverse("receita_saude_config")).status_code == 302
    assert client.post(reverse("aluno_receita_saude_arquivo", args=[aluno_id]), {"acao": "gerar"}).status_code == 302
    assert client.post(reverse("aluno_receita_saude_pagador", args=[aluno_id]), {"cpf_pagador": CPF_PAI}).status_code == 302
    cenario["aluno"].refresh_from_db()
    assert cenario["aluno"].cpf_pagador_recibo == ""
