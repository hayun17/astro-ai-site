import React, { useState } from "react";

type Question = "love" | "type" | "spark" | "needs";
const QUESTIONS: { id: Question; symbol: string; title: string; sub: string }[] = [
  {id:"love",symbol:"♡",title:"What's my love language?",sub:"Venus, Moon & Mercury"},
  {id:"type",symbol:"✧",title:"Who's actually my type?",sub:"Your 7th house & attraction"},
  {id:"spark",symbol:"⚡",title:"Why do I catch feelings?",sub:"Spark vs. stability"},
  {id:"needs",symbol:"☾",title:"How should someone love me?",sub:"Your emotional cheat sheet"},
];
function Evidence({items}:{items?:string[]}) {
  return <details className="cosmicEvidence"><summary>Show the placements behind this reading</summary>
    <p>{items?.length ? items.join(" · ") : "Not enough reliable placement data for a precise explanation."}</p>
    <small>These are symbolic astrology interpretations, not facts about someone's personality or a relationship's future.</small>
  </details>;
}
function Traits({values}:{values?:string[]}) {
  if(!values?.length) return null;
  return <div className="cosmicTraits">{values.slice(0,4).map((value,i)=><span key={`${value}-${i}`}>{value}</span>)}</div>;
}
function NatalBigThree({chart}:{chart:any}) {
  const sun=chart?.planets?.Sun, moon=chart?.planets?.Moon, rising=chart?.points?.Asc;
  const timeUnknown=Boolean(chart?.time_unknown);
  const items=[
    {icon:"☼",name:"Your Sun",value:sun?.sign||"—",meaning:"Your core drive"},
    {icon:"☾",name:"Your Moon",value:moon?.sign_uncertain ? "Time needed" : moon?.sign || "Time needed",meaning:"Your inner world"},
    {icon:"↑",name:"Your Rising",value:timeUnknown ? "Time needed" : rising?.sign||"Time needed",meaning:"Your first impression"},
  ];
  return <div className="cosmicBigThree" aria-label="Your Big Three">
    {items.map(item=><div key={item.name} className="cosmicBigThreeItem"><span className="cosmicPlanetIcon">{item.icon}</span><div><small>{item.name}</small><strong>{item.value}</strong><span>{item.meaning}</span></div></div>)}
  </div>;
}
export function NatalSignatureSuite({data,chart}:{data:any;chart?:any}) {
  const [active,setActive]=useState<Question>("love");
  if(!data) return null;
  const signature=data.signature || {};
  const blueprint=data.partner_blueprint || {};
  const split=data.attract_vs_need || {};
  const manual=data.emotional_manual || {};
  const venus=chart?.planets?.Venus?.sign;
  const moon=chart?.planets?.Moon?.sign_uncertain ? null : chart?.planets?.Moon?.sign;
  const mercury=chart?.planets?.Mercury?.sign;
  return <section className="cosmicSection" aria-label="Popular questions about your birth chart">
    <div className="cosmicHeading"><span className="cosmicEyebrow">✦ THE ASTROMYLA EDIT</span><h3>Okay, here's the interesting part.</h3>
      <p>Forget the generic horoscope. Let's answer the questions people actually ask about their chart.</p>
    </div>
    <NatalBigThree chart={chart}/>
    <div className="cosmicQuestionNav" role="tablist" aria-label="Explore your chart">
      {QUESTIONS.map(item=><button key={item.id} type="button" role="tab" id={`myla-tab-${item.id}`} aria-controls="myla-story" aria-selected={active===item.id} className={active===item.id?"cosmicQuestion active":"cosmicQuestion"} onClick={()=>setActive(item.id)}>
        <span className="cosmicQuestionIcon">{item.symbol}</span><span className="cosmicQuestionText"><strong>{item.title}</strong><small>{item.sub}</small></span><span className="cosmicQuestionArrow">↗</span>
      </button>)}
    </div>
    <article className={`cosmicAnswer cosmicAnswer-${active}`} id="myla-story" role="tabpanel" aria-labelledby={`myla-tab-${active}`}>
      <span className="cosmicEyebrow">YOUR CHART, WITHOUT THE FLUFF</span>
      {active==="love" && <>
        <h4>You don't love by just one rule.</h4>
        <p className="cosmicLead">{venus ? <>With <strong>Venus in {venus}</strong>, your style of showing affection has its own signature. </> : "Your Venus placement isn't available. "}
          {moon ? <>But your <strong>{moon} Moon</strong> says emotional safety matters just as much as attraction. </> : "An exact birth time can help resolve Moon-dependent details. "}
          {mercury ? <>And <strong>Mercury in {mercury}</strong>? That's the part that shapes how you talk things through.</> : null}</p>
        <div className="cosmicQuote"><span>WHAT FEELS LIKE LOVE TO YOU</span><p>{blueprint.emotional_style || "Honest care and room to be yourself."}</p></div>
        <div className="cosmicAnswerFoot"><span>How to communicate with you</span><p>{blueprint.communication || "Make intentions clear and listen closely."}</p></div>
        <Evidence items={[...(manual.evidence||[]),...(blueprint.evidence||[])]}/>
      </>}
      {active==="type" && <>
        <h4>So, who's actually your kind of person?</h4>
        <p className="cosmicLead">Not a destined Sun sign — more like the qualities that make a connection feel worth exploring. The chart suggests you might be drawn to people with this energy:</p>
        <Traits values={blueprint.attraction}/>
        <div className="cosmicQuote"><span>FOR THE LONG HAUL</span><Traits values={blueprint.long_term}/></div>
        {blueprint.time_note && <p className="cosmicNote">{blueprint.time_note}</p>}
        <Evidence items={blueprint.evidence}/>
      </>}
      {active==="spark" && <>
        <h4>The spark and the safe place can be different.</h4>
        <p className="cosmicLead">You know that instant click? It's worth asking whether the same qualities still feel good after the excitement settles. Here are the two sides your placements emphasize:</p>
        <div className="cosmicTwoSides"><div><span>⚡ WHAT CATCHES YOUR EYE</span><Traits values={split.attract}/></div><div><span>♡ WHAT FEELS GOOD OVER TIME</span><Traits values={split.need}/></div></div>
        <Evidence items={split.evidence}/>
      </>}
      {active==="needs" && <>
        <h4>Send this to someone who loves you.</h4>
        <p className="cosmicLead">“I don't need you to read my mind. I just feel more understood when there's {manual.helps?.[0] || "honest attention and care"}.”</p>
        <div className="cosmicQuote"><span>WHEN WE HAVE AN ARGUMENT</span><p>{manual.repair_style || "Give each other space to understand what happened."}</p></div>
        <div className="cosmicAnswerFoot"><span>What actually reassures you</span><p>{manual.reassurance}</p></div>
        <Evidence items={manual.evidence}/>
      </>}
    </article>
    <div className="cosmicIdentity"><span>✧ YOUR ASTROMYLA SIGNATURE</span><strong>{signature.headline || "A one-of-a-kind chart"}</strong><small>{signature.dominant_element && `${signature.dominant_element} emphasis`}{signature.dominant_modality && ` · ${signature.dominant_modality} emphasis`}</small></div>
  </section>;
}
export function MylaMatch({match}:{match:any}) {
  const [focus,setFocus]=useState(0);
  if(!match?.themes?.length)return null;
  const themes=(match.themes||[]).slice(0,4);
  const selected=themes[Math.min(focus,themes.length-1)];
  return <section className="cosmicMatch" aria-label="What connects your charts">
    <span className="cosmicEyebrow">♡ MYLA MATCH</span><h3>What's the actual chemistry here?</h3><p>These are the patterns that show up in your two charts — not a random “soulmate percentage”.</p>
    <div className="cosmicMatchNav">{themes.map((t:any,i:number)=><button type="button" key={`${i}-${t.title}`} className={focus===i?"active":""} onClick={()=>setFocus(i)}>{t.title}</button>)}</div>
    <div className="cosmicMatchStory"><strong>{selected.title}</strong><p>{selected.description}</p><small>{selected.evidence}</small></div>
  </section>;
}
