"""
Lidl NL JSON connector — structured data, no vision LLM needed.

Lidl serves leaflet/offer data via the Schwarz Group's leaflets CDN. This
connector queries the most likely API endpoints. If the structured path works,
it returns richer and more reliable data than vision extraction from images.

If all endpoints 404/fail, the store is skipped gracefully.

As of 2026-07 all candidate URLs below are dead (DNS failures or plain 404s) —
Lidl has no discoverable public leaflet API left; the working endpoint likely
now requires capturing real traffic from the Lidl Plus app. Until someone
updates this connector, Lidl will export 0 deals (the pipeline handles that
gracefully) — treat it the same as the 16 vision-LLM stores: run it through
the PDF/JPG + local-LLM path instead, or fix this connector with a fresh
endpoint capture.

Community reference:
  https://github.com/hermitdave/lidl-api
  Schwarz CDN: https://leaflets.schwarz
"""
import logging
import re
from typing import List, Optional

import requests

from modules.models import DealItem

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Accept": "application/json, */*",
    "Accept-Language": "nl-NL,nl;q=0.9",
    "x-country": "NL",
}

_CANDIDATES = [
    "https://leaflets.schwarz/api/v1/folders?countryCode=NL&language=nl",
    "https://api.lidl.com/v1/leaflets?country=nl",
    "https://api.lidl.com/v1/offers?country=nl&language=nl",
    "https://app.lidl.nl/api/v1/folders",
    "https://www.lidl.nl/api/leaflets",
]


# ── Parsing ────────────────────────────────────────────────────────────────────

def _parse_volume(text: str) -> tuple[Optional[int], Optional[str]]:
    if not text:
        return None, None
    m = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(g|gr|gram|ml|l|liter|kg|stuks?|st\.?)",
        str(text), re.IGNORECASE
    )
    if not m:
        return None, None
    raw_val = float(m.group(1).replace(",", "."))
    unit = m.group(2).lower().rstrip(".")
    unit_map = {"gr": "gram", "g": "gram", "l": "liter", "st": "stuks"}
    unit = unit_map.get(unit, unit)
    if unit == "liter" and raw_val < 10:
        return int(raw_val * 1000), "ml"
    return int(raw_val), unit


def _parse_item(raw: dict) -> Optional[DealItem]:
    try:
        name = (
            raw.get("name")
            or raw.get("title")
            or raw.get("productName")
            or raw.get("description", "")
        )
        if not name:
            return None

        price = None
        for key in ("price", "currentPrice", "actionPrice", "offerPrice"):
            p = raw.get(key)
            if p is None:
                continue
            if isinstance(p, dict):
                price = p.get("amount") or p.get("value") or p.get("normal") or p.get("now")
            elif isinstance(p, (int, float)):
                price = float(p)
            if price is not None:
                break

        promo = (
            raw.get("promotionText")
            or raw.get("subtitle")
            or raw.get("shortDescription")
            or raw.get("offerText", "")
        )

        unit_size = raw.get("unitSize") or raw.get("quantity") or raw.get("packageSize", "")
        volume, unit = _parse_volume(str(unit_size))

        return DealItem(
            winkel="Lidl",
            productnaam=str(name).strip(),
            korting_tekst=str(promo).strip() or None,
            actieprijs=float(price) if price is not None else None,
            inhoud_waarde=volume,
            inhoud_unit=unit,
        )
    except Exception as e:
        logger.debug(f"[Lidl] Item parse error: {e} — raw: {str(raw)[:120]}")
        return None


def _extract_items(data: object) -> List[dict]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("offers", "products", "items", "leafletItems", "folders", "data"):
        val = data.get(key)
        if isinstance(val, list) and val:
            # folders response may need a second level of nesting
            if key == "folders" and val and isinstance(val[0], dict):
                nested = []
                for folder in val:
                    nested.extend(folder.get("items") or folder.get("products") or [])
                return nested if nested else val
            return val
    return []


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_lidl_deals() -> List[DealItem]:
    """
    Fetch current Lidl NL offers as structured DealItems.
    Returns an empty list (never raises) if the API is unavailable.
    """
    for url in _CANDIDATES:
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=30)
            if resp.status_code != 200:
                logger.debug(f"[Lidl] {url} → {resp.status_code}")
                continue

            try:
                data = resp.json()
            except Exception:
                logger.debug(f"[Lidl] {url} returned non-JSON")
                continue

            items = _extract_items(data)
            if not items:
                logger.debug(f"[Lidl] {url} returned no items")
                continue

            deals = [_parse_item(i) for i in items]
            valid = [d for d in deals if d is not None]
            logger.info(f"[Lidl] {len(valid)} deals from {url}")
            return valid

        except Exception as e:
            logger.debug(f"[Lidl] {url} error: {e}")

    logger.warning(
        "[Lidl] All API endpoints failed. "
        "Lidl's Schwarz CDN endpoints may have changed. "
        "Consider Playwright-based scraping as an alternative."
    )
    return []
