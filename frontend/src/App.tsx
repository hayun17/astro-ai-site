import React, { useEffect, useMemo, useState } from "react";
import ChartWheel from "./components/chart/ChartWheel";
import AspectTriangle from "./components/chart/AspectTriangle";
import Distributions from "./components/chart/Distributions";
import BirthDataForm, { BirthDraft, makeBirthDraft } from "./components/BirthDataForm";
import AstrocartographyMap from "./components/AstrocartographyMap";
import PrecisePositions from "./components/PrecisePositions";
import PremiumReadings from "./components/PremiumReadings";
import InterpretationView from "./components/InterpretationView";
import SynastryBiWheel from "./components/chart/SynastryBiWheel";
import TransitBiWheel from "./components/chart/TransitBiWheel";
import AccountPanel from "./components/AccountPanel";
import CalculationProgress from "./components/CalculationProgress";
import { ConnectionProfile, CompositeSignature } from "./components/ResultInsights";
import { NatalSignatureSuite, MylaMatch } from "./components/SignatureInsights";
import { fetchWithTimeout, geocodePlace, readApiError } from "./lib/api";

type Mode = "natal" | "transits" | "synastry" | "composite" | "astrocartography";

const RAW_ENV_API =
  (import.meta.env.VITE_API_BASE_URL as string) ||
  (import.meta.env.VITE_API_BASE as string) ||
  "https://astromyla.onrender.com";

function normalizeBase(url: string) {
  return (url || "").trim().replace(/\/+$/, "");
}
const DEFAULT_API_BASE = normalizeBase(RAW_ENV_API);
const IS_DEV = import.meta.env.DEV;

async function prepareBirth(draft: BirthDraft, style: string, focus: string) {
  const year = Number(draft.year);
  const month = Number(draft.month);
  const day = Number(draft.day);
  if (!draft.year || !draft.month || !draft.day || !Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) {
    throw new Error("Please enter your full date of birth in Day / Month / Year order.");
  }
  const d = new Date(Date.UTC(year, month - 1, day));
  const validDate = d.getUTCFullYear() === year && d.getUTCMonth() === month - 1 && d.getUTCDate() === day;
  if (!validDate) throw new Error("Please enter a valid date of birth in Day / Month / Year order.");

  const hour = draft.timeUnknown ? 12 : Number(draft.hour);
  const minute = draft.timeUnknown ? 0 : Number(draft.minute);
  if (!draft.timeUnknown && (draft.hour === "" || draft.minute === "" || !Number.isInteger(hour) || !Number.isInteger(minute) || hour < 0 || hour > 23 || minute < 0 || minute > 59)) {
    throw new Error("Please enter your birth time, or choose ‘I don’t know my birth time’. ");
  }

  let geo = draft.geo;
  if (!draft.useAdvancedCoords && !geo) {
    geo = await geocodePlace(draft.birthplace);
  }
  const lat = draft.useAdvancedCoords ? draft.latitude : geo?.lat;
  const lon = draft.useAdvancedCoords ? draft.longitude : geo?.lon;
  if (lat === "" || lon === "" || !Number.isFinite(Number(lat)) || !Number.isFinite(Number(lon))) {
    throw new Error("Could not resolve birthplace. Choose a city suggestion or use Advanced manual coordinates.");
  }
  const timezone = draft.useAdvancedCoords ? null : geo?.timezone || null;
  const offset = Number(draft.tz_offset_hours);
  if (!timezone && (draft.tz_offset_hours === "" || !Number.isFinite(offset) || offset < -14 || offset > 14)) {
    throw new Error("Choose a birthplace suggestion with a timezone, or enter the UTC offset in Advanced/manual mode.");
  }
  return {
    name: draft.name,
    year,
    month,
    day,
    hour,
    minute,
    latitude: Number(lat),
    longitude: Number(lon),
    tz_offset_hours: timezone ? 0 : offset,
    house_system: draft.house_system || "P",
    style,
    focus,
    time_unknown: draft.timeUnknown,
    timezone,
    birthplace: draft.birthplace || null,
  };
}

function draftFromBirth(birth: any): BirthDraft {
  return {
    name: birth?.name || "", year: Number(birth?.year) || "", month: Number(birth?.month) || "", day: Number(birth?.day) || "",
    hour: birth?.time_unknown ? "" : (Number.isFinite(Number(birth?.hour)) ? Number(birth.hour) : ""),
    minute: birth?.time_unknown ? "" : (Number.isFinite(Number(birth?.minute)) ? Number(birth.minute) : ""),
    latitude: Number.isFinite(Number(birth?.latitude)) ? Number(birth.latitude) : "", longitude: Number.isFinite(Number(birth?.longitude)) ? Number(birth.longitude) : "",
    tz_offset_hours: Number.isFinite(Number(birth?.tz_offset_hours)) ? Number(birth.tz_offset_hours) : "", house_system: birth?.house_system || "P",
    birthplace: birth?.birthplace || "", geo: birth?.timezone ? {lat:Number(birth.latitude),lon:Number(birth.longitude),displayName:birth?.birthplace||"Saved place",timezone:birth.timezone}:null,
    useAdvancedCoords: !birth?.timezone, timeUnknown: Boolean(birth?.time_unknown),
  };
}

function allChartAspects(chart: any) {
  const aspects = chart?.aspects || {};
  return [
    ...(Array.isArray(aspects.planet_aspects) ? aspects.planet_aspects : []),
    ...(Array.isArray(aspects.other_aspects) ? aspects.other_aspects : []),
  ];
}

function chartBodies(chart: any) {
  const preferred = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Asc", "DSC", "MC", "IC", "TrueNode", "Lilith", "Chiron", "Vertex", "Fortune",
  ];
  const present = new Set<string>([
    ...Object.keys(chart?.planets || {}),
    ...Object.keys(chart?.points || {}),
  ]);
  return preferred.filter((name) => present.has(name));
}

function planetSummary(chart: any) {
  const planets = chart?.planets || {};
  return ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    .filter((k) => planets[k]?.sign)
    .map((k) => {
      const p = planets[k];
      if (p.sign_uncertain) return `${k}: ${(p.possible_signs || []).join("/")}?`;
      const deg = Number.isFinite(Number(p.deg_in_sign)) ? Math.floor(Number(p.deg_in_sign)) : 0;
      return `${k}: ${p.sign}${chart?.time_unknown ? "" : ` ${deg}°`}`;
    })
    .join(" • ");
}

function ChartPanel({ chart, title }: { chart: any; title?: string }) {
  if (!chart) return null;
  const aspects = allChartAspects(chart);
  const bodies = chartBodies(chart);
  return (
    <div className="chartPanel">
      {title && <h3>{title}</h3>}
      {chart.time_unknown && (
        <div className="timeUnknownNotice">
          <strong>Birth time unknown mode</strong>
          <span>Houses, angles and time-sensitive Moon aspects are intentionally not guessed.</span>
        </div>
      )}
      <div className="pill">{planetSummary(chart)}</div>
      <div className="chartCenter">
        <div className="chartBox chartBoxSmall"><ChartWheel chart={chart} /></div>
      </div>
      {aspects.length > 0 && bodies.length > 1 && (
        <div className="chartCenter"><AspectTriangle aspects={aspects} bodies={bodies} /></div>
      )}
      <div className="chartCenter distCenter"><Distributions planets={chart.planets} /></div>
      <PrecisePositions chart={chart} />
    </div>
  );
}

function SynastryAspectTable({ aspects, aName, bName }: { aspects: any[]; aName: string; bName: string }) {
  if (!aspects?.length) return <p className="muted">No major cross-chart aspects within the configured orbs.</p>;
  return (
    <div className="synastryTableWrap">
      <table className="synastryTable">
        <thead><tr><th>{aName || "Person A"}</th><th>Aspect</th><th>{bName || "Person B"}</th><th>Orb</th></tr></thead>
        <tbody>
          {aspects.slice(0, 36).map((a, idx) => (
            <tr key={`${a.a}-${a.aspect}-${a.b}-${idx}`}>
              <td>{a.a}</td><td>{a.aspect}</td><td>{a.b}</td><td>{Number(a.orb).toFixed(2)}°</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState<Mode>("natal");
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);
  const [personA, setPersonA] = useState<BirthDraft>(makeBirthDraft());
  const [personB, setPersonB] = useState<BirthDraft>(makeBirthDraft());
  const [style, setStyle] = useState("modern");
  const [focus, setFocus] = useState("general");
  const [orbProfile, setOrbProfile] = useState("standard");
  const [transitDate, setTransitDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [progress, setProgress] = useState({percent:0,label:""});
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [paidOrderToken, setPaidOrderToken] = useState<string | null>(null);
  const [paymentNotice, setPaymentNotice] = useState<string | null>(null);

  const base = IS_DEV ? normalizeBase(apiBase) : DEFAULT_API_BASE;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const payment = params.get("payment");
    const order = params.get("order");
    if (payment === "success" && order) {
      setPaidOrderToken(order);
      setPaymentNotice("Payment verified ✨ Your premium report is ready to generate and download.");
    } else if (payment === "failed") {
      setPaymentNotice("The payment was not completed. No premium report was unlocked.");
    }
  }, []);

  const title = useMemo(() => ({
    natal: "Birth Chart",
    transits: "Current Transits",
    synastry: "Synastry",
    composite: "Composite Chart",
    astrocartography: "Astrocartography",
  }[mode]), [mode]);

  function changeMode(next: Mode) {
    setMode(next);
    setResult(null);
    setError(null);
  }

  async function postJson(path: string, payload: any) {
    const resp = await fetchWithTimeout(`${base}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, 90000);
    if (!resp.ok) throw new Error(await readApiError(resp));
    return resp.json();
  }

  async function runTool() {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress({percent:6,label:"Validating your birth data"});
    let timer: number | undefined;
    try {
      setProgress({percent:14,label:"Resolving place & historical timezone"});
      const a = await prepareBirth(personA, style, focus);
      let payloadResult: any;
      setProgress({percent:32,label:"Calculating planetary positions"});
      timer = window.setInterval(() => setProgress(prev => ({...prev, percent: Math.min(92, prev.percent + (prev.percent < 65 ? 4 : 1))})), 650);
      if (mode === "natal") {
        setProgress({percent:48,label:"Calculating houses & aspects"});
        payloadResult = await postJson("/api/interpret/natal", a);
      } else if (mode === "transits") {
        setProgress({percent:46,label:"Calculating the current sky"});
        payloadResult = await postJson("/api/interpret/daily", { birth: a, target_date: transitDate || null, style });
      } else if (mode === "astrocartography") {
        if (a.time_unknown) throw new Error("Astrocartography needs a known birth time. Uncheck ‘I don’t know my birth time’ to calculate angular lines.");
        setProgress({percent:52,label:"Tracing angular lines around the world"});
        payloadResult = await postJson("/api/interpret/astrocartography", a);
      } else {
        setProgress({percent:28,label:"Preparing both birth charts"});
        const b = await prepareBirth(personB, style, "relationships");
        const payload = { person_a: a, person_b: b, style, orb_profile: orbProfile };
        setProgress({percent:52,label: mode === "synastry" ? "Comparing inter-chart aspects" : "Building midpoint composite"});
        payloadResult = await postJson(mode === "synastry" ? "/api/interpret/synastry" : "/api/interpret/composite", payload);
      }
      if (timer) window.clearInterval(timer);
      setProgress({percent:96,label:"Finishing your interpretation"});
      setResult(payloadResult);
      setProgress({percent:100,label:"Your chart is ready ✨"});
      window.setTimeout(()=>setProgress({percent:0,label:""}), 900);
    } catch (e: any) {
      if (timer) window.clearInterval(timer);
      setProgress({percent:0,label:""});
      setError(e?.name === "AbortError" ? "The request timed out. Please try again." : e?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  function reportPayload() {
    const reportTitle = mode === "natal"
      ? `AstroMYLA Natal Report - ${personA.name || "Chart"}`
      : mode === "astrocartography"
      ? `AstroMYLA Astrocartography - ${personA.name || "Chart"}`
      : mode === "transits"
      ? `AstroMYLA Current Transits - ${personA.name || "Chart"}`
      : `AstroMYLA ${mode === "synastry" ? "Synastry" : "Composite"} - ${personA.name || "A"} x ${personB.name || "B"}`;
    return {
      kind: mode,
      title: reportTitle,
      data: result,
      interpretation: result?.interpretation || "",
    };
  }

  async function downloadPdf() {
    if (!result) return;
    setPdfLoading(true);
    setError(null);
    try {
      const resp = await fetchWithTimeout(`${base}/api/report/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reportPayload()),
      }, 90000);
      if (!resp.ok) throw new Error(await readApiError(resp));
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const disposition = resp.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^";]+)"?/i);
      a.download = match?.[1] || `astromyla-${mode}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e: any) {
      setError(e?.message || "Could not download PDF.");
    } finally {
      setPdfLoading(false);
    }
  }


  async function startCheckout(product: "personalized_reading" | "deep_reading", buyer: any, questions: string[]) {
    setCheckoutBusy(true);
    setCheckoutError(null);
    try {
      const birth = await prepareBirth(personA, style, focus);
      const data = await postJson("/api/payments/checkout", { product, buyer, birth, questions });
      if (!data?.payment_page_url || !String(data.payment_page_url).startsWith("https://")) throw new Error("Secure checkout URL was not returned.");
      window.location.assign(data.payment_page_url);
    } catch (e:any) {
      setCheckoutError(e?.message || "Could not start secure checkout.");
    } finally {
      setCheckoutBusy(false);
    }
  }

  async function downloadPaidOrderReport() {
    if (!paidOrderToken) return;
    setPdfLoading(true);
    setError(null);
    try {
      const resp = await fetchWithTimeout(`${base}/api/orders/${encodeURIComponent(paidOrderToken)}/report`, {method:"GET"}, 180000);
      if (!resp.ok) throw new Error(await readApiError(resp));
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const disposition = resp.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^";]+)"?/i);
      a.download = match?.[1] || "astromyla-premium-reading.pdf";
      document.body.appendChild(a); a.click(); a.remove();
      window.setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(e:any) { setError(e?.message || "Could not generate premium report."); }
    finally { setPdfLoading(false); }
  }

  return (
    <div className="appShell">
      <header className="hero">
        <div>
          <h1>AstroMYLA</h1>
          <p>Personal astrology, current transits, relationship maps and AstroMYLA signature insights — with downloadable reports.</p>
        </div>
        <div className="heroActions">
          <AccountPanel apiBase={base} prepareBirthA={() => prepareBirth(personA, style, focus)} prepareBirthB={() => prepareBirth(personB, style, "relationships")} showPersonB={mode === "synastry" || mode === "composite"} onLoadBirth={(birth,slot)=>{if(slot === "B") setPersonB(draftFromBirth(birth)); else setPersonA(draftFromBirth(birth)); setResult(null);}} />
          {IS_DEV && (
            <label className="devApiField">API Base (dev only)<input value={apiBase} onChange={(e) => setApiBase(e.target.value)} /></label>
          )}
        </div>
      </header>

      <nav className="toolTabs" aria-label="Astrology tools">
        {([
          ["natal", "Birth Chart"],
          ["transits", "Transits"],
          ["synastry", "Synastry"],
          ["composite", "Composite"],
          ["astrocartography", "Astrocartography"],
        ] as [Mode, string][]).map(([key, label]) => (
          <button key={key} className={mode === key ? "active" : ""} onClick={() => changeMode(key)}>{label}</button>
        ))}
      </nav>

      <section className="card inputCard">
        <div className="sectionHeading">
          <div><h2>{title} ✨</h2><p className="muted">
            {mode === "natal" && "Enter one person’s birth data."}
            {mode === "transits" && "Layer the current sky over your natal chart and read the strongest active themes."}
            {mode === "synastry" && "Compare two natal charts through a bi-wheel, cross-chart aspects and a transparent connection profile."}
            {mode === "composite" && "Build a zodiacal midpoint composite to explore the relationship as a symbolic whole."}
            {mode === "astrocartography" && "Map where natal planets were on the ASC, DSC, MC and IC at the birth moment."}
          </p></div>
        </div>

        <div className={mode === "synastry" || mode === "composite" ? "dualBirthForms" : "singleBirthForm"}>
          <BirthDataForm value={personA} onChange={setPersonA} title={mode === "synastry" || mode === "composite" ? "Person A" : undefined} compact={mode !== "natal"} />
          {(mode === "synastry" || mode === "composite") && <BirthDataForm value={personB} onChange={setPersonB} title="Person B" compact />}
        </div>

        <div className="readingPrefs">
          <label>Style<select value={style} onChange={(e) => setStyle(e.target.value)}><option value="modern">Modern</option><option value="traditional">Traditional</option><option value="psychological">Psychological</option></select></label>
          {mode === "natal" && <label>Focus<select value={focus} onChange={(e) => setFocus(e.target.value)}><option value="general">General</option><option value="relationships">Relationships</option><option value="career">Career</option><option value="year_ahead">Year Ahead</option></select></label>}
          {mode === "transits" && <label>Transit date <span className="dateFormatHint">leave blank for now</span><div className="transitDateControl"><input type="date" value={transitDate} onChange={(e)=>setTransitDate(e.target.value)}/>{transitDate && <button type="button" className="secondary" onClick={()=>setTransitDate("")}>Use now</button>}</div></label>}
          {(mode === "synastry" || mode === "composite") && <label>Aspect orbs<select value={orbProfile} onChange={(e)=>setOrbProfile(e.target.value)}><option value="tight">Tight</option><option value="standard">Standard</option><option value="wide">Wide</option></select></label>}
        </div>

        {mode === "astrocartography" && personA.timeUnknown && <div className="warningBox">Astrocartography cannot be calculated reliably without an exact birth time because the angular lines rotate with sidereal time.</div>}

        <div className="actions">
          <button onClick={runTool} disabled={loading}>{loading ? "Calculating…" : `Generate ${title}`}</button>
        </div>
        {loading && progress.percent > 0 && <CalculationProgress percent={progress.percent} label={progress.label} />}
        {error && <p className="error">{error}</p>}
      </section>

      {result && (
        <>
          <section className="card results">
            <div className="resultHeader">
              <h2>{title} Results ✨</h2>
              <button className="secondary downloadButton" onClick={downloadPdf} disabled={pdfLoading}>{pdfLoading ? "Preparing PDF…" : "Download PDF report"}</button>
            </div>

            {mode === "natal" && <>
              <NatalSignatureSuite data={result.astromyla} />
              <ChartPanel chart={result.chart} />
            </>}

            {mode === "transits" && (
              <>
                <TransitBiWheel natal={result.natal} transits={result.transits} />
                <div className="transitSummaryGrid">
                  <div className="overlayCard"><strong>Strongest active transits</strong><div className="overlayList">{(result.transits?.top_aspects||[]).slice(0,8).map((x:any,i:number)=><span key={i}><b>{x.transit} {x.aspect} natal {x.natal}</b> · {Number(x.orb).toFixed(2)}° · {x.applying?"applying":"separating"}</span>)}</div></div>
                  <div className="overlayCard"><strong>Planets moving through your natal houses</strong><div className="overlayList">{(result.transits?.house_overlays||[]).slice(0,10).map((x:any)=><span key={x.planet}><b>{x.planet} → House {x.house}</b> · {x.theme}</span>)}{!(result.transits?.house_overlays||[]).length&&<span className="muted">House transits require a known birth time.</span>}</div></div>
                </div>
                <p className="muted methodNote">Current transits describe symbolic timing and emphasis, not fixed predictions.</p>
              </>
            )}

            {mode === "synastry" && (
              <>
                <SynastryBiWheel
                  chartA={result.synastry?.person_a}
                  chartB={result.synastry?.person_b}
                  aspects={result.synastry?.aspects || []}
                  aName={personA.name}
                  bName={personB.name}
                />
                <ConnectionProfile profile={result.synastry?.connection_profile} />
                <MylaMatch match={result.synastry?.myla_match} />
                <h3>Cross-chart aspects</h3>
                <SynastryAspectTable aspects={result.synastry?.aspects || []} aName={personA.name} bName={personB.name} />
                {(result.synastry?.house_overlays?.a_in_b_houses?.length > 0 || result.synastry?.house_overlays?.b_in_a_houses?.length > 0) && (
                  <>
                    <h3>House overlays</h3>
                    <div className="houseActivationSummary">
                      <strong>Most activated houses</strong>
                      <div className="activationChips">{(result.synastry?.house_overlays?.a_activates_b||[]).slice(0,4).map((x:any)=><span key={`a-${x.house}`}>{personA.name||"A"} → {personB.name||"B"} H{x.house} · {x.count}</span>)}{(result.synastry?.house_overlays?.b_activates_a||[]).slice(0,4).map((x:any)=><span key={`b-${x.house}`}>{personB.name||"B"} → {personA.name||"A"} H{x.house} · {x.count}</span>)}</div>
                    </div>
                    <div className="overlayGrids">
                      <div className="overlayCard">
                        <strong>{personA.name || "Person A"} planets in {personB.name || "Person B"}'s houses</strong>
                        <div className="overlayList">
                          {(result.synastry?.house_overlays?.a_in_b_houses || []).map((x: any) => <span key={`ab-${x.planet}`}><b>{x.planet} → House {x.house}</b> · {x.theme}</span>)}
                        </div>
                      </div>
                      <div className="overlayCard">
                        <strong>{personB.name || "Person B"} planets in {personA.name || "Person A"}'s houses</strong>
                        <div className="overlayList">
                          {(result.synastry?.house_overlays?.b_in_a_houses || []).map((x: any) => <span key={`ba-${x.planet}`}><b>{x.planet} → House {x.house}</b> · {x.theme}</span>)}
                        </div>
                      </div>
                    </div>
                  </>
                )}
                <p className="muted methodNote">The profile above measures which relationship themes are most activated. It is not a probability that the relationship will succeed.</p>
              </>
            )}

            {mode === "composite" && (
              <>
                <CompositeSignature signature={result.signature} />
                <div className="compositeIntro"><strong>About this chart:</strong> Composite planets use zodiacal midpoints. When both birth times are known, midpoint house cusps are included as a symbolic relationship layer.</div>
                <ChartPanel chart={result.composite} title={`${personA.name || "A"} × ${personB.name || "B"}`} />
              </>
            )}

            {mode === "astrocartography" && <AstrocartographyMap data={result.astrocartography} />}
          </section>

          <section className="card interpretationCard">
            <div className="resultHeader"><h2>Interpretation ✨</h2></div>
            <InterpretationView text={result.interpretation} />
          </section>
        </>
      )}

      {paymentNotice && <section className="card paymentNotice"><strong>{paymentNotice}</strong>{paidOrderToken && <button onClick={downloadPaidOrderReport} disabled={pdfLoading}>{pdfLoading ? "Creating your premium PDF…" : "Download my premium report"}</button>}</section>}

      <PremiumReadings apiBase={base} onCheckout={startCheckout} checkoutBusy={checkoutBusy} checkoutError={checkoutError} />

      <footer className="footer"><p>© {new Date().getFullYear()} AstroMYLA</p><p className="muted">Astrology is interpretive and is not scientific or professional advice.</p></footer>
    </div>
  );
}
