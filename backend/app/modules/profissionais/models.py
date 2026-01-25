from datetime import datetime, date
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Profissional(Base):
    __tablename__ = "profissional"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    perfil_acesso_id: Mapped[int] = mapped_column(ForeignKey("perfil_acesso.id"))
    data_nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    crefito: Mapped[str | None] = mapped_column(String(50), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    perfil = relationship("PerfilAcesso", back_populates="profissionais")
