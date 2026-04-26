from datetime import date, timedelta
from django.core import signing
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction
from django.utils import timezone
from . import models
from .repositories import list_aulas, create_reserva, create_contas_receber, create_contrato


def gerar_parcelas(valor, inicio, fim, meses, recorrencia="MENSAL"):
    def _add_months(base_date, months):
        offset = (base_date.month - 1) + months
        year = base_date.year + (offset // 12)
        month = (offset % 12) + 1
        day = min(base_date.day, 28)
        return date(year, month, day)

    parcelas = []
    if recorrencia == "SEMANAL":
        vencimento = inicio
        while vencimento <= fim:
            competencia = vencimento.strftime("%Y-%m-%d")
            parcelas.append({"valor": valor, "vencimento": vencimento, "competencia": competencia})
            vencimento += timedelta(days=7)
    else:
        total_parcelas = max(int(meses or 1), 1)
        for idx in range(total_parcelas):
            vencimento = _add_months(inicio, idx)
            competencia = vencimento.strftime("%Y-%m")
            parcelas.append({"valor": valor, "vencimento": vencimento, "competencia": competencia})
    return parcelas


def criar_contrato_e_contas(data_contrato, valor_parcela, recorrencia=None):
    plano = data_contrato["cdPlano"]
    meses = plano.duracao_meses
    recorrencia = recorrencia or getattr(plano, "recorrencia", "MENSAL")
    with transaction.atomic():
        contrato = create_contrato(data_contrato)
        parcelas = gerar_parcelas(
            valor_parcela,
            data_contrato["dtInicioContrato"],
            data_contrato["dtFimContrato"],
            meses,
            recorrencia=recorrencia,
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


def _currency(valor):
    try:
        return f"R$ {float(valor):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        return "R$ 0,00"


def render_contrato_html(contrato):
    aluno = contrato.cdAluno
    endereco = aluno.cdEndereco
    plano = contrato.cdPlano
    profissional = contrato.cdProfissional
    unidade = contrato.cdUnidade
    hoje = timezone.localdate()
    substitutions = {
        "{ALUNO_NOME}": aluno.dsNome,
        "{ALUNO_CPF}": aluno.dsCPF,
        "{ALUNO_RG}": aluno.dsRg or "",
        "{ALUNO_NASCIMENTO}": aluno.dtNascimento.strftime("%d/%m/%Y") if aluno.dtNascimento else "",
        "{ALUNO_ESTADO_CIVIL}": aluno.get_estado_civil_display() if aluno.estado_civil else "",
        "{ALUNO_PROFISSAO}": str(aluno.cdProfissao) if aluno.cdProfissao else "",
        "{ALUNO_EMAIL}": aluno.dsEmail or "",
        "{ALUNO_TELEFONE}": ", ".join(aluno.telefones.values_list("dsTelefone", flat=True)),
        "{ALUNO_ENDERECO}": f"{endereco.dsLogradouro}, {endereco.dsNumero} - {endereco.dsBairro} - {endereco.dsCidade} ({endereco.dsCEP})"
        if endereco
        else "",
        "{ENDERECO_LOGRADOURO}": endereco.dsLogradouro if endereco else "",
        "{ENDERECO_NUMERO}": endereco.dsNumero if endereco else "",
        "{ENDERECO_BAIRRO}": endereco.dsBairro if endereco else "",
        "{ENDERECO_CIDADE}": endereco.dsCidade if endereco else "",
        "{ENDERECO_CEP}": endereco.dsCEP if endereco else "",
        "{PROFISSIONAL_NOME}": str(profissional),
        "{PROFISSIONAL_CREFITO}": profissional.crefito or "",
        "{UNIDADE_NOME}": str(unidade),
        "{UNIDADE_CAPACIDADE}": str(unidade.capacidade or ""),
        "{PLANO_NOME}": str(plano),
        "{PLANO_AULAS_SEMANA}": str(plano.aulas_por_semana or ""),
        "{PLANO_DURACAO_MESES}": str(plano.duracao_meses or ""),
        "{PLANO_RECORRENCIA}": plano.get_recorrencia_display() if plano and hasattr(plano, "get_recorrencia_display") else "",
        "{TIPO_SERVICO}": str(plano.cdTipoServico) if plano and plano.cdTipoServico else "",
        "{CONTRATO_NUMERO}": str(contrato.cdContrato),
        "{CONTRATO_INICIO}": contrato.dtInicioContrato.strftime("%d/%m/%Y"),
        "{CONTRATO_FIM}": contrato.dtFimContrato.strftime("%d/%m/%Y"),
        "{CONTRATO_RECORRENCIA}": contrato.get_recorrencia_display() if contrato.recorrencia else "",
        "{CONTRATO_MODO_PAGAMENTO}": contrato.get_modo_pagamento_display() if contrato.modo_pagamento else "",
        "{CONTRATO_VALOR_PARCELA}": _currency(contrato.valor_parcela),
        "{CONTRATO_VALOR_TOTAL}": _currency(contrato.valor_total),
        "{DATA_HOJE}": hoje.strftime("%d/%m/%Y"),
    }
    template = plano.modeloContrato.conteudo_html if plano and plano.modeloContrato else ""
    if not template:
        template = (
            "<h3>Contrato {CONTRATO_NUMERO}</h3>"
            "<p>Aluno: {ALUNO_NOME} - {ALUNO_CPF}</p>"
            "<p>Plano: {PLANO_NOME}</p>"
            "<p>Recorrencia: {CONTRATO_RECORRENCIA}</p>"
            "<p>Periodo: {CONTRATO_INICIO} a {CONTRATO_FIM}</p>"
            "<p>Valor parcela: {CONTRATO_VALOR_PARCELA}</p>"
            "<p>Valor total: {CONTRATO_VALOR_TOTAL}</p>"
        )
    for key, value in substitutions.items():
        template = template.replace(key, value or "")
    return template


def render_contrato_pdf(contrato):
    html = render_contrato_html(contrato)
    try:
        from weasyprint import HTML, CSS

        doc_html = f"""
        <html>
          <head>
            <meta charset="utf-8" />
            <style>
              @page {{
                size: A4;
                margin: 2.2cm 2cm;
              }}
              body {{
                font-family: 'Manrope', Arial, sans-serif;
                font-size: 12.5pt;
                color: #1f2937;
                line-height: 1.6;
              }}
              h1, h2, h3 {{
                margin: 0 0 12px 0;
                color: #111827;
              }}
              p {{
                margin: 0 0 10px 0;
              }}
              .contrato-header {{
                border-bottom: 1px solid #e5e7eb;
                margin-bottom: 16px;
                padding-bottom: 8px;
              }}
              .contrato-meta {{
                font-size: 11pt;
                color: #4b5563;
              }}
              .contrato-body {{
                margin-top: 16px;
              }}
            </style>
          </head>
          <body>
            <div class="contrato-header">
              <h2>Contrato {contrato.cdContrato}</h2>
              <div class="contrato-meta">Aluno: {contrato.cdAluno.dsNome} · Plano: {contrato.cdPlano}</div>
            </div>
            <div class="contrato-body">
              {html}
            </div>
          </body>
        </html>
        """
        pdf = HTML(string=doc_html, base_url="").write_pdf(
            stylesheets=[CSS(string="")],
        )
        return pdf
    except Exception:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        text = strip_tags(html or "")
        text = text.replace("\r", "")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"Contrato {contrato.cdContrato}", styles["Title"]),
            Spacer(1, 10),
            Paragraph(f"Aluno: {contrato.cdAluno.dsNome}", styles["Normal"]),
            Paragraph(f"Plano: {contrato.cdPlano}", styles["Normal"]),
            Spacer(1, 12),
        ]
        body = "<br/>".join(lines) if lines else ""
        if body:
            story.append(Paragraph(body, styles["Normal"]))
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Contrato {contrato.cdContrato}")
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


def gerar_token_contrato(contrato):
    signer = signing.TimestampSigner(salt="contrato-assinatura")
    return signer.sign(str(contrato.pk))


def validar_token_contrato(token, max_age_days=7):
    signer = signing.TimestampSigner(salt="contrato-assinatura")
    pk = signer.unsign(token, max_age=max_age_days * 86400)
    return int(pk)


def enviar_contrato_para_assinatura(contrato, base_url):
    if not contrato.cdAluno.dsEmail:
        return False
    email_cfg = models.EmailConfiguracao.objects.filter(ativo=True).order_by("-dtCadastro").first()
    token = gerar_token_contrato(contrato)
    link = f"{base_url.rstrip('/')}/contratos/assinar/{token}/"
    html = render_contrato_html(contrato)
    subject = f"Contrato {contrato.cdContrato} - Assinatura"
    body_html = render_to_string(
        "emails/contrato_assinatura.html",
        {
            "aluno": contrato.cdAluno,
            "contrato": contrato,
            "plano": contrato.cdPlano,
            "unidade": contrato.cdUnidade,
            "profissional": contrato.cdProfissional,
            "link_assinatura": link,
            "contrato_html": html,
        },
    )
    connection = None
    from_email = None
    if email_cfg:
        connection = get_connection(
            host=email_cfg.host,
            port=email_cfg.porta,
            username=email_cfg.usuario,
            password=email_cfg.senha,
            use_tls=email_cfg.use_tls,
        )
        from_email = email_cfg.remetente
    msg = EmailMultiAlternatives(
        subject,
        strip_tags(body_html),
        from_email=from_email,
        to=[contrato.cdAluno.dsEmail],
        connection=connection,
    )
    msg.attach_alternative(body_html, "text/html")
    msg.send(fail_silently=True)
    return True
