from datetime import date, datetime
from pydantic import BaseModel
from app.shared.schemas import ORMModel


class ContratoCreate(BaseModel):
    aluno_id: int
    plano_id: int
    unidade_id: int
    tipo_plano_id: int | None = None
    profissional_id: int | None = None
    inicio: date
    fim: date | None = None
    status: str = "ativo"
    observacoes: str | None = None
    idempotency_key: str | None = None


class ContratoOut(ORMModel):
    id: int
    aluno_id: int
    plano_id: int
    unidade_id: int
    tipo_plano_id: int | None
    profissional_id: int | None
    inicio: date
    fim: date | None
    status: str
    observacoes: str | None
    agenda_gerada_em: datetime | None
    idempotency_key: str | None


class AulaResumo(ORMModel):
    id: int
    inicio_datetime: datetime
    fim_datetime: datetime
    status: str


class ContratoAgendaResumo(BaseModel):
    total_aulas: int
    proximas_aulas: list[AulaResumo] = []


class ContratoDetailOut(ContratoOut):
    agenda_resumo: ContratoAgendaResumo


class AgendaGeracaoOut(BaseModel):
    total_aulas: int
    agenda_gerada_em: datetime | None


class ContratoModeloCreate(BaseModel):
    titulo: str
    descricao: str
    ativo: bool = True


class ContratoModeloUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    ativo: bool | None = None


class ContratoModeloOut(ORMModel):
    id: int
    titulo: str
    descricao: str
    ativo: bool
