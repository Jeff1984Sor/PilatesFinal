from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Recorrencia(Base):
    __tablename__ = "recorrencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(100))
    intervalo_meses: Mapped[int] = mapped_column(Integer)


class TipoPlano(Base):
    __tablename__ = "tipo_plano"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(100))
    recorrencia_id: Mapped[int] = mapped_column(ForeignKey("recorrencia.id"))

    recorrencia = relationship("Recorrencia")


class TipoServico(Base):
    __tablename__ = "tipo_servico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(100))


class Plano(Base):
    __tablename__ = "plano"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(200))
    tipo_plano_id: Mapped[int] = mapped_column(ForeignKey("tipo_plano.id"))
    tipo_servico_id: Mapped[int] = mapped_column(ForeignKey("tipo_servico.id"))
    preco: Mapped[float] = mapped_column(Numeric(10, 2))
    quantidade_aulas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tipo_plano = relationship("TipoPlano")
    tipo_servico = relationship("TipoServico")
