import json
from app.modules.integracoes.models import WhatsappLog
from app.modules.integracoes.whatsapp_evolution.client import EvolutionClient


class WhatsappService:
    def __init__(self, client: EvolutionClient, db):
        self.client = client
        self.db = db

    def send(self, to: str, message: str):
        resp = self.client.send_message(to, message)
        log = WhatsappLog(to=to, message=message, status="sent", response_payload=json.dumps(resp))
        self.db.add(log)
        self.db.commit()
        return resp
