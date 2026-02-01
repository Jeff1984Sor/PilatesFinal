import re

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.alunos.schemas import (
    AlunoCreate,
    AlunoOut,
    EnderecoAlunoCreate,
    EnderecoAlunoOut,
    AlunoTermoPdfIn,
    AlunoAnexoOut,
    AlunoTelefoneLookupOut,
    AlunoWhatsappMessageIn,
    AlunoWhatsappMessageOut,
    ContextoIAOut,
    ContextoAulaOut,
)
from app.modules.alunos.repository import AlunoRepository, EnderecoRepository, AlunoAnexoRepository
from app.modules.alunos.service import AlunoService, AlunoAnexoService
from app.modules.termos.repository import TermoRepository
from app.modules.termos.service import TermoRenderer
from app.shared.pagination import Page, PageMeta

router = APIRouter(prefix="/alunos", tags=["alunos"])
PHONE_CLEAN_REGEX = re.compile(r"\\D+")


def _normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    digits = PHONE_CLEAN_REGEX.sub("", raw)
    if not digits:
        return None
    if digits.startswith("55"):
        return digits
    if len(digits) in (10, 11):
        return f"55{digits}"
    return digits


def _phone_variants(digits: str) -> list[str]:
    variants = {digits}
    if digits.startswith("55") and len(digits) > 2:
        variants.add(digits[2:])
    if not digits.startswith("55") and len(digits) in (10, 11):
        variants.add(f"55{digits}")
    return sorted(variants)


@router.post("", response_model=AlunoOut)
def create_aluno(payload: AlunoCreate, db: Session = Depends(get_db)):
    service = AlunoService(AlunoRepository(db), EnderecoRepository(db))
    return service.create(payload.model_dump())


@router.get("/{aluno_id:int}", response_model=AlunoOut)
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


@router.get("/buscar-telefone", response_model=AlunoTelefoneLookupOut)
def find_by_phone(telefone: str, db: Session = Depends(get_db)):
    normalized = _normalize_phone(telefone)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telefone invalido")
    variants = _phone_variants(normalized)
    normalized_sql = (
        "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(t.\"dsTelefone\", '+', ''), '-', ''), ' ', ''), '(', ''), ')', '')"
    )
    sql = text(
        f"""
        SELECT a.id as aluno_id, a."cdAluno" as codigo, a."dsNome" as nome, t."dsTelefone" as telefone
        FROM core_telefonealuno t
        JOIN core_aluno a ON a.id = t."cdAluno_id"
        WHERE {normalized_sql} IN :phones
        ORDER BY a."dsNome"
        LIMIT 10
        """
    ).bindparams(bindparam("phones", expanding=True))
    rows = db.execute(sql, {"phones": variants}).mappings().all()
    matches = [dict(row) for row in rows]
    return {"exists": bool(matches), "matches": matches}


@router.post("/{aluno_id:int}/whatsapp", response_model=AlunoWhatsappMessageOut)
def create_whatsapp_message(aluno_id: int, payload: AlunoWhatsappMessageIn, db: Session = Depends(get_db)):
    aluno = db.execute(text('SELECT id FROM core_aluno WHERE id = :aluno_id'), {"aluno_id": aluno_id}).first()
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno not found")
    telefone = _normalize_phone(payload.telefone) or payload.telefone
    insert_sql = text(
        """
        INSERT INTO core_alunowhatsappmessage
            (tipo, telefone, mensagem, status, response_payload, enviado_em, aluno_id, contrato_id)
        VALUES
            (:tipo, :telefone, :mensagem, :status, :response_payload, CURRENT_TIMESTAMP, :aluno_id, :contrato_id)
        """
    )
    db.execute(
        insert_sql,
        {
            "tipo": payload.tipo,
            "telefone": telefone,
            "mensagem": payload.mensagem,
            "status": payload.status,
            "response_payload": payload.response_payload or "",
            "aluno_id": aluno_id,
            "contrato_id": payload.contrato_id,
        },
    )
    db.commit()
    select_sql = text(
        """
        SELECT id, aluno_id, contrato_id, telefone, mensagem, tipo, status, response_payload, enviado_em
        FROM core_alunowhatsappmessage
        WHERE aluno_id = :aluno_id
        ORDER BY enviado_em DESC, id DESC
        LIMIT 1
        """
    )
    row = db.execute(select_sql, {"aluno_id": aluno_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save WhatsApp message")
    return dict(row)


@router.get("/{aluno_id:int}/whatsapp", response_model=list[AlunoWhatsappMessageOut])
def list_whatsapp_messages(
    aluno_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    aluno = db.execute(text('SELECT id FROM core_aluno WHERE id = :aluno_id'), {"aluno_id": aluno_id}).first()
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno not found")
    select_sql = text(
        """
        SELECT id, aluno_id, contrato_id, telefone, mensagem, tipo, status, response_payload, enviado_em
        FROM core_alunowhatsappmessage
        WHERE aluno_id = :aluno_id
        ORDER BY enviado_em DESC, id DESC
        LIMIT :limit
        """
    )
    rows = db.execute(select_sql, {"aluno_id": aluno_id, "limit": limit}).mappings().all()
    return [dict(row) for row in rows]


@router.get("/{aluno_id:int}/contexto-ia", response_model=ContextoIAOut)
def contexto_ia(aluno_id: int, db: Session = Depends(get_db)):
    aluno_sql = text(
        """
        SELECT a.id as aluno_id, a."dsNome" as nome, a."dsCPF" as cpf, a."dsEmail" as email,
               u."dsUnidade" as unidade
        FROM core_aluno a
        LEFT JOIN core_unidade u ON u.id = a."cdUnidade_id"
        WHERE a.id = :aluno_id
        """
    )
    aluno = db.execute(aluno_sql, {"aluno_id": aluno_id}).mappings().first()
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno not found")

    contratos_sql = text(
        """
        SELECT c.id,
               c."cdContrato" as codigo,
               c."dtInicioContrato" as dt_inicio,
               c."dtFimContrato" as dt_fim,
               c.status,
               c.valor_parcela,
               c.valor_total,
               p."dsPlano" as plano,
               u."dsUnidade" as unidade,
               pr.profissional as profissional
        FROM core_contrato c
        LEFT JOIN core_plano p ON p.id = c."cdPlano_id"
        LEFT JOIN core_unidade u ON u.id = c."cdUnidade_id"
        LEFT JOIN core_profissional pr ON pr.id = c."cdProfissional_id"
        WHERE c."cdAluno_id" = :aluno_id
        ORDER BY c."dtFimContrato" DESC, c.id DESC
        """
    )
    contratos = db.execute(contratos_sql, {"aluno_id": aluno_id}).mappings().all()

    aulas_sql = text(
        """
        SELECT r.id as reserva_id,
               r.status,
               a.data,
               a."horaInicio" as hora_inicio,
               a."horaFim" as hora_fim,
               ts."dsTipoServico" as tipo_servico,
               pr.profissional as profissional,
               u."dsUnidade" as unidade
        FROM core_reserva r
        JOIN core_aulasessao a ON a.id = r."aulaSessao_id"
        LEFT JOIN core_tiposervico ts ON ts.id = a."tipoServico_id"
        LEFT JOIN core_profissional pr ON pr.id = a.profissional_id
        LEFT JOIN core_unidade u ON u.id = a.unidade_id
        WHERE r.aluno_id = :aluno_id
        ORDER BY a.data DESC, a."horaInicio" DESC
        """
    )
    aulas = db.execute(aulas_sql, {"aluno_id": aluno_id}).mappings().all()

    faturas_sql = text(
        """
        SELECT cr.id,
               cr.contrato_id,
               cr.status,
               cr.valor,
               cr."dtVencimento" as dt_vencimento,
               cr."dtPagamento" as dt_pagamento
        FROM core_contasreceber cr
        JOIN core_contrato c ON c.id = cr.contrato_id
        WHERE c."cdAluno_id" = :aluno_id
          AND cr.status = 'ABERTO'
        ORDER BY cr."dtVencimento" ASC
        """
    )
    faturas = db.execute(faturas_sql, {"aluno_id": aluno_id}).mappings().all()

    evolucoes_sql = text(
        """
        SELECT e.id,
               e.texto,
               e."dtEvolucao" as dt_evolucao,
               e.reserva_id,
               pr.profissional as profissional
        FROM core_evolucaoaluno e
        JOIN core_reserva r ON r.id = e.reserva_id
        LEFT JOIN core_profissional pr ON pr.id = e.profissional_id
        WHERE r.aluno_id = :aluno_id
        ORDER BY e."dtEvolucao" DESC
        """
    )
    evolucoes = db.execute(evolucoes_sql, {"aluno_id": aluno_id}).mappings().all()

    whatsapp_sql = text(
        """
        SELECT id,
               aluno_id,
               contrato_id,
               telefone,
               mensagem,
               tipo,
               status,
               response_payload,
               enviado_em
        FROM core_alunowhatsappmessage
        WHERE aluno_id = :aluno_id
        ORDER BY enviado_em DESC, id DESC
        LIMIT 200
        """
    )
    whatsapp = db.execute(whatsapp_sql, {"aluno_id": aluno_id}).mappings().all()

    resumo = {
        "total_contratos": len(contratos),
        "total_aulas": len(aulas),
        "total_faturas_abertas": len(faturas),
        "total_evolucoes": len(evolucoes),
        "total_whatsapp": len(whatsapp),
    }

    return {
        **dict(aluno),
        "contratos": [dict(row) for row in contratos],
        "aulas_agendadas": [dict(row) for row in aulas],
        "faturas_abertas": [dict(row) for row in faturas],
        "evolucoes": [dict(row) for row in evolucoes],
        "whatsapp": [dict(row) for row in whatsapp],
        "resumo": resumo,
    }


@router.get("/{aluno_id:int}/proximas-aulas", response_model=list[ContextoAulaOut])
def proximas_aulas(
    aluno_id: int,
    limit: int = Query(2, ge=1, le=10),
    db: Session = Depends(get_db),
):
    aluno = db.execute(text('SELECT id FROM core_aluno WHERE id = :aluno_id'), {"aluno_id": aluno_id}).first()
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno not found")
    aulas_sql = text(
        """
        SELECT r.id as reserva_id,
               r.status,
               a.data,
               a."horaInicio" as hora_inicio,
               a."horaFim" as hora_fim,
               ts."dsTipoServico" as tipo_servico,
               pr.profissional as profissional,
               u."dsUnidade" as unidade
        FROM core_reserva r
        JOIN core_aulasessao a ON a.id = r."aulaSessao_id"
        LEFT JOIN core_tiposervico ts ON ts.id = a."tipoServico_id"
        LEFT JOIN core_profissional pr ON pr.id = a.profissional_id
        LEFT JOIN core_unidade u ON u.id = a.unidade_id
        WHERE r.aluno_id = :aluno_id
          AND (
            a.data > CURRENT_DATE
            OR (a.data = CURRENT_DATE AND a."horaInicio" >= CURRENT_TIME)
          )
        ORDER BY a.data ASC, a."horaInicio" ASC
        LIMIT :limit
        """
    )
    rows = db.execute(aulas_sql, {"aluno_id": aluno_id, "limit": limit}).mappings().all()
    return [dict(row) for row in rows]
