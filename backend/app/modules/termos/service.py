from __future__ import annotations

import base64
import re
from datetime import date, datetime
from html.parser import HTMLParser
from io import BytesIO
from typing import Any

import httpx
import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as PdfImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.alunos.models import Aluno
from app.modules.contratos.models import Contrato
from app.modules.planos.models import Plano, TipoPlano, TipoServico
from app.modules.profissionais.models import Profissional
from app.modules.termos.repository import TermoRepository
from app.modules.unidades.models import Unidade

TERMO_VARIAVEIS = [
    {"key": "aluno.nome", "label": "Nome do aluno", "example": "Maria Silva"},
    {"key": "aluno.cpf", "label": "CPF do aluno", "example": "123.456.789-00"},
    {"key": "aluno.rg", "label": "RG do aluno", "example": "12.345.678-9"},
    {"key": "aluno.status", "label": "Status do aluno", "example": "ativo"},
    {"key": "aluno.criado_em", "label": "Data de cadastro do aluno", "example": "2025-01-12"},
    {"key": "unidade.nome", "label": "Nome da unidade", "example": "Centro"},
    {"key": "unidade.ocupacao_max", "label": "Ocupacao maxima da unidade", "example": "16"},
    {"key": "contrato.id", "label": "Codigo do contrato", "example": "245"},
    {"key": "contrato.inicio", "label": "Inicio do contrato", "example": "2025-02-01"},
    {"key": "contrato.fim", "label": "Fim do contrato", "example": "2025-08-01"},
    {"key": "contrato.status", "label": "Status do contrato", "example": "ativo"},
    {"key": "plano.descricao", "label": "Descricao do plano", "example": "Pilates 2x semana"},
    {"key": "plano.preco", "label": "Preco do plano", "example": "250.00"},
    {"key": "tipo_plano.descricao", "label": "Tipo do plano", "example": "Mensal"},
    {"key": "tipo_servico.descricao", "label": "Tipo de servico", "example": "Pilates"},
    {"key": "profissional.nome", "label": "Nome do profissional", "example": "Carla Souza"},
    {"key": "data_atual", "label": "Data atual", "example": "2026-01-21"},
]


class TermoService:
    def __init__(self, repo: TermoRepository):
        self.repo = repo


class TermoRenderer:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TermoRepository(db)

    def variables(self) -> list[dict[str, str]]:
        return TERMO_VARIAVEIS

    def render(self, template: str, context: dict[str, Any]) -> str:
        pattern = re.compile(r"{{\s*([\w\.]+)\s*}}")

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            value = self._resolve_key(context, key)
            return value if value is not None else match.group(0)

        return pattern.sub(replace, template)

    def build_context(self, aluno_id: int, contrato_id: int | None = None) -> dict[str, Any]:
        aluno = self.db.get(Aluno, aluno_id)
        if not aluno:
            return {}

        unidade = self.db.get(Unidade, aluno.unidade_id) if aluno.unidade_id else None
        contrato = self._get_contrato(aluno_id, contrato_id)
        plano = self.db.get(Plano, contrato.plano_id) if contrato and contrato.plano_id else None
        tipo_plano = self.db.get(TipoPlano, plano.tipo_plano_id) if plano else None
        tipo_servico = self.db.get(TipoServico, plano.tipo_servico_id) if plano else None
        profissional = self.db.get(Profissional, contrato.profissional_id) if contrato and contrato.profissional_id else None

        return {
            "aluno": {
                "nome": aluno.nome,
                "cpf": aluno.cpf,
                "rg": aluno.rg,
                "status": aluno.status,
                "criado_em": self._format_date(aluno.criado_em),
            },
            "unidade": {
                "nome": unidade.nome if unidade else "",
                "ocupacao_max": unidade.ocupacao_max if unidade else "",
            },
            "contrato": {
                "id": contrato.id if contrato else "",
                "inicio": self._format_date(contrato.inicio) if contrato else "",
                "fim": self._format_date(contrato.fim) if contrato else "",
                "status": contrato.status if contrato else "",
            },
            "plano": {
                "descricao": plano.descricao if plano else "",
                "preco": f"{plano.preco:.2f}" if plano and plano.preco is not None else "",
            },
            "tipo_plano": {"descricao": tipo_plano.descricao if tipo_plano else ""},
            "tipo_servico": {"descricao": tipo_servico.descricao if tipo_servico else ""},
            "profissional": {"nome": profissional.nome if profissional else ""},
            "data_atual": date.today().isoformat(),
        }

    def generate_pdf(self, text: str) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        html = text if self._looks_like_html(text) else markdown.markdown(text)
        body = self._html_to_flowables(html, styles, doc.width)
        if not body:
            body = [Paragraph("Termo de uso", styles["Normal"])]
        doc.build(body)
        return buffer.getvalue()

    def _get_contrato(self, aluno_id: int, contrato_id: int | None) -> Contrato | None:
        if contrato_id:
            return self.db.get(Contrato, contrato_id)
        stmt = (
            select(Contrato)
            .where(Contrato.aluno_id == aluno_id)
            .order_by(Contrato.criado_em.desc())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _format_date(self, value: date | datetime | None) -> str:
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.date().isoformat()
        return value.isoformat()

    def _resolve_key(self, context: dict[str, Any], key: str) -> str | None:
        if key in context and not isinstance(context[key], dict):
            return self._stringify(context[key])
        current: Any = context
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return self._stringify(current)

    def _stringify(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    def _looks_like_html(self, value: str) -> bool:
        return "<" in value and ">" in value

    def _html_to_flowables(self, html: str, styles, max_width: float):
        parser = _HtmlToFlowables(styles, max_width)
        parser.feed(html)
        parser.close()
        return parser.flowables


class _HtmlToFlowables(HTMLParser):
    def __init__(self, styles, max_width: float):
        super().__init__()
        self.styles = styles
        self.max_width = max_width
        self.flowables: list = []
        self._buffer: list[str] = []
        self._block_tag: str | None = None
        self._list_depth = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in {"p", "h1", "h2", "h3", "li"}:
            self._flush_buffer()
            self._block_tag = tag
            if tag == "li":
                self._buffer.append("• ")
            return

        if tag == "ul":
            self._list_depth += 1
            return

        if tag == "img":
            self._flush_buffer()
            src = self._get_attr(attrs, "src")
            if src:
                image = self._build_image(src)
                if image:
                    self.flowables.append(image)
                    self.flowables.append(Spacer(1, 12))
            return

        if tag == "strong":
            self._buffer.append("<b>")
        elif tag == "em":
            self._buffer.append("<i>")
        elif tag == "u":
            self._buffer.append("<u>")
        elif tag == "a":
            href = self._get_attr(attrs, "href") or ""
            self._buffer.append(f'<a href="{href}">')

    def handle_endtag(self, tag: str):
        if tag in {"p", "h1", "h2", "h3", "li"}:
            self._flush_buffer()
            self._block_tag = None
            return
        if tag == "ul":
            self._list_depth = max(0, self._list_depth - 1)
            return
        if tag == "strong":
            self._buffer.append("</b>")
        elif tag == "em":
            self._buffer.append("</i>")
        elif tag == "u":
            self._buffer.append("</u>")
        elif tag == "a":
            self._buffer.append("</a>")

    def handle_data(self, data: str):
        if not data:
            return
        self._buffer.append(data)

    def _flush_buffer(self):
        text = "".join(self._buffer).strip()
        if not text:
            self._buffer = []
            return
        style = self._get_style()
        self.flowables.append(Paragraph(text, style))
        self.flowables.append(Spacer(1, 12))
        self._buffer = []

    def _get_style(self):
        if self._block_tag == "h1":
            return self.styles["Heading1"]
        if self._block_tag == "h2":
            return self.styles["Heading2"]
        if self._block_tag == "h3":
            return self.styles["Heading3"]
        return self.styles["Normal"]

    def _get_attr(self, attrs, key: str) -> str | None:
        for name, value in attrs:
            if name == key:
                return value
        return None

    def _build_image(self, src: str):
        data = self._load_image_bytes(src)
        if not data:
            return None
        try:
            image = ImageReader(BytesIO(data))
            width, height = image.getSize()
            scale = min(1.0, self.max_width / float(width)) if width else 1.0
            return PdfImage(BytesIO(data), width=width * scale, height=height * scale)
        except Exception:
            return None

    def _load_image_bytes(self, src: str) -> bytes | None:
        if src.startswith("data:image/") and ";base64," in src:
            try:
                payload = src.split(";base64,", 1)[1]
                return base64.b64decode(payload)
            except Exception:
                return None
        if src.startswith("http://") or src.startswith("https://"):
            try:
                resp = httpx.get(src, timeout=10.0)
                if resp.status_code == 200:
                    return resp.content
            except Exception:
                return None
        return None
