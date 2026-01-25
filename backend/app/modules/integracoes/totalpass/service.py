import json
from app.modules.integracoes.models import TotalPassLog
from app.modules.integracoes.totalpass.port import TotalPassClient


class TotalPassService:
    def __init__(self, client: TotalPassClient, db):
        self.client = client
        self.db = db

    def validar_aluno(self, cpf: str):
        resp = self.client.validar_aluno(cpf)
        self._log("validate", resp)
        return resp

    def registrar_presenca(self, cpf: str, evento_id: int):
        resp = self.client.registrar_presenca(cpf, evento_id)
        self._log("checkin", resp)
        return resp

    def _log(self, status: str, response_payload: dict):
        log = TotalPassLog(
            status=status,
            request_payload=None,
            response_payload=json.dumps(response_payload),
        )
        self.db.add(log)
        self.db.commit()
