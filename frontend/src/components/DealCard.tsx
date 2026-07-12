import type { EnrichedDeal } from "../types";
import { formatPrice, formatQuantity } from "../utils/format";

interface DealCardProps {
  deal: EnrichedDeal;
}

export function DealCard({ deal }: DealCardProps) {
  const price = formatPrice(deal.actieprijs);
  const quantity = formatQuantity(deal.inhoud_waarde, deal.inhoud_unit);

  return (
    <article className="group flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-150 hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-lg hover:shadow-slate-900/5 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-indigo-500/40 dark:hover:shadow-black/20">
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between gap-3">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-700 dark:text-slate-300">
            <span
              className="h-1.5 w-1.5 rounded-full bg-emerald-500"
              aria-hidden="true"
            />
            {deal.storeName}
          </span>
          {quantity && (
            <span className="shrink-0 text-xs font-medium text-slate-400 dark:text-slate-500">
              {quantity}
            </span>
          )}
        </div>

        {deal.categorie && (
          <span className="w-fit rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400">
            {deal.categorie}
          </span>
        )}

        <h3 className="line-clamp-2 text-base leading-snug font-semibold text-slate-900 dark:text-slate-50">
          {deal.productnaam}
        </h3>

        {deal.korting_tekst && (
          <p className="w-fit rounded-lg bg-emerald-50 px-2.5 py-1 text-sm font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
            {deal.korting_tekst}
          </p>
        )}
      </div>

      <div className="mt-4 flex items-end justify-between gap-2">
        {price ? (
          <span className="text-2xl font-bold tracking-tight text-indigo-600 dark:text-indigo-400">
            {price}
          </span>
        ) : (
          <span className="text-sm text-slate-400 italic dark:text-slate-500">Prijs onbekend</span>
        )}
        {deal.geldig_tekst && (
          <span className="shrink-0 text-right text-xs text-slate-400 dark:text-slate-500">
            {deal.geldig_tekst}
          </span>
        )}
      </div>
    </article>
  );
}
