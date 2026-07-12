interface EmptyStateProps {
  onReset?: () => void;
}

export function EmptyState({ onReset }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-16 text-center dark:border-slate-700 dark:bg-slate-800/40">
      <span className="text-4xl" aria-hidden="true">
        🛒
      </span>
      <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
        Geen aanbiedingen gevonden
      </h3>
      <p className="max-w-sm text-sm text-slate-500 dark:text-slate-400">
        Probeer een andere zoekterm of pas de winkelselectie aan. Sommige winkels zijn nog niet
        lokaal gescand en hebben daarom nog geen aanbiedingen.
      </p>
      {onReset && (
        <button
          type="button"
          onClick={onReset}
          className="mt-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700"
        >
          Filters wissen
        </button>
      )}
    </div>
  );
}
