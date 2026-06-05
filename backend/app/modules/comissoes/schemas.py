from datetime import date
from pydantic import BaseModel
from app.shared.schemas import ORMModel


class ComissaoOut(ORMModel):
    id: int
    profissional_id: int
    conta_receber_id: int | None
    contrato_id: int | None
    competencia: date
    valor_base: float
    percentual: float
    valor: float
    status: str
    pago_em: date | None


class GerarComissoesIn(BaseModel):
    competencia: str  # formato "YYYY-MM"


class GerarComissoesOut(BaseModel):
    competencia: str
    geradas: int
    valor_total: float


class ResumoProfissional(BaseModel):
    profissional_id: int
    profissional_nome: str
    competencia: str | None = None
    quantidade: int
    valor_pendente: float
    valor_pago: float
    valor_total: float


class ResumoOut(BaseModel):
    competencia: str | None = None
    itens: list[ResumoProfissional]
    valor_total: float
