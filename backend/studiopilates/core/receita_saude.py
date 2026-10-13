"""Arquivo de importacao em lote do Receita Saude (Receita Federal).

Formato conforme o Manual do Receita Saude v2.1 (perguntas 24 e 25): CSV com campos separados
por ponto e virgula, ate 1000 linhas, todos os pagamentos do mesmo ano, sem cabecalho.
O profissional importa o arquivo no e-CAC > Carne-Leao > Escrituracao > Importar Escrituracao.
Nao existe API para emitir o recibo direto: quem emite e a Receita, apos a importacao.

Colunas, na ordem:
 1 Data do pagamento (DD/MM/AAAA)          9 CPF do beneficiario (11 digitos)
 2 Codigo do rendimento (R01.001.001)     10 Ind. CPF nao informado (vazio)
 3 Codigo da ocupacao (231 = fisioterapeuta) 11 CNPJ (vazio)
 4 Valor do pagamento (1234,56)           12 Indicador de IRRF (vazio)
 5 Valor da deducao (vazio)               13 Valor IRRF (vazio)
 6 Descricao (ate 255)                    14 Indicador de recibo (S)
 7 Recebido de (PF)                       15 CPF do profissional (11 digitos)
 8 CPF do pagador (11 digitos)            16 Registro profissional (ate 15)
"""
import csv
import io
import re
import unicodedata
from decimal import Decimal

CODIGO_RENDIMENTO = "R01.001.001"
MAX_LINHAS = 1000
OCUPACOES = {
    "225": "Medico",
    "226": "Odontologo",
    "230": "Fonoaudiologo",
    "231": "Fisioterapeuta",
    "232": "Terapeuta ocupacional",
    "255": "Psicologo",
}


def so_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def cpf_valido(cpf):
    """Confere tamanho e digitos verificadores (a Receita recusa a linha com CPF invalido)."""
    cpf = so_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        if ((soma * 10) % 11) % 10 != int(cpf[tamanho]):
            return False
    return True


def _sem_acentos(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def descricao_recibo(conta, config):
    base = (getattr(conta, "descricao", "") or "").strip() or config.descricao_padrao
    competencia = (getattr(conta, "competencia", "") or "").strip()
    if competencia and competencia not in base:
        base = f"{base} - competencia {competencia}"
    # sem acento, sem ';' nem quebra de linha: evita problema de codificacao e de coluna
    limpo = _sem_acentos(base).replace(";", ",")
    limpo = re.sub(r"\s+", " ", limpo).strip()
    return limpo[:255]


def formatar_valor(valor):
    """1234.5 -> '1234,50' (virgula decimal, sem separador de milhar)."""
    return f"{Decimal(valor).quantize(Decimal('0.01'))}".replace(".", ",")


def problemas_da_configuracao(config):
    problemas = []
    if config is None:
        return ["Configure o CPF do profissional em Configuracoes > Receita Saude."]
    if not cpf_valido(config.cpf_profissional):
        problemas.append("CPF do profissional invalido em Configuracoes > Receita Saude.")
    if config.codigo_ocupacao not in OCUPACOES:
        problemas.append("Codigo de ocupacao invalido em Configuracoes > Receita Saude.")
    return problemas


def cpfs_do_aluno(aluno):
    """(cpf do pagador, cpf do beneficiario). O pagador padrao e o proprio aluno."""
    beneficiario = so_digitos(aluno.dsCPF) if not aluno.sem_cpf else ""
    pagador = so_digitos(getattr(aluno, "cpf_pagador_recibo", "")) or beneficiario
    return pagador, beneficiario


def problemas_da_conta(conta, aluno):
    """Motivos pelos quais esta cobranca nao pode virar linha do arquivo (lista vazia = ok)."""
    problemas = []
    if aluno is None:
        return ["Cobranca sem aluno vinculado."]
    if conta.status != "PAGO":
        problemas.append("Ainda nao esta paga.")
    if not conta.dtPagamento:
        problemas.append("Sem data de pagamento.")
    if not conta.valor or Decimal(conta.valor) <= 0:
        problemas.append("Valor deve ser maior que zero.")
    pagador, beneficiario = cpfs_do_aluno(aluno)
    if not beneficiario:
        problemas.append("Aluno sem CPF (obrigatorio no recibo).")
    elif not cpf_valido(beneficiario):
        problemas.append("CPF do aluno invalido.")
    if pagador and not cpf_valido(pagador):
        problemas.append("CPF do pagador invalido.")
    return problemas


def montar_linha(conta, aluno, config):
    pagador, beneficiario = cpfs_do_aluno(aluno)
    return [
        conta.dtPagamento.strftime("%d/%m/%Y"),
        CODIGO_RENDIMENTO,
        config.codigo_ocupacao,
        formatar_valor(conta.valor),
        "",  # valor da deducao: nao se aplica a recibo
        descricao_recibo(conta, config),
        "PF",
        pagador,
        beneficiario,
        "", "", "", "",  # ind. CPF nao informado, CNPJ, indicador de IRRF, valor IRRF
        "S",
        so_digitos(config.cpf_profissional),
        (config.registro_profissional or "").strip()[:15],
    ]


def gerar_arquivo(itens, config):
    """itens: lista de (conta, aluno). Retorna (conteudo_csv, erros).

    Se houver qualquer erro, nao devolve arquivo: a Receita rejeita o lote inteiro pelo erro de uma linha.
    """
    erros = problemas_da_configuracao(config)
    if not itens:
        erros.append("Selecione ao menos um pagamento.")
    if len(itens) > MAX_LINHAS:
        erros.append(f"O arquivo aceita ate {MAX_LINHAS} linhas; foram selecionados {len(itens)}.")
    for conta, aluno in itens:
        for problema in problemas_da_conta(conta, aluno):
            erros.append(f"{conta.dtVencimento:%d/%m/%Y} (R$ {formatar_valor(conta.valor or 0)}): {problema}")
    anos = {conta.dtPagamento.year for conta, _ in itens if conta.dtPagamento}
    if len(anos) > 1:
        erros.append("Todos os pagamentos do arquivo devem ser do mesmo ano (selecionados: " + ", ".join(str(a) for a in sorted(anos)) + ").")
    if erros:
        return None, erros

    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_NONE, escapechar="\\")
    for conta, aluno in itens:
        escritor.writerow(montar_linha(conta, aluno, config))
    return saida.getvalue(), []
