"""
Jumbo JSON... actually DOM connector — structured data, no vision LLM needed.

Jumbo's mobile/GraphQL APIs are behind Akamai Bot Manager (confirmed: plain
`requests` calls get a bot-mitigation challenge page even against the site's
own GraphQL endpoint). But the public *website* itself renders fine for a
real browser — Akamai's block triggers on the API traffic pattern, not on
loading the page. So instead of calling an API, we drive a real (headless)
Chromium via Playwright to https://www.jumbo.com/aanbiedingen/nu and read the
already-rendered deal cards straight out of the DOM — no OCR/vision needed,
since the text is plain HTML, just not reachable via a bare HTTP request.

Note: this "Nu in de aanbieding" page is a curated highlights page, not
Jumbo's full weekly folder — expect a few dozen items, not everything on
sale.
"""
import logging
import re
from typing import List, Optional

from modules.models import DealItem

logger = logging.getLogger(__name__)

_URL = "https://www.jumbo.com/aanbiedingen/nu"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _parse_price(tag_text: str) -> Optional[float]:
    """Pull a euro price out of tags like 'voor 2,49' or '2 voor 4,00'."""
    numbers = re.findall(r"(\d+,\d{2})", tag_text)
    if not numbers:
        return None
    return float(numbers[-1].replace(",", "."))


def fetch_jumbo_deals() -> List[DealItem]:
    """
    Fetch Jumbo's current highlighted offers by rendering the page with a
    headless browser and reading the deal cards' DOM text directly.
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
                page.goto(_URL, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(5000)

                # Trigger any lazy-loaded cards further down the page.
                prev_count = -1
                for _ in range(15):
                    page.mouse.wheel(0, 4000)
                    page.wait_for_timeout(400)
                    count = page.locator('[data-testid="promotion-card"]').count()
                    if count == prev_count:
                        break
                    prev_count = count

                cards = page.locator('[data-testid="promotion-card"]').all()
                for card in cards:
                    try:
                        title = card.locator("h3").first.inner_text().strip()
                        if not title:
                            continue
                        tag_text = ""
                        tag_loc = card.locator(".tag")
                        if tag_loc.count():
                            tag_text = tag_loc.first.inner_text().strip()

                        deals.append(DealItem(
                            winkel="Jumbo",
                            productnaam=title,
                            korting_tekst=tag_text or None,
                            actieprijs=_parse_price(tag_text),
                            inhoud_waarde=None,
                            inhoud_unit=None,
                        ))
                    except Exception as e:
                        logger.debug(f"[Jumbo] Card parse error: {e}")
            finally:
                browser.close()
    except Exception as e:
        logger.warning(f"[Jumbo] Playwright render failed: {e}")
        return []

    if not deals:
        logger.warning("[Jumbo] Rendered the page but found no deal cards — Jumbo may have changed its layout.")
    else:
        logger.info(f"[Jumbo] {len(deals)} deals read from the rendered page")
    return deals
