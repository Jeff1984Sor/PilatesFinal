from sqlalchemy.orm import Session
from app.shared.repository import BaseRepository
from app.modules.financeiro.models import Fornecedor, Categoria, Subcategoria, ContasPagar, ContasReceber


class FornecedorRepository(BaseRepository[Fornecedor]):
    def __init__(self, db: Session):
        super().__init__(db, Fornecedor)


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, db: Session):
        super().__init__(db, Categoria)


class SubcategoriaRepository(BaseRepository[Subcategoria]):
    def __init__(self, db: Session):
        super().__init__(db, Subcategoria)


class ContasPagarRepository(BaseRepository[ContasPagar]):
    def __init__(self, db: Session):
        super().__init__(db, ContasPagar)


class ContasReceberRepository(BaseRepository[ContasReceber]):
    def __init__(self, db: Session):
        super().__init__(db, ContasReceber)
