import type { StoreIndexEntry } from "../types";

interface StoreFilterBarProps {
  stores: StoreIndexEntry[];
  selected: Set<string>;
  onToggle: (slug: string) => void;
  onSelectAll: () => void;
}

export function StoreFilterBar({ stores, selected, onToggle, onSelectAll }: StoreFilterBarProps) {
  const allSelected = selected.size === 0;

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filter op winkel">
      <Chip label="Alle winkels" count={null} active={allSelected} onClick={onSelectAll} />
      {stores.map((store) => {
        const hasData = store.deal_count > 0 && store.updated_at !== null;
        const active = !allSelected && selected.has(store.slug);
        return (
          <Chip
            key={store.slug}
            label={store.name}
            count={store.deal_count}
            active={active}
            muted={!hasData}
            title={hasData ? undefined : "Nog niet gescand"}
            onClick={() => onToggle(store.slug)}
          />
        );
      })}
    </div>
  );
}

interface ChipProps {
  label: string;
  count: number | null;
  active: boolean;
  muted?: boolean;
  title?: string;
  onClick: () => void;
}

function Chip({ label, count, active, muted, title, onClick }: ChipProps) {
  const base =
    "inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500";

  const stateClasses = active
    ? "border-indigo-600 bg-indigo-600 text-white shadow-sm shadow-indigo-600/30 dark:border-indigo-500 dark:bg-indigo-500"
    : muted
      ? "border-slate-200 bg-slate-50 text-slate-400 hover:border-slate-300 hover:text-slate-500 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-500 dark:hover:text-slate-400"
      : "border-slate-200 bg-white text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-indigo-500/60 dark:hover:bg-slate-700/60";

  return (
    <button type="button" onClick={onClick} title={title} className={`${base} ${stateClasses}`}>
      <span>{label}</span>
      {count !== null && (
        <span
          className={`rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums ${
            active
              ? "bg-white/25 text-white"
              : muted
                ? "bg-slate-200/70 text-slate-400 dark:bg-slate-700 dark:text-slate-500"
                : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
          }`}
        >
          {count}
        </span>
      )}
    </button>
  );
}
