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


def _extract_error_payload(resp: httpx.Response | None = None, exc: Exception | None = None) -> dict:
    payload: dict = {}
    if resp is not None:
        payload["status_code"] = resp.status_code
        try:
            data = resp.json()
            if isinstance(data, dict):
                payload["response"] = data
        except Exception:
            payload["response_text"] = (resp.text or "").strip()
        retry_after = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
        if retry_after:
            try:
                payload["retry_after"] = int(float(retry_after))
            except (TypeError, ValueError):
                payload["retry_after"] = retry_after
        if resp.status_code == 429:
            payload["rate_limited"] = True
    if exc is not None:
        payload["error"] = str(exc)
    return payload


class EvolutionClient:
    def __init__(
        self,
        *,
        endpoint_url: str | None = None,
        token: str | None = None,
        base_url: str | None = None,
        instance: str | None = None,
    ):
        effective_endpoint = endpoint_url or settings.WASENDER_API_URL or None
        effective_token = token or settings.WASENDER_API_TOKEN or None
        self.endpoint_url = _normalize_endpoint(effective_endpoint) if effective_endpoint else None
        self.base_url = base_url or settings.EVOLUTION_BASE_URL
        self.token = effective_token or settings.EVOLUTION_TOKEN
        self.instance = instance or settings.EVOLUTION_INSTANCE

    def send_message(self, to: str, message: str) -> dict:
        if self.endpoint_url:
            url = self.endpoint_url.rstrip("/")
            if not self.token:
                logger.warning("WhatsApp API token is not configured.")
                headers = {}
            else:
                headers = {"Authorization": f"Bearer {self.token}"}
            normalized = to if to.startswith("+") else f"+{to}"
            payload = {"to": normalized, "text": message}
            method = "post"
        else:
            if not self.base_url or not self.token or not self.instance:
                logger.warning("WhatsApp API configuration is not configured.")
                return {"error": "WhatsApp configuration missing"}
            url = f"{self.base_url.rstrip('/')}/message/sendText/{self.instance}"
            headers = {"apikey": self.token}
            payload = {"number": to, "textMessage": {"text": message}}
            method = "post"
        try:
            resp = httpx.request(method, url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as exc:
            logger.exception("Failed to send WhatsApp message to %s", to)
            return _extract_error_payload(exc=exc) | {"error": str(exc)}
        except httpx.HTTPStatusError as exc:
            logger.exception("WasenderAPI returned bad status for %s", to)
            return _extract_error_payload(resp=exc.response, exc=exc) | {"error": str(exc)}

    def send_document(self, to: str, media_url: str, filename: str, caption: str | None = None) -> dict:
        if not media_url:
            return {"error": "Media URL missing"}
        if self.endpoint_url:
            url = settings.WASENDER_MEDIA_URL or self.endpoint_url.rstrip("/").replace("send-message", "send-media")
            if not self.token:
                logger.warning("WhatsApp API token is not configured.")
                headers = {}
            else:
                headers = {"Authorization": f"Bearer {self.token}"}
            normalized = to if to.startswith("+") else f"+{to}"
            payload = {
                "to": normalized,
                "mediaUrl": media_url,
                "fileName": filename,
                "caption": caption or "",
                "type": "document",
            }
            method = "post"
        else:
            if not self.base_url or not self.token or not self.instance:
                logger.warning("WhatsApp API configuration is not configured.")
                return {"error": "WhatsApp configuration missing"}
            url = f"{self.base_url.rstrip('/')}/message/sendMedia/{self.instance}"
            headers = {"apikey": self.token}
            payload = {
                "number": to,
                "mediaMessage": {
                    "mediatype": "document",
                    "media": media_url,
                    "fileName": filename,
                    "caption": caption or "",
                },
            }
            method = "post"
        try:
            resp = httpx.request(method, url, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as exc:
            logger.exception("Failed to send WhatsApp document to %s", to)
            return {"error": str(exc)}
        except httpx.HTTPStatusError as exc:
            logger.exception("WasenderAPI returned bad status for %s", to)
            return {"error": str(exc)}


class WhatsappService:
    def __init__(self):
        self.client = EvolutionClient(endpoint_url=settings.WASENDER_API_URL, token=settings.WASENDER_API_TOKEN)

    @staticmethod
    def _get_config_for_unidade(unidade: models.Unidade | None) -> models.WhatsappConfiguracao | None:
        if not unidade:
            return None
        return models.WhatsappConfiguracao.objects.filter(unidade=unidade).first()

    def _get_client_for_unidade(self, unidade: models.Unidade | None) -> EvolutionClient:
        config = self._get_config_for_unidade(unidade)
        if config:
            return EvolutionClient(
                endpoint_url=config.evolution_url or settings.WASENDER_API_URL or None,
                token=config.evolution_senha or settings.WASENDER_API_TOKEN or None,
            )
        return self.client

    @staticmethod
    def clean_phone(raw: str | None) -> str | None:
        if not raw:
            return None
        cleaned = PHONE_CLEAN_REGEX.sub("", raw).lstrip("0")
        if not cleaned:
            return None
        if cleaned.startswith("55"):
            return cleaned if len(cleaned) >= 12 else None
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

    def send_document(
        self,
        aluno: models.Aluno,
        telefone: str,
        media_url: str,
        filename: str,
        caption: str | None = None,
        contrato: models.Contrato | None = None,
        tipo: models.WhatsappMessageType = models.WhatsappMessageType.CONTRACT_PDF,
    ) -> dict:
        cliente = self._get_client_for_unidade(getattr(aluno, "cdUnidade", None))
        resp = cliente.send_document(telefone, media_url, filename, caption=caption)
        status = "sent" if "error" not in resp else "failed"
        models.AlunoWhatsappMessage.objects.create(
            aluno=aluno,
            contrato=contrato,
            tipo=tipo,
            telefone=telefone,
            mensagem=caption or "",
            status=status,
            response_payload=json.dumps(resp, ensure_ascii=False),
        )
        return resp
