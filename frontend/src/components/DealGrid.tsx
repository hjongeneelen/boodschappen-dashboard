import type { EnrichedDeal } from "../types";
import { DealCard } from "./DealCard";
import { EmptyState } from "./EmptyState";

interface DealGridProps {
  deals: EnrichedDeal[];
  onResetFilters?: () => void;
}

export function DealGrid({ deals, onResetFilters }: DealGridProps) {
  if (deals.length === 0) {
    return <EmptyState onReset={onResetFilters} />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {deals.map((deal) => (
        <DealCard key={deal.id} deal={deal} />
      ))}
    </div>
  );
}
