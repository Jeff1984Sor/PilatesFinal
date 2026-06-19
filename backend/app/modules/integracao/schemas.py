from datetime import date, time
from pydantic import BaseModel


class AlunoOut(BaseModel):
    id: int
    cdAluno: int | None = None
    dsNome: str
    dsCPF: str | None = None
    dsEmail: str | None = None
    dsTelefone: str | None = None
    status: str | None = None


class FaturaOut(BaseModel):
    id: int
    cdAluno: int | None = None
    contrato_id: int | None = None
    descricao: str
    competencia: str | None = None
    valor: float
    vencimento: date | None = None
    dt_pagamento: date | None = None
    status: str


class ContratoOut(BaseModel):
    id: int
    cdContrato: int | None = None
    cdAluno: int | None = None
    plano: str | None = None
    profissional: str | None = None
    unidade: str | None = None
    dt_inicio: date | None = None
    dt_fim: date | None = None
    status: str | None = None
    valor_parcela: float | None = None
    valor_total: float | None = None


class AulaOut(BaseModel):
    reserva_id: int
    cdAluno: int | None = None
    data: date | None = None
    hora_inicio: time | None = None
    hora_fim: time | None = None
    tipo_servico: str | None = None
    profissional: str | None = None
    unidade: str | None = None
    status: str | None = None
