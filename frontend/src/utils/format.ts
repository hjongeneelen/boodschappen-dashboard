const eurFormatter = new Intl.NumberFormat("nl-NL", {
  style: "currency",
  currency: "EUR",
});

/** Formats a euro amount Dutch-style, e.g. 1.99 -> "€ 1,99". Returns null if no price. */
export function formatPrice(price: number | null): string | null {
  if (price === null || Number.isNaN(price)) return null;
  return eurFormatter.format(price);
}

const unitLabels: Record<string, string> = {
  gram: "g",
  gr: "g",
  g: "g",
  kg: "kg",
  ml: "ml",
  liter: "L",
  l: "L",
  stuks: "st.",
  stuk: "st.",
};

/** Formats a package size + unit, e.g. (1500, "ml") -> "1500 ml". Returns null if unknown. */
export function formatQuantity(value: number | null, unit: string | null): string | null {
  if (value === null || Number.isNaN(value)) return null;
  const label = unit ? (unitLabels[unit.toLowerCase()] ?? unit) : "";
  const num = Number.isInteger(value) ? value.toString() : value.toString().replace(".", ",");
  return label ? `${num} ${label}` : num;
}

/** Formats an ISO timestamp as a readable Dutch date/time, e.g. "12 jul 2026, 08:00". */
export function formatDateTime(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/** Formats an ISO timestamp as a relative "x geleden" string, falling back to a date. */
export function formatRelative(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return "zojuist";
  if (diffMin < 60) return `${diffMin} min. geleden`;
  const diffHours = Math.round(diffMin / 60);
  if (diffHours < 24) return `${diffHours} u. geleden`;
  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 7) return `${diffDays} d. geleden`;
  return formatDateTime(iso);
}
