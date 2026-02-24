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
  house_system?: string; // optional
};

/**
 * ENV:
 * - Local: create frontend/.env  -> VITE_API_BASE_URL=http://localhost:8000 (or your backend)
 * - Render/Prod: set env var in Render -> VITE_API_BASE_URL=https://astromyla.onrender.com
 *
 * In production we hide the "API Base" input to keep UI clean & trustworthy.
 */
const RAW_ENV_API =
  (import.meta.env.VITE_API_BASE_URL as string) ||
  (import.meta.env.VITE_API_BASE as string) || // backward compatibility (senin eski env ismi)
  "https://astromyla.onrender.com";

function normalizeBase(url: string) {
  return (url || "").trim().replace(/\/+$/, "");
}

const DEFAULT_API_BASE = normalizeBase(RAW_ENV_API);

// Vite sets import.meta.env.DEV / PROD flags
const IS_DEV = import.meta.env.DEV;

export default function App() {
  // In prod, apiBase is fixed from ENV. In dev, allow override via input.
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

  const [style, setStyle] = useState("modern");
  const [focus, setFocus] = useState("general");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // result shape: { chart, interpretation, retrieval }
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

  const chartForWheel = useMemo(() => {
    // ChartWheel expects backend chart JSON
    return result?.chart ?? null;
  }, [result]);

  const planetAspects = useMemo(() => {
    return result?.chart?.aspects?.planet_aspects ?? [];
  }, [result]);

  async function runInterpretation() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        ...birth,
        // TODO: istersen style/focus'u da backend'e ekleriz
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

      // If you want the chart JSON easily:
      // console.log("CHART JSON:", data?.chart);
    } catch (e: any) {
      setError(e?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  /**
   * SECURITY NOTE:
   * "Rebuild index" endpoint should NOT be public in production.
   * We hide the button in prod. (Backend tarafında da auth koymak en iyisi.)
   */
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

          {/* ✅ 1) CHANGE THIS TEXT (SEO / CTR) */}
          <p className="sub">AI Birth Chart + Source-Backed Interpretation</p>
        </div>

        {/* DEV ONLY: show API Base override */}
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

      {/* TOP: Birth form */}
      <section className="card">
        <h2>Enter your birth datas babe :)</h2>

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
              Date (Y-M-D)
              <input
                value={`${birth.year}-${String(birth.month).padStart(2, "0")}-${String(
                  birth.day
                ).padStart(2, "0")}`}
                onChange={(e) => {
                  const [y, m, d] = e.target.value
                    .split("-")
                    .map((n) => parseInt(n, 10));
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
                  const [hh, mm] = e.target.value
                    .split(":")
                    .map((n) => parseInt(n, 10));
                  if (Number.isFinite(hh) && Number.isFinite(mm))
                    setBirth({ ...birth, hour: hh, minute: mm });
                }}
              />
            </label>
          </div>

          <div className="row">
            <label>
              Latitude
              <input
                type="number"
                step="0.0001"
                value={birth.latitude}
                onChange={(e) =>
                  setBirth({ ...birth, latitude: parseFloat(e.target.value) })
                }
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

          <div className="row">
            <label>
              House system
              <input
                value={birth.house_system || "P"}
                onChange={(e) =>
                  setBirth({ ...birth, house_system: e.target.value || "P" })
                }
                placeholder="P (Placidus), W (Whole Sign), K (Koch) ..."
              />
            </label>

            <label>
              Style
              <input
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                placeholder="modern / traditional / psychological"
              />
            </label>

            <label>
              Focus
              <input
                value={focus}
                onChange={(e) => setFocus(e.target.value)}
                placeholder="career / relationships / 2026 themes"
              />
            </label>
          </div>

          <div className="actions">
            <button onClick={runInterpretation} disabled={loading}>
              Generate interpretation
            </button>

            {/* DEV ONLY */}
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

      {/* BOTTOM: LEFT chart, RIGHT interpretation */}
      <div className="grid2">
        <section className="card">
          <h2>Your Special Chart :)</h2>

          {!result && <p className="muted">Generate interpretation to render the chart.</p>}

          {result && (
            <>
              <div className="pill">{planetsSummary}</div>

              <div className="chartBox">
                {chartForWheel ? (
                  <ChartWheel chart={chartForWheel} />
                ) : (
                  <p className="muted">No chart data found.</p>
                )}
              </div>

              {/* ✅ 3) NEW: aspect triangle + distributions */}
              <div className="extras">
                <AspectTriangle aspects={planetAspects} />
                <Distributions planets={result?.chart?.planets} />
              </div>
            </>
          )}
        </section>

        <section className="card">
          <h2> Your Interpretations HERE !!! </h2>
          {!result && <p className="muted">Run an interpretation to see outputs.</p>}

          {result && (
            <>
              <pre className="output">{result.interpretation}</pre>

              <details>
                <summary>Retrieval (RAG) sources</summary>
                <pre className="output">{JSON.stringify(result.retrieval, null, 2)}</pre>
              </details>

              <details>
                <summary>Chart JSON</summary>
                <pre className="output">{JSON.stringify(result.chart, null, 2)}</pre>
              </details>
            </>
          )}
        </section>
      </div>

      {/* ✅ 2) REMOVED that big dev tip footer */}
      <footer className="footer">
        <p>© {new Date().getFullYear()} AstroMYLA</p>
      </footer>
    </div>
  );
}