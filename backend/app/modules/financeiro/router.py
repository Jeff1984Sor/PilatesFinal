from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.financeiro.schemas import (
    FornecedorCreate, FornecedorOut, CategoriaCreate, CategoriaOut,
    SubcategoriaCreate, SubcategoriaOut, ContasPagarCreate, ContasPagarOut,
    ContasReceberCreate, ContasReceberOut,
)
from app.modules.financeiro.repository import (
    FornecedorRepository, CategoriaRepository, SubcategoriaRepository,
    ContasPagarRepository, ContasReceberRepository,
)
from app.modules.financeiro.service import FinanceiroService
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/financeiro", tags=["financeiro"])


def _service(db: Session) -> FinanceiroService:
    return FinanceiroService(
        FornecedorRepository(db),
        CategoriaRepository(db),
        SubcategoriaRepository(db),
        ContasPagarRepository(db),
        ContasReceberRepository(db),
    )


@router.post("/fornecedores", response_model=FornecedorOut)
def create_fornecedor(payload: FornecedorCreate, db: Session = Depends(get_db)):
    service = _service(db)
    return service.fornecedor.create(payload.model_dump())


@router.get("/fornecedores", response_model=Page[FornecedorOut])
def list_fornecedores(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = _service(db)
    items, total = service.fornecedor.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/categorias", response_model=CategoriaOut)
def create_categoria(payload: CategoriaCreate, db: Session = Depends(get_db)):
    service = _service(db)
    return service.categoria.create(payload.model_dump())


@router.get("/categorias", response_model=Page[CategoriaOut])
def list_categorias(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = _service(db)
    items, total = service.categoria.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/subcategorias", response_model=SubcategoriaOut)
def create_subcategoria(payload: SubcategoriaCreate, db: Session = Depends(get_db)):
    service = _service(db)
    return service.subcategoria.create(payload.model_dump())


@router.get("/subcategorias", response_model=Page[SubcategoriaOut])
def list_subcategorias(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = _service(db)
    items, total = service.subcategoria.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/contas-pagar", response_model=ContasPagarOut)
def create_contas_pagar(payload: ContasPagarCreate, db: Session = Depends(get_db)):
    service = _service(db)
    return service.contas_pagar.create(payload.model_dump())


@router.post("/contas-receber", response_model=ContasReceberOut)
def create_contas_receber(payload: ContasReceberCreate, db: Session = Depends(get_db)):
    service = _service(db)
    return service.contas_receber.create(payload.model_dump())


@router.get("/contas-pagar", response_model=Page[ContasPagarOut])
def list_contas_pagar(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = _service(db)
    items, total = service.contas_pagar.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/contas-receber", response_model=Page[ContasReceberOut])
def list_contas_receber(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = _service(db)
    items, total = service.contas_receber.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))
