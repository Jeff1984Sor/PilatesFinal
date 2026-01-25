from fastapi import HTTPException, status
from sqlalchemy import select, and_

from app.modules.agenda.repository import AgendaEventoRepository, AgendaParticipanteRepository
from app.modules.agenda.models import AgendaEvento, AgendaParticipante, EventoStatus, ParticipanteStatus


class AgendaService:
    def __init__(self, evento_repo: AgendaEventoRepository, participante_repo: AgendaParticipanteRepository):
        self.evento_repo = evento_repo
        self.participante_repo = participante_repo

    def create_evento(self, data: dict):
        self._check_conflict(data)
        return self.evento_repo.create(data)

    def _check_conflict(self, data: dict):
        stmt = select(AgendaEvento).where(
            and_(
                AgendaEvento.profissional_id == data["profissional_id"],
                AgendaEvento.inicio_datetime < data["fim_datetime"],
                AgendaEvento.fim_datetime > data["inicio_datetime"],
                AgendaEvento.status != EventoStatus.cancelado,
            )
        )
        conflict = self.evento_repo.db.execute(stmt).scalar_one_or_none()
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profissional conflitante no horario")

    def add_participante(self, evento_id: int, data: dict):
        evento = self.evento_repo.get(evento_id)
        if not evento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento not found")

        stmt = select(AgendaParticipante).where(
            AgendaParticipante.evento_id == evento_id,
            AgendaParticipante.status.in_([ParticipanteStatus.reservado, ParticipanteStatus.confirmado])
        )
        current = self.participante_repo.db.execute(stmt).scalars().all()
        if len(current) >= evento.capacidade:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Capacidade excedida")

        data["evento_id"] = evento_id
        return self.participante_repo.create(data)
