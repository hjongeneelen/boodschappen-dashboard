export type SortOption = "price-asc" | "price-desc" | "store-asc";

interface SearchAndSortProps {
  query: string;
  onQueryChange: (value: string) => void;
  sort: SortOption;
  onSortChange: (value: SortOption) => void;
  resultCount: number;
}

export function SearchAndSort({
  query,
  onQueryChange,
  sort,
  onSortChange,
  resultCount,
}: SearchAndSortProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="relative w-full sm:max-w-sm">
        <svg
          className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-4.35-4.35M17 10.5A6.5 6.5 0 114 10.5a6.5 6.5 0 0113 0z"
          />
        </svg>
        <input
          type="search"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Zoek op productnaam..."
          className="w-full rounded-lg border border-slate-200 bg-white py-2 pr-3 pl-9 text-sm text-slate-800 placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/30 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
          aria-label="Zoek op productnaam"
        />
      </div>

      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-500 tabular-nums dark:text-slate-400">
          {resultCount.toLocaleString("nl-NL")} {resultCount === 1 ? "resultaat" : "resultaten"}
        </span>
        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <span className="hidden sm:inline">Sorteer:</span>
          <select
            value={sort}
            onChange={(e) => onSortChange(e.target.value as SortOption)}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm text-slate-700 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/30 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <option value="price-asc">Prijs (laag - hoog)</option>
            <option value="price-desc">Prijs (hoog - laag)</option>
            <option value="store-asc">Winkelnaam (A-Z)</option>
          </select>
        </label>
      </div>
    </div>
  );
}
