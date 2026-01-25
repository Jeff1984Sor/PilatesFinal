from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.profissionais.schemas import ProfissionalCreate, ProfissionalOut, ProfissionalUpdate
from app.modules.profissionais.repository import ProfissionalRepository
from app.modules.profissionais.service import ProfissionalService
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/profissionais", tags=["profissionais"])


@router.post("", response_model=ProfissionalOut)
def create_profissional(payload: ProfissionalCreate, db: Session = Depends(get_db)):
    service = ProfissionalService(ProfissionalRepository(db))
    return service.repo.create(payload.model_dump())


@router.get("/{profissional_id}", response_model=ProfissionalOut)
def get_profissional(profissional_id: int, db: Session = Depends(get_db)):
    service = ProfissionalService(ProfissionalRepository(db))
    return service.get_or_404(profissional_id)


@router.put("/{profissional_id}", response_model=ProfissionalOut)
def update_profissional(
    profissional_id: int,
    payload: ProfissionalUpdate,
    db: Session = Depends(get_db),
):
    service = ProfissionalService(ProfissionalRepository(db))
    profissional = service.get_or_404(profissional_id)
    data = payload.model_dump(exclude_unset=True)
    return service.repo.update(profissional, data)


@router.delete("/{profissional_id}", status_code=204)
def delete_profissional(profissional_id: int, db: Session = Depends(get_db)):
    service = ProfissionalService(ProfissionalRepository(db))
    profissional = service.get_or_404(profissional_id)
    service.repo.delete(profissional)


@router.get("", response_model=Page[ProfissionalOut])
def list_profissionais(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str | None = None,
    order_dir: str = "asc",
    db: Session = Depends(get_db),
):
    service = ProfissionalService(ProfissionalRepository(db))
    items, total = service.repo.list(order_by=order_by, order_dir=order_dir, offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))
