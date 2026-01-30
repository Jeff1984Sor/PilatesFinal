import httpx

from app.core.config import settings


def _normalize_endpoint(url: str) -> str:
    normalized = url.strip()
    if "api-docs/messages/send-text-message" in normalized:
        normalized = normalized.replace("api-docs/messages/send-text-message", "api/send-message")
        if normalized.startswith("https://wasenderapi.com"):
            normalized = normalized.replace("https://wasenderapi.com", "https://www.wasenderapi.com")
    return normalized


class EvolutionClient:
    def __init__(self):
        self.base_url = settings.EVOLUTION_BASE_URL
        self.token = settings.EVOLUTION_TOKEN
        self.instance = settings.EVOLUTION_INSTANCE

    def send_message(self, to: str, message: str) -> dict:
        if not self.base_url:
            return {"error": "EVOLUTION_BASE_URL not configured"}
        base_url = _normalize_endpoint(self.base_url)
        if "wasenderapi" in base_url or base_url.endswith("/api/send-message"):
            if not self.token:
                return {"error": "EVOLUTION_TOKEN not configured"}
            url = base_url.rstrip("/")
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {"to": to if to.startswith("+") else f"+{to}", "text": message}
        else:
            url = f"{base_url.rstrip('/')}/message/sendText/{self.instance}"
            headers = {"apikey": self.token}
            payload = {"number": to, "textMessage": {"text": message}}
        resp = httpx.post(url, json=payload, headers=headers)
        return resp.json()
