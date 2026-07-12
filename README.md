# Boodschappen Dashboard

A live dashboard of Dutch supermarket deals — search, filter, and sort weekly
grocery offers from Albert Heijn, Lidl, and (as data comes in) 16 other Dutch
retailers, published as a static site on GitHub Pages.

**Live site:** `https://hjongeneelen.github.io/boodschappen-dashboard/` (once
Pages is enabled — see [Deploying](#deploying) below)

This project adapts an earlier Google Sheets–based scraper
([hjongeneelen/boodschappen](https://github.com/hjongeneelen/boodschappen))
into a public website: same scraping engine, but the output is JSON consumed
by a React dashboard instead of a spreadsheet only you could see.

## How it works

```
┌─────────────────┐     JSON      ┌──────────────────┐     static build     ┌───────────────┐
│  backend/        │  ─────────▶  │ frontend/public/  │  ─────────────────▶ │ GitHub Pages   │
│  Python scrapers  │              │ data/*.json        │                     │ (this repo)    │
└─────────────────┘               └──────────────────┘                     └───────────────┘
        │
        ├─ api mode  → Albert Heijn, Lidl: direct JSON APIs, no LLM
        └─ pdf/jpg   → 16 other retailers: PDF/JPEG folder → vision LLM (Ollama) → structured JSON
```

- **`backend/`** — Python pipeline that scrapes 18 Dutch retailers' weekly
  deals and writes one JSON file per store into `frontend/public/data/stores/`,
  plus a manifest at `frontend/public/data/index.json`. See
  [backend/README.md](backend/README.md).
- **`frontend/`** — React + TypeScript + Vite site that fetches that JSON and
  renders a searchable, filterable, sortable deal grid. See
  [frontend/README.md](frontend/README.md).
- **`.github/workflows/update-and-deploy.yml`** — runs daily: re-scrapes
  Albert Heijn + Lidl (the two stores with a structured, no-LLM API), commits
  any changes, builds the frontend, and deploys it to GitHub Pages.

## Data coverage

Not all 18 stores can be automated the same way:

| Store | Mode | Status |
|---|---|---|
| Albert Heijn | `api` | ✅ Automated daily via GitHub Actions (anonymous-token search API, ~1500 live bonus items) |
| Lidl | `api` | ⚠️ Currently returns 0 — Lidl's public leaflet endpoints are dead; see [backend/README.md](backend/README.md#connector-status) |
| Hoogvliet, Boni, Poiesz, DA Drogist, Jumbo, Coop, Kruidvat, Etos, Nettorama, Plus, Dekamarkt, Blokker, Gamma, Praxis, Aldi | `pdf` | 🔧 Needs a local run with a vision LLM (Ollama) — not yet run |
| Dirk | `jpg` | 🔧 Needs a local run with a vision LLM (Ollama) — not yet run |

The site handles unscraped stores gracefully (shown muted in the filter bar
with a "not yet scraped" tooltip) rather than erroring. Running the other 16
stores locally and committing the resulting JSON is the easiest way to grow
coverage — see below.

## Local development

**Backend** (scrape and export JSON):
```bash
cd backend
pip install -r requirements.txt
cp .env.template .env   # configure LLM endpoint / store URL overrides
python main.py --stores albert-heijn lidl   # no LLM needed
python main.py                                # all 18 stores — needs Ollama running locally for the pdf/jpg stores
```

**Frontend** (view the dashboard):
```bash
cd frontend
npm install
npm run dev
```

Full details, including Poppler/Ollama setup for the PDF/JPG stores, are in
[backend/README.md](backend/README.md).

## Deploying

This repo is built to deploy itself:

1. Push this repo to GitHub (public, so GitHub Pages is free) under the name
   `boodschappen-dashboard` — the frontend's Vite `base` and this README's
   live-site URL both assume that repo name. If you rename the repo, update
   `frontend/vite.config.ts`'s `base` to match.
2. In the repo's **Settings → Pages**, set **Source** to "GitHub Actions".
3. Run the **Update deals & deploy** workflow once manually (Actions tab →
   select it → *Run workflow*), or just push to `main` — it also runs daily
   at 06:00 UTC via cron.

No secrets are required: the automated part of the pipeline (Albert Heijn +
Lidl) only calls public, unauthenticated-by-key JSON endpoints.

## License

[MIT](LICENSE)
