from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.modules.auth.schemas import LoginIn, RefreshIn, TokenOut, UsuarioCreate, UsuarioOut, PerfilAcessoCreate, PerfilAcessoOut
from app.modules.auth.repository import UsuarioRepository, PerfilRepository
from app.modules.auth.service import AuthService, UsuarioService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    service = AuthService(UsuarioRepository(db))
    tokens = service.login(payload.email, payload.senha)
    return TokenOut(**tokens)


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshIn, db: Session = Depends(get_db)):
    service = AuthService(UsuarioRepository(db))
    tokens = service.refresh(payload.refresh_token)
    return TokenOut(**tokens)


@router.get("/me", response_model=UsuarioOut)
def me(user=Depends(get_current_user)):
    return user


@router.post("/usuarios", response_model=UsuarioOut)
def create_user(payload: UsuarioCreate, db: Session = Depends(get_db)):
    service = UsuarioService(UsuarioRepository(db))
    return service.create(payload.model_dump())


@router.get("/usuarios", response_model=list[UsuarioOut])
def list_users(db: Session = Depends(get_db)):
    repo = UsuarioRepository(db)
    items, _ = repo.list()
    return items


@router.post("/perfis", response_model=PerfilAcessoOut)
def create_perfil(payload: PerfilAcessoCreate, db: Session = Depends(get_db)):
    repo = PerfilRepository(db)
    return repo.create(payload.model_dump())


@router.get("/perfis", response_model=list[PerfilAcessoOut])
def list_perfis(db: Session = Depends(get_db)):
    repo = PerfilRepository(db)
    items, _ = repo.list()
    return items
