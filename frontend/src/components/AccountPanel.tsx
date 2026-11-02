import React, { useCallback, useEffect, useState } from "react";
import { fetchWithTimeout, readApiError } from "../lib/api";

type SaveRequest = { id: number; slot: "A" | "B"; birth: any } | null;
type Props = {
  apiBase: string;
  saveRequest?: SaveRequest;
  onLoadBirth: (birth: any, slot: "A" | "B", snapshot?: any) => void;
};
type SavedChart = { id: string; label: string; birth: any; updated_at: number; natal_snapshot?: any };
const SESSION_KEY = "astromyla_session";

export default function AccountPanel({ apiBase, saveRequest, onLoadBirth }: Props) {
  const [open, setOpen] = useState(false);
  const [screen, setScreen] = useState<"sign-in" | "sign-up">("sign-in");
  const [token, setToken] = useState(() => { try { return localStorage.getItem(SESSION_KEY) || ""; } catch { return ""; } });
  const [user, setUser] = useState<any>(null);
  const [charts, setCharts] = useState<SavedChart[]>([]);
  const [ready, setReady] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [pending, setPending] = useState<SaveRequest>(null);
  const [label, setLabel] = useState("");

  const api = useCallback(async (path: string, options: RequestInit = {}, authToken = token) => {
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
    const response = await fetchWithTimeout(`${apiBase}${path}`, { ...options, headers }, 30000);
    if (!response.ok) {
      const ex: any = new Error(await readApiError(response));
      ex.status = response.status;
      throw ex;
    }
    return response.status === 204 ? null : response.json();
  }, [apiBase, token]);

  const refresh = useCallback(async (authToken = token) => {
    if (!authToken) return;
    try {
      const data = await api("/api/account/me", {}, authToken);
      setUser(data.user);
      setCharts(data.charts || []);
      setError("");
    } catch (e: any) {
      if (e.status === 401) {
        try { localStorage.removeItem(SESSION_KEY); } catch {}
        setToken(""); setUser(null); setCharts([]);
        setError("Your session expired. Sign in again to see your saved charts.");
      } else {
        setError("Couldn't load your saved charts. Please check your connection and try again.");
      }
    }
  }, [api, token]);

  useEffect(() => {
    fetch(`${apiBase}/api/account/config`)
      .then(r => r.ok ? r.json() : null)
      .then(d => setReady(Boolean(d?.ready)))
      .catch(() => setReady(false));
  }, [apiBase]);
  useEffect(() => { if (token) void refresh(token); }, [token]);
  useEffect(() => {
    if (!saveRequest) return;
    setPending(saveRequest);
    setLabel(saveRequest.birth?.name?.trim() || (saveRequest.slot === "A" ? "My chart" : "Partner"));
    setError(""); setNotice(""); setOpen(true);
  }, [saveRequest?.id]);

  async function authorize(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const data = await api(screen === "sign-in" ? "/api/account/login" : "/api/account/register", {
        method: "POST", body: JSON.stringify(screen === "sign-in" ? { email, password } : { email, password, display_name: displayName }),
      }, "");
      try { localStorage.setItem(SESSION_KEY, data.token); } catch {}
      setToken(data.token); setUser(data.user); setPassword("");
      await refresh(data.token);
      setNotice(pending ? "You're signed in! Name this chart below to keep it in My AstroMYLA." : "Welcome to My AstroMYLA ✨");
    } catch (e: any) { setError(e.message || "Couldn't sign in. Please try again."); }
    finally { setBusy(false); }
  }

  async function store() {
    if (!pending || !token || !user) return;
    const clean = label.trim();
    if (!clean) { setError("Give this chart a name so you can find it later."); return; }
    setBusy(true); setError("");
    try {
      const data = await api("/api/account/charts", { method: "POST", body: JSON.stringify({ label: clean, birth: pending.birth }) });
      // Trust the server response, not an optimistic local-only save.
      setCharts(previous => [data.chart, ...previous]);
      setNotice(`Saved “${data.chart.label}” — including its calculated natal chart — to your account.`);
      setPending(null); setLabel("");
    } catch (e: any) { setError(e.message || "Couldn't save this chart. Please try again."); }
    finally { setBusy(false); }
  }

  async function erase(id: string, name: string) {
    if (!window.confirm(`Delete “${name}” from your saved charts?`)) return;
    setBusy(true); setError("");
    try {
      await api(`/api/account/charts/${encodeURIComponent(id)}`, { method: "DELETE" });
      setCharts(previous => previous.filter(item => item.id !== id));
      setNotice(`“${name}” was deleted.`);
    } catch (e: any) { setError(e.message || "Couldn't delete chart."); }
    finally { setBusy(false); }
  }

  async function logOut() {
    try { await api("/api/account/logout", { method: "POST", body: "{}" }); } catch {}
    try { localStorage.removeItem(SESSION_KEY); } catch {}
    setToken(""); setUser(null); setCharts([]); setOpen(false); setPending(null); setNotice("");
  }

  return <>
    <button type="button" className="accountButton" onClick={() => { setOpen(true); setError(""); void refresh(); }}>
      {user ? `✦ My AstroMYLA · ${user.display_name}` : "✦ My AstroMYLA"}
    </button>
    {open && <div className="checkoutOverlay" role="dialog" aria-modal="true" aria-label="My AstroMYLA saved charts" onClick={e => { if (e.target === e.currentTarget) setOpen(false); }}>
      <div className="accountModal mylaLibraryModal">
        <button type="button" className="checkoutClose" aria-label="Close" onClick={() => setOpen(false)}>×</button>
        <span className="premiumKicker">YOUR PRIVATE CHART LIBRARY</span>
        <h3>My AstroMYLA ✨</h3>
        {ready === null ? <p>Checking your chart library…</p> : ready === false ? <div className="libraryEmpty"><strong>Saved charts aren't available yet.</strong><p>Charts need a connected account database to stay saved between visits. Your free calculations still work; we won't pretend a chart was saved.</p><button type="button" className="secondary" onClick={() => window.location.reload()}>Try again</button></div> : !user ? <>
          <p className="muted">Save a chart once, return to it whenever you like, and reuse it for synastry and transits.</p>
          {pending && <p className="savePrompt">✨ Your chart is ready. Sign in or create an account, then choose its name.</p>}
          <form className="accountForm" onSubmit={authorize}>
            {screen === "sign-up" && <label>How should we call you?<input value={displayName} maxLength={80} onChange={e => setDisplayName(e.target.value)} autoComplete="nickname" /></label>}
            <label>Email<input type="email" required value={email} autoComplete="email" onChange={e => setEmail(e.target.value)} /></label>
            <label>Password<input type="password" required minLength={8} value={password} autoComplete={screen === "sign-in" ? "current-password" : "new-password"} onChange={e => setPassword(e.target.value)} /></label>
            {error && <p role="alert" className="error">{error}</p>}
            <button disabled={busy} type="submit" className="premiumCta">{busy ? "One moment…" : screen === "sign-in" ? "Sign in" : "Create my account"}</button>
          </form>
          <button type="button" className="linkButton" onClick={() => { setScreen(screen === "sign-in" ? "sign-up" : "sign-in"); setError(""); }}>
            {screen === "sign-in" ? "New here? Create an account" : "Already have an account? Sign in"}
          </button>
        </> : <>
          <p className="libraryHello">Hi, {user.display_name}. Your charts live here, linked to <strong>{user.email}</strong>.</p>
          {pending && <div className="quickSavePanel">
            <span className="premiumKicker">KEEP THIS CHART ✨</span>
            <h4>What should we call this chart?</h4>
            <p className="muted">We save your birth details and the calculated natal chart, so you can open it again anytime.</p>
            <label htmlFor="saved-chart-name">Chart name</label>
            <input id="saved-chart-name" autoFocus maxLength={80} value={label} placeholder="Me, Partner, Best friend…" onChange={e => setLabel(e.target.value)} onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); void store(); } }} />
            <div className="quickSaveActions"><button type="button" disabled={busy} onClick={store}>{busy ? "Saving…" : "Save to My AstroMYLA"}</button><button type="button" className="secondary" onClick={() => setPending(null)}>Maybe later</button></div>
          </div>}
          {notice && <p role="status" className="librarySuccess">✓ {notice}</p>}
          {error && <p role="alert" className="error">{error}</p>}
          <div className="libraryHeading"><h4>Your saved charts</h4><span>{charts.length} saved</span></div>
          {charts.length === 0 ? <p className="libraryEmpty">No charts saved yet. Generate a chart and tap <strong>Save this chart</strong> to start your collection.</p> : <div className="savedChartsList">
            {charts.map(c => <div className="savedChartItem" key={c.id}>
              <div className="savedChartInfo"><strong>{c.label}</strong><span>{c.birth?.birthplace || "Birthplace not named"} · {c.birth?.day}/{c.birth?.month}/{c.birth?.year}</span></div>
              <div className="savedChartActions">
                <button type="button" className="secondary" onClick={() => { onLoadBirth(c.birth, "A", c.natal_snapshot); setOpen(false); }}>{c.natal_snapshot ? "Open chart / Use as A" : "Use as A"}</button>
                <button type="button" className="secondary" onClick={() => { onLoadBirth(c.birth, "B", c.natal_snapshot); setOpen(false); }}>Use as B</button>
                <button type="button" className="dangerLink" disabled={busy} onClick={() => void erase(c.id, c.label)}>Delete</button>
              </div>
            </div>)}
          </div>}
          <button type="button" className="linkButton" onClick={logOut}>Sign out</button>
        </>}
      </div>
    </div>}
  </>;
}
