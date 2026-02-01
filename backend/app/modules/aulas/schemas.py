from datetime import date, time
from pydantic import BaseModel


class AulaAmanhaOut(BaseModel):
    reserva_id: int
    aluno_id: int
    telefone: str | None = None
    data: date
    hora_inicio: time
    professora: str | None = None
