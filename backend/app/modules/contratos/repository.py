from sqlalchemy.orm import Session
from app.shared.repository import BaseRepository
from app.modules.contratos.models import Contrato, ContratoModelo


class ContratoRepository(BaseRepository[Contrato]):
    def __init__(self, db: Session):
        super().__init__(db, Contrato)


class ContratoModeloRepository(BaseRepository[ContratoModelo]):
    def __init__(self, db: Session):
        super().__init__(db, ContratoModelo)
