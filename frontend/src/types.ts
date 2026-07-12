/**
 * Type definitions matching the backend's static JSON data contract exactly.
 * See public/data/index.json and public/data/stores/<slug>.json.
 */

/** How a store's deals are collected. */
export type StoreMode = "api" | "pdf" | "jpg";

/** One entry in public/data/index.json's `stores` array. */
export interface StoreIndexEntry {
  slug: string;
  name: string;
  mode: StoreMode;
  deal_count: number;
  updated_at: string | null;
}

/** Shape of public/data/index.json. */
export interface DataIndex {
  generated_at: string;
  stores: StoreIndexEntry[];
}

/** One deal as it appears in a per-store JSON file's `deals` array. */
export interface DealItem {
  productnaam: string;
  korting_tekst: string | null;
  actieprijs: number | null;
  inhoud_waarde: number | null;
  inhoud_unit: string | null;
}

/** Shape of public/data/stores/<slug>.json. */
export interface StoreData {
  store: string;
  slug: string;
  mode: StoreMode;
  updated_at: string | null;
  deals: DealItem[];
}

/** A deal enriched with the store info it came from, for flat rendering/filtering. */
export interface EnrichedDeal extends DealItem {
  storeSlug: string;
  storeName: string;
  storeMode: StoreMode;
  /** Stable identity for React keys (index-based, scoped to store). */
  id: string;
}
