from datetime import datetime, date
from enum import Enum
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Numeric, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ContaStatus(str, Enum):
    aberto = "aberto"
    pago = "pago"
    vencido = "vencido"
    cancelado = "cancelado"


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    documento: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(100))


class Subcategoria(Base):
    __tablename__ = "subcategoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"))
    descricao: Mapped[str] = mapped_column(String(100))


class ContasPagar(Base):
    __tablename__ = "contas_pagar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id"))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"))
    subcategoria_id: Mapped[int | None] = mapped_column(ForeignKey("subcategoria.id"), nullable=True)
    vencimento: Mapped[date] = mapped_column(Date)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    valor: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[ContaStatus] = mapped_column(SAEnum(ContaStatus, native_enum=False), default=ContaStatus.aberto)
    pago_em: Mapped[date | None] = mapped_column(Date, nullable=True)
    forma_pagamento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContasReceber(Base):
    __tablename__ = "contas_receber"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contrato.id"), nullable=True)
    vencimento: Mapped[date] = mapped_column(Date)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    valor: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[ContaStatus] = mapped_column(SAEnum(ContaStatus, native_enum=False), default=ContaStatus.aberto)
    recebido_em: Mapped[date | None] = mapped_column(Date, nullable=True)
    forma_pagamento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    origem: Mapped[str | None] = mapped_column(String(50), nullable=True)
