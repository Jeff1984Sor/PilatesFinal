from datetime import datetime, date
from enum import Enum
from sqlalchemy import Integer, Date, DateTime, ForeignKey, Numeric, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ComissaoStatus(str, Enum):
    pendente = "pendente"
    pago = "pago"


class Comissao(Base):
    __tablename__ = "comissao"
    __table_args__ = (
        UniqueConstraint("conta_receber_id", name="uq_comissao_conta_receber"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissional.id"))
    conta_receber_id: Mapped[int | None] = mapped_column(ForeignKey("contas_receber.id"), nullable=True)
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contrato.id"), nullable=True)
    competencia: Mapped[date] = mapped_column(Date)
    valor_base: Mapped[float] = mapped_column(Numeric(10, 2))
    percentual: Mapped[float] = mapped_column(Numeric(5, 2))
    valor: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[ComissaoStatus] = mapped_column(
        SAEnum(ComissaoStatus, native_enum=False), default=ComissaoStatus.pendente
    )
    pago_em: Mapped[date | None] = mapped_column(Date, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
