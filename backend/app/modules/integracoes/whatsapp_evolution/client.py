import httpx

from app.core.config import settings


class EvolutionClient:
    def __init__(self):
        self.base_url = settings.EVOLUTION_BASE_URL
        self.token = settings.EVOLUTION_TOKEN
        self.instance = settings.EVOLUTION_INSTANCE

    def send_message(self, to: str, message: str) -> dict:
        if not self.base_url:
            return {"error": "EVOLUTION_BASE_URL not configured"}
        url = f"{self.base_url}/message/sendText/{self.instance}"
        headers = {"apikey": self.token}
        payload = {"number": to, "textMessage": {"text": message}}
        resp = httpx.post(url, json=payload, headers=headers)
        return resp.json()
