from pydantic import BaseModel
from app.shared.schemas import ORMModel


class RecorrenciaCreate(BaseModel):
    descricao: str
    intervalo_meses: int


class RecorrenciaOut(ORMModel):
    id: int
    descricao: str
    intervalo_meses: int


class TipoPlanoCreate(BaseModel):
    descricao: str
    recorrencia_id: int


class TipoPlanoOut(ORMModel):
    id: int
    descricao: str
    recorrencia_id: int


class TipoServicoCreate(BaseModel):
    descricao: str


class TipoServicoOut(ORMModel):
    id: int
    descricao: str


class PlanoCreate(BaseModel):
    descricao: str
    tipo_plano_id: int
    tipo_servico_id: int
    preco: float
    quantidade_aulas: int | None = None
    ativo: bool = True


class PlanoOut(ORMModel):
    id: int
    descricao: str
    tipo_plano_id: int
    tipo_servico_id: int
    preco: float
    quantidade_aulas: int | None
    ativo: bool
