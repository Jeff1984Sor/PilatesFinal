import httpx

from app.modules.integracoes.totalpass.port import TotalPassClient
from app.core.config import settings


class HttpTotalPassClient(TotalPassClient):
    def __init__(self):
        self.base_url = settings.TOTALPASS_BASE_URL
        self.api_key = settings.TOTALPASS_API_KEY

    def validar_aluno(self, cpf: str) -> dict:
        if not self.base_url:
            return {"error": "TOTALPASS_BASE_URL not configured"}
        resp = httpx.get(f"{self.base_url}/validate", params={"cpf": cpf}, headers={"X-API-KEY": self.api_key})
        return resp.json()

    def registrar_presenca(self, cpf: str, evento_id: int) -> dict:
        if not self.base_url:
            return {"error": "TOTALPASS_BASE_URL not configured"}
        resp = httpx.post(
            f"{self.base_url}/checkin",
            json={"cpf": cpf, "evento_id": evento_id},
            headers={"X-API-KEY": self.api_key},
        )
        return resp.json()
