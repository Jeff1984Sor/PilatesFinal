from pydantic import BaseModel
from app.shared.schemas import ORMModel


class UnidadeCreate(BaseModel):
    nome: str
    ocupacao_max: int
    ativo: bool = True


class UnidadeOut(ORMModel):
    id: int
    nome: str
    ocupacao_max: int
    ativo: bool
