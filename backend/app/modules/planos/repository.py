from sqlalchemy.orm import Session
from app.shared.repository import BaseRepository
from app.modules.planos.models import Recorrencia, TipoPlano, TipoServico, Plano


class RecorrenciaRepository(BaseRepository[Recorrencia]):
    def __init__(self, db: Session):
        super().__init__(db, Recorrencia)


class TipoPlanoRepository(BaseRepository[TipoPlano]):
    def __init__(self, db: Session):
        super().__init__(db, TipoPlano)


class TipoServicoRepository(BaseRepository[TipoServico]):
    def __init__(self, db: Session):
        super().__init__(db, TipoServico)


class PlanoRepository(BaseRepository[Plano]):
    def __init__(self, db: Session):
        super().__init__(db, Plano)
