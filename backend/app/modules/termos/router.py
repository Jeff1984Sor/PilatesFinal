from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.termos.schemas import TermoUsoCreate, TermoUsoOut, TermoVariavelOut
from app.modules.termos.repository import TermoRepository
from app.modules.termos.service import TermoService, TermoRenderer
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/termos", tags=["termos"])


@router.post("", response_model=TermoUsoOut)
def create_termo(payload: TermoUsoCreate, db: Session = Depends(get_db)):
    service = TermoService(TermoRepository(db))
    return service.repo.create(payload.model_dump())


@router.get("", response_model=Page[TermoUsoOut])
def list_termos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str | None = None,
    order_dir: str = "asc",
    db: Session = Depends(get_db),
):
    service = TermoService(TermoRepository(db))
    items, total = service.repo.list(order_by=order_by, order_dir=order_dir, offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/variaveis", response_model=list[TermoVariavelOut])
def list_variaveis(db: Session = Depends(get_db)):
    renderer = TermoRenderer(db)
    return renderer.variables()
