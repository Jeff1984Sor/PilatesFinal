from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.unidades.schemas import UnidadeCreate, UnidadeOut
from app.modules.unidades.repository import UnidadeRepository
from app.modules.unidades.service import UnidadeService
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/unidades", tags=["unidades"])


@router.post("", response_model=UnidadeOut)
def create_unidade(payload: UnidadeCreate, db: Session = Depends(get_db)):
    service = UnidadeService(UnidadeRepository(db))
    return service.repo.create(payload.model_dump())


@router.get("", response_model=Page[UnidadeOut])
def list_unidades(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str | None = None,
    order_dir: str = "asc",
    db: Session = Depends(get_db),
):
    service = UnidadeService(UnidadeRepository(db))
    items, total = service.repo.list(order_by=order_by, order_dir=order_dir, offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))
