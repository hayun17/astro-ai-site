import React from "react";

const LABELS: Record<string,string> = {
  emotional: "Emotional Resonance",
  communication: "Communication",
  chemistry: "Chemistry & Attraction",
  stability: "Stability & Commitment",
  growth: "Growth & Transformation",
  friction: "Friction / Activation",
};

export function ConnectionProfile({ profile }: { profile: any }) {
  if (!profile?.scores) return null;
  return (
    <section className="insightCard connectionProfile">
      <div className="insightKicker">Connection Profile ✨</div>
      <h3>{(profile.keywords || []).join(" · ")}</h3>
      <p>{profile.summary}</p>
      <div className="scoreGrid">
        {Object.entries(profile.scores).map(([key, value]) => (
          <div className="scoreRow" key={key}>
            <div className="scoreLabel"><span>{LABELS[key] || key}</span><b>{Number(value)}%</b></div>
            <div className="scoreTrack"><div className={`scoreFill score-${key}`} style={{width:`${Number(value)}%`}} /></div>
          </div>
        ))}
      </div>
      <details className="scoreMethod"><summary>How is this calculated?</summary><p>{profile.method_note}</p></details>
    </section>
  );
}

export function CompositeSignature({ signature }: { signature: any }) {
  if (!signature) return null;
  const a = signature.strongest_aspect;
  return (
    <section className="insightCard compositeSignature">
      <div className="insightKicker">Relationship Identity</div>
      <h3>{signature.headline || "Layered · Evolving"}</h3>
      <div className="keywordChips">{(signature.keywords || []).map((k:string)=><span key={k}>{k}</span>)}</div>
      {a && <p className="strongestSignature"><b>Strongest composite signature:</b> {a.p1} {a.aspect} {a.p2} · orb {Number(a.orb).toFixed(2)}°</p>}
      <p className="muted">{signature.method_note}</p>
    </section>
  );
}
