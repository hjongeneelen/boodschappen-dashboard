import { useMemo, useState } from "react";
import { Header } from "./components/Header";
import { StoreFilterBar } from "./components/StoreFilterBar";
import { CategoryFilterBar } from "./components/CategoryFilterBar";
import { SearchAndSort, type SortOption } from "./components/SearchAndSort";
import { DealGrid } from "./components/DealGrid";
import { useDeals } from "./hooks/useDeals";

function App() {
  const { loading, error, generatedAt, stores, deals } = useDeals();

  const [selectedStores, setSelectedStores] = useState<Set<string>>(new Set());
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortOption>("price-asc");

  const toggleStore = (slug: string) => {
    setSelectedStores((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      return next;
    });
  };

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const resetFilters = () => {
    setSelectedStores(new Set());
    setSelectedCategories(new Set());
    setQuery("");
  };

  const categoryEntries = useMemo(() => {
    const counts = new Map<string, number>();
    for (const deal of deals) {
      if (deal.categorie) {
        counts.set(deal.categorie, (counts.get(deal.categorie) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [deals]);

  const uncategorizedCount = useMemo(
    () => deals.filter((d) => !d.categorie).length,
    [deals],
  );

  const visibleDeals = useMemo(() => {
    const q = query.trim().toLowerCase();

    const filtered = deals.filter((deal) => {
      const storeMatches = selectedStores.size === 0 || selectedStores.has(deal.storeSlug);
      const categoryMatches =
        selectedCategories.size === 0 || (deal.categorie !== null && selectedCategories.has(deal.categorie));
      const queryMatches = q === "" || deal.productnaam.toLowerCase().includes(q);
      return storeMatches && categoryMatches && queryMatches;
    });

    return [...filtered].sort((a, b) => {
      switch (sort) {
        case "price-asc": {
          if (a.actieprijs === null) return 1;
          if (b.actieprijs === null) return -1;
          return a.actieprijs - b.actieprijs;
        }
        case "price-desc": {
          if (a.actieprijs === null) return 1;
          if (b.actieprijs === null) return -1;
          return b.actieprijs - a.actieprijs;
        }
        case "store-asc":
          return (
            a.storeName.localeCompare(b.storeName, "nl") ||
            a.productnaam.localeCompare(b.productnaam, "nl")
          );
        default:
          return 0;
      }
    });
  }, [deals, selectedStores, selectedCategories, query, sort]);

  const scrapedStoreCount = stores.filter((s) => s.deal_count > 0 && s.updated_at !== null).length;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <Header
        generatedAt={generatedAt}
        totalDeals={deals.length}
        storeCount={stores.length}
        scrapedStoreCount={scrapedStoreCount}
      />

      <main className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-400">
            Er ging iets mis bij het laden van de data: {error}
          </div>
        )}

        {loading ? (
          <LoadingState />
        ) : (
          <>
            <section className="flex flex-col gap-3">
              <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase dark:text-slate-400">
                Winkels
              </h2>
              <StoreFilterBar
                stores={stores}
                selected={selectedStores}
                onToggle={toggleStore}
                onSelectAll={() => setSelectedStores(new Set())}
              />
            </section>

            {categoryEntries.length > 0 && (
              <section className="flex flex-col gap-3">
                <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase dark:text-slate-400">
                  Categorieën
                </h2>
                <CategoryFilterBar
                  categories={categoryEntries}
                  selected={selectedCategories}
                  onToggle={toggleCategory}
                  onSelectAll={() => setSelectedCategories(new Set())}
                  uncategorizedCount={uncategorizedCount}
                />
              </section>
            )}

            <section className="sticky top-0 z-10 -mx-4 border-b border-slate-200 bg-slate-50/90 px-4 py-3 backdrop-blur-sm sm:mx-0 sm:rounded-xl sm:border sm:px-4 dark:border-slate-800 dark:bg-slate-900/90">
              <SearchAndSort
                query={query}
                onQueryChange={setQuery}
                sort={sort}
                onSortChange={setSort}
                resultCount={visibleDeals.length}
              />
            </section>

            <section>
              <DealGrid deals={visibleDeals} onResetFilters={resetFilters} />
            </section>
          </>
        )}
      </main>

      <footer className="mx-auto max-w-7xl px-4 pb-8 text-center text-xs text-slate-400 sm:px-6 lg:px-8 dark:text-slate-600">
        Gegevens worden periodiek automatisch of handmatig bijgewerkt per winkel. Prijzen kunnen
        afwijken van de prijs in de winkel zelf.
      </footer>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="h-40 animate-pulse rounded-2xl border border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-800"
        />
      ))}
    </div>
  );
}

export default App;
