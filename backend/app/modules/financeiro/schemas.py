from datetime import date
from pydantic import BaseModel
from app.shared.schemas import ORMModel


class FornecedorCreate(BaseModel):
    nome: str
    documento: str | None = None
    whatsapp: str | None = None


class FornecedorOut(ORMModel):
    id: int
    nome: str
    documento: str | None
    whatsapp: str | None


class CategoriaCreate(BaseModel):
    descricao: str


class CategoriaOut(ORMModel):
    id: int
    descricao: str


class SubcategoriaCreate(BaseModel):
    categoria_id: int
    descricao: str


class SubcategoriaOut(ORMModel):
    id: int
    categoria_id: int
    descricao: str


class ContasPagarCreate(BaseModel):
    fornecedor_id: int
    categoria_id: int
    subcategoria_id: int | None = None
    vencimento: date
    valor: float
    status: str = "aberto"
    pago_em: date | None = None
    forma_pagamento: str | None = None
    observacao: str | None = None


class ContasPagarOut(ORMModel):
    id: int
    fornecedor_id: int
    categoria_id: int
    subcategoria_id: int | None
    vencimento: date
    valor: float
    status: str
    pago_em: date | None
    forma_pagamento: str | None
    observacao: str | None


class ContasReceberCreate(BaseModel):
    aluno_id: int
    contrato_id: int | None = None
    vencimento: date
    valor: float
    status: str = "aberto"
    recebido_em: date | None = None
    forma_pagamento: str | None = None
    observacao: str | None = None
    origem: str | None = None


class ContasReceberOut(ORMModel):
    id: int
    aluno_id: int
    contrato_id: int | None
    vencimento: date
    valor: float
    status: str
    recebido_em: date | None
    forma_pagamento: str | None
    observacao: str | None
    origem: str | None
