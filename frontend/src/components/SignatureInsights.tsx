import React from "react";

function Chips({ values }: { values?: string[] }) {
  if (!values?.length) return null;
  return <div className="keywordChips">{values.map((x) => <span key={x}>{x}</span>)}</div>;
}

function Evidence({ values }: { values?: string[] }) {
  if (!values?.length) return null;
  return <details className="scoreMethod"><summary>Why AstroMYLA sees this</summary><p>{values.join(" · ")}</p></details>;
}

export function NatalSignatureSuite({ data }: { data: any }) {
  if (!data) return null;
  const sig = data.signature;
  const partner = data.partner_blueprint;
  const split = data.attract_vs_need;
  const manual = data.emotional_manual;
  return (
    <section className="signatureSuite" aria-label="AstroMYLA signature insights">
      {sig && <article className="insightCard signatureHero">
        <div className="insightKicker">Your AstroMYLA Signature ✨</div>
        <h3>{sig.headline}</h3>
        <p>{sig.summary}</p>
        <div className="signatureMiniGrid">
          <div><strong>Core energy</strong><Chips values={sig.core_energy} /></div>
          <div><strong>Needs</strong><Chips values={sig.needs} /></div>
          <div><strong>Watch-outs</strong><ul>{(sig.watch_outs || []).map((x:string)=><li key={x}>{x}</li>)}</ul></div>
        </div>
        <div className="signatureMeta"><span>{sig.dominant_element} emphasis</span><span>{sig.dominant_modality} emphasis</span></div>
        <Evidence values={sig.evidence} />
        <p className="muted signatureMethod">{sig.method_note}</p>
      </article>}

      <div className="signatureTwoCol">
        {partner && <article className="insightCard">
          <div className="insightKicker">Relationship Blueprint</div>
          <h3>{partner.headline}</h3>
          <p>{partner.summary}</p>
          <div className="blueprintRows">
            <div><strong>Emotionally</strong><span>{partner.emotional_style}</span></div>
            <div><strong>Communication</strong><span>{partner.communication}</span></div>
            <div><strong>Attraction</strong><Chips values={partner.attraction} /></div>
            <div><strong>Long-term energy</strong><Chips values={partner.long_term} /></div>
            <div><strong>Best match energy</strong><Chips values={partner.best_match_energy} /></div>
          </div>
          {partner.time_note && <p className="muted">{partner.time_note}</p>}
          <Evidence values={partner.evidence} />
        </article>}

        {split && <article className="insightCard attractNeedCard">
          <div className="insightKicker">Attraction vs Compatibility</div>
          <h3>Who You Attract vs Who You Actually Need</h3>
          <p>{split.summary}</p>
          <div className="attractNeedGrid">
            <div><strong>Who you attract</strong><Chips values={split.attract} /></div>
            <div><strong>Who you thrive with</strong><Chips values={split.need} /></div>
          </div>
          <Evidence values={split.evidence} />
        </article>}
      </div>

      {manual && <article className="insightCard emotionalManual">
        <div className="insightKicker">How to love you well</div>
        <h3>{manual.headline}</h3>
        <div className="manualGridCards">
          <div><strong>More of this</strong><ul>{(manual.helps || []).map((x:string)=><li key={x}>{x}</li>)}</ul></div>
          <div><strong>Handle with care</strong><ul>{(manual.avoid || []).map((x:string)=><li key={x}>{x}</li>)}</ul></div>
          <div><strong>Repair style</strong><p>{manual.repair_style}</p></div>
          <div><strong>Reassurance that lands</strong><p>{manual.reassurance}</p></div>
        </div>
        <Evidence values={manual.evidence} />
      </article>}
    </section>
  );
}

export function MylaMatch({ match }: { match: any }) {
  if (!match?.themes?.length) return null;
  return (
    <section className="insightCard mylaMatchCard">
      <div className="insightKicker">Myla Match ✨</div>
      <h3>{match.headline}</h3>
      <p>{match.summary}</p>
      <div className="mylaThemeGrid">
        {match.themes.map((theme:any) => <article key={`${theme.title}-${theme.evidence}`}>
          <strong>{theme.title}</strong>
          <p>{theme.description}</p>
          <span>{theme.evidence}</span>
        </article>)}
      </div>
      <p className="muted signatureMethod">{match.method_note}</p>
    </section>
  );
}
