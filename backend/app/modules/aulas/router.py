from datetime import date, datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.aulas.schemas import (
    AulaAmanhaOut,
    AulaOperacaoListOut,
    AulaOperacaoOut,
    AulaOperacaoAlunoOut,
    AulaOperacaoProfissionalOut,
    AulaOperacaoPlanoOut,
    AulaOperacaoFlagsOut,
    AulaOperacaoEvolucaoOut,
    AulaEvolucaoCreate,
    AulaEvolucaoOut,
    AulaStatusUpdate,
)

router = APIRouter(prefix="/aulas", tags=["aulas"])
TZ = ZoneInfo("America/Sao_Paulo")
logger = logging.getLogger(__name__)

STATUS_MAP = {
    "RESERVADA": "aguardando_chegar",
    "PENDENTE": "aguardando_chegar",
    "CONCLUIDA": "finalizada",
    "FALTOU_AVISOU": "faltou",
    "FALTOU_SEM_AVISAR": "faltou",
    "CANCELADA": "remarcada",
}

STATUS_ACTION_MAP = {
    "chegou": "RESERVADA",
    "iniciar": "RESERVADA",
    "finalizar": "CONCLUIDA",
    "faltou": "FALTOU_SEM_AVISAR",
    "remarcar": "CANCELADA",
}


@router.get("/amanha", response_model=list[AulaAmanhaOut])
def aulas_amanha(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    target_date = date.today() + timedelta(days=1)
    sql = text(
        """
        SELECT r.id as reserva_id,
               r.aluno_id as aluno_id,
               (
                   SELECT t."dsTelefone"
                   FROM core_telefonealuno t
                   WHERE t."cdAluno_id" = r.aluno_id
                   ORDER BY t."dtCadastro" DESC, t.id DESC
                   LIMIT 1
               ) as telefone,
               a.data,
               a."horaInicio" as hora_inicio,
               pr.profissional as professora
        FROM core_reserva r
        JOIN core_aulasessao a ON a.id = r."aulaSessao_id"
        LEFT JOIN core_profissional pr ON pr.id = a.profissional_id
        WHERE a.data = :target_date
        """
        + (" AND r.status = :status" if status else "")
        + """
        ORDER BY a."horaInicio" ASC, r.id ASC
        """
    )
    params = {"target_date": target_date}
    if status:
        params["status"] = status
    rows = db.execute(sql, params).mappings().all()
    return [dict(row) for row in rows]


def _map_status(raw_status: str, start_dt: datetime, end_dt: datetime) -> str:
    mapped = STATUS_MAP.get(raw_status, "aguardando_chegar")
    if mapped == "aguardando_chegar":
        now = datetime.now(TZ)
        if start_dt <= now <= end_dt:
            return "em_aula"
    return mapped


def _build_date_range(target: date | None, periodo: str | None) -> tuple[date, date]:
    today = date.today()
    if periodo == "amanha":
        target = today + timedelta(days=1)
    elif periodo == "semana":
        base = target or today
        start = base - timedelta(days=base.weekday())
        end = start + timedelta(days=6)
        return start, end
    if target is None:
        target = today
    return target, target


@router.get("/operacao", response_model=AulaOperacaoListOut)
def aulas_operacao(
    data: date | None = Query(None),
    periodo: str | None = Query(None, description="hoje | amanha | semana"),
    unidade_id: int | None = None,
    profissional_id: int | None = None,
    status_aula: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = _build_date_range(data, periodo)

    filters = ["a.data BETWEEN :start_date AND :end_date"]
    params = {"start_date": start_date, "end_date": end_date}
    if unidade_id:
        filters.append("a.unidade_id = :unidade_id")
        params["unidade_id"] = unidade_id
    if profissional_id:
        filters.append("a.profissional_id = :profissional_id")
        params["profissional_id"] = profissional_id
    if q:
        filters.append(
            "(LOWER(al.\"dsNome\") LIKE :q OR al.\"dsCPF\" LIKE :q OR EXISTS ("
            "SELECT 1 FROM core_telefonealuno t WHERE t.\"cdAluno_id\" = al.id AND t.\"dsTelefone\" LIKE :q))"
        )
        params["q"] = f"%{q.lower()}%"

    where_clause = " AND ".join(filters)
    sql = text(
        f"""
        SELECT r.id as reserva_id,
               r.status as reserva_status,
               a.id as aula_sessao_id,
               a.data,
               a."horaInicio" as hora_inicio,
               a."horaFim" as hora_fim,
               u.id as unidade_id,
               u."dsUnidade" as unidade,
               pr.id as profissional_id,
               pr.profissional as profissional,
               al.id as aluno_id,
               al."dsNome" as aluno_nome,
               al.foto as aluno_foto,
               (
                   SELECT t."dsTelefone"
                   FROM core_telefonealuno t
                   WHERE t."cdAluno_id" = al.id
                   ORDER BY t."dtCadastro" DESC, t.id DESC
                   LIMIT 1
               ) as aluno_telefone,
               (
                   SELECT p.id
                   FROM core_contrato c
                   JOIN core_plano p ON p.id = c."cdPlano_id"
                   WHERE c."cdAluno_id" = al.id
                     AND c."dtInicioContrato" <= a.data
                     AND c."dtFimContrato" >= a.data
                     AND c.status IN ('ASSINADO', 'ASSINADO_DIGITALMENTE')
                   ORDER BY c."dtFimContrato" DESC, c.id DESC
                   LIMIT 1
               ) as plano_id,
               (
                   SELECT p."dsPlano"
                   FROM core_contrato c
                   JOIN core_plano p ON p.id = c."cdPlano_id"
                   WHERE c."cdAluno_id" = al.id
                     AND c."dtInicioContrato" <= a.data
                     AND c."dtFimContrato" >= a.data
                     AND c.status IN ('ASSINADO', 'ASSINADO_DIGITALMENTE')
                   ORDER BY c."dtFimContrato" DESC, c.id DESC
                   LIMIT 1
               ) as plano_descricao,
               CASE WHEN al.termo_aceite_em IS NOT NULL THEN 1 ELSE 0 END as tem_preliminares,
               CASE WHEN EXISTS (
                   SELECT 1
                   FROM core_contasreceber cr
                   JOIN core_contrato c2 ON c2.id = cr.contrato_id
                   WHERE c2."cdAluno_id" = al.id
                     AND cr.status = 'ABERTO'
               ) THEN 1 ELSE 0 END as cobranca_pendente,
               (
                   SELECT e.texto
                   FROM core_evolucaoaluno e
                   WHERE e.reserva_id = r.id
                   ORDER BY e."dtEvolucao" DESC
                   LIMIT 1
               ) as ultima_evolucao,
               (
                   SELECT e."dtEvolucao"
                   FROM core_evolucaoaluno e
                   WHERE e.reserva_id = r.id
                   ORDER BY e."dtEvolucao" DESC
                   LIMIT 1
               ) as ultima_evolucao_em
        FROM core_reserva r
        JOIN core_aulasessao a ON a.id = r."aulaSessao_id"
        JOIN core_aluno al ON al.id = r.aluno_id
        LEFT JOIN core_profissional pr ON pr.id = a.profissional_id
        LEFT JOIN core_unidade u ON u.id = a.unidade_id
        WHERE {where_clause}
        ORDER BY a.data ASC, a."horaInicio" ASC, al."dsNome" ASC
        """
    )

    rows = db.execute(sql, params).mappings().all()
    items: list[AulaOperacaoOut] = []
    for row in rows:
        start_dt = datetime.combine(row["data"], row["hora_inicio"], tzinfo=TZ)
        end_dt = datetime.combine(row["data"], row["hora_fim"], tzinfo=TZ)
        status_calc = _map_status(row["reserva_status"], start_dt, end_dt)
        if status_aula and status_calc != status_aula:
            continue

        items.append(
            AulaOperacaoOut(
                id=row["reserva_id"],
                aula_sessao_id=row["aula_sessao_id"],
                dt_inicio=start_dt,
                dt_fim=end_dt,
                unidade_id=row["unidade_id"],
                unidade=row["unidade"],
                sala=None,
                profissional=AulaOperacaoProfissionalOut(
                    id=row["profissional_id"],
                    nome=row["profissional"],
                ),
                aluno=AulaOperacaoAlunoOut(
                    id=row["aluno_id"],
                    nome=row["aluno_nome"],
                    telefone=row["aluno_telefone"],
                    avatar_url=row["aluno_foto"],
                ),
                plano=AulaOperacaoPlanoOut(
                    id=row["plano_id"],
                    descricao=row["plano_descricao"],
                ),
                status_aula=status_calc,
                confirmacao=row["reserva_status"] != "PENDENTE",
                flags=AulaOperacaoFlagsOut(
                    tem_preliminares=bool(row["tem_preliminares"]),
                    cobranca_pendente=bool(row["cobranca_pendente"]),
                    observacao_importante=False,
                ),
                ultima_evolucao=AulaOperacaoEvolucaoOut(
                    texto=row["ultima_evolucao"],
                    dt_evolucao=row["ultima_evolucao_em"],
                ),
            )
        )

    return AulaOperacaoListOut(data_inicio=start_date, data_fim=end_date, total=len(items), items=items)


@router.post("/{reserva_id}/evolucoes", response_model=AulaEvolucaoOut)
def criar_evolucao(
    reserva_id: int,
    payload: AulaEvolucaoCreate,
    db: Session = Depends(get_db),
):
    reserva = db.execute(text('SELECT id FROM core_reserva WHERE id = :reserva_id'), {"reserva_id": reserva_id}).first()
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva not found")

    insert_sql = text(
        """
        INSERT INTO core_evolucaoaluno (reserva_id, profissional_id, texto, "dtEvolucao")
        VALUES (:reserva_id, :profissional_id, :texto, CURRENT_TIMESTAMP)
        """
    )
    db.execute(
        insert_sql,
        {
            "reserva_id": reserva_id,
            "profissional_id": payload.profissional_id,
            "texto": payload.texto,
        },
    )

    if payload.finalizar:
        db.execute(
            text("UPDATE core_reserva SET status = 'CONCLUIDA' WHERE id = :reserva_id"),
            {"reserva_id": reserva_id},
        )

    db.commit()
    logger.info("aula.evolucao.saved reserva_id=%s finalizar=%s", reserva_id, payload.finalizar)

    select_sql = text(
        """
        SELECT id, reserva_id, texto, "dtEvolucao" as dt_evolucao
        FROM core_evolucaoaluno
        WHERE reserva_id = :reserva_id
        ORDER BY "dtEvolucao" DESC, id DESC
        LIMIT 1
        """
    )
    row = db.execute(select_sql, {"reserva_id": reserva_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao salvar evolucao")
    return dict(row)


@router.patch("/{reserva_id}/status")
def atualizar_status(
    reserva_id: int,
    payload: AulaStatusUpdate,
    db: Session = Depends(get_db),
):
    if payload.acao not in STATUS_ACTION_MAP:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Acao invalida")

    status_target = STATUS_ACTION_MAP[payload.acao]
    result = db.execute(
        text("UPDATE core_reserva SET status = :status WHERE id = :reserva_id"),
        {"status": status_target, "reserva_id": reserva_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva not found")
    db.commit()
    logger.info("aula.status.updated reserva_id=%s status=%s acao=%s", reserva_id, status_target, payload.acao)
    return {"reserva_id": reserva_id, "status": status_target}
