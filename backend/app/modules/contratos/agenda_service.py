from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.aulas.models import Aula, AulaAluno, AulaStatus
from app.modules.contratos.models import Contrato, ContratoStatus
from app.modules.contratos.scheduler import TZ, SLOT_DURATION, daily_slots, iter_weeks, preferred_weekdays
from app.modules.planos.models import Plano
from app.modules.unidades.models import Unidade

logger = logging.getLogger(__name__)


@dataclass
class AgendaGeracaoResultado:
    total_aulas: int


class AgendaContratoErro(Exception):
    pass


class AgendaJaGerada(AgendaContratoErro):
    def __init__(self, contrato_id: int):
        super().__init__(f"Agenda ja gerada para contrato {contrato_id}")
        self.contrato_id = contrato_id


class AgendaCapacidadeInsuficiente(AgendaContratoErro):
    def __init__(self, pendencias: list[dict], faltantes: int):
        super().__init__("Capacidade insuficiente para gerar todas as aulas")
        self.pendencias = pendencias
        self.faltantes = faltantes


class AgendaContratoService:
    def __init__(self, db: Session):
        self.db = db

    def gerar_agenda_contrato(self, contrato: Contrato, *, force: bool = False) -> AgendaGeracaoResultado:
        if contrato.status != ContratoStatus.ativo:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contrato nao esta ativo")

        plano = self.db.get(Plano, contrato.plano_id)
        unidade = self.db.get(Unidade, contrato.unidade_id)
        if not plano or not unidade:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plano ou unidade invalidos")

        aulas_por_semana = plano.aulas_por_semana
        if aulas_por_semana is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plano sem aulas_por_semana")

        duracao_meses = plano.duracao_meses
        if duracao_meses is None and plano.tipo_plano and plano.tipo_plano.recorrencia:
            duracao_meses = plano.tipo_plano.recorrencia.intervalo_meses

        if duracao_meses is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plano sem duracao_meses")

        fim_calculado = contrato.inicio + relativedelta(months=duracao_meses)
        if contrato.fim != fim_calculado:
            contrato.fim = fim_calculado

        if contrato.agenda_gerada_em and not force:
            raise AgendaJaGerada(contrato.id)

        existing_count = self._count_aulas_contrato(contrato.id)
        if existing_count and not force:
            raise AgendaJaGerada(contrato.id)

        if force and existing_count:
            self.db.execute(delete(AulaAluno).where(AulaAluno.contrato_id == contrato.id))

        return self._gerar_agenda(
            contrato=contrato,
            unidade=unidade,
            aulas_por_semana=aulas_por_semana,
        )

    def _gerar_agenda(self, contrato: Contrato, unidade: Unidade, aulas_por_semana: int) -> AgendaGeracaoResultado:
        inicio = contrato.inicio
        fim = contrato.fim
        if fim is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contrato sem data fim")

        logger.info(
            "agenda.contrato.start contrato_id=%s aluno_id=%s unidade_id=%s inicio=%s fim=%s aulas_semana=%s",
            contrato.id,
            contrato.aluno_id,
            contrato.unidade_id,
            inicio,
            fim,
            aulas_por_semana,
        )

        try:
            preferred = preferred_weekdays(aulas_por_semana)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        period_start = datetime.combine(inicio, datetime.min.time(), tzinfo=TZ)
        period_end = datetime.combine(fim, datetime.max.time(), tzinfo=TZ)

        aulas_by_start = self._load_aulas_unidade(unidade.id, period_start, period_end)
        counts_by_aula = self._load_aula_counts(aulas_by_start.values())
        aluno_times, aluno_days = self._load_aluno_ocupacao(contrato.aluno_id, period_start, period_end)

        total_criadas = 0
        pendencias = []

        for week_start in iter_weeks(inicio, fim):
            week_days = self._week_days_in_range(week_start, inicio, fim)
            if not week_days:
                continue

            week_target = [day for day in week_days if day.weekday() in preferred]
            scheduled_this_week = 0
            used_days = set(day for day in week_days if day in aluno_days)
            failed_days = []

            scheduled_this_week += self._schedule_on_days(
                contrato,
                unidade,
                week_target,
                aulas_by_start,
                counts_by_aula,
                aluno_times,
                aluno_days,
                used_days,
                aulas_por_semana - scheduled_this_week,
                allow_same_day=False,
                failed_days=failed_days,
            )

            if scheduled_this_week < aulas_por_semana:
                remaining_days = [day for day in week_days if day not in week_target]
                scheduled_this_week += self._schedule_on_days(
                    contrato,
                    unidade,
                    remaining_days,
                    aulas_by_start,
                    counts_by_aula,
                    aluno_times,
                    aluno_days,
                    used_days,
                    aulas_por_semana - scheduled_this_week,
                    allow_same_day=False,
                    failed_days=failed_days,
                )

            if scheduled_this_week < aulas_por_semana:
                scheduled_this_week += self._schedule_on_days(
                    contrato,
                    unidade,
                    week_days,
                    aulas_by_start,
                    counts_by_aula,
                    aluno_times,
                    aluno_days,
                    used_days,
                    aulas_por_semana - scheduled_this_week,
                    allow_same_day=True,
                    failed_days=failed_days,
                )

            if scheduled_this_week < aulas_por_semana:
                pendencias.append(
                    {
                        "week_start": week_start.isoformat(),
                        "week_end": (week_start + timedelta(days=6)).isoformat(),
                        "faltantes": aulas_por_semana - scheduled_this_week,
                        "dias_sem_vaga": sorted({d.isoformat() for d in failed_days}),
                    }
                )

            total_criadas += scheduled_this_week

        if pendencias:
            faltantes = sum(item["faltantes"] for item in pendencias)
            logger.warning(
                "agenda.contrato.capacity_insufficient contrato_id=%s faltantes=%s pendencias=%s",
                contrato.id,
                faltantes,
                pendencias,
            )
            # Optamos por falhar a geracao para manter a criacao atômica e evitar agenda parcial.
            raise AgendaCapacidadeInsuficiente(pendencias=pendencias, faltantes=faltantes)

        contrato.agenda_gerada_em = datetime.now(TZ)

        logger.info(
            "agenda.contrato.done contrato_id=%s total_aulas=%s",
            contrato.id,
            total_criadas,
        )
        return AgendaGeracaoResultado(total_aulas=total_criadas)

    def _week_days_in_range(self, week_start: date, inicio: date, fim: date) -> list[date]:
        days = []
        for offset in range(5):
            current = week_start + timedelta(days=offset)
            if inicio <= current <= fim:
                days.append(current)
        return days

    def _schedule_on_days(
        self,
        contrato: Contrato,
        unidade: Unidade,
        days: Iterable[date],
        aulas_by_start: dict[datetime, Aula],
        counts_by_aula: dict[int, int],
        aluno_times: set[datetime],
        aluno_days: set[date],
        used_days: set[date],
        quantidade: int,
        *,
        allow_same_day: bool,
        failed_days: list[date],
    ) -> int:
        if quantidade <= 0:
            return 0

        scheduled = 0
        for target_date in days:
            if scheduled >= quantidade:
                break

            if not allow_same_day and target_date in used_days:
                continue

            created = self._schedule_single_day(
                contrato,
                unidade,
                target_date,
                aulas_by_start,
                counts_by_aula,
                aluno_times,
                aluno_days,
                allow_same_day,
            )
            if created:
                scheduled += 1
                used_days.add(target_date)
            else:
                failed_days.append(target_date)

        return scheduled

    def _schedule_single_day(
        self,
        contrato: Contrato,
        unidade: Unidade,
        target_date: date,
        aulas_by_start: dict[datetime, Aula],
        counts_by_aula: dict[int, int],
        aluno_times: set[datetime],
        aluno_days: set[date],
        allow_same_day: bool,
    ) -> bool:
        if not allow_same_day and target_date in aluno_days:
            return False

        slots = daily_slots(target_date)
        if not slots:
            return False

        for inicio_dt in slots:
            fim_dt = inicio_dt + SLOT_DURATION
            if inicio_dt in aluno_times:
                continue

            aula = aulas_by_start.get(inicio_dt)
            if aula is None:
                aula = Aula(
                    unidade_id=unidade.id,
                    inicio_datetime=inicio_dt,
                    fim_datetime=fim_dt,
                    status=AulaStatus.agendada,
                )
                self.db.add(aula)
                self.db.flush()
                aulas_by_start[inicio_dt] = aula
                counts_by_aula[aula.id] = 0
            else:
                self.db.execute(select(Aula.id).where(Aula.id == aula.id).with_for_update())

            current_count = counts_by_aula.get(aula.id, 0)
            if current_count >= unidade.ocupacao_max:
                continue

            self.db.add(
                AulaAluno(
                    aula_id=aula.id,
                    aluno_id=contrato.aluno_id,
                    contrato_id=contrato.id,
                )
            )
            counts_by_aula[aula.id] = current_count + 1
            aluno_times.add(inicio_dt)
            aluno_days.add(target_date)
            return True

        return False

    def _load_aulas_unidade(self, unidade_id: int, start_dt: datetime, end_dt: datetime) -> dict[datetime, Aula]:
        stmt = select(Aula).where(
            Aula.unidade_id == unidade_id,
            Aula.inicio_datetime >= start_dt,
            Aula.inicio_datetime <= end_dt,
        )
        aulas = self.db.execute(stmt).scalars().all()
        return {aula.inicio_datetime: aula for aula in aulas}

    def _load_aula_counts(self, aulas: Iterable[Aula]) -> dict[int, int]:
        aula_ids = [aula.id for aula in aulas]
        if not aula_ids:
            return {}

        stmt = (
            select(AulaAluno.aula_id, func.count())
            .where(AulaAluno.aula_id.in_(aula_ids))
            .group_by(AulaAluno.aula_id)
        )
        rows = self.db.execute(stmt).all()
        return {row[0]: row[1] for row in rows}

    def _load_aluno_ocupacao(self, aluno_id: int, start_dt: datetime, end_dt: datetime) -> tuple[set[datetime], set[date]]:
        stmt = (
            select(Aula.inicio_datetime)
            .join(AulaAluno, AulaAluno.aula_id == Aula.id)
            .where(
                AulaAluno.aluno_id == aluno_id,
                Aula.inicio_datetime >= start_dt,
                Aula.inicio_datetime <= end_dt,
            )
        )
        rows = self.db.execute(stmt).all()
        times = {row[0] for row in rows}
        days = {row[0].date() for row in rows}
        return times, days

    def _count_aulas_contrato(self, contrato_id: int) -> int:
        stmt = select(func.count()).select_from(AulaAluno).where(AulaAluno.contrato_id == contrato_id)
        return int(self.db.execute(stmt).scalar_one())
