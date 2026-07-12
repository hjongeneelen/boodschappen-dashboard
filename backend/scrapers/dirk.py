"""
Dirk scraper — uses direct JPG images, bypasses the PDF pipeline entirely.

Dirk van den Broek does NOT publish a PDF. Their folder viewer at
folder.dirk.nl serves each page as an individual JPEG from:
    https://web-fileserver.dirk.nl/...

Strategy:
  1. GET folder.dirk.nl and extract web-fileserver.dirk.nl image URLs.
  2. If no URLs found in static HTML (JS-rendered), try constructing URLs
     from the expected week-based path pattern.
  3. Return the full ordered list of page image URLs.

Because Dirk's viewer may be partially JavaScript-rendered, this may not
always find all pages. Set DIRK_FALLBACK_NOTE in .env for manual override.
If Playwright is available, a headless scrape gives 100% reliability.
"""
import logging
import re
from typing import List, Optional

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_FOLDER_PAGE = "https://folder.dirk.nl"
_FILESERVER = "https://web-fileserver.dirk.nl"

# Pattern for page image filenames (e.g. page_001.jpg, blad-01.jpg)
_PAGE_PATTERN = re.compile(
    r"https?://web-fileserver\.dirk\.nl/[^\s\"'<>]+\.(?:jpg|jpeg|png)",
    re.IGNORECASE,
)


class DirkScraper(BaseScraper):
    store_name = "Dirk"

    def discover_pdf_url(self) -> Optional[str]:
        # Dirk has no PDF — always use discover_jpg_urls()
        return None

    def discover_jpg_urls(self) -> Optional[List[str]]:
        resp = self._get(_FOLDER_PAGE)
        if not resp:
            logger.warning("[Dirk] Could not reach folder.dirk.nl")
            return None

        # Deduplicate while preserving order
        urls = list(dict.fromkeys(_PAGE_PATTERN.findall(resp.text)))

        if urls:
            logger.info(f"[Dirk] Found {len(urls)} page images in static HTML")
            return urls[:30]

        # Fallback: try to infer the base path and enumerate pages 1–N
        base = self._infer_base_path(resp.text)
        if base:
            urls = self._probe_pages(base)
            if urls:
                logger.info(f"[Dirk] Enumerated {len(urls)} pages from base: {base}")
                return urls

        logger.warning(
            "[Dirk] Could not find page images — the viewer appears to be "
            "JavaScript-rendered. Options:\n"
            "  1. Use Playwright to fully render folder.dirk.nl and extract image URLs.\n"
            "  2. Manually inspect the page's network requests for "
            "     web-fileserver.dirk.nl URLs and add them to the DIRK_PAGE_URLS "
            "     setting in .env (comma-separated)."
        )
        return None

    def _infer_base_path(self, html: str) -> Optional[str]:
        """Look for a partial web-fileserver URL that reveals the base path."""
        m = re.search(
            r'["\'](' + re.escape(_FILESERVER) + r'/[^"\'<>\s]+?)(?:page|blad|pagina|p)?0*1',
            html, re.IGNORECASE,
        )
        return m.group(1) if m else None

    def _probe_pages(self, base: str, max_pages: int = 24) -> List[str]:
        """Probe sequentially until a 404 is returned."""
        import requests as req
        urls = []
        for i in range(1, max_pages + 1):
            url = f"{base}{i:03d}.jpg"
            try:
                r = req.head(url, timeout=8)
                if r.status_code == 200:
                    urls.append(url)
                else:
                    break
            except Exception:
                break
        return urls
