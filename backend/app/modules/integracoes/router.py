from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.integracoes.totalpass.fake import FakeTotalPassClient
from app.modules.integracoes.totalpass.service import TotalPassService
from app.modules.integracoes.whatsapp_evolution.client import EvolutionClient
from app.modules.integracoes.whatsapp_evolution.service import WhatsappService

router = APIRouter(prefix="/integracoes", tags=["integracoes"])


@router.get("/totalpass/validar")
def totalpass_validar(cpf: str, db: Session = Depends(get_db)):
    service = TotalPassService(FakeTotalPassClient(), db)
    return service.validar_aluno(cpf)


@router.post("/whatsapp/enviar")
def whatsapp_enviar(to: str, message: str, db: Session = Depends(get_db)):
    service = WhatsappService(EvolutionClient(), db)
    return service.send(to, message)
