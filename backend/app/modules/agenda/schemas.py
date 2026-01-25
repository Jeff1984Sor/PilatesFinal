from datetime import datetime
from pydantic import BaseModel
from app.shared.schemas import ORMModel


class AgendaEventoCreate(BaseModel):
    unidade_id: int
    profissional_id: int
    sala_id: int | None = None
    tipo_servico_id: int
    inicio_datetime: datetime
    fim_datetime: datetime
    capacidade: int
    status: str = "marcado"
    observacao: str | None = None


class AgendaEventoOut(ORMModel):
    id: int
    unidade_id: int
    profissional_id: int
    sala_id: int | None
    tipo_servico_id: int
    inicio_datetime: datetime
    fim_datetime: datetime
    capacidade: int
    status: str
    observacao: str | None


class AgendaParticipanteCreate(BaseModel):
    aluno_id: int
    status: str = "reservado"
    origem: str | None = None


class AgendaParticipanteOut(ORMModel):
    id: int
    evento_id: int
    aluno_id: int
    status: str
    origem: str | None


class AgendaRecorrenciaCreate(BaseModel):
    aluno_id: int
    profissional_id: int
    unidade_id: int
    tipo_servico_id: int
    regra_rrule: str | None = None
    inicio: datetime
    fim: datetime | None = None
    ativo: bool = True


class AgendaRecorrenciaOut(ORMModel):
    id: int
    aluno_id: int
    profissional_id: int
    unidade_id: int
    tipo_servico_id: int
    regra_rrule: str | None
    inicio: datetime
    fim: datetime | None
    ativo: bool
