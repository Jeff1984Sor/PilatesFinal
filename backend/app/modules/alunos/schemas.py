from datetime import datetime

from pydantic import BaseModel
from app.shared.schemas import ORMModel


class EnderecoAlunoCreate(BaseModel):
    logradouro: str
    numero: str
    cep: str
    cidade: str
    bairro: str
    principal: bool = False


class EnderecoAlunoOut(ORMModel):
    id: int
    logradouro: str
    numero: str
    cep: str
    cidade: str
    bairro: str
    principal: bool


class AlunoCreate(BaseModel):
    nome: str
    cpf: str
    rg: str | None = None
    unidade_id: int
    termo_uso_id: int | None = None
    status: str = "ativo"
    observacoes: str | None = None


class AlunoOut(ORMModel):
    id: int
    nome: str
    cpf: str
    rg: str | None
    unidade_id: int
    termo_uso_id: int | None
    status: str
    observacoes: str | None
    enderecos: list[EnderecoAlunoOut] = []


class AlunoTermoPdfIn(BaseModel):
    termo_id: int | None = None
    contrato_id: int | None = None


class AlunoAnexoOut(ORMModel):
    id: int
    aluno_id: int
    termo_uso_id: int | None
    contrato_id: int | None
    tipo: str
    arquivo_nome: str
    mime_type: str
    criado_em: datetime


class AlunoTelefoneMatch(BaseModel):
    aluno_id: int
    codigo: int | None = None
    nome: str
    telefone: str


class AlunoTelefoneLookupOut(BaseModel):
    exists: bool
    matches: list[AlunoTelefoneMatch] = []


class AlunoWhatsappMessageIn(BaseModel):
    telefone: str
    mensagem: str
    tipo: str = "manual"
    status: str = "sent"
    contrato_id: int | None = None
    response_payload: str | None = None


class AlunoWhatsappMessageOut(BaseModel):
    id: int
    aluno_id: int
    contrato_id: int | None
    telefone: str
    mensagem: str
    tipo: str
    status: str
    enviado_em: datetime
    response_payload: str | None


class ContextoContratoOut(BaseModel):
    id: int
    codigo: int | None = None
    dt_inicio: datetime | None = None
    dt_fim: datetime | None = None
    status: str | None = None
    plano: str | None = None
    unidade: str | None = None
    profissional: str | None = None
    valor_parcela: float | None = None
    valor_total: float | None = None


class ContextoAulaOut(BaseModel):
    reserva_id: int
    status: str
    data: datetime | None = None
    hora_inicio: datetime | None = None
    hora_fim: datetime | None = None
    tipo_servico: str | None = None
    profissional: str | None = None
    unidade: str | None = None


class ContextoFaturaOut(BaseModel):
    id: int
    contrato_id: int
    status: str
    valor: float | None = None
    dt_vencimento: datetime | None = None
    dt_pagamento: datetime | None = None


class ContextoEvolucaoOut(BaseModel):
    id: int
    texto: str
    dt_evolucao: datetime | None = None
    reserva_id: int
    profissional: str | None = None


class ContextoIAOut(BaseModel):
    aluno_id: int
    nome: str
    cpf: str | None = None
    email: str | None = None
    unidade: str | None = None
    contratos: list[ContextoContratoOut] = []
    aulas_agendadas: list[ContextoAulaOut] = []
    faturas_abertas: list[ContextoFaturaOut] = []
    evolucoes: list[ContextoEvolucaoOut] = []
    whatsapp: list[AlunoWhatsappMessageOut] = []
    resumo: dict
