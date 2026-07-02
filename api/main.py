import os
import re
import sys
import django
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Header, Query
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

from django.utils import timezone

from studiopilates.core import models
from studiopilates.core import services
from shared.ai.gemini_client import extract_address_from_proof, extract_student_from_document
from .schemas import (
    AlunoIn, AlunoOut, ContratoIn, AulaSessaoIn, ReservaIn, WhatsappMensagemIn,
    AlunoLoginSolicitar, AlunoLoginConfirmar,
)
import secrets
from datetime import timedelta
from studiopilates.core.whatsapp_service import WhatsappService, WhatsappMessageType

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


# ---------------------------------------------------------------------------
# API de Integracao externa (empresas). Autenticada por API key cadastrada na
# tela "Configuracoes > Tokens de Integracao" (models.IntegracaoToken).
# ---------------------------------------------------------------------------

_MESES = [
    "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
_STATUS_FATURA = {"aberto": "ABERTO", "pago": "PAGO", "atrasado": "ATRASADO", "cancelado": "CANCELADO"}


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
):
    """Aceita X-API-Key: <token> ou Authorization: Bearer <token>. Valida contra
    os tokens ATIVOS cadastrados em Tokens de Integracao."""
    provided = x_api_key
    if not provided and authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    if not provided:
        raise HTTPException(status_code=401, detail="API key ausente")
    tok = models.IntegracaoToken.objects.filter(token=provided, ativo=True).first()
    if not tok:
        raise HTTPException(status_code=401, detail="API key invalida")
    models.IntegracaoToken.objects.filter(pk=tok.pk).update(ultimo_uso=timezone.now())
    return provided


def _descricao_fatura(competencia):
    if competencia and "-" in competencia:
        try:
            ano, mes = competencia.split("-")[:2]
            return f"Mensalidade {_MESES[int(mes)]}/{ano}"
        except (ValueError, IndexError):
            pass
    return "Mensalidade"


def _aluno_payload(aluno, telefone=None):
    return {
        "id": aluno.id,
        "cdAluno": aluno.cdAluno,
        "dsNome": aluno.dsNome,
        "dsCPF": aluno.dsCPF,
        "dsEmail": aluno.dsEmail,
        "dsTelefone": telefone if telefone is not None else aluno.dsTelefone,
        "status": aluno.status,
    }


def _telefone_canon(raw):
    """Reduz um telefone a (ddd, 8_digitos_finais), tolerando DDI 55 e o 9 do
    celular. Ex.: '5515997762467', '(15) 99776-2467' e '(15) 9776-2467' viram
    todos ('15', '97762467'). Retorna None se nao der pra normalizar."""
    d = re.sub(r"\D", "", raw or "")
    if not d:
        return None
    if d.startswith("55") and len(d) > 11:
        d = d[2:]  # remove DDI
    if len(d) < 10:
        return None
    ultimos8 = d[-8:]
    resto = d[:-8]  # DDD (+ possivel 9 do celular)
    if len(resto) >= 3 and resto[-1] == "9":
        resto = resto[:-1]  # remove o 9 do celular
    ddd = resto[-2:]
    if len(ddd) != 2:
        return None
    return (ddd, ultimos8)


@app.get("/integracao/alunos/por-telefone")
def integ_aluno_por_telefone(telefone: str = Query(...), _: str = Depends(require_api_key)):
    digits = re.sub(r"\D", "", telefone or "")
    if not digits:
        raise HTTPException(status_code=400, detail="Telefone invalido")
    alvo = _telefone_canon(telefone)
    nucleo = digits[-8:] if len(digits) >= 8 else digits

    # 1) Procura na tabela TelefoneAluno (fonte principal), filtrando pelo nucleo
    candidatos = models.TelefoneAluno.objects.select_related("cdAluno").filter(dsTelefone__contains=nucleo)
    for t in candidatos:
        if alvo and _telefone_canon(t.dsTelefone) == alvo:
            return _aluno_payload(t.cdAluno, t.dsTelefone)

    # 2) Fallback: campo celular no proprio Aluno, caso exista/venha a existir
    if hasattr(models.Aluno, "celular") and alvo:
        for aluno in models.Aluno.objects.filter(celular__contains=nucleo):
            if _telefone_canon(aluno.celular) == alvo:
                return _aluno_payload(aluno, aluno.celular)

    raise HTTPException(status_code=404, detail="Aluno nao encontrado")


@app.get("/integracao/alunos/por-codigo/{cd_aluno}")
def integ_aluno_por_codigo(cd_aluno: int, _: str = Depends(require_api_key)):
    aluno = models.Aluno.objects.filter(cdAluno=cd_aluno).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    tel = aluno.telefones.first()
    return _aluno_payload(aluno, tel.dsTelefone if tel else None)


@app.get("/integracao/alunos")
def integ_listar_alunos(
    nome: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: str = Depends(require_api_key),
):
    qs = models.Aluno.objects.all()
    if nome:
        qs = qs.filter(dsNome__icontains=nome)
    if status:
        qs = qs.filter(status=status.upper())
    qs = qs.order_by("dsNome")[:limit]
    return [_aluno_payload(a) for a in qs]


@app.get("/integracao/faturas")
def integ_faturas(
    cdAluno: int = Query(...),
    status: str | None = Query(None, description="aberto|pago|atrasado|cancelado"),
    _: str = Depends(require_api_key),
):
    qs = models.ContasReceber.objects.select_related("contrato", "contrato__cdAluno").filter(
        contrato__cdAluno__cdAluno=cdAluno
    )
    if status:
        qs = qs.filter(status=_STATUS_FATURA.get(status.strip().lower(), status.strip().upper()))
    qs = qs.order_by("dtVencimento")
    return [
        {
            "id": cr.id,
            "cdAluno": cdAluno,
            "contrato_id": cr.contrato_id,
            "descricao": _descricao_fatura(cr.competencia),
            "competencia": cr.competencia or None,
            "valor": float(cr.valor),
            "vencimento": cr.dtVencimento,
            "dt_pagamento": cr.dtPagamento,
            "status": (cr.status or "").lower(),
        }
        for cr in qs
    ]


@app.get("/integracao/contratos")
def integ_contratos(cdAluno: int = Query(...), _: str = Depends(require_api_key)):
    qs = (
        models.Contrato.objects.select_related("cdAluno", "cdPlano", "cdProfissional", "cdUnidade")
        .filter(cdAluno__cdAluno=cdAluno)
        .order_by("-dtFimContrato", "-id")
    )
    return [
        {
            "id": c.id,
            "cdContrato": c.cdContrato,
            "cdAluno": cdAluno,
            "plano": c.cdPlano.dsPlano if c.cdPlano_id else None,
            "profissional": c.cdProfissional.profissional if c.cdProfissional_id else None,
            "unidade": c.cdUnidade.dsUnidade if c.cdUnidade_id else None,
            "dt_inicio": c.dtInicioContrato,
            "dt_fim": c.dtFimContrato,
            "status": c.status,
            "valor_parcela": float(c.valor_parcela) if c.valor_parcela is not None else None,
            "valor_total": float(c.valor_total) if c.valor_total is not None else None,
        }
        for c in qs
    ]


@app.post("/integracao/whatsapp-mensagens")
def integ_whatsapp_mensagem(data: WhatsappMensagemIn, _: str = Depends(require_api_key)):
    """Salva uma mensagem de WhatsApp na aba WhatsApp do aluno."""
    aluno = models.Aluno.objects.filter(cdAluno=data.cdAluno).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    direcao = (data.direcao or "").strip().lower()
    if direcao not in ("recebida", "enviada"):
        raise HTTPException(status_code=400, detail="direcao deve ser 'recebida' ou 'enviada'")
    contrato_id = data.contrato_id
    if contrato_id and not models.Contrato.objects.filter(pk=contrato_id).exists():
        contrato_id = None
    msg = models.AlunoWhatsappMessage.objects.create(
        aluno=aluno,
        contrato_id=contrato_id,
        tipo=models.WhatsappMessageType.MANUAL,
        direcao=direcao,
        telefone=data.telefone or "",
        mensagem=data.texto,
        status="received" if direcao == "recebida" else "sent",
        enviado_em=data.data_iso or timezone.now(),
    )
    return {
        "id": msg.id,
        "cdAluno": aluno.cdAluno,
        "direcao": direcao,
        "enviado_em": msg.enviado_em,
    }


@app.get("/integracao/aulas")
def integ_aulas(
    cdAluno: int = Query(...),
    apenas_proximas: bool = False,
    limit: int = Query(50, ge=1, le=200),
    _: str = Depends(require_api_key),
):
    qs = models.Reserva.objects.select_related(
        "aluno", "aulaSessao", "aulaSessao__tipoServico", "aulaSessao__profissional", "aulaSessao__unidade"
    ).filter(aluno__cdAluno=cdAluno)
    if apenas_proximas:
        hoje = timezone.localdate()
        qs = qs.filter(aulaSessao__data__gte=hoje)
    qs = qs.order_by("-aulaSessao__data", "-aulaSessao__horaInicio")[:limit]
    result = []
    for r in qs:
        a = r.aulaSessao
        result.append(
            {
                "reserva_id": r.id,
                "cdAluno": cdAluno,
                "data": a.data if a else None,
                "hora_inicio": a.horaInicio if a else None,
                "hora_fim": a.horaFim if a else None,
                "tipo_servico": a.tipoServico.dsTipoServico if a and a.tipoServico_id else None,
                "profissional": a.profissional.profissional if a and a.profissional_id else None,
                "unidade": a.unidade.dsUnidade if a and a.unidade_id else None,
                "status": r.status,
            }
        )
    return result


# ===========================================================================
# APP DO ALUNO (PWA) - login por CPF + codigo no WhatsApp
# ===========================================================================

def _so_digitos(v):
    return re.sub(r"\D", "", v or "")


def _achar_aluno_por_cpf(cpf_digitos):
    if not cpf_digitos:
        return None
    for a in models.Aluno.objects.all():
        if _so_digitos(a.dsCPF) == cpf_digitos:
            return a
    return None


def create_aluno_token(aluno):
    secret = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-secret")
    return jwt.encode({"aluno_id": aluno.id, "type": "aluno"}, secret, algorithm="HS256")


def verify_aluno_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    secret = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-secret")
    try:
        payload = jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalido")
    if payload.get("type") != "aluno":
        raise HTTPException(status_code=401, detail="Token invalido")
    aluno = models.Aluno.objects.filter(pk=payload.get("aluno_id")).first()
    if not aluno:
        raise HTTPException(status_code=401, detail="Aluno nao encontrado")
    return aluno


@app.post("/aluno-app/login/solicitar")
def aluno_app_login_solicitar(data: AlunoLoginSolicitar):
    cpf = _so_digitos(data.cpf)
    if len(cpf) != 11:
        raise HTTPException(status_code=400, detail="CPF invalido")
    aluno = _achar_aluno_por_cpf(cpf)
    if not aluno:
        raise HTTPException(status_code=404, detail="CPF nao encontrado")
    service = WhatsappService()
    telefone = service.get_aluno_phone(aluno)
    if not telefone:
        raise HTTPException(status_code=400, detail="Aluno sem telefone cadastrado")
    codigo = f"{secrets.randbelow(1000000):06d}"
    models.AlunoAppCodigo.objects.create(
        aluno=aluno, codigo=codigo, expira_em=timezone.now() + timedelta(minutes=10),
    )
    service.send(
        aluno, telefone,
        f"Mayris Pilates: seu codigo de acesso ao app e {codigo} (valido por 10 minutos).",
        WhatsappMessageType.MANUAL,
    )
    return {"ok": True, "telefone": "****" + telefone[-4:]}


@app.post("/aluno-app/login/confirmar")
def aluno_app_login_confirmar(data: AlunoLoginConfirmar):
    cpf = _so_digitos(data.cpf)
    aluno = _achar_aluno_por_cpf(cpf)
    if not aluno:
        raise HTTPException(status_code=404, detail="CPF nao encontrado")
    codigo = (
        models.AlunoAppCodigo.objects.filter(
            aluno=aluno, codigo=_so_digitos(data.codigo), usado=False, expira_em__gte=timezone.now(),
        )
        .order_by("-criado_em")
        .first()
    )
    if not codigo:
        raise HTTPException(status_code=401, detail="Codigo invalido ou expirado")
    codigo.usado = True
    codigo.save(update_fields=["usado"])
    return {"access_token": create_aluno_token(aluno), "nome": aluno.dsNome, "aluno_id": aluno.id}


@app.get("/aluno-app/me")
def aluno_app_me(aluno=Depends(verify_aluno_jwt)):
    return {
        "id": aluno.id,
        "cdAluno": aluno.cdAluno,
        "nome": aluno.dsNome,
        "cpf": aluno.dsCPF,
        "unidade": aluno.cdUnidade.dsUnidade if aluno.cdUnidade_id else None,
    }


@app.get("/aluno-app/aulas")
def aluno_app_aulas(aluno=Depends(verify_aluno_jwt)):
    hoje = timezone.localdate()
    reservas = (
        models.Reserva.objects.filter(aluno=aluno, aulaSessao__data__gte=hoje)
        .exclude(status="CANCELADA")
        .select_related("aulaSessao", "aulaSessao__tipoServico", "aulaSessao__profissional", "aulaSessao__unidade")
        .order_by("aulaSessao__data", "aulaSessao__horaInicio")
    )
    out = []
    for r in reservas:
        a = r.aulaSessao
        out.append({
            "reserva_id": r.id,
            "data": a.data,
            "hora_inicio": a.horaInicio.strftime("%H:%M") if a.horaInicio else None,
            "hora_fim": a.horaFim.strftime("%H:%M") if a.horaFim else None,
            "tipo_servico": a.tipoServico.dsTipoServico if a.tipoServico_id else None,
            "profissional": a.profissional.profissional if a.profissional_id else None,
            "unidade": a.unidade.dsUnidade if a.unidade_id else None,
            "status": r.status,
            "confirmada": bool(r.confirmada_em),
            "pode_alterar": a.data >= hoje,
        })
    return out


@app.post("/aluno-app/aulas/{reserva_id}/confirmar")
def aluno_app_confirmar(reserva_id: int, aluno=Depends(verify_aluno_jwt)):
    reserva = models.Reserva.objects.filter(pk=reserva_id, aluno=aluno).select_related("aulaSessao").first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada")
    if reserva.status == "CANCELADA":
        raise HTTPException(status_code=400, detail="Aula cancelada")
    if reserva.aulaSessao.data < timezone.localdate():
        raise HTTPException(status_code=400, detail="Aula ja passou")
    reserva.confirmada_em = timezone.now()
    reserva.save(update_fields=["confirmada_em"])
    return {"ok": True, "reserva_id": reserva.id, "confirmada": True}


@app.post("/aluno-app/aulas/{reserva_id}/desmarcar")
def aluno_app_desmarcar(reserva_id: int, aluno=Depends(verify_aluno_jwt)):
    reserva = models.Reserva.objects.filter(pk=reserva_id, aluno=aluno).select_related("aulaSessao").first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva nao encontrada")
    if reserva.status == "CANCELADA":
        raise HTTPException(status_code=400, detail="Aula ja desmarcada")
    if reserva.aulaSessao.data < timezone.localdate():
        raise HTTPException(status_code=400, detail="Nao e possivel desmarcar uma aula que ja passou")
    reposicao_ate = reserva.aulaSessao.data + timedelta(days=30)
    reserva.status = "CANCELADA"
    reserva.confirmada_em = None
    reserva.desmarcada_em = timezone.now()
    reserva.reposicao_ate = reposicao_ate
    reserva.save(update_fields=["status", "confirmada_em", "desmarcada_em", "reposicao_ate"])
    return {
        "ok": True,
        "reserva_id": reserva.id,
        "reposicao_ate": reposicao_ate.isoformat(),
        "mensagem": f"Aula desmarcada. Voce pode repor ate {reposicao_ate.strftime('%d/%m/%Y')} (30 dias).",
    }
