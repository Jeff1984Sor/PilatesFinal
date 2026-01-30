import json
import logging
import re

import httpx
from django.conf import settings

from . import models
from .models import WhatsappMessageType

logger = logging.getLogger(__name__)
PHONE_CLEAN_REGEX = re.compile(r"\D+")


def _normalize_endpoint(url: str) -> str:
    normalized = url.strip()
    if "api-docs/messages/send-text-message" in normalized:
        normalized = normalized.replace("api-docs/messages/send-text-message", "api/send-message")
        if normalized.startswith("https://wasenderapi.com"):
            normalized = normalized.replace("https://wasenderapi.com", "https://www.wasenderapi.com")
    return normalized


class EvolutionClient:
    def __init__(
        self,
        *,
        endpoint_url: str | None = None,
        token: str | None = None,
        base_url: str | None = None,
        instance: str | None = None,
    ):
        self.endpoint_url = _normalize_endpoint(endpoint_url) if endpoint_url else None
        self.base_url = base_url or settings.EVOLUTION_BASE_URL
        self.token = token or settings.EVOLUTION_TOKEN
        self.instance = instance or settings.EVOLUTION_INSTANCE

    def send_message(self, to: str, message: str) -> dict:
        if self.endpoint_url:
            url = self.endpoint_url.rstrip("/")
            if "wasenderapi" in url:
                if not self.token:
                    logger.warning("WhatsApp API token is not configured.")
                    headers = {}
                else:
                    headers = {"Authorization": f"Bearer {self.token}"}
                payload = {"to": to if to.startswith("+") else f"+{to}", "text": message}
            else:
                headers = {"apikey": self.token} if self.token else {}
                payload = {"number": to, "textMessage": {"text": message}}
        else:
            if not self.base_url or not self.token or not self.instance:
                logger.warning("WhatsApp API configuration is not configured.")
                return {"error": "WhatsApp configuration missing"}
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
    def _get_config_for_unidade(unidade: models.Unidade | None) -> models.WhatsappConfiguracao | None:
        if not unidade:
            return None
        return models.WhatsappConfiguracao.objects.filter(unidade=unidade).first()

    def _get_client_for_unidade(self, unidade: models.Unidade | None) -> EvolutionClient:
        config = self._get_config_for_unidade(unidade)
        if not config:
            return self.client
        token = config.evolution_senha or config.evolution_usuario or None
        return EvolutionClient(endpoint_url=config.evolution_url or None, token=token)

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
        cliente = self._get_client_for_unidade(getattr(aluno, "cdUnidade", None))
        resp = cliente.send_message(telefone, mensagem)
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
