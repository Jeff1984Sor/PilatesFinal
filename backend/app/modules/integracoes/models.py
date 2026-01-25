from datetime import datetime
from sqlalchemy import Integer, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class TotalPassLog(Base):
    __tablename__ = "totalpass_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), default="totalpass")
    request_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WhatsappLog(Base):
    __tablename__ = "whatsapp_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    to: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    response_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
