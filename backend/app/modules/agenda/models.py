from datetime import datetime
from enum import Enum
from sqlalchemy import Integer, DateTime, ForeignKey, String, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class EventoStatus(str, Enum):
    marcado = "marcado"
    confirmado = "confirmado"
    cancelado = "cancelado"
    no_show = "no_show"
    concluido = "concluido"


class ParticipanteStatus(str, Enum):
    reservado = "reservado"
    confirmado = "confirmado"
    cancelado = "cancelado"
    presente = "presente"
    no_show = "no_show"


class Sala(Base):
    __tablename__ = "sala"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    nome: Mapped[str] = mapped_column(String(100))


class AgendaEvento(Base):
    __tablename__ = "agenda_evento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissional.id"))
    sala_id: Mapped[int | None] = mapped_column(ForeignKey("sala.id"), nullable=True)
    tipo_servico_id: Mapped[int] = mapped_column(ForeignKey("tipo_servico.id"))
    inicio_datetime: Mapped[datetime] = mapped_column(DateTime)
    fim_datetime: Mapped[datetime] = mapped_column(DateTime)
    capacidade: Mapped[int] = mapped_column(Integer)
    status: Mapped[EventoStatus] = mapped_column(SAEnum(EventoStatus, native_enum=False), default=EventoStatus.marcado)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgendaParticipante(Base):
    __tablename__ = "agenda_participante"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("agenda_evento.id"))
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    status: Mapped[ParticipanteStatus] = mapped_column(SAEnum(ParticipanteStatus, native_enum=False), default=ParticipanteStatus.reservado)
    origem: Mapped[str | None] = mapped_column(String(50), nullable=True)
    checkin_totalpass_id: Mapped[int | None] = mapped_column(ForeignKey("totalpass_log.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AgendaRecorrencia(Base):
    __tablename__ = "agenda_recorrencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissional.id"))
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    tipo_servico_id: Mapped[int] = mapped_column(ForeignKey("tipo_servico.id"))
    regra_rrule: Mapped[str | None] = mapped_column(String(200), nullable=True)
    inicio: Mapped[datetime] = mapped_column(DateTime)
    fim: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
