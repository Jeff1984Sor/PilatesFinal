import os
import sys
import django
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from django.contrib.auth import authenticate
import jwt

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
for path in (ROOT_DIR, BACKEND_DIR):
    if path not in sys.path:
        sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studiopilates.settings")
django.setup()

from studiopilates.core import models
from studiopilates.core import services
from shared.ai.gemini_client import extract_address_from_proof, extract_student_from_document
from .schemas import AlunoIn, AlunoOut, ContratoIn, AulaSessaoIn, ReservaIn

app = FastAPI(title="StudioPilates API")
security = HTTPBearer()


def create_token(user):
    secret = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-secret")
    return jwt.encode({"user_id": user.id}, secret, algorithm="HS256")


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    secret = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-secret")
    try:
        payload = jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalido")
    return payload


@app.post("/api/auth/token")
def token(username: str, password: str):
    user = authenticate(username=username, password=password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais invalidas")
    return {"access_token": create_token(user)}


@app.get("/api/alunos", response_model=list[AlunoOut])
def listar_alunos(_: dict = Depends(verify_jwt)):
    return list(models.Aluno.objects.all())


@app.post("/api/alunos", response_model=AlunoOut)
def criar_aluno(data: AlunoIn, _: dict = Depends(verify_jwt)):
    aluno = models.Aluno.objects.create(**data.model_dump())
    return aluno


@app.get("/api/alunos/{aluno_id}", response_model=AlunoOut)
def detalhe_aluno(aluno_id: int, _: dict = Depends(verify_jwt)):
    return models.Aluno.objects.get(pk=aluno_id)


@app.put("/api/alunos/{aluno_id}", response_model=AlunoOut)
def atualizar_aluno(aluno_id: int, data: AlunoIn, _: dict = Depends(verify_jwt)):
    models.Aluno.objects.filter(pk=aluno_id).update(**data.model_dump())
    return models.Aluno.objects.get(pk=aluno_id)


@app.delete("/api/alunos/{aluno_id}")
def excluir_aluno(aluno_id: int, _: dict = Depends(verify_jwt)):
    models.Aluno.objects.filter(pk=aluno_id).delete()
    return {"status": "ok"}


@app.get("/api/contratos")
def listar_contratos(_: dict = Depends(verify_jwt)):
    return list(models.Contrato.objects.values())


@app.post("/api/contratos")
def criar_contrato(data: ContratoIn, _: dict = Depends(verify_jwt)):
    contrato_data = data.to_contrato_data()
    contrato, conflitos = services.criar_contrato_e_agenda(contrato_data, data.valor)
    return {"id": contrato.id, "conflitos": conflitos}


@app.get("/api/agenda/aulas")
def listar_aulas(_: dict = Depends(verify_jwt)):
    return list(models.AulaSessao.objects.values())


@app.post("/api/agenda/aulas")
def criar_aula(data: AulaSessaoIn, _: dict = Depends(verify_jwt)):
    aula = models.AulaSessao.objects.create(**data.model_dump())
    return {"id": aula.id}


@app.post("/api/agenda/reservas")
def criar_reserva(data: ReservaIn, _: dict = Depends(verify_jwt)):
    reserva = models.Reserva(aluno_id=data.aluno_id, aulaSessao_id=data.aula_sessao_id, status=data.status)
    reserva.full_clean()
    reserva.save()
    return {"id": reserva.id}


@app.post("/api/agenda/reservas/cancelar")
def cancelar_reserva(reserva_id: int, _: dict = Depends(verify_jwt)):
    models.Reserva.objects.filter(pk=reserva_id).update(status="CANCELADA")
    return {"status": "ok"}


@app.post("/api/ai/documento/extrair")
def ai_documento(file: UploadFile = File(...), _: dict = Depends(verify_jwt)):
    data = extract_student_from_document(file.file.read(), file.filename)
    return data


@app.post("/api/ai/endereco/extrair")
def ai_endereco(file: UploadFile = File(...), _: dict = Depends(verify_jwt)):
    data = extract_address_from_proof(file.file.read(), file.filename)
    return data
