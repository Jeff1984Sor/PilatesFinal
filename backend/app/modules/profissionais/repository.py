from sqlalchemy.orm import Session
from app.shared.repository import BaseRepository
from app.modules.profissionais.models import Profissional


class ProfissionalRepository(BaseRepository[Profissional]):
    def __init__(self, db: Session):
        super().__init__(db, Profissional)
