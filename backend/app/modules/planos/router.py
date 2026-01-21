from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.planos.schemas import (
    RecorrenciaCreate, RecorrenciaOut, TipoPlanoCreate, TipoPlanoOut,
    TipoServicoCreate, TipoServicoOut, PlanoCreate, PlanoOut,
)
from app.modules.planos.repository import RecorrenciaRepository, TipoPlanoRepository, TipoServicoRepository, PlanoRepository
from app.modules.planos.service import PlanosService
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/planos", tags=["planos"])


@router.post("/recorrencias", response_model=RecorrenciaOut)
def create_recorrencia(payload: RecorrenciaCreate, db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    return service.recorrencia.create(payload.model_dump())


@router.get("/recorrencias", response_model=Page[RecorrenciaOut])
def list_recorrencias(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    items, total = service.recorrencia.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/tipos", response_model=TipoPlanoOut)
def create_tipo_plano(payload: TipoPlanoCreate, db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    return service.tipo_plano.create(payload.model_dump())


@router.get("/tipos", response_model=Page[TipoPlanoOut])
def list_tipos_plano(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    items, total = service.tipo_plano.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/servicos", response_model=TipoServicoOut)
def create_tipo_servico(payload: TipoServicoCreate, db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    return service.tipo_servico.create(payload.model_dump())


@router.get("/servicos", response_model=Page[TipoServicoOut])
def list_tipos_servico(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    items, total = service.tipo_servico.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))

@router.post("", response_model=PlanoOut)
def create_plano(payload: PlanoCreate, db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    return service.plano.create(payload.model_dump())


@router.get("", response_model=Page[PlanoOut])
def list_planos(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    service = PlanosService(RecorrenciaRepository(db), TipoPlanoRepository(db), TipoServicoRepository(db), PlanoRepository(db))
    items, total = service.plano.list(offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))
