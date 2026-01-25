from sqlalchemy.orm import Session
from sqlalchemy import select

from app.shared.repository import BaseRepository
from app.modules.auth.models import Usuario, PerfilAcesso


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, db: Session):
        super().__init__(db, Usuario)

    def get_by_email(self, email: str):
        return self.db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none()


class PerfilRepository(BaseRepository[PerfilAcesso]):
    def __init__(self, db: Session):
        super().__init__(db, PerfilAcesso)
