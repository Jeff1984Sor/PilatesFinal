from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.repository import BaseRepository
from app.modules.termos.models import TermoUso


class TermoRepository(BaseRepository[TermoUso]):
    def __init__(self, db: Session):
        super().__init__(db, TermoUso)

    def get_active(self) -> TermoUso | None:
        stmt = select(TermoUso).where(TermoUso.ativo.is_(True)).order_by(TermoUso.id.desc())
        return self.db.execute(stmt).scalar_one_or_none()
