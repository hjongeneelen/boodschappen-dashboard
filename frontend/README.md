# Frontend — Boodschappen Dashboard

A static React + TypeScript + Vite site that renders Dutch supermarket deals.
It reads plain JSON from `public/data/` — no server, no API calls beyond
fetching those static files — which is what makes it deployable as-is on
GitHub Pages.

See the repo-root [README](../README.md) for the full project picture
(backend + frontend + deployment). This file only covers frontend-local dev.

## Develop

```bash
npm install
npm run dev
```

## Build

```bash
npm run build   # outputs to dist/, base path set to /boodschappen-dashboard/
npm run preview # serve the production build locally
```

## Data contract

The app fetches `${import.meta.env.BASE_URL}data/index.json` and then each
referenced `data/stores/<slug>.json`. Both files are written by the Python
backend (`../backend/`) — see `src/types.ts` for the exact shape, and
`src/hooks/useDeals.ts` for how they're fetched and merged. Stores with
`deal_count: 0` / `updated_at: null` in the index simply haven't been scraped
yet and render as muted/"not yet scraped" in the store filter — this is
expected, not an error state.

## Stack

React 19, TypeScript, Vite, Tailwind CSS v4. No router (single page), no
backend calls at runtime beyond the static JSON fetches above.
