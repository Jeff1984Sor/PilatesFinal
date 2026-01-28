import json
import logging
import re

import httpx
from django.conf import settings

from . import models

logger = logging.getLogger(__name__)
PHONE_CLEAN_REGEX = re.compile(r"\D+")


class EvolutionClient:
    def __init__(self):
        self.base_url = settings.EVOLUTION_BASE_URL
        self.token = settings.EVOLUTION_TOKEN
        self.instance = settings.EVOLUTION_INSTANCE

    def send_message(self, to: str, message: str) -> dict:
        if not self.base_url or not self.token or not self.instance:
            logger.warning("Evolution credentials are not configured.")
            return {"error": "Evolution configuration missing"}
        url = f"{self.base_url.rstrip('/')}/message/sendText/{self.instance}"
        headers = {"apikey": self.token}
        payload = {"number": to, "textMessage": {"text": message}}
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as exc:
            logger.exception("Failed to send WhatsApp message to %s", to)
            return {"error": str(exc)}
        except httpx.HTTPStatusError as exc:
            logger.exception("Evolution returned bad status for %s", to)
            return {"error": str(exc)}


class WhatsappService:
    def __init__(self):
        self.client = EvolutionClient()

    @staticmethod
    def clean_phone(raw: str | None) -> str | None:
        if not raw:
            return None
        cleaned = PHONE_CLEAN_REGEX.sub("", raw)
        if not cleaned:
            return None
        if cleaned.startswith("55"):
            return cleaned
        if len(cleaned) in (10, 11):
            return f"55{cleaned}"
        return cleaned

    def get_aluno_phone(self, aluno: models.Aluno) -> str | None:
        for telefone in aluno.telefones.values_list("dsTelefone", flat=True):
            cleaned = self.clean_phone(telefone)
            if cleaned:
                return cleaned
        return None

    def get_profissional_phone(self, profissional: models.Profissional) -> str | None:
        return self.clean_phone(getattr(profissional, "celular", None))

    def send(
        self,
        aluno: models.Aluno,
        telefone: str,
        mensagem: str,
        tipo: models.WhatsappMessageType,
        contrato: models.Contrato | None = None,
    ) -> dict:
        resp = self.client.send_message(telefone, mensagem)
        status = "sent" if "error" not in resp else "failed"
        models.AlunoWhatsappMessage.objects.create(
            aluno=aluno,
            contrato=contrato,
            tipo=tipo,
            telefone=telefone,
            mensagem=mensagem,
            status=status,
            response_payload=json.dumps(resp, ensure_ascii=False),
        )
        return resp
