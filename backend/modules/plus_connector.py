"""
Plus DOM connector — structured data, no vision LLM needed.

Plus's own backend (a Gravitee API gateway) and its OutSystems Reactive
frontend don't expose a guessable public JSON endpoint, and the OutSystems
screen-action call needed is only fetched lazily after client-side JS
navigation. Simplest robust route: drive a real (headless) Chromium via
Playwright to https://www.plus.nl/aanbiedingen, dismiss the cookie banner,
and read the already-rendered deal cards straight out of the DOM.
"""
import logging
import re
from typing import List, Optional, Tuple

from modules.models import DealItem

logger = logging.getLogger(__name__)

_URL = "https://www.plus.nl/aanbiedingen"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _parse_volume(text: str) -> Tuple[Optional[int], Optional[str]]:
    if not text:
        return None, None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(g|gr|gram|ml|l|liter|kg|cl|stuks?|st\.?)", text, re.IGNORECASE)
    if not m:
        return None, None
    raw_val = float(m.group(1).replace(",", "."))
    unit = m.group(2).lower().rstrip(".")
    unit_map = {"gr": "gram", "g": "gram", "l": "liter", "st": "stuks", "cl": "ml"}
    unit = unit_map.get(unit, unit)
    if unit == "cl" or (m.group(2).lower() == "cl"):
        raw_val *= 10  # cl -> ml
        unit = "ml"
    if unit == "liter" and raw_val < 10:
        return int(raw_val * 1000), "ml"
    return int(raw_val), unit


def fetch_plus_deals() -> List[DealItem]:
    """
    Fetch Plus's current offers by rendering the page with a headless
    browser and reading the deal cards' DOM text directly.
    Returns an empty list (never raises) if Playwright/the page is unavailable.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("[Plus] Playwright not installed — run `pip install playwright` "
                        "and `playwright install chromium` to enable this connector.")
        return []

    deals: List[DealItem] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(user_agent=_USER_AGENT)
                page.goto(_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                try:
                    page.get_by_role("button", name="Accepteer").click(timeout=5000)
                except Exception:
                    pass

                # The SPA re-renders its product list after the cookie banner closes,
                # so poll for priced cards to actually appear rather than a fixed sleep.
                priced_locator = page.locator(".plp-item-wrapper:has(.product-header-price-integer)")
                for _ in range(20):
                    if priced_locator.count() > 0:
                        break
                    page.wait_for_timeout(500)

                cards = page.locator(".plp-item-wrapper").all()
                for card in cards:
                    try:
                        price_int_loc = card.locator(".product-header-price-integer")
                        if not price_int_loc.count():
                            continue  # e.g. "gratis bezorging" threshold cards with no per-product price
                        price_dec_loc = card.locator(".product-header-price-decimals")
                        int_part = re.sub(r"\D", "", price_int_loc.first.inner_text())
                        dec_part = re.sub(r"\D", "", price_dec_loc.first.inner_text()) if price_dec_loc.count() else "00"
                        price = float(f"{int_part}.{dec_part or '00'}")
                        if price <= 0:
                            continue  # "gratis bezorging bij X euro" threshold cards, not a real product deal

                        name_loc = card.locator(".plp-item-name span")
                        title = name_loc.first.inner_text().strip() if name_loc.count() else None
                        if not title:
                            continue

                        label_loc = card.locator(".promo-offer-label span")
                        label = label_loc.first.inner_text().strip() if label_loc.count() else None

                        desc_loc = card.locator(".plp-item-complementary span")
                        desc = desc_loc.first.inner_text().strip() if desc_loc.count() else ""
                        volume, unit = _parse_volume(desc)

                        deals.append(DealItem(
                            winkel="Plus",
                            productnaam=title,
                            korting_tekst=label,
                            actieprijs=price,
                            inhoud_waarde=volume,
                            inhoud_unit=unit,
                        ))
                    except Exception as e:
                        logger.debug(f"[Plus] Card parse error: {e}")
            finally:
                browser.close()
    except Exception as e:
        logger.warning(f"[Plus] Playwright render failed: {e}")
        return []

    if not deals:
        logger.warning("[Plus] Rendered the page but found no priced deal cards — Plus may have changed its layout.")
    else:
        logger.info(f"[Plus] {len(deals)} deals read from the rendered page")
    return deals
