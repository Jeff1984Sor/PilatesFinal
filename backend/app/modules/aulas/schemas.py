from datetime import date, datetime, time
from pydantic import BaseModel


class AulaAmanhaOut(BaseModel):
    reserva_id: int
    aluno_id: int
    telefone: str | None = None
    data: date
    hora_inicio: time
    professora: str | None = None


class AulaOperacaoAlunoOut(BaseModel):
    id: int
    nome: str
    telefone: str | None = None
    avatar_url: str | None = None


class AulaOperacaoProfissionalOut(BaseModel):
    id: int | None = None
    nome: str | None = None


class AulaOperacaoPlanoOut(BaseModel):
    id: int | None = None
    descricao: str | None = None


class AulaOperacaoFlagsOut(BaseModel):
    tem_preliminares: bool
    cobranca_pendente: bool
    observacao_importante: bool


class AulaOperacaoEvolucaoOut(BaseModel):
    texto: str | None = None
    dt_evolucao: datetime | None = None


class AulaOperacaoOut(BaseModel):
    id: int
    aula_sessao_id: int
    dt_inicio: datetime
    dt_fim: datetime
    unidade_id: int | None = None
    unidade: str | None = None
    sala: str | None = None
    profissional: AulaOperacaoProfissionalOut
    aluno: AulaOperacaoAlunoOut
    plano: AulaOperacaoPlanoOut
    status_aula: str
    confirmacao: bool
    flags: AulaOperacaoFlagsOut
    ultima_evolucao: AulaOperacaoEvolucaoOut


class AulaOperacaoListOut(BaseModel):
    data_inicio: date
    data_fim: date
    total: int
    items: list[AulaOperacaoOut]


class AulaEvolucaoCreate(BaseModel):
    texto: str
    profissional_id: int
    finalizar: bool = False


class AulaStatusUpdate(BaseModel):
    acao: str


class AulaEvolucaoOut(BaseModel):
    id: int
    reserva_id: int
    texto: str
    dt_evolucao: datetime
