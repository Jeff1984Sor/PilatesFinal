from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AulaStatus(str, Enum):
    agendada = "agendada"
    cancelada = "cancelada"
    concluida = "concluida"


class Aula(Base):
    __tablename__ = "aula"
    __table_args__ = (
        UniqueConstraint("unidade_id", "inicio_datetime", "fim_datetime", name="uq_aula_unidade_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    inicio_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[AulaStatus] = mapped_column(SAEnum(AulaStatus, native_enum=False), default=AulaStatus.agendada)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AulaAluno(Base):
    __tablename__ = "aula_aluno"
    __table_args__ = (
        UniqueConstraint("aula_id", "aluno_id", name="uq_aula_aluno"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aula_id: Mapped[int] = mapped_column(ForeignKey("aula.id"))
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    contrato_id: Mapped[int] = mapped_column(ForeignKey("contrato.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
