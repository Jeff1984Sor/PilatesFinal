from sqlalchemy.orm import Session

from app.core.database import SessionLocal, import_all_models
from app.modules.auth.repository import UsuarioRepository, PerfilRepository
from app.core.security import get_password_hash


def main():
    import_all_models()
    db: Session = SessionLocal()
    try:
        perfil_repo = PerfilRepository(db)
        perfil = perfil_repo.get(1)
        if not perfil:
            perfil = perfil_repo.create({"descricao": "admin"})

        usuario_repo = UsuarioRepository(db)
        if not usuario_repo.get_by_email("admin@studiopilates.local"):
            usuario_repo.create({
                "email": "admin@studiopilates.local",
                "senha_hash": get_password_hash("admin123"),
                "perfil_acesso_id": perfil.id,
                "ativo": True,
                "profissional_id": None,
            })
        print("admin seeded")
    finally:
        db.close()


if __name__ == "__main__":
    main()
