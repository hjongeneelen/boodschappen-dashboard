"""
Jumbo DOM connector — structured data, no vision LLM needed.

Jumbo's mobile/GraphQL APIs are behind Akamai Bot Manager (confirmed: plain
`requests` calls get a bot-mitigation challenge page even against the site's
own GraphQL endpoint). But the public *website* itself renders fine for a
real browser — Akamai's block triggers on the API traffic pattern, not on
loading the page. So instead of calling an API, we drive a real (headless)
Chromium via Playwright and read deal cards straight out of the DOM — no
OCR/vision needed, since the text is plain HTML, just not reachable via a
bare HTTP request.

We read /producten/alle-aanbiedingen/ (the "Alle aanbiedingen" filter a
shopper would click on the site) rather than the curated /aanbiedingen/nu
highlights page — same ~24 items on the first page, but with much richer
data: full titles including pack size (e.g. "Hertog Jan - Pils - Krat - 24 x
300ML"), which we parse for inhoud_waarde/inhoud_unit, and cleaner prices.

This listing says it has ~1300 products across ~54 pages, but its pagination
turned out to be a dead end for a headless browser: neither navigating
`?page=N` directly nor clicking the page-N button (even with a realistic
mouse move + down/up, not just a synthetic click) changes the rendered
results — the app never fires a request or updates `aria-current`. Rather
than dig further into why (which risks turning into working around
whatever's gating it), we only read page 1. If someone figures out the
pagination trigger later, this is the place to extend it.
"""
import logging
import re
from typing import List, Optional, Tuple

from modules.models import DealItem

logger = logging.getLogger(__name__)

_LISTING_URL = "https://www.jumbo.com/producten/alle-aanbiedingen/"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_VOLUME_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(x)?\s*(\d+(?:[.,]\d+)?)?\s*(gram|gr|g|ml|cl|liter|ltr|l|kg)\b",
    re.IGNORECASE,
)
_UNIT_MAP = {"gr": "gram", "g": "gram", "ltr": "liter", "l": "liter", "cl": "ml"}


def _parse_volume(title: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Pull a pack size out of a Jumbo product title, e.g.:
      'Jumbo Aardbeien Hollands 400 g'      -> (400, 'gram')
      'Coca-Cola ... 6 x 1,5 L'             -> (9000, 'ml')   (6 * 1.5L)
      'Hertog Jan - Pils - Krat - 24 x 300ML' -> (7200, 'ml') (24 * 300ml)
    """
    m = _VOLUME_RE.search(title)
    if not m:
        return None, None
    first_num = float(m.group(1).replace(",", "."))
    has_multiplier = m.group(2) is not None and m.group(3) is not None
    unit = m.group(4).lower()
    unit = _UNIT_MAP.get(unit, unit)

    if has_multiplier:
        pack_count = first_num
        per_unit = float(m.group(3).replace(",", "."))
    else:
        pack_count = 1
        per_unit = first_num

    total = pack_count * per_unit
    if unit == "cl":
        total *= 10
        unit = "ml"
    if unit == "liter":
        total *= 1000
        unit = "ml"
    if unit == "kg":
        # Always convert to grams — Jumbo pack sizes are often fractional kg
        # (e.g. "1,5 kg"), which would truncate to 1 if kept as an int kg count.
        total *= 1000
        unit = "gram"
    return int(round(total)), unit


def _parse_price(card) -> Optional[float]:
    whole = card.locator(".current-price .whole")
    frac = card.locator(".current-price .fractional")
    if not whole.count():
        return None
    whole_txt = re.sub(r"\D", "", whole.first.inner_text())
    frac_txt = re.sub(r"\D", "", frac.first.inner_text()) if frac.count() else "00"
    if not whole_txt:
        return None
    return float(f"{whole_txt}.{frac_txt or '00'}")


def fetch_jumbo_deals() -> List[DealItem]:
    """
    Fetch Jumbo's current offers (first page of the "alle aanbiedingen"
    listing — see module docstring for why pagination isn't followed) by
    rendering it with a headless browser and reading the product cards
    straight out of the DOM.
    Returns an empty list (never raises) if Playwright/the page is unavailable.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("[Jumbo] Playwright not installed — run `pip install playwright` "
                        "and `playwright install chromium` to enable this connector.")
        return []

    deals: List[DealItem] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(user_agent=_USER_AGENT)
                page.goto(_LISTING_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                cards = page.locator('[data-testid^="product-card-"]').all()
                for card in cards:
                    try:
                        title_loc = card.locator("h3")
                        title = title_loc.first.inner_text().strip() if title_loc.count() else None
                        if not title:
                            continue

                        price = _parse_price(card)
                        volume, unit = _parse_volume(title)

                        tag_loc = card.locator(".product-tags")
                        tag_text = tag_loc.first.inner_text().strip() if tag_loc.count() else ""

                        deals.append(DealItem(
                            winkel="Jumbo",
                            productnaam=title,
                            korting_tekst=tag_text or None,
                            actieprijs=price,
                            inhoud_waarde=volume,
                            inhoud_unit=unit,
                        ))
                    except Exception as e:
                        logger.debug(f"[Jumbo] Card parse error: {e}")
            finally:
                browser.close()
    except Exception as e:
        logger.warning(f"[Jumbo] Playwright render failed: {e}")
        return []

    if not deals:
        logger.warning("[Jumbo] Rendered the catalog but found no deal cards — Jumbo may have changed its layout.")
    else:
        logger.info(f"[Jumbo] {len(deals)} deals read from the rendered offers catalog")
    return deals
