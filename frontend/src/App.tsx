import React, { useMemo, useState } from "react";
import ChartWheel from "./components/chart/ChartWheel.tsx";

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

const DEFAULT_API_BASE =
  (import.meta.env.VITE_API_BASE as string) || "https://astromyla.onrender.com";

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

  async function runInterpretation() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        ...birth,
        // şimdilik style/focus backend'e gitmiyor (istersen sonra ekleriz)
      };

      const resp = await fetch(`${apiBase}/api/interpret/natal`, {
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
      const resp = await fetch(`${apiBase}/api/rebuild-index`, { method: "POST" });
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
          <p className="sub">Natal chart + RAG-grounded interpretation</p>
        </div>

        <div className="api">
          <label>
            API Base
            <input
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              placeholder="http://localhost:8000"
            />
          </label>
        </div>
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
            <button onClick={rebuildIndex} disabled={loading} className="secondary">
              Rebuild corpus index
            </button>
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

      <footer className="footer">
        <p>
          Tip: add licensed text under <code>backend/data/corpus</code> then click{" "}
          “Rebuild corpus index”. Set <code>OPENAI_API_KEY</code> in{" "}
          <code>backend/.env</code> to enable AI interpretations.
        </p>
      </footer>
    </div>
  );
}
