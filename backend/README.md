# Backend — Dutch Supermarket Deal Scraper

Pulls weekly folder deals from 18 Dutch retailers and exports structured JSON
into `frontend/public/data/` for the static dashboard site to consume. This is
a fork of an earlier Google Sheets–based scraper, with the Sheets upload step
replaced by a plain JSON exporter (`modules/exporter.py`).

Two processing modes per store:
- `api` — structured JSON API, or a headless-browser (Playwright) DOM read of
  the store's own deals page — no vision LLM needed either way (Albert Heijn,
  Lidl, Dirk, Jumbo, Plus, Aldi)
- `pdf` — download PDF → pdf2image → vision LLM → parse (12 stores)

## Install

```bash
pip install -r requirements.txt
python -m playwright install chromium   # needed for the Jumbo/Plus/Aldi connectors
```

**Windows + PDF stores:** `pdf2image` requires Poppler on `PATH`. Download from
https://github.com/oschwartz10612/poppler-windows/releases, extract, and add
the `Library/bin` folder to your system `PATH`.

**Vision LLM stores:** install [Ollama](https://ollama.com) and pull a vision
model, e.g. `ollama pull llava:13b` (any vision-capable model works — set
`LLM_MODEL` in `.env` to whatever you have pulled, e.g. `qwen3.5:9b`). The
connector talks to Ollama's OpenAI-compatible API at `http://localhost:11434/v1`
by default.

## Configure

```bash
cp .env.template .env
```

Edit `.env` to point at your LLM endpoint/model and, optionally, override
per-store PDF URLs (auto-discovery works for most stores; a few need a
manually pasted URL — see comments in `.env.template`).

## Usage

```bash
python main.py                                       # all stores, full JSON export
python main.py --stores jumbo hoogvliet              # only these stores
python main.py --categorize                          # also tag each deal with a category via the local LLM
python main.py --no-export                           # extract only, skip JSON export
python main.py --clear-cache                          # force re-download PDFs
python main.py --list-stores                          # show all configured stores
```

`--categorize` runs `modules/categorizer.py`: batches of 20 product names are
sent to your local LLM (`LLM_MODEL` in `.env`) asking it to pick one of a
fixed Dutch category list (Groente & Fruit, Vlees & Vis, Zuivel & Eieren,
Dranken, ...) per product; the result is written to each deal's `categorie`
field. Tested at ~2000 deals in ~5 minutes with `qwen3.5:9b`. If you're on
Ollama with a hybrid-reasoning model (Qwen3-family models default to
"thinking" mode), this module talks to Ollama's native `/api/chat` with
`think: false` — without that, the model burns its entire token budget on
internal reasoning before ever producing the JSON answer (confirmed: a
3-item batch used all 2048 tokens thinking and returned nothing). It falls
back to a plain OpenAI-compatible call for non-Ollama backends, without that
optimization.

Each store's deals are exported immediately after processing to
`../frontend/public/data/stores/<slug>.json` (e.g. `albert-heijn.json`), and
`../frontend/public/data/index.json` is updated with a manifest entry for that
store. This means an interrupted run still persists whichever stores finished,
and other stores' data is never wiped by a partial `--stores` run.

## Automation notes

- **Albert Heijn, Lidl, Dirk, Jumbo, Plus, and Aldi** (`api` mode) need no
  local vision LLM — fully automatable in CI/a scheduled job (see
  `.github/workflows/update-and-deploy.yml` at the repo root, which runs this
  on a daily cron). Jumbo/Plus/Aldi specifically need Playwright's Chromium
  (`python -m playwright install chromium`) since they work by rendering the
  store's own page with a real headless browser rather than calling an API.
- **The other 12 stores** (`pdf` mode) need a local vision LLM via Ollama, so
  they must be run locally (or on a machine with Ollama installed) and their
  output JSON committed into `frontend/public/data/` for the static site to
  pick up. Auto-discovery of the weekly PDF URL currently fails for all 12 of
  them (see below) — you'll need to paste a URL manually in `.env` for now.

## Connector status

- **Albert Heijn**: works. AH's product-search API requires a short-lived
  anonymous bearer token (fetched automatically); the connector pages through
  search results and keeps items carrying bonus fields. No API key needed.
- **Dirk**: works. Dirk's `aanbiedingen` page is server-rendered (Nuxt) with
  the full current-offers dataset embedded in the page's `__NUXT_DATA__`
  payload — `modules/dirk_connector.py` decodes that devalue-style payload
  directly with a plain GET, no auth needed. (Dirk's GraphQL API also exists
  at `web-gateway.dirk.nl` but returns empty results without a browser
  session — the embedded payload sidesteps that.)
- **Jumbo, Plus, Aldi**: work, via a different technique than the others.
  Their APIs/backends are bot-protected (Akamai/Imperva — see below), but
  their consumer-facing deals pages render completely normally for a real
  browser; the blocking is on the API traffic pattern, not on loading the
  page. `modules/jumbo_connector.py`, `plus_connector.py`, and
  `aldi_connector.py` each launch headless Chromium via Playwright, load the
  store's own page, dismiss the cookie banner where present, and read the
  deal cards straight out of the rendered DOM (`page.locator(...)` +
  `.inner_text()`) — no OCR/vision model involved, since it's real HTML once
  rendered.
  - Aldi (195 items) and Plus (36 items) return everything their own
    `/aanbiedingen` page shows — confirmed with `window.scrollTo` down to a
    stable page height (5 consecutive unchanged heights) that no more cards
    load; neither page is lazy beyond what's rendered on load.
  - Jumbo's `/aanbiedingen/nu` page IS lazy-loaded, but deceptively so: a
    shallow scroll (a handful of `mouse.wheel` ticks, or ~5 scroll-to-bottom
    rounds) looks fully loaded at ~24 cards and then jumps to 100+ once you
    keep scrolling past that point. `jumbo_connector.py` scrolls until the
    page height is stable across 5 consecutive rounds (up to 60 rounds)
    before reading cards — this reads ~103 items instead of 24.
  - We separately tried Jumbo's `/producten/alle-aanbiedingen/` catalog (a
    different, larger ~1300-item listing with richer per-item data — pack
    sizes embedded in the title). Its first page alone matches what the
    `/nu` page's full scroll now gives us, and its pagination is a genuine
    dead end for a headless browser: neither navigating `?page=N` directly
    nor clicking the page-N button (even with a realistic mouse move + down/
    up, not just a synthetic click) changes the rendered results or fires a
    request — the app silently no-ops it. That smells like it's specifically
    gating scripted interaction, so we didn't push further into working
    around it, and stuck with the `/nu` page's full-scroll result instead.
- **Lidl**: currently returns 0 deals — every candidate endpoint in
  `modules/lidl_connector.py` is dead (DNS failures / 404s) as of 2026-07.
  Lidl no longer appears to expose a public leaflet API, and (unlike Jumbo/
  Plus/Aldi) it has no single obvious own-site deals page to render instead;
  fixing this needs a fresh capture of real traffic from the Lidl Plus app.
  Until then, treat Lidl like the vision-LLM stores.
- **Coop, Kruidvat, Etos investigated, no automated path found**: Coop NL's
  own site has been decommissioned (redirects to plus.nl — Coop NL was
  acquired by Plus Retail), so there's no page left to render. Kruidvat and
  Etos are blocked by Akamai Bot Manager even for a real headless browser
  (unlike Jumbo/Plus/Aldi, which only blocked the raw API) — getting past
  that would mean specifically working around bot detection rather than just
  rendering a public page normally, which we're deliberately not pursuing.
  All three remain on the PDF + vision-LLM path.
