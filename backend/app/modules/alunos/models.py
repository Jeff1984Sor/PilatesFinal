from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AlunoStatus(str, Enum):
    ativo = "ativo"
    inativo = "inativo"


class Aluno(Base):
    __tablename__ = "aluno"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    cpf: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    termo_uso_id: Mapped[int | None] = mapped_column(ForeignKey("termo_uso.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[AlunoStatus] = mapped_column(SAEnum(AlunoStatus, native_enum=False), default=AlunoStatus.ativo)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    enderecos = relationship("EnderecoAluno", back_populates="aluno", cascade="all, delete-orphan")


class EnderecoAluno(Base):
    __tablename__ = "endereco_aluno"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    logradouro: Mapped[str] = mapped_column(String(200))
    numero: Mapped[str] = mapped_column(String(20))
    cep: Mapped[str] = mapped_column(String(10))
    cidade: Mapped[str] = mapped_column(String(100))
    bairro: Mapped[str] = mapped_column(String(100))
    principal: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    aluno = relationship("Aluno", back_populates="enderecos")


class AlunoAnexo(Base):
    __tablename__ = "aluno_anexo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    termo_uso_id: Mapped[int | None] = mapped_column(ForeignKey("termo_uso.id"), nullable=True)
    contrato_id: Mapped[int | None] = mapped_column(ForeignKey("contrato.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50))
    arquivo_nome: Mapped[str] = mapped_column(String(255))
    arquivo_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
