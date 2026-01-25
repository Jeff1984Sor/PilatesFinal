from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.agenda.schemas import (
    AgendaEventoCreate, AgendaEventoOut, AgendaParticipanteCreate,
    AgendaParticipanteOut, AgendaRecorrenciaCreate, AgendaRecorrenciaOut,
)
from app.modules.agenda.repository import AgendaEventoRepository, AgendaParticipanteRepository, AgendaRecorrenciaRepository
from app.modules.agenda.service import AgendaService
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/agenda", tags=["agenda"])


@router.post("/eventos", response_model=AgendaEventoOut)
def create_evento(payload: AgendaEventoCreate, db: Session = Depends(get_db)):
    service = AgendaService(AgendaEventoRepository(db), AgendaParticipanteRepository(db))
    return service.create_evento(payload.model_dump())


@router.get("/eventos", response_model=Page[AgendaEventoOut])
def list_eventos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unidade_id: int | None = None,
    profissional_id: int | None = None,
    db: Session = Depends(get_db),
):
    repo = AgendaEventoRepository(db)
    filters = []
    if unidade_id:
        filters.append(repo.model.unidade_id == unidade_id)
    if profissional_id:
        filters.append(repo.model.profissional_id == profissional_id)
    items, total = repo.list(filters=filters, offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/eventos/{evento_id}/participantes", response_model=AgendaParticipanteOut)
def add_participante(evento_id: int, payload: AgendaParticipanteCreate, db: Session = Depends(get_db)):
    service = AgendaService(AgendaEventoRepository(db), AgendaParticipanteRepository(db))
    return service.add_participante(evento_id, payload.model_dump())


@router.post("/recorrencias", response_model=AgendaRecorrenciaOut)
def create_recorrencia(payload: AgendaRecorrenciaCreate, db: Session = Depends(get_db)):
    return AgendaRecorrenciaRepository(db).create(payload.model_dump())
