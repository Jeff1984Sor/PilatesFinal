from pydantic import BaseModel, EmailStr
from app.shared.schemas import ORMModel


class PerfilAcessoCreate(BaseModel):
    descricao: str


class PerfilAcessoOut(ORMModel):
    id: int
    descricao: str


class UsuarioCreate(BaseModel):
    email: EmailStr
    senha: str
    perfil_acesso_id: int
    profissional_id: int | None = None


class UsuarioOut(ORMModel):
    id: int
    email: EmailStr
    perfil_acesso_id: int
    profissional_id: int | None
    ativo: bool


class LoginIn(BaseModel):
    email: EmailStr
    senha: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
