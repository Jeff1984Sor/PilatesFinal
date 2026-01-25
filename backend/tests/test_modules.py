from app.core.security import get_password_hash
from app.core.database import SessionLocal
from app.modules.auth.repository import UsuarioRepository, PerfilRepository


def test_auth_login(client):
    db = SessionLocal()
    perfil = PerfilRepository(db).create({"descricao": "admin"})
    UsuarioRepository(db).create({
        "email": "admin@test.local",
        "senha_hash": get_password_hash("admin123"),
        "perfil_acesso_id": perfil.id,
        "ativo": True,
        "profissional_id": None,
    })
    db.close()

    resp = client.post("/auth/login", json={"email": "admin@test.local", "senha": "admin123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_list_endpoints(client):
    endpoints = [
        "/profissionais",
        "/unidades",
        "/termos",
        "/alunos",
        "/planos",
        "/contratos",
        "/financeiro/fornecedores",
        "/agenda/eventos",
        "/integracoes/totalpass/validar?cpf=00000000000",
    ]
    for url in endpoints:
        resp = client.get(url)
        assert resp.status_code in (200, 404)
