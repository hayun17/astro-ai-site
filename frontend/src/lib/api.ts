export type GeoHit = {
  lat: number;
  lon: number;
  displayName: string;
  timezone?: string;
  country?: string;
  admin1?: string;
  id?: number;
};

export async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = 75000
) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    window.clearTimeout(timer);
  }
}

export async function readApiError(resp: Response): Promise<string> {
  try {
    const data = await resp.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) return data.detail.map((x: any) => x?.msg || String(x)).join("; ");
    return JSON.stringify(data);
  } catch {
    const text = await resp.text();
    return text || `Request failed (${resp.status})`;
  }
}

export async function searchPlaces(q: string, count = 6): Promise<GeoHit[]> {
  const query = (q || "").trim();
  if (query.length < 2) return [];
  const language = (navigator.language || "en").split("-")[0].toLowerCase();
  const url =
    "https://geocoding-api.open-meteo.com/v1/search?format=json&count=" +
    encodeURIComponent(String(count)) +
    "&language=" + encodeURIComponent(language) +
    "&name=" + encodeURIComponent(query);
  const resp = await fetchWithTimeout(url, {}, 10000);
  if (!resp.ok) return [];
  const data = await resp.json();
  const results = Array.isArray(data?.results) ? data.results : [];
  return results.map((hit: any) => {
    const lat = Number(hit?.latitude);
    const lon = Number(hit?.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    const parts = [hit?.name, hit?.admin1, hit?.country].map((x) => String(x || "").trim()).filter(Boolean);
    return {
      lat,
      lon,
      displayName: Array.from(new Set(parts)).join(", ") || query,
      timezone: hit?.timezone ? String(hit.timezone) : undefined,
      country: hit?.country ? String(hit.country) : undefined,
      admin1: hit?.admin1 ? String(hit.admin1) : undefined,
      id: Number.isFinite(Number(hit?.id)) ? Number(hit.id) : undefined,
    } as GeoHit;
  }).filter(Boolean) as GeoHit[];
}

export async function geocodePlace(q: string): Promise<GeoHit | null> {
  const hits = await searchPlaces(q, 1);
  return hits[0] || null;
}
