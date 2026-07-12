"""
Aldi NL scraper — Tier C (JS-rendered viewer, no PDF).

Aldi uses a proprietary JavaScript viewer. Simple HTML scraping rarely finds
anything useful. The most reliable workaround:

  1. Open https://www.aldi.nl/aanbiedingen.html in Chrome
  2. DevTools → Network → filter "pdf" or "folder"
  3. Copy the URL and paste it into ALDI_PDF_URL in .env

When a PDF URL is configured, it is used directly — this scraper is only
called as a fallback when that env var is blank.
"""
import logging
import re
from typing import Optional

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AldiScraper(BaseScraper):
    store_name = "Aldi"
    _FOLDER_PAGE = "https://www.aldi.nl/aanbiedingen.html"
    _PDF_RE = re.compile(r'https?://[^\s"\'<>]+\.pdf', re.IGNORECASE)

    def discover_pdf_url(self) -> Optional[str]:
        resp = self._get(self._FOLDER_PAGE)
        if resp:
            for url in self._PDF_RE.findall(resp.text):
                if any(k in url.lower() for k in ("folder", "aanbieding", "actie", "week")):
                    logger.info(f"[Aldi] Found PDF link in HTML: {url}")
                    return url

        logger.warning(
            "[Aldi] Auto-discovery failed (JS-rendered viewer). "
            "Set ALDI_PDF_URL in .env — see scraper docstring for instructions."
        )
        return None
