import re

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.modules.integracao.schemas import AlunoOut, FaturaOut, ContratoOut, AulaOut

# Todos os endpoints exigem Bearer token (get_current_user).
router = APIRouter(prefix="/integracao", tags=["integracao"], dependencies=[Depends(get_current_user)])

_PHONE_RE = re.compile(r"\D+")
_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
_STATUS_FATURA = {"aberto": "ABERTO", "pago": "PAGO", "atrasado": "ATRASADO", "cancelado": "CANCELADO"}


def _normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    digits = _PHONE_RE.sub("", raw)
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


def _descricao_fatura(competencia: str | None) -> str:
    if competencia and "-" in competencia:
        try:
            ano, mes = competencia.split("-")[:2]
            return f"Mensalidade {_MESES[int(mes)]}/{ano}"
        except (ValueError, IndexError):
            pass
    return "Mensalidade"


@router.get("/alunos/por-telefone", response_model=AlunoOut)
def aluno_por_telefone(telefone: str = Query(..., description="Telefone, pode ser so digitos"), db: Session = Depends(get_db)):
    normalized = _normalize_phone(telefone)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telefone invalido")
    variants = _phone_variants(normalized)
    tel_norm = "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(t.\"dsTelefone\", '+', ''), '-', ''), ' ', ''), '(', ''), ')', '')"
    sql = text(
        f"""
        SELECT a.id, a."cdAluno" AS "cdAluno", a."dsNome" AS "dsNome",
               a."dsCPF" AS "dsCPF", a."dsEmail" AS "dsEmail",
               t."dsTelefone" AS "dsTelefone", a.status
        FROM core_telefonealuno t
        JOIN core_aluno a ON a.id = t."cdAluno_id"
        WHERE {tel_norm} IN :phones
        ORDER BY a."dsNome"
        LIMIT 1
        """
    ).bindparams(bindparam("phones", expanding=True))
    row = db.execute(sql, {"phones": variants}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno nao encontrado")
    return dict(row)


@router.get("/alunos/por-codigo/{cd_aluno}", response_model=AlunoOut)
def aluno_por_codigo(cd_aluno: int, db: Session = Depends(get_db)):
    sql = text(
        """
        SELECT a.id, a."cdAluno" AS "cdAluno", a."dsNome" AS "dsNome",
               a."dsCPF" AS "dsCPF", a."dsEmail" AS "dsEmail",
               (SELECT t."dsTelefone" FROM core_telefonealuno t WHERE t."cdAluno_id" = a.id ORDER BY t.id LIMIT 1) AS "dsTelefone",
               a.status
        FROM core_aluno a
        WHERE a."cdAluno" = :cd_aluno
        LIMIT 1
        """
    )
    row = db.execute(sql, {"cd_aluno": cd_aluno}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno nao encontrado")
    return dict(row)


@router.get("/alunos", response_model=list[AlunoOut])
def listar_alunos(
    nome: str | None = Query(None, description="Filtro por parte do nome"),
    status_filtro: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    where = []
    params: dict = {"limit": limit}
    if nome:
        where.append('a."dsNome" ILIKE :nome')
        params["nome"] = f"%{nome}%"
    if status_filtro:
        where.append("a.status = :status")
        params["status"] = status_filtro.upper()
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = text(
        f"""
        SELECT a.id, a."cdAluno" AS "cdAluno", a."dsNome" AS "dsNome",
               a."dsCPF" AS "dsCPF", a."dsEmail" AS "dsEmail",
               NULL AS "dsTelefone", a.status
        FROM core_aluno a
        {where_sql}
        ORDER BY a."dsNome"
        LIMIT :limit
        """
    )
    rows = db.execute(sql, params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/faturas", response_model=list[FaturaOut])
def listar_faturas(
    cdAluno: int = Query(..., description="Codigo do aluno (cdAluno)"),
    status_filtro: str | None = Query(None, alias="status", description="aberto|pago|atrasado|cancelado"),
    db: Session = Depends(get_db),
):
    params: dict = {"cd_aluno": cdAluno}
    status_sql = ""
    if status_filtro:
        mapped = _STATUS_FATURA.get(status_filtro.strip().lower(), status_filtro.strip().upper())
        status_sql = "AND cr.status = :status"
        params["status"] = mapped
    sql = text(
        f"""
        SELECT cr.id, a."cdAluno" AS "cdAluno", cr.contrato_id,
               cr.competencia, cr.valor, cr."dtVencimento" AS vencimento,
               cr."dtPagamento" AS dt_pagamento, cr.status
        FROM core_contasreceber cr
        JOIN core_contrato c ON c.id = cr.contrato_id
        JOIN core_aluno a ON a.id = c."cdAluno_id"
        WHERE a."cdAluno" = :cd_aluno
        {status_sql}
        ORDER BY cr."dtVencimento" ASC
        """
    )
    rows = db.execute(sql, params).mappings().all()
    result = []
    for r in rows:
        d = dict(r)
        d["descricao"] = _descricao_fatura(d.get("competencia"))
        d["status"] = (d.get("status") or "").lower()
        result.append(d)
    return result


@router.get("/contratos", response_model=list[ContratoOut])
def listar_contratos(
    cdAluno: int = Query(..., description="Codigo do aluno (cdAluno)"),
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT c.id, c."cdContrato" AS "cdContrato", a."cdAluno" AS "cdAluno",
               p."dsPlano" AS plano, pr.profissional AS profissional,
               u."dsUnidade" AS unidade,
               c."dtInicioContrato" AS dt_inicio, c."dtFimContrato" AS dt_fim,
               c.status, c.valor_parcela, c.valor_total
        FROM core_contrato c
        JOIN core_aluno a ON a.id = c."cdAluno_id"
        LEFT JOIN core_plano p ON p.id = c."cdPlano_id"
        LEFT JOIN core_profissional pr ON pr.id = c."cdProfissional_id"
        LEFT JOIN core_unidade u ON u.id = c."cdUnidade_id"
        WHERE a."cdAluno" = :cd_aluno
        ORDER BY c."dtFimContrato" DESC, c.id DESC
        """
    )
    rows = db.execute(sql, {"cd_aluno": cdAluno}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/aulas", response_model=list[AulaOut])
def listar_aulas(
    cdAluno: int = Query(..., description="Codigo do aluno (cdAluno)"),
    apenas_proximas: bool = Query(False, description="Somente aulas de hoje em diante"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    params: dict = {"cd_aluno": cdAluno, "limit": limit}
    proximas_sql = ""
    if apenas_proximas:
        proximas_sql = (
            'AND (a.data > CURRENT_DATE OR (a.data = CURRENT_DATE AND a."horaInicio" >= CURRENT_TIME))'
        )
    sql = text(
        f"""
        SELECT r.id AS reserva_id, al."cdAluno" AS "cdAluno", r.status,
               a.data, a."horaInicio" AS hora_inicio, a."horaFim" AS hora_fim,
               ts."dsTipoServico" AS tipo_servico, pr.profissional AS profissional,
               u."dsUnidade" AS unidade
        FROM core_reserva r
        JOIN core_aluno al ON al.id = r.aluno_id
        JOIN core_aulasessao a ON a.id = r."aulaSessao_id"
        LEFT JOIN core_tiposervico ts ON ts.id = a."tipoServico_id"
        LEFT JOIN core_profissional pr ON pr.id = a.profissional_id
        LEFT JOIN core_unidade u ON u.id = a.unidade_id
        WHERE al."cdAluno" = :cd_aluno
        {proximas_sql}
        ORDER BY a.data DESC, a."horaInicio" DESC
        LIMIT :limit
        """
    )
    rows = db.execute(sql, params).mappings().all()
    return [dict(r) for r in rows]
