from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_roles
from app.modules.comissoes.schemas import (
    ComissaoOut, GerarComissoesIn, GerarComissoesOut, ResumoOut,
)
from app.modules.comissoes.service import ComissaoService

router = APIRouter(prefix="/comissoes", tags=["comissoes"])


def _scope_profissional_id(user, requested: int | None) -> int | None:
    """Admin pode consultar qualquer profissional (ou todos). Demais usuarios
    sao restritos ao proprio profissional vinculado."""
    is_admin = bool(user.perfil and user.perfil.descricao == "admin")
    if is_admin:
        return requested
    if not user.profissional_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem profissional vinculado")
    return user.profissional_id


@router.post("/gerar", response_model=GerarComissoesOut, dependencies=[Depends(require_roles("admin"))])
def gerar_comissoes(payload: GerarComissoesIn, db: Session = Depends(get_db)):
    service = ComissaoService(db)
    return service.gerar(payload.competencia)


@router.get("", response_model=list[ComissaoOut])
def listar_comissoes(
    profissional_id: int | None = None,
    competencia: str | None = Query(None, description="YYYY-MM"),
    status_filtro: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    service = ComissaoService(db)
    prof_id = _scope_profissional_id(user, profissional_id)
    return service.listar(prof_id, competencia, status_filtro)


@router.get("/resumo", response_model=ResumoOut)
def resumo_comissoes(
    profissional_id: int | None = None,
    competencia: str | None = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    service = ComissaoService(db)
    prof_id = _scope_profissional_id(user, profissional_id)
    return service.resumo(prof_id, competencia)


@router.post("/{comissao_id}/pagar", response_model=ComissaoOut, dependencies=[Depends(require_roles("admin"))])
def pagar_comissao(comissao_id: int, pago_em: date | None = None, db: Session = Depends(get_db)):
    service = ComissaoService(db)
    return service.pagar(comissao_id, pago_em)
