from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class TermoUso(Base):
    __tablename__ = "termo_uso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(Text)
    versao: Mapped[str] = mapped_column(String(50))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
