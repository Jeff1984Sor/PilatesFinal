from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.contratos.schemas import (
    ContratoCreate,
    ContratoOut,
    ContratoModeloCreate,
    ContratoModeloUpdate,
    ContratoModeloOut,
)
from app.modules.contratos.repository import ContratoRepository, ContratoModeloRepository
from app.modules.contratos.service import ContratoService
from app.modules.termos.service import TERMO_VARIAVEIS
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.post("", response_model=ContratoOut)
def create_contrato(payload: ContratoCreate, db: Session = Depends(get_db)):
    service = ContratoService(ContratoRepository(db))
    return service.repo.create(payload.model_dump())


@router.get("", response_model=Page[ContratoOut])
def list_contratos(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = ContratoService(ContratoRepository(db))
    items, total = service.repo.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/modelos", response_model=ContratoModeloOut)
def create_modelo(payload: ContratoModeloCreate, db: Session = Depends(get_db)):
    repo = ContratoModeloRepository(db)
    return repo.create(payload.model_dump())


@router.get("/modelos", response_model=Page[ContratoModeloOut])
def list_modelos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str | None = None,
    order_dir: str = "desc",
    db: Session = Depends(get_db),
):
    repo = ContratoModeloRepository(db)
    items, total = repo.list(order_by=order_by, order_dir=order_dir, offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/modelos/variaveis")
def list_modelo_variaveis():
    return TERMO_VARIAVEIS


@router.get("/modelos/{modelo_id}", response_model=ContratoModeloOut)
def get_modelo(modelo_id: int, db: Session = Depends(get_db)):
    repo = ContratoModeloRepository(db)
    item = repo.get(modelo_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo not found")
    return item


@router.put("/modelos/{modelo_id}", response_model=ContratoModeloOut)
def update_modelo(modelo_id: int, payload: ContratoModeloUpdate, db: Session = Depends(get_db)):
    repo = ContratoModeloRepository(db)
    db_obj = repo.get(modelo_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo not found")
    return repo.update(db_obj, payload.model_dump(exclude_unset=True))
