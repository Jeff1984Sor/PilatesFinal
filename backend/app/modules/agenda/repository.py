from sqlalchemy.orm import Session
from app.shared.repository import BaseRepository
from app.modules.agenda.models import AgendaEvento, AgendaParticipante, AgendaRecorrencia


class AgendaEventoRepository(BaseRepository[AgendaEvento]):
    def __init__(self, db: Session):
        super().__init__(db, AgendaEvento)


class AgendaParticipanteRepository(BaseRepository[AgendaParticipante]):
    def __init__(self, db: Session):
        super().__init__(db, AgendaParticipante)


class AgendaRecorrenciaRepository(BaseRepository[AgendaRecorrencia]):
    def __init__(self, db: Session):
        super().__init__(db, AgendaRecorrencia)
