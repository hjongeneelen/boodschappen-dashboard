# Backend — Dutch Supermarket Deal Scraper

Pulls weekly folder deals from 18 Dutch retailers and exports structured JSON
into `frontend/public/data/` for the static dashboard site to consume. This is
a fork of an earlier Google Sheets–based scraper, with the Sheets upload step
replaced by a plain JSON exporter (`modules/exporter.py`).

Two processing modes per store:
- `api` — direct structured JSON API, no LLM (Albert Heijn, Lidl, Dirk)
- `pdf` — download PDF → pdf2image → vision LLM → parse (15 stores)

## Install

```bash
pip install -r requirements.txt
```

**Windows + PDF stores:** `pdf2image` requires Poppler on `PATH`. Download from
https://github.com/oschwartz10612/poppler-windows/releases, extract, and add
the `Library/bin` folder to your system `PATH`.

**Vision LLM stores:** install [Ollama](https://ollama.com) and pull a vision
model, e.g. `ollama pull llava:13b`. The connector talks to Ollama's
OpenAI-compatible API at `http://localhost:11434/v1` by default.

## Configure

```bash
cp .env.template .env
```

Edit `.env` to point at your LLM endpoint/model and, optionally, override
per-store PDF URLs (auto-discovery works for most stores; a few need a
manually pasted URL — see comments in `.env.template`).

## Usage

```bash
python main.py                                  # all stores, full JSON export
python main.py --stores jumbo hoogvliet         # only these stores
python main.py --no-export                      # extract only, skip JSON export
python main.py --clear-cache                     # force re-download PDFs
python main.py --list-stores                     # show all configured stores
```

Each store's deals are exported immediately after processing to
`../frontend/public/data/stores/<slug>.json` (e.g. `albert-heijn.json`), and
`../frontend/public/data/index.json` is updated with a manifest entry for that
store. This means an interrupted run still persists whichever stores finished,
and other stores' data is never wiped by a partial `--stores` run.

## Automation notes

- **Albert Heijn, Lidl, and Dirk** (`api` mode) need no LLM and no local
  machine — fully automatable in CI/a scheduled job (see
  `.github/workflows/update-and-deploy.yml` at the repo root, which runs this
  on a daily cron).
- **The other 15 stores** (`pdf` mode) need a local vision LLM via Ollama, so
  they must be run locally (or on a machine with Ollama installed) and their
  output JSON committed into `frontend/public/data/` for the static site to
  pick up.

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
- **Lidl**: currently returns 0 deals — every candidate endpoint in
  `modules/lidl_connector.py` is dead (DNS failures / 404s) as of 2026-07.
  Lidl no longer appears to expose a public leaflet API; fixing this needs a
  fresh capture of real traffic from the Lidl Plus app. Until then, treat Lidl
  like the vision-LLM stores.
- **Other stores investigated (Jumbo, Plus, Coop, Kruidvat, Etos, Aldi)**: no
  usable public API found. Jumbo/Kruidvat are behind Akamai Bot Manager
  (requires real browser JS-challenge solving, not a plain `requests` call).
  Plus is behind an Imperva WAF and its OutSystems frontend only reveals the
  offers-screen API call after client-side JS execution. Coop NL's own site
  has been decommissioned (redirects to plus.nl — Coop NL was acquired by
  Plus Retail). Etos sits behind Akamai too, and is not registered as an
  application on AH's shared `api.ah.nl` backend despite being an Ahold
  Delhaize brand. Aldi's legacy REST API (`webservice.aldi.nl`) responds but
  returns empty payloads. All of these remain on the PDF + vision-LLM path.
