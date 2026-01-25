from pydantic import BaseModel
from app.shared.schemas import ORMModel


class TermoUsoCreate(BaseModel):
    descricao: str
    versao: str
    ativo: bool = True


class TermoUsoOut(ORMModel):
    id: int
    descricao: str
    versao: str
    ativo: bool


class TermoVariavelOut(BaseModel):
    key: str
    label: str
    example: str
