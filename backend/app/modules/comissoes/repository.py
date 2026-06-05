from sqlalchemy.orm import Session
from app.shared.repository import BaseRepository
from app.modules.comissoes.models import Comissao


class ComissaoRepository(BaseRepository[Comissao]):
    def __init__(self, db: Session):
        super().__init__(db, Comissao)
