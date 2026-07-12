interface CategoryEntry {
  name: string;
  count: number;
}

interface CategoryFilterBarProps {
  categories: CategoryEntry[];
  selected: Set<string>;
  onToggle: (category: string) => void;
  onSelectAll: () => void;
  /** Deals with no categorie assigned yet (categorizer pass not run for their store). */
  uncategorizedCount: number;
}

export function CategoryFilterBar({
  categories,
  selected,
  onToggle,
  onSelectAll,
  uncategorizedCount,
}: CategoryFilterBarProps) {
  const allSelected = selected.size === 0;

  if (categories.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filter op categorie">
      <Chip label="Alle categorieën" count={null} active={allSelected} onClick={onSelectAll} />
      {categories.map((cat) => (
        <Chip
          key={cat.name}
          label={cat.name}
          count={cat.count}
          active={!allSelected && selected.has(cat.name)}
          onClick={() => onToggle(cat.name)}
        />
      ))}
      {uncategorizedCount > 0 && (
        <span
          className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-slate-200 px-3.5 py-1.5 text-sm text-slate-400 dark:border-slate-700 dark:text-slate-500"
          title="Deze winkels zijn nog niet door de categorie-classifier gehaald"
        >
          {uncategorizedCount} zonder categorie
        </span>
      )}
    </div>
  );
}

interface ChipProps {
  label: string;
  count: number | null;
  active: boolean;
  onClick: () => void;
}

function Chip({ label, count, active, onClick }: ChipProps) {
  const base =
    "inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500";

  const stateClasses = active
    ? "border-emerald-600 bg-emerald-600 text-white shadow-sm shadow-emerald-600/30 dark:border-emerald-500 dark:bg-emerald-500"
    : "border-slate-200 bg-white text-slate-700 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-emerald-500/60 dark:hover:bg-slate-700/60";

  return (
    <button type="button" onClick={onClick} className={`${base} ${stateClasses}`}>
      <span>{label}</span>
      {count !== null && (
        <span
          className={`rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums ${
            active ? "bg-white/25 text-white" : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
          }`}
        >
          {count}
        </span>
      )}
    </button>
  );
}
