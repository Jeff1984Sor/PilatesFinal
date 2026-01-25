from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.alunos.schemas import (
    AlunoCreate,
    AlunoOut,
    EnderecoAlunoCreate,
    EnderecoAlunoOut,
    AlunoTermoPdfIn,
    AlunoAnexoOut,
)
from app.modules.alunos.repository import AlunoRepository, EnderecoRepository, AlunoAnexoRepository
from app.modules.alunos.service import AlunoService, AlunoAnexoService
from app.modules.termos.repository import TermoRepository
from app.modules.termos.service import TermoRenderer
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/alunos", tags=["alunos"])


@router.post("", response_model=AlunoOut)
def create_aluno(payload: AlunoCreate, db: Session = Depends(get_db)):
    service = AlunoService(AlunoRepository(db), EnderecoRepository(db))
    return service.create(payload.model_dump())


@router.get("/{aluno_id}", response_model=AlunoOut)
def get_aluno(aluno_id: int, db: Session = Depends(get_db)):
    repo = AlunoRepository(db)
    return repo.get(aluno_id)


@router.get("", response_model=Page[AlunoOut])
def list_alunos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str | None = None,
    order_dir: str = "asc",
    status: str | None = None,
    db: Session = Depends(get_db),
):
    repo = AlunoRepository(db)
    filters = []
    if status:
        filters.append(repo.model.status == status)
    items, total = repo.list(filters=filters, order_by=order_by, order_dir=order_dir, offset=(page - 1) * page_size, limit=page_size)
    return Page(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.post("/{aluno_id}/enderecos", response_model=EnderecoAlunoOut)
def add_endereco(aluno_id: int, payload: EnderecoAlunoCreate, db: Session = Depends(get_db)):
    service = AlunoService(AlunoRepository(db), EnderecoRepository(db))
    return service.add_endereco(aluno_id, payload.model_dump())


@router.post("/{aluno_id}/termo-pdf", response_model=AlunoAnexoOut)
def generate_termo_pdf(aluno_id: int, payload: AlunoTermoPdfIn, db: Session = Depends(get_db)):
    service = AlunoAnexoService(
        AlunoRepository(db),
        AlunoAnexoRepository(db),
        TermoRepository(db),
        TermoRenderer(db),
    )
    return service.create_termo_pdf(aluno_id, payload.termo_id, payload.contrato_id)


@router.get("/{aluno_id}/anexos", response_model=list[AlunoAnexoOut])
def list_anexos(aluno_id: int, db: Session = Depends(get_db)):
    repo = AlunoAnexoRepository(db)
    items, _ = repo.list(filters=[repo.model.aluno_id == aluno_id], order_by="criado_em", order_dir="desc", limit=100)
    return items


@router.get("/{aluno_id}/anexos/{anexo_id}")
def download_anexo(aluno_id: int, anexo_id: int, db: Session = Depends(get_db)):
    repo = AlunoAnexoRepository(db)
    anexo = repo.get(anexo_id)
    if not anexo or anexo.aluno_id != aluno_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anexo not found")
    return FileResponse(anexo.arquivo_path, media_type=anexo.mime_type, filename=anexo.arquivo_nome)
