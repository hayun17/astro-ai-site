import React, { useState } from "react";

function Reason({ evidence }: { evidence?: string[] }) {
  if (!evidence?.length) return null;
  return <details className="mylaWhy"><summary>How we read your chart</summary><p>Based on {evidence.join(" · ")}. These are symbolic astrological interpretations, not facts about your personality or future.</p></details>;
}
function Tags({ items, limit = 4 }: { items?: string[]; limit?: number }) {
  return <div className="mylaTraitTags">{(items || []).slice(0, limit).map((s: string, i: number) => <span key={`${s}-${i}`}>{s}</span>)}</div>;
}

export function NatalSignatureSuite({ data }: { data: any }) {
  const [side, setSide] = useState<"spark" | "steadiness">("spark");
  if (!data) return null;
  const sig = data.signature, partner = data.partner_blueprint, split = data.attract_vs_need, manual = data.emotional_manual;
  return <section className="mylaStorySuite" aria-label="AstroMYLA signature insights">
    {sig && <article className="mylaStoryHero">
      <span className="mylaStarArt" aria-hidden="true">✧</span>
      <span className="mylaHeroEyebrow">✦ YOUR ASTROMYLA SIGNATURE</span>
      <h3>{sig.headline}</h3>
      <p className="mylaHeroDescription">{sig.summary}</p>
      <div className="mylaHeroDivider"/>
      <span className="mylaMicroLabel">YOUR VIBE IN FOUR WORDS</span>
      <Tags items={sig.core_energy} />
      <div className="mylaHeroFooter"><span>{sig.dominant_element} energy</span><span>{sig.dominant_modality} energy</span></div>
      <Reason evidence={sig.evidence}/>
    </article>}

    {partner && <article className="mylaEditorial mylaPartner">
      <div className="mylaEditorialIcon" aria-hidden="true">♡</div>
      <span className="mylaMicroLabel">THE RELATIONSHIP BLUEPRINT</span>
      <h3>So, who's your kind of person?</h3>
      <p className="mylaEditorialLead">Not a zodiac sign. A feeling. Your chart points toward someone who can meet you emotionally <em>and</em> keep things interesting.</p>
      <div className="mylaProfileLines">
        <div><span>THE WAY THEY LOVE</span><p>{partner.emotional_style}</p></div>
        <div><span>THE WAY THEY TALK</span><p>{partner.communication}</p></div>
        <div><span>THE SPARK</span><Tags items={partner.attraction} limit={3}/></div>
        <div><span>WHAT MAKES IT LAST</span><Tags items={partner.long_term} limit={3}/></div>
      </div>
      {partner.time_note && <p className="mylaQuietNote">{partner.time_note}</p>}
      <Reason evidence={partner.evidence}/>
    </article>}

    {split && <article className="mylaEditorial mylaAttraction">
      <span className="mylaMicroLabel">THE TWIST ✨</span>
      <h3>The spark isn't always the safe place.</h3>
      <p className="mylaEditorialLead">Sometimes the traits that catch your eye aren't the same ones that help love feel steady. Explore both sides of your chart.</p>
      <div className="mylaSwitch" role="group" aria-label="Attraction versus compatibility"><button type="button" aria-pressed={side === "spark"} className={side === "spark" ? "selected" : ""} onClick={() => setSide("spark")}>⚡ Who catches your eye</button><button type="button" aria-pressed={side === "steadiness"} className={side === "steadiness" ? "selected" : ""} onClick={() => setSide("steadiness")}>♡ Who feels right</button></div>
      <div className="mylaSwitchContent" key={side}>
        <span>{side === "spark" ? "WHAT PULLS YOU IN" : "WHAT HELPS YOU THRIVE"}</span>
        <Tags items={side === "spark" ? split.attract : split.need} limit={5}/>
        <p>{side === "spark" ? "The immediate magnetism — exciting, compelling, sometimes complicated." : "The qualities that can support trust, understanding and real consistency over time."}</p>
      </div>
      <Reason evidence={split.evidence}/>
    </article>}

    {manual && <article className="mylaEditorial mylaManual">
      <span className="mylaMicroLabel">A LITTLE NOTE TO SOMEONE WHO LOVES YOU</span>
      <h3>Here's how to love you well.</h3>
      <p className="mylaEditorialLead">Imagine handing your person a tiny note that says, “These things help me feel seen.”</p>
      <div className="mylaManualMain"><span>♡ MORE OF THIS, PLEASE</span><p>{(manual.helps || []).slice(0,3).join(" · ")}</p></div>
      <div className="mylaManualBottom"><div><span>WHEN THINGS GET TENSE</span><p>{manual.repair_style}</p></div><div><span>WHAT REASSURES YOU</span><p>{manual.reassurance}</p></div></div>
      <Reason evidence={manual.evidence}/>
    </article>}
  </section>;
}

export function MylaMatch({ match }: { match: any }) {
  if (!match?.themes?.length) return null;
  return <section className="mylaEditorial mylaMatchEditorial">
    <span className="mylaMicroLabel">MYLA MATCH ✦</span>
    <h3>Okay, here's the chemistry.</h3>
    <p className="mylaEditorialLead">Not a magic compatibility percentage — these are the patterns your two charts actually activate together.</p>
    <div className="mylaMatchFeatures">{match.themes.slice(0,4).map((theme:any,i:number) => <div key={`${theme.title}-${i}`}><span>0{i+1}</span><div><strong>{theme.title}</strong><p>{theme.description}</p><small>{theme.evidence}</small></div></div>)}</div>
    <p className="mylaQuietNote">{match.method_note}</p>
  </section>;
}
