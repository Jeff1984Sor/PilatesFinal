from sqlalchemy.orm import Session
from app.shared.repository import BaseRepository
from app.modules.unidades.models import Unidade


class UnidadeRepository(BaseRepository[Unidade]):
    def __init__(self, db: Session):
        super().__init__(db, Unidade)
