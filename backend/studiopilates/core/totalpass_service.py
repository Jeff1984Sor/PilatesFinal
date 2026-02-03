import httpx
from django.conf import settings


def _base_url():
    return getattr(settings, "TOTALPASS_BOOKING_BASE_URL", "https://booking-api.totalpass.com").rstrip("/")


def authenticate(partner_api_key, place_api_key):
    url = f"{_base_url()}/partner/auth"
    payload = {
        "partner_api_key": partner_api_key,
        "place_api_key": place_api_key,
    }
    resp = httpx.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json() if resp.content else {}
    token = data.get("token") or data.get("access_token") or data.get("jwt") or ""
    return token


def fetch_slots(token, date_from, date_to, place_id=""):
    url = f"{_base_url()}/partner/slot"
    params = {
        "slotDateFrom": date_from,
        "slotDateTo": date_to,
    }
    if place_id:
        params["placeId"] = place_id
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }
    resp = httpx.get(url, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json() if resp.content else {}
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("items") or data.get("data") or data.get("slots") or []
    return []

