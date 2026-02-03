from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.modules.contratos.agenda_service import (
    AgendaCapacidadeInsuficiente,
    AgendaContratoService,
    AgendaJaGerada,
)
from app.modules.contratos.models import Contrato
from app.modules.contratos.repository import ContratoRepository
from app.modules.contratos.schemas import ContratoCreate
from app.modules.planos.models import Plano
from app.modules.contratos.scheduler import TZ
from app.modules.aulas.models import Aula, AulaAluno


class ContratoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContratoRepository(db)
        self.agenda_service = AgendaContratoService(db)

    def create_with_agenda(self, payload: ContratoCreate) -> Contrato:
        if payload.idempotency_key:
            existing = self._get_by_idempotency(payload.idempotency_key)
            if existing:
                return existing

        plano = self.db.get(Plano, payload.plano_id)
        if not plano:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plano invalido")

        with self.db.begin():
            contrato = Contrato(
                aluno_id=payload.aluno_id,
                plano_id=payload.plano_id,
                unidade_id=payload.unidade_id,
                tipo_plano_id=payload.tipo_plano_id,
                profissional_id=payload.profissional_id,
                inicio=payload.inicio,
                fim=payload.fim,
                status=payload.status,
                observacoes=payload.observacoes,
                idempotency_key=payload.idempotency_key,
            )
            self.db.add(contrato)
            self.db.flush()

            try:
                self.agenda_service.gerar_agenda_contrato(contrato)
            except AgendaCapacidadeInsuficiente as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "capacidade_insuficiente",
                        "message": str(exc),
                        "faltantes": exc.faltantes,
                        "pendencias": exc.pendencias,
                    },
                )

        return contrato

    def gerar_agenda(self, contrato_id: int, *, force: bool = False) -> dict:
        contrato = self._get_for_update(contrato_id)
        if not contrato:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato not found")

        with self.db.begin():
            try:
                result = self.agenda_service.gerar_agenda_contrato(contrato, force=force)
            except AgendaJaGerada:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agenda ja gerada")
            except AgendaCapacidadeInsuficiente as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "capacidade_insuficiente",
                        "message": str(exc),
                        "faltantes": exc.faltantes,
                        "pendencias": exc.pendencias,
                    },
                )

        return {"total_aulas": result.total_aulas, "agenda_gerada_em": contrato.agenda_gerada_em}

    def get_detail(self, contrato_id: int) -> tuple[Contrato, dict]:
        contrato = self.repo.get(contrato_id)
        if not contrato:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato not found")

        now = datetime.now(TZ)
        total_stmt = select(func.count()).select_from(AulaAluno).where(AulaAluno.contrato_id == contrato_id)
        total_aulas = int(self.db.execute(total_stmt).scalar_one())

        proximas_stmt = (
            select(Aula)
            .join(AulaAluno, AulaAluno.aula_id == Aula.id)
            .where(
                AulaAluno.contrato_id == contrato_id,
                Aula.inicio_datetime >= now,
            )
            .order_by(Aula.inicio_datetime.asc())
            .limit(5)
        )
        proximas = self.db.execute(proximas_stmt).scalars().all()

        resumo = {
            "total_aulas": total_aulas,
            "proximas_aulas": proximas,
        }
        return contrato, resumo

    def _get_by_idempotency(self, key: str) -> Contrato | None:
        stmt = select(Contrato).where(Contrato.idempotency_key == key)
        return self.db.execute(stmt).scalar_one_or_none()

    def _get_for_update(self, contrato_id: int) -> Contrato | None:
        stmt = select(Contrato).where(Contrato.id == contrato_id).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()
