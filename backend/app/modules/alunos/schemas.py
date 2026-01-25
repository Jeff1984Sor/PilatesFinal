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
