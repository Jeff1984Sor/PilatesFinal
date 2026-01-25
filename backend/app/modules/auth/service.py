from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.modules.auth.repository import UsuarioRepository, PerfilRepository


class AuthService:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def authenticate(self, email: str, senha: str):
        user = self.repo.get_by_email(email)
        if not user or not verify_password(senha, user.senha_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.ativo:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
        return user

    def login(self, email: str, senha: str):
        user = self.authenticate(email, senha)
        return {
            "access_token": create_access_token(str(user.id)),
            "refresh_token": create_refresh_token(str(user.id)),
        }

    def refresh(self, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            user_id = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {
            "access_token": create_access_token(str(user_id)),
            "refresh_token": create_refresh_token(str(user_id)),
        }


class UsuarioService:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def create(self, data: dict):
        if self.repo.get_by_email(data["email"]):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        data["senha_hash"] = get_password_hash(data.pop("senha"))
        return self.repo.create(data)


class PerfilService:
    def __init__(self, repo: PerfilRepository):
        self.repo = repo
