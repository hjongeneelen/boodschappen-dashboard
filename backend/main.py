"""
Dutch Supermarket Deal Scraper
──────────────────────────────
Pulls weekly folder deals from 18 Dutch retailers, extracts structured data,
and exports it as JSON for the static dashboard site (frontend/public/data/)
instead of pushing to a Google Sheet.

Three processing modes per store:
  pdf  → download PDF → pdf2image → Vision LLM → parse → JSON export
  jpg  → scrape direct JPEG pages → Vision LLM → parse → JSON export  (Dirk)
  api  → call JSON API directly → parse → JSON export                  (AH, Lidl)

Usage:
  python main.py                                    # all stores, full export
  python main.py --stores jumbo hoogvliet           # only these stores
  python main.py --no-export                        # extract only, skip JSON export
  python main.py --clear-cache                      # force re-download PDFs
  python main.py --list-stores                      # show all configured stores
"""

import argparse
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Literal, Optional

from openai import OpenAI

from config import settings
from modules.ah_connector import fetch_ah_deals
from modules.converter import pdf_to_images
from modules.downloader import download_images_from_urls, download_pdf
from modules.exporter import export_store
from modules.lidl_connector import fetch_lidl_deals
from modules.llm_connector import extract_deals_from_image, get_llm_client
from modules.models import DealItem
from modules.parser import parse_llm_response
from scrapers.aldi import AldiScraper
from scrapers.base import BaseScraper
from scrapers.dirk import DirkScraper
from scrapers.hoogvliet import HoogvlietScraper
from scrapers.kruidvat import KruidvatScraper
from scrapers.publitas import PublitasScraper

# ── Logging ───────────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252, which can't encode the box-drawing chars below
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── Store registry ────────────────────────────────────────────────────────────

@dataclass
class StoreConfig:
    name: str
    mode: Literal["pdf", "jpg", "api"]
    # For pdf/jpg modes: optional manual URL override, optional scraper
    env_url: Optional[str] = None
    scraper: Optional[BaseScraper] = None
    # For api mode: callable that returns deals directly
    api_fn: Optional[Callable[[], List[DealItem]]] = None
    # Human-readable note shown in --list-stores
    note: str = ""


STORES: List[StoreConfig] = [
    # ── Tier A: Fully automatable ─────────────────────────────────────────────
    StoreConfig(
        name="Hoogvliet",
        mode="pdf",
        env_url=settings.hoogvliet_pdf_url,
        scraper=HoogvlietScraper(),
        note="Week-number URL (folder_YYYY_WW) — fully auto",
    ),
    StoreConfig(
        name="Boni",
        mode="pdf",
        env_url=settings.boni_pdf_url,
        scraper=PublitasScraper("Boni", "boni-supermarkt"),
        note="Publitas redirect — fully auto",
    ),
    StoreConfig(
        name="Poiesz",
        mode="pdf",
        env_url=settings.poiesz_pdf_url,
        scraper=PublitasScraper("Poiesz", "okkinga-communicatie"),
        note="Publitas redirect — fully auto (Friesland/Groningen)",
    ),
    StoreConfig(
        name="DA Drogist",
        mode="pdf",
        env_url=settings.da_drogist_pdf_url,
        scraper=PublitasScraper("DA Drogist", "da-drogisterij"),
        note="Publitas redirect — bi-weekly folder",
    ),
    # ── Tier B: Publitas API ──────────────────────────────────────────────────
    StoreConfig(
        name="Jumbo",
        mode="pdf",
        env_url=settings.jumbo_pdf_url,
        scraper=PublitasScraper("Jumbo", "jumbo-supermarkten"),
        note="Publitas (jumbo-supermarkten)",
    ),
    StoreConfig(
        name="Coop",
        mode="pdf",
        env_url=settings.coop_pdf_url,
        scraper=PublitasScraper("Coop", "coop-supermarkten"),
        note="Publitas (coop-supermarkten) — full + Compact folder",
    ),
    StoreConfig(
        name="Kruidvat",
        mode="pdf",
        env_url=settings.kruidvat_pdf_url,
        scraper=KruidvatScraper(),
        note="Publitas group ID 189",
    ),
    StoreConfig(
        name="Etos",
        mode="pdf",
        env_url=settings.etos_pdf_url,
        scraper=PublitasScraper("Etos", "etos", base_url="https://folder.etos.nl"),
        note="Publitas custom domain — bi-weekly folder",
    ),
    StoreConfig(
        name="Nettorama",
        mode="pdf",
        env_url=settings.nettorama_pdf_url,
        scraper=PublitasScraper("Nettorama", "91409"),
        note="Publitas group ID 91409",
    ),
    StoreConfig(
        name="Plus",
        mode="pdf",
        env_url=settings.plus_pdf_url,
        scraper=PublitasScraper("Plus", "plus-supermarkt"),
        note="Publitas — slug unconfirmed, may need PLUS_PDF_URL override",
    ),
    StoreConfig(
        name="Dekamarkt",
        mode="pdf",
        env_url=settings.dekamarkt_pdf_url,
        scraper=PublitasScraper("Dekamarkt", "dekamarkt", base_url="https://folder.dekamarkt.nl"),
        note="Publitas custom domain — Noord-Holland regional",
    ),
    StoreConfig(
        name="Blokker",
        mode="pdf",
        env_url=settings.blokker_pdf_url,
        scraper=PublitasScraper("Blokker", "blokker"),
        note="Publitas (blokker) — housewares",
    ),
    StoreConfig(
        name="Gamma",
        mode="pdf",
        env_url=settings.gamma_pdf_url,
        scraper=PublitasScraper("Gamma", "gamma-nl", base_url="https://folder.gamma.nl"),
        note="Publitas custom domain — DIY/hardware",
    ),
    StoreConfig(
        name="Praxis",
        mode="pdf",
        env_url=settings.praxis_pdf_url,
        scraper=PublitasScraper("Praxis", "10", base_url="https://folder.praxis.nl"),
        note="Publitas custom domain — DIY/hardware",
    ),
    # ── Tier C: Special cases ─────────────────────────────────────────────────
    StoreConfig(
        name="Dirk",
        mode="jpg",
        scraper=DirkScraper(),
        note="No PDF — scrapes direct JPEGs from web-fileserver.dirk.nl",
    ),
    StoreConfig(
        name="Aldi",
        mode="pdf",
        env_url=settings.aldi_pdf_url,
        scraper=AldiScraper(),
        note="JS-rendered viewer — set ALDI_PDF_URL manually in .env",
    ),
    # ── Structured JSON (no LLM) ──────────────────────────────────────────────
    StoreConfig(
        name="Albert Heijn",
        mode="api",
        api_fn=fetch_ah_deals,
        note="Mobile API — structured data, no vision LLM needed",
    ),
    StoreConfig(
        name="Lidl",
        mode="api",
        api_fn=fetch_lidl_deals,
        note="Schwarz CDN API — structured data, no vision LLM needed",
    ),
]

_STORE_NAMES_LOWER = {s.name.lower().replace(" ", "-"): s.name for s in STORES}


# ── Per-store processing ──────────────────────────────────────────────────────

def _process_via_llm(
    images: List,
    store_name: str,
    client: OpenAI,
) -> List[DealItem]:
    """Run a list of PIL Images through the vision LLM and collect deals."""
    deals: List[DealItem] = []
    for page_num, image in enumerate(images, start=1):
        try:
            raw = extract_deals_from_image(image, store_name, client)
            page_deals = parse_llm_response(raw, store_name, page_num)
            deals.extend(page_deals)
            logger.info(f"[{store_name}] Page {page_num}: {len(page_deals)} deals")
        except Exception as e:
            logger.error(f"[{store_name}] Page {page_num} failed and was skipped: {e}")
    return deals


def _run_store(store: StoreConfig, client: Optional[OpenAI]) -> List[DealItem]:
    """Dispatch to the right processing path based on store.mode."""

    # ── API mode: structured JSON, no LLM ────────────────────────────────────
    if store.mode == "api":
        assert store.api_fn is not None
        return store.api_fn()

    # ── JPG mode: direct image URLs ───────────────────────────────────────────
    if store.mode == "jpg":
        assert store.scraper is not None
        urls = store.scraper.discover_jpg_urls()
        if not urls:
            logger.warning(f"[{store.name}] No image URLs found — skipping.")
            return []
        images = download_images_from_urls(urls, store.name)
        if not images:
            return []
        return _process_via_llm(images, store.name, client)

    # ── PDF mode ──────────────────────────────────────────────────────────────
    pdf_url = store.env_url
    if not pdf_url and store.scraper:
        logger.info(f"[{store.name}] No URL in .env — running auto-discovery...")
        pdf_url = store.scraper.discover_pdf_url()

    if not pdf_url:
        logger.warning(f"[{store.name}] No PDF URL available — skipping.")
        return []

    pdf_path = download_pdf(pdf_url, store.name)
    if not pdf_path:
        logger.warning(f"[{store.name}] PDF download failed — skipping.")
        return []

    images = list(pdf_to_images(pdf_path, store.name))
    if not images:
        return []
    # pdf_to_images yields (page_num, image) tuples
    pil_images = [img for _, img in images]
    return _process_via_llm(pil_images, store.name, client)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dutch supermarket deal scraper → JSON export for static site",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Delete all cached PDFs and re-download from scratch",
    )
    parser.add_argument(
        "--stores",
        nargs="+",
        metavar="STORE",
        help=(
            "Process only these stores (default: all). "
            "Use lowercase with hyphens, e.g.: jumbo hoogvliet albert-heijn"
        ),
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Extract deals but skip JSON export (useful for testing)",
    )
    parser.add_argument(
        "--list-stores",
        action="store_true",
        help="Print all configured stores with their modes and exit",
    )
    args = parser.parse_args()

    if args.list_stores:
        print(f"\n{'Store':<20} {'Mode':<6} Note")
        print("─" * 70)
        for s in STORES:
            url_marker = " [URL set]" if s.env_url else ""
            print(f"  {s.name:<18} {s.mode:<6} {s.note}{url_marker}")
        print()
        return

    if args.clear_cache and settings.cache_dir.exists():
        shutil.rmtree(settings.cache_dir)
        logger.info("PDF cache cleared.")

    # Resolve which stores to run
    if args.stores:
        selected_names = set()
        for arg in args.stores:
            canonical = _STORE_NAMES_LOWER.get(arg.lower())
            if canonical:
                selected_names.add(canonical)
            else:
                logger.warning(f"Unknown store '{arg}' — ignoring. Run --list-stores to see options.")
        active_stores = [s for s in STORES if s.name in selected_names]
    else:
        active_stores = STORES

    # Only initialise the LLM client if we have at least one pdf/jpg store
    needs_llm = any(s.mode in ("pdf", "jpg") for s in active_stores)
    client = get_llm_client() if needs_llm else None

    logger.info("═" * 64)
    logger.info("  Dutch Supermarket Deal Scraper")
    if client:
        logger.info(f"  LLM: {settings.llm_base_url}  model={settings.llm_model}")
    logger.info(f"  Stores: {', '.join(s.name for s in active_stores)}")
    logger.info("═" * 64)

    all_deals: List[DealItem] = []

    for store in active_stores:
        logger.info(f"\n── {store.name} {'─' * max(1, 52 - len(store.name))}")
        try:
            store_deals = _run_store(store, client)
            logger.info(f"[{store.name}] ✓ {len(store_deals)} deals extracted")
            all_deals.extend(store_deals)

            if not args.no_export:
                export_store(store.name, store.mode, store_deals, settings.data_dir)
                logger.info(f"[{store.name}] Exported {len(store_deals)} deals to JSON")
        except Exception as e:
            logger.error(f"[{store.name}] Unexpected error — store skipped: {e}")

    logger.info(f"\n{'═' * 64}")
    logger.info(f"  Grand total: {len(all_deals)} deals across {len(active_stores)} stores")
    logger.info(f"{'═' * 64}")

    if not all_deals:
        logger.warning("No deals found. Check your .env URLs and LLM endpoint.")
        return

    if args.no_export:
        logger.info("Export skipped (--no-export).")
        logger.info("Sample output (first 5 deals):")
        for deal in all_deals[:5]:
            logger.info(f"  {deal.model_dump()}")
        return

    logger.info(f"Pipeline complete — JSON exported to {settings.data_dir}")


if __name__ == "__main__":
    main()
