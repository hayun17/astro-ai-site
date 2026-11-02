import React, {useState} from "react";
type Chapter={house:number;headline:string;planets:string[];count:number;opening:string;story:string;question:string};
type Direction={visitor:string;host:string;available:boolean;summary:string;chapters:Chapter[]};
export default function HouseOverlayStories({stories,personA,personB}:{stories:any;personA:string;personB:string}) {
  const [which,setWhich]=useState<"a_to_b"|"b_to_a">("a_to_b");
  const [expanded,setExpanded]=useState(false);
  if(!stories) return null;
  const a=personA.trim()||"Person A",b=personB.trim()||"Person B";
  const selected:Direction|undefined=stories[which];
  const visitor=which==="a_to_b"?a:b, host=which==="a_to_b"?b:a;
  const chapters=selected?.chapters||[];
  return <section className="houseStoryV2" aria-label="Synastry house overlays in both directions">
    <span className="cosmicEyebrow">✧ REAL SYNASTRY, REAL HOUSES</span>
    <h3>Where you get under each other's skin.</h3>
    <p>The question isn't just “are we compatible?” It's <em>which part of each other's lives do we light up?</em> Let's look at both directions.</p>
    <div className="houseStorySwitcher" role="group" aria-label="Choose house overlay direction">
      <button type="button" className={which==="a_to_b"?"active":""} onClick={()=>{setWhich("a_to_b");setExpanded(false);}}><strong>{a} → {b}</strong><small>How {a} affects {b}</small></button>
      <button type="button" className={which==="b_to_a"?"active":""} onClick={()=>{setWhich("b_to_a");setExpanded(false);}}><strong>{b} → {a}</strong><small>How {b} affects {a}</small></button>
    </div>
    {!selected?.available?<div className="houseStoryFocus"><h4>We need {host}'s birth time for this part.</h4><p>House overlays depend on the exact birth time of the person receiving the planets. We won't invent placements.</p></div>:
    <div className="houseStoryFocus">
      <span className="cosmicEyebrow">{visitor.toUpperCase()} IN {host.toUpperCase()}'S CHART</span>
      {chapters.slice(0,expanded?4:1).map((ch,i)=><article key={ch.house} className="houseStoryFeature">
        <div className="houseStoryFeatureNum">{String(ch.house).padStart(2,"0")}</div>
        <div className="houseStoryFeatureCopy"><small>{i===0?"THE BIGGEST HOUSE ACTIVATION":"ANOTHER AREA YOU ACTIVATE"}</small><h4>{host}'s {ch.house}{ch.house===1?"st":ch.house===2?"nd":ch.house===3?"rd":"th"} house</h4>
        <div className="cosmicTraits">{ch.planets.map(p=><span key={p}>{visitor}'s {p}</span>)}</div>
        <p className="houseStoryFeatureOpening">{ch.opening}</p><p>{ch.story}</p></div>
      </article>)}
      {chapters.length>1&&<button type="button" className="houseStoryExpand" onClick={()=>setExpanded(!expanded)}>{expanded?"Show only the biggest influence ↑":`Explore ${Math.min(chapters.length-1,3)} more house themes ↓`}</button>}
    </div>}
    <details className="cosmicEvidence"><summary>What does a house overlay mean?</summary><p>The visitor brings their planets into the other person's natal houses. We count only calculated placements and don't predict anyone's actions. Exact receiving birth time is required.</p></details>
  </section>;
}
