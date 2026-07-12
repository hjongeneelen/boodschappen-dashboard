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
        ├─ api mode  → Albert Heijn, Lidl, Dirk: direct JSON / embedded page payload
        ├─ api mode  → Jumbo, Plus, Aldi: headless-browser (Playwright) DOM read of
        │              the store's own deals page — their APIs are bot-protected,
        │              the rendered page isn't
        └─ pdf mode  → 12 other retailers: PDF folder → vision LLM (Ollama) → structured JSON
```

- **`backend/`** — Python pipeline that scrapes 18 Dutch retailers' weekly
  deals and writes one JSON file per store into `frontend/public/data/stores/`,
  plus a manifest at `frontend/public/data/index.json`. See
  [backend/README.md](backend/README.md).
- **`frontend/`** — React + TypeScript + Vite site that fetches that JSON and
  renders a searchable, filterable, sortable deal grid. See
  [frontend/README.md](frontend/README.md).
- **`.github/workflows/update-and-deploy.yml`** — runs daily: re-scrapes the
  6 structured stores (Albert Heijn, Lidl, Dirk, Jumbo, Plus, Aldi), commits
  any changes, builds the frontend, and deploys it to GitHub Pages. Budget
  ~10 minutes for the scrape step — Jumbo's group-deal expansion alone
  (dozens of extra page visits) takes ~7 of those.

## Data coverage

Not all 18 stores can be automated the same way:

| Store | Mode | Status |
|---|---|---|
| Albert Heijn | `api` | ✅ Automated daily via GitHub Actions (anonymous-token search API, ~1500 live bonus items) |
| Jumbo | `api` | ✅ Automated daily via GitHub Actions (headless-browser DOM read of jumbo.com/aanbiedingen/nu, scrolled until fully lazy-loaded, "Alle X" group deals expanded into their individual products; ~700 live items) |
| Lidl | `api` | ✅ Automated daily via GitHub Actions (headless-browser DOM read across Lidl's 3 weekly-wave tabs, categorized from Lidl's own taxonomy; ~200 live items) |
| Aldi | `api` | ✅ Automated daily via GitHub Actions (headless-browser DOM read of aldi.nl — its legacy API is dead, the page isn't; ~195 live items) |
| Dirk | `api` | ✅ Automated daily via GitHub Actions (offers embedded in the page's server-rendered payload, no auth needed; ~124 live items) |
| Plus | `api` | ✅ Automated daily via GitHub Actions (headless-browser DOM read of plus.nl/aanbiedingen, both the current- and next-week tabs; ~40 live items — Plus's inventory changes between runs, this varies) |
| Hoogvliet, Boni, Poiesz, DA Drogist, Coop, Kruidvat, Etos, Nettorama, Dekamarkt, Blokker, Gamma, Praxis | `pdf` | 🔧 Needs a local run with a vision LLM (Ollama) — not yet run. Auto-discovery of the weekly PDF URL currently fails for all of these (Publitas changed its site since this was written) |

The site handles unscraped stores gracefully (shown muted in the filter bar
with a "not yet scraped" tooltip) rather than erroring. Running the other 12
stores locally and committing the resulting JSON is the easiest way to grow
coverage — see below.

## Beyond the basics: validity dates and categories

Two extra fields, both optional and both filled in only where the underlying
source actually supports them:

- **`geldig_tekst`** — a free-text validity period ("8 - 14 jul", "vanaf 12
  jul"), shown on each deal card. Albert Heijn and Dirk give clean ISO dates
  we format ourselves (`modules/date_utils.py`); Jumbo/Plus read whatever
  human-readable validity text/banner the store's own page already shows.
  Not every store exposes this — cards without it just omit the line.
- **`categorie`** — a Dutch grocery category (Groente & Fruit, Zuivel &
  Eieren, Dranken, ...) assigned by an optional local-LLM pass
  (`python main.py --categorize`, see [backend/README.md](backend/README.md)),
  filterable in the site's "Categorieën" chip row. This is opt-in and local
  only — it needs your own Ollama instance, so it isn't part of the daily
  GitHub Actions run. Run it yourself and commit the result to add
  categories to the live site.

We looked into whether the blocked-API stores have a structured API the way
Albert Heijn does — for Jumbo, Plus, Aldi, and Lidl, the API itself is
bot-protected (Akamai/Imperva) or simply dead, but their own *website*
renders just fine for a real (headless) browser, so `modules/jumbo_connector.py`,
`plus_connector.py`, `aldi_connector.py`, and `lidl_connector.py` use
Playwright to render the page and read the deal cards straight out of the
DOM — no vision/OCR needed, since it's real HTML once rendered. Jumbo and
Lidl both also have "buy one of several variants" group deals (e.g. "Alle
burgers") that we expand into individual products via each group's detail
page. Kruidvat and Etos are blocked even for a real headless browser
(Akamai edge-level); Coop NL's site has been decommissioned entirely
(redirects to plus.nl). Full findings are in
[backend/README.md](backend/README.md#connector-status).

## Local development

**Backend** (scrape and export JSON):
```bash
cd backend
pip install -r requirements.txt
cp .env.template .env   # configure LLM endpoint / store URL overrides
python main.py --stores albert-heijn lidl dirk jumbo plus aldi   # no LLM needed
python main.py --categorize                                       # also tag every deal with a category (needs Ollama)
python main.py                                                     # all 18 stores — needs Ollama running locally for the pdf stores
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
