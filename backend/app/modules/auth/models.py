from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PerfilAcesso(Base):
    __tablename__ = "perfil_acesso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    usuarios = relationship("Usuario", back_populates="perfil")
    profissionais = relationship("Profissional", back_populates="perfil")


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    profissional_id: Mapped[int | None] = mapped_column(ForeignKey("profissional.id"), nullable=True)
    perfil_acesso_id: Mapped[int] = mapped_column(ForeignKey("perfil_acesso.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    perfil = relationship("PerfilAcesso", back_populates="usuarios")
    profissional = relationship("Profissional")
