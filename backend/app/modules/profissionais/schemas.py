from datetime import date
from pydantic import BaseModel
from app.shared.schemas import ORMModel


class ProfissionalCreate(BaseModel):
    nome: str
    perfil_acesso_id: int
    data_nascimento: date | None = None
    crefito: str | None = None


class ProfissionalUpdate(BaseModel):
    nome: str | None = None
    perfil_acesso_id: int | None = None
    data_nascimento: date | None = None
    crefito: str | None = None


class ProfissionalOut(ORMModel):
    id: int
    nome: str
    perfil_acesso_id: int
    data_nascimento: date | None
    crefito: str | None
