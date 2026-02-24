import React, { useMemo, useState } from "react";
import ChartWheel from "./components/chart/ChartWheel.tsx";
import AspectTriangle from "./components/chart/AspectTriangle.tsx";
import Distributions from "./components/chart/Distributions.tsx";

type Birth = {
  name: string;
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  latitude: number;
  longitude: number;
  tz_offset_hours: number;
  house_system?: string;
};

const RAW_ENV_API =
  (import.meta.env.VITE_API_BASE_URL as string) ||
  (import.meta.env.VITE_API_BASE as string) ||
  "https://astromyla.onrender.com";

function normalizeBase(url: string) {
  return (url || "").trim().replace(/\/+$/, "");
}
const DEFAULT_API_BASE = normalizeBase(RAW_ENV_API);
const IS_DEV = import.meta.env.DEV;

type GeoHit = { lat: number; lon: number; displayName: string };

async function geocodePlace(q: string): Promise<GeoHit | null> {
  const query = (q || "").trim();
  if (!query) return null;

  // OpenStreetMap Nominatim (simple, free).
  // If this ever rate-limits, we can move geocoding to backend later.
  const url =
    "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" +
    encodeURIComponent(query);

  const resp = await fetch(url, {
    headers: {
      "Accept-Language": "en",
    },
  });

  if (!resp.ok) return null;
  const data = await resp.json();
  if (!Array.isArray(data) || data.length === 0) return null;

  const hit = data[0];
  const lat = parseFloat(hit?.lat);
  const lon = parseFloat(hit?.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;

  return {
    lat,
    lon,
    displayName: String(hit?.display_name || query),
  };
}

export default function App() {
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);

  const [birth, setBirth] = useState<Birth>({
    name: "Example",
    year: 2002,
    month: 1,
    day: 25,
    hour: 9,
    minute: 30,
    latitude: 40.653,
    longitude: 35.833,
    tz_offset_hours: 3.0,
    house_system: "P",
  });

  // UX: user-friendly inputs
  const [birthplace, setBirthplace] = useState("Merzifon, Amasya, Türkiye");
  const [geoResolved, setGeoResolved] = useState<GeoHit | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);

  const [useAdvancedCoords, setUseAdvancedCoords] = useState(false);

  // Dropdowns
  const [houseSystem, setHouseSystem] = useState<string>(birth.house_system || "P");
  const [style, setStyle] = useState("modern");
  const [focus, setFocus] = useState("general");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [result, setResult] = useState<any>(null);

  const planetsSummary = useMemo(() => {
    const planets = result?.chart?.planets;
    if (!planets) return null;

    const keys = [
      "Sun",
      "Moon",
      "Mercury",
      "Venus",
      "Mars",
      "Jupiter",
      "Saturn",
      "Uranus",
      "Neptune",
      "Pluto",
    ];

    return keys
      .filter((k) => planets[k])
      .map((k) => {
        const p = planets[k];
        const deg = Number.isFinite(p?.deg_in_sign) ? Math.floor(p.deg_in_sign) : 0;
        return `${k}: ${p.sign} ${deg}°`;
      })
      .join(" • ");
  }, [result]);

  const chartForWheel = useMemo(() => result?.chart ?? null, [result]);

  const aspectRows = useMemo(() => {
    const aspects = result?.chart?.aspects;
    if (!aspects) return [];
    const a1 = Array.isArray(aspects?.planet_aspects) ? aspects.planet_aspects : [];
    const a2 = Array.isArray(aspects?.other_aspects) ? aspects.other_aspects : [];
    return [...a1, ...a2];
  }, [result]);

  const aspectBodies = useMemo(() => {
    // prefer list, but only include bodies actually present in chart data
    const preferred = [
      "Sun",
      "Moon",
      "Mercury",
      "Venus",
      "Mars",
      "Jupiter",
      "Saturn",
      "Uranus",
      "Neptune",
      "Pluto",
      "Asc",
      "DSC",
      "MC",
      "IC",
      "TrueNode",
      "Lilith",
      "Chiron",
      "Vertex",
      "Fortune",
    ];

    const planets = result?.chart?.planets || {};
    const points = result?.chart?.points || {};

    const present = new Set<string>();
    Object.keys(planets).forEach((k) => present.add(k));
    Object.keys(points).forEach((k) => present.add(k));

    // normalize some possible backend naming variants
    const aliases: Record<string, string[]> = {
      Asc: ["ASC", "Ascendant"],
      DSC: ["Desc", "Descendant", "DC"],
      MC: ["Midheaven"],
      IC: ["ImumCoeli"],
      TrueNode: ["NorthNode", "Node", "NNode"],
      Lilith: ["BlackMoonLilith", "BML"],
      Fortune: ["PartOfFortune", "POF"],
    };

    const exists = (name: string) => {
      if (present.has(name)) return true;
      const al = aliases[name] || [];
      return al.some((a) => present.has(a));
    };

    const out = preferred.filter(exists);

    // if there are other “interesting” points in points, optionally add them at the end
    // (keeps it future-proof)
    for (const k of Object.keys(points)) {
      if (!out.includes(k) && out.length < 22) out.push(k);
    }

    return out;
  }, [result]);

  async function resolveGeocodeIfNeeded(): Promise<{ lat: number; lon: number } | null> {
    if (useAdvancedCoords) {
      if (Number.isFinite(birth.latitude) && Number.isFinite(birth.longitude)) {
        return { lat: birth.latitude, lon: birth.longitude };
      }
      return null;
    }

    // If already resolved and user didn't change birthplace, reuse
    if (geoResolved && geoResolved.displayName && birthplace.trim().length > 0) {
      return { lat: geoResolved.lat, lon: geoResolved.lon };
    }

    setGeoLoading(true);
    try {
      const hit = await geocodePlace(birthplace);
      if (!hit) return null;
      setGeoResolved(hit);
      return { lat: hit.lat, lon: hit.lon };
    } finally {
      setGeoLoading(false);
    }
  }

  async function runInterpretation() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const coords = await resolveGeocodeIfNeeded();
      if (!coords) {
        throw new Error(
          "Could not resolve birthplace to coordinates. Try a more specific place (City, Country) or open Advanced and enter latitude/longitude manually."
        );
      }

      const payload = {
        ...birth,
        latitude: coords.lat,
        longitude: coords.lon,
        house_system: houseSystem || "P",
        // style/focus are UX fields for now; we can send them to backend later if you want
      };

      const base = IS_DEV ? normalizeBase(apiBase) : DEFAULT_API_BASE;

      const resp = await fetch(`${base}/api/interpret/natal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || `Request failed (${resp.status})`);
      }

      const data = await resp.json();
      setResult(data);

      // Optional: see raw chart JSON in DEV console only
      if (IS_DEV) {
        // eslint-disable-next-line no-console
        console.log("CHART JSON:", data?.chart);
      }
    } catch (e: any) {
      setError(e?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function rebuildIndex() {
    setLoading(true);
    setError(null);

    try {
      const base = IS_DEV ? normalizeBase(apiBase) : DEFAULT_API_BASE;

      const resp = await fetch(`${base}/api/rebuild-index`, { method: "POST" });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || `Request failed (${resp.status})`);
      }
      const data = await resp.json();
      alert(`Index rebuilt. Chunks: ${data.chunks}`);
    } catch (e: any) {
      setError(e?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>AstroMYLA</h1>
          <p className="sub">AI Birth Chart + Source-Backed Interpretation</p>
        </div>

        {IS_DEV && (
          <div className="api">
            <label>
              API Base (dev only)
              <input
                value={apiBase}
                onChange={(e) => setApiBase(e.target.value)}
                placeholder="http://localhost:8000"
              />
            </label>
          </div>
        )}
      </header>

      {/* FORM */}
      <section className="card">
        <h2>Enter your birth data ✨</h2>

        <div className="form">
          <label>
            Name
            <input
              value={birth.name}
              onChange={(e) => setBirth({ ...birth, name: e.target.value })}
            />
          </label>

          <div className="row">
            <label>
              Date (YYYY-MM-DD)
              <input
                value={`${birth.year}-${String(birth.month).padStart(2, "0")}-${String(
                  birth.day
                ).padStart(2, "0")}`}
                onChange={(e) => {
                  const [y, m, d] = e.target.value.split("-").map((n) => parseInt(n, 10));
                  if (y && m && d) setBirth({ ...birth, year: y, month: m, day: d });
                }}
              />
            </label>

            <label>
              Time (HH:MM)
              <input
                value={`${String(birth.hour).padStart(2, "0")}:${String(birth.minute).padStart(
                  2,
                  "0"
                )}`}
                onChange={(e) => {
                  const [hh, mm] = e.target.value.split(":").map((n) => parseInt(n, 10));
                  if (Number.isFinite(hh) && Number.isFinite(mm))
                    setBirth({ ...birth, hour: hh, minute: mm });
                }}
              />
            </label>

            <label>
              UTC Offset
              <input
                type="number"
                step="0.5"
                value={birth.tz_offset_hours}
                onChange={(e) =>
                  setBirth({ ...birth, tz_offset_hours: parseFloat(e.target.value) })
                }
              />
            </label>
          </div>

          <label>
            Birthplace (City, Country)
            <input
              value={birthplace}
              onChange={(e) => {
                setBirthplace(e.target.value);
                setGeoResolved(null);
              }}
              placeholder="e.g., Ankara, Türkiye"
            />
            <span className="help">
              {geoLoading
                ? "Looking up coordinates…"
                : geoResolved
                ? `Resolved: ${geoResolved.displayName}  (lat ${geoResolved.lat.toFixed(
                    3
                  )}, lon ${geoResolved.lon.toFixed(3)})`
                : "Tip: If lookup fails, try a more specific query like “City, Country”."}
            </span>
          </label>

          <div className="row">
            <label>
              House system
              <select
                value={houseSystem}
                onChange={(e) => {
                  setHouseSystem(e.target.value);
                  setBirth({ ...birth, house_system: e.target.value });
                }}
              >
                <option value="P">Placidus (P)</option>
                <option value="W">Whole Sign (W)</option>
                <option value="K">Koch (K)</option>
                <option value="R">Regiomontanus (R)</option>
                <option value="C">Campanus (C)</option>
                <option value="E">Equal (E)</option>
              </select>
            </label>

            <label>
              Style
              <select value={style} onChange={(e) => setStyle(e.target.value)}>
                <option value="modern">Modern</option>
                <option value="traditional">Traditional</option>
                <option value="psychological">Psychological</option>
              </select>
            </label>

            <label>
              Focus
              <select value={focus} onChange={(e) => setFocus(e.target.value)}>
                <option value="general">General</option>
                <option value="relationships">Relationships</option>
                <option value="career">Career</option>
                <option value="year_ahead">Year Ahead</option>
              </select>
            </label>
          </div>

          <details className="advanced">
            <summary>
              Advanced (manual coordinates){" "}
              <span className="muted">(use only if birthplace lookup fails)</span>
            </summary>
            <div className="row">
              <label>
                Use manual latitude/longitude
                <select
                  value={useAdvancedCoords ? "yes" : "no"}
                  onChange={(e) => setUseAdvancedCoords(e.target.value === "yes")}
                >
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </label>

              <label>
                Latitude
                <input
                  type="number"
                  step="0.0001"
                  value={birth.latitude}
                  onChange={(e) =>
                    setBirth({ ...birth, latitude: parseFloat(e.target.value) })
                  }
                  disabled={!useAdvancedCoords}
                />
              </label>

              <label>
                Longitude
                <input
                  type="number"
                  step="0.0001"
                  value={birth.longitude}
                  onChange={(e) =>
                    setBirth({ ...birth, longitude: parseFloat(e.target.value) })
                  }
                  disabled={!useAdvancedCoords}
                />
              </label>
            </div>
          </details>

          <div className="actions">
            <button onClick={runInterpretation} disabled={loading}>
              Generate interpretation
            </button>

            {IS_DEV && (
              <button onClick={rebuildIndex} disabled={loading} className="secondary">
                Rebuild corpus index (dev only)
              </button>
            )}
          </div>

          {error && <p className="error">{error}</p>}
          {loading && <p className="muted">Working…</p>}
        </div>
      </section>

      {/* RESULTS (CENTERED STACK) */}
      <section className="card results">
        <h2>Your Chart ✨</h2>

        {!result && <p className="muted">Generate an interpretation to render your chart.</p>}

        {result && (
          <>
            <div className="pill">{planetsSummary}</div>

            <div className="chartCenter">
              <div className="chartBox chartBoxSmall">
                {chartForWheel ? <ChartWheel chart={chartForWheel} /> : <p>No chart data.</p>}
              </div>
            </div>

            {/* Aspect table centered, then distributions under it */}
            <div className="chartCenter">
              <AspectTriangle aspects={aspectRows} bodies={aspectBodies} />
            </div>

            <div className="chartCenter distCenter">
              <Distributions planets={result?.chart?.planets} />
            </div>
          </>
        )}
      </section>

      <section className="card">
        <h2>Your Interpretation ✨</h2>
        {!result && <p className="muted">Run an interpretation to see the output.</p>}
        {result && <pre className="output">{result.interpretation}</pre>}

        {/* IMPORTANT: We intentionally do NOT show RAG sources or raw Chart JSON to users. */}
      </section>

      <footer className="footer">
        <p>© {new Date().getFullYear()} AstroMYLA</p>
      </footer>
    </div>
  );
}