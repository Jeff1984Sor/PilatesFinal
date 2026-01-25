from datetime import datetime, date
from enum import Enum
from sqlalchemy import Integer, Date, DateTime, ForeignKey, Text, Enum as SAEnum, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ContratoStatus(str, Enum):
    ativo = "ativo"
    pausado = "pausado"
    encerrado = "encerrado"


class Contrato(Base):
    __tablename__ = "contrato"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    plano_id: Mapped[int] = mapped_column(ForeignKey("plano.id"))
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    tipo_plano_id: Mapped[int | None] = mapped_column(ForeignKey("tipo_plano.id"), nullable=True)
    profissional_id: Mapped[int | None] = mapped_column(ForeignKey("profissional.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    inicio: Mapped[date] = mapped_column(Date)
    fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ContratoStatus] = mapped_column(SAEnum(ContratoStatus, native_enum=False), default=ContratoStatus.ativo)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContratoModelo(Base):
    __tablename__ = "contrato_modelo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
