from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.aulas.schemas import AulaAmanhaOut

router = APIRouter(prefix="/aulas", tags=["aulas"])


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
