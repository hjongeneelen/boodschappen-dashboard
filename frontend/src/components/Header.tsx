import { formatDateTime } from "../utils/format";

interface HeaderProps {
  generatedAt: string | null;
  totalDeals: number;
  storeCount: number;
  scrapedStoreCount: number;
}

export function Header({ generatedAt, totalDeals, storeCount, scrapedStoreCount }: HeaderProps) {
  const updated = formatDateTime(generatedAt);

  return (
    <header className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-indigo-600 to-emerald-500 text-white">
      <div
        className="pointer-events-none absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 20%, white 1px, transparent 1px), radial-gradient(circle at 80% 60%, white 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
        aria-hidden="true"
      />
      <div className="relative mx-auto flex max-w-7xl flex-col gap-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-2">
          <span className="w-fit rounded-full bg-white/15 px-3 py-1 text-xs font-medium tracking-wide uppercase backdrop-blur-sm">
            Nederland &middot; Boodschappen
          </span>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Boodschappen Dashboard</h1>
          <p className="max-w-2xl text-sm text-indigo-50/90 sm:text-base">
            Alle actuele aanbiedingen van Nederlandse supermarkten en winkels, overzichtelijk op
            &eacute;&eacute;n plek verzameld.
          </p>
        </div>

        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="Aanbiedingen" value={totalDeals.toLocaleString("nl-NL")} />
          <Stat label="Winkels totaal" value={storeCount.toString()} />
          <Stat label="Al gescand" value={scrapedStoreCount.toString()} />
          <Stat label="Laatst bijgewerkt" value={updated ?? "onbekend"} small />
        </dl>
      </div>
    </header>
  );
}

function Stat({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <div className="rounded-xl bg-white/10 px-4 py-3 backdrop-blur-sm ring-1 ring-white/15">
      <dt className="text-xs font-medium text-indigo-50/80">{label}</dt>
      <dd className={`mt-0.5 font-semibold text-white ${small ? "text-sm" : "text-xl"}`}>
        {value}
      </dd>
    </div>
  );
}
