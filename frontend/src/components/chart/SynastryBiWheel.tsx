import React, { useMemo, useState } from "react";
import "./chartStyles.css";

const SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"];
const SIGN_GLYPHS: Record<string,string> = {Aries:"♈",Taurus:"♉",Gemini:"♊",Cancer:"♋",Leo:"♌",Virgo:"♍",Libra:"♎",Scorpio:"♏",Sagittarius:"♐",Capricorn:"♑",Aquarius:"♒",Pisces:"♓"};
const BODY_ORDER = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto","TrueNode","Lilith","Chiron","Asc","MC","DSC","IC","Vertex"];
const BODY_GLYPHS: Record<string,string> = {Sun:"☉",Moon:"☽",Mercury:"☿",Venus:"♀",Mars:"♂",Jupiter:"♃",Saturn:"♄",Uranus:"♅",Neptune:"♆",Pluto:"♇",TrueNode:"☊",Lilith:"⚸",Chiron:"⚷",Asc:"ASC",MC:"MC",DSC:"DSC",IC:"IC",Vertex:"Vx"};

function wrap360(v:number){ const x=v%360; return x<0?x+360:x; }
function polar(cx:number,cy:number,r:number,deg:number){ const a=(deg-90)*Math.PI/180; return {x:cx+r*Math.cos(a),y:cy+r*Math.sin(a)}; }
function aspectStyle(name:string){
  const n=(name||"").toLowerCase();
  if(n==="conjunction") return {stroke:"#d85f9a",width:2.5,opacity:.78};
  if(n==="opposition") return {stroke:"#805ad5",width:2.3,opacity:.75};
  if(n==="square") return {stroke:"#e07a35",width:2.2,opacity:.72};
  if(n==="trine") return {stroke:"#4e8fc7",width:2.0,opacity:.66};
  if(n==="sextile") return {stroke:"#3c9f80",width:1.9,opacity:.62};
  return {stroke:"#a890bd",width:1.6,opacity:.45};
}
function chartObjects(chart:any){
  const merged:any={...(chart?.planets||{}),...(chart?.points||{})};
  return BODY_ORDER.flatMap((name)=>{
    const o=merged[name];
    if(!o || o.available===false || typeof o.lon!=="number") return [];
    if(chart?.time_unknown && (name==="Moon" || ["Asc","MC","DSC","IC","Vertex"].includes(name))) return [];
    return [{name,lon:Number(o.lon)}];
  });
}
function cuspArray(chart:any){
  const c=chart?.houses?.cusps;
  return Array.isArray(c)&&c.length===12 ? c.map(Number).filter(Number.isFinite) : [];
}

export default function SynastryBiWheel({chartA,chartB,aspects,aName,bName}:{chartA:any;chartB:any;aspects:any[];aName:string;bName:string}){
  const [inner,setInner]=useState<"A"|"B">("A");
  const innerChart=inner==="A"?chartA:chartB;
  const outerChart=inner==="A"?chartB:chartA;
  const innerName=inner==="A"?(aName||"Person A"):(bName||"Person B");
  const outerName=inner==="A"?(bName||"Person B"):(aName||"Person A");

  const size=700,cx=350,cy=350;
  const R_OUT=330,R_SIGN_IN=292,R_OUTER_PLANET=276,R_INNER_PLANET=233,R_HOUSE_IN=175,R_ASPECT=158;
  const asc=innerChart?.points?.Asc?.lon ?? innerChart?.houses?.ascendant;
  const rot=typeof asc==="number"?wrap360(270-asc):0;
  const innerBodies=useMemo(()=>chartObjects(innerChart),[innerChart]);
  const outerBodies=useMemo(()=>chartObjects(outerChart),[outerChart]);
  const cusps=useMemo(()=>cuspArray(innerChart),[innerChart]);

  const labels=(items:any[],baseR:number)=>items.map((o,idx)=>{
    const r=baseR-(idx%3)*10;
    const p=polar(cx,cy,r,wrap360(o.lon+rot));
    return {...o,...p,r};
  });
  const innerPts=labels(innerBodies,R_INNER_PLANET);
  const outerPts=labels(outerBodies,R_OUTER_PLANET);

  const aspectLines=(Array.isArray(aspects)?aspects:[]).slice(0,60).flatMap((a:any,idx:number)=>{
    const aObj=(chartA?.planets?.[a.a]||chartA?.points?.[a.a]);
    const bObj=(chartB?.planets?.[a.b]||chartB?.points?.[a.b]);
    if(!aObj||!bObj||typeof aObj.lon!=="number"||typeof bObj.lon!=="number") return [];
    if((chartA?.time_unknown&&a.a==="Moon")||(chartB?.time_unknown&&a.b==="Moon")) return [];
    const p1=polar(cx,cy,R_ASPECT,wrap360(Number(aObj.lon)+rot));
    const p2=polar(cx,cy,R_ASPECT,wrap360(Number(bObj.lon)+rot));
    return [{...a,...aspectStyle(a.aspect),p1,p2,key:`${a.a}-${a.aspect}-${a.b}-${idx}`}];
  });

  return <div className="synastryWheelShell">
    <div className="synastryWheelHeader">
      <div><strong>Synastry bi-wheel</strong><span>Same zodiac, both charts layered together.</span></div>
      <button type="button" className="secondary synastrySwap" onClick={()=>setInner(inner==="A"?"B":"A")}>Swap inner chart</button>
    </div>
    <div className="synastryLegend">
      <span className="legendInner"><i />{innerName} · inner + houses</span>
      <span className="legendOuter"><i />{outerName} · outer</span>
      <span className="muted">Inter-chart aspects cross the center</span>
    </div>
    <svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Synastry bi-wheel for ${aName||"Person A"} and ${bName||"Person B"}`} className="synastryBiWheel">
      <defs>
        <radialGradient id="synBg" cx="50%" cy="45%" r="65%"><stop offset="0%" stopColor="#fffdfd"/><stop offset="75%" stopColor="#fbf5ff"/><stop offset="100%" stopColor="#f8edf5"/></radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={R_OUT} fill="url(#synBg)" stroke="#b9a0d8" strokeWidth="3"/>
      <circle cx={cx} cy={cy} r={R_SIGN_IN} fill="none" stroke="#c8b7dd" strokeWidth="2"/>
      <circle cx={cx} cy={cy} r={252} fill="none" stroke="#e1d4e9" strokeWidth="1.5"/>
      <circle cx={cx} cy={cy} r={205} fill="none" stroke="#d5c6e4" strokeWidth="1.2"/>
      <circle cx={cx} cy={cy} r={R_ASPECT+8} fill="rgba(255,255,255,.52)" stroke="#eadfea" strokeWidth="1"/>

      {SIGNS.map((sign,i)=>{
        const boundary=polar(cx,cy,R_OUT,wrap360(i*30+rot));
        const boundaryIn=polar(cx,cy,R_SIGN_IN,wrap360(i*30+rot));
        const lab=polar(cx,cy,(R_OUT+R_SIGN_IN)/2,wrap360(i*30+15+rot));
        return <g key={sign}><line x1={boundaryIn.x} y1={boundaryIn.y} x2={boundary.x} y2={boundary.y} stroke="#baa2d3" strokeWidth="1.4"/><text x={lab.x} y={lab.y} textAnchor="middle" dominantBaseline="middle" fontSize="21" fill="#5c3b70">{SIGN_GLYPHS[sign]}</text></g>;
      })}

      {cusps.map((c:number,i:number)=>{
        const p1=polar(cx,cy,R_HOUSE_IN,wrap360(c+rot)); const p2=polar(cx,cy,R_SIGN_IN,wrap360(c+rot));
        const lp=polar(cx,cy,190,wrap360(c+rot+8));
        return <g key={`h-${i}`}><line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke="#a995c2" strokeWidth={i===0||i===3||i===6||i===9?2.2:1} opacity=".78"/><text x={lp.x} y={lp.y} textAnchor="middle" dominantBaseline="middle" fontSize="10" fill="#7a628b">{i+1}</text></g>;
      })}

      {aspectLines.map((l:any)=><line key={l.key} x1={l.p1.x} y1={l.p1.y} x2={l.p2.x} y2={l.p2.y} stroke={l.stroke} strokeWidth={l.width} opacity={l.opacity}/>) }

      {innerPts.map((p:any)=><g key={`in-${p.name}`}><circle cx={p.x} cy={p.y} r="11" fill="#f1e9ff" stroke="#8766ad" strokeWidth="1.2"/><text x={p.x} y={p.y+.5} textAnchor="middle" dominantBaseline="middle" fontSize={p.name.length>3?8:15} fontWeight="700" fill="#5c3b70">{BODY_GLYPHS[p.name]||p.name.slice(0,2)}</text></g>)}
      {outerPts.map((p:any)=><g key={`out-${p.name}`}><circle cx={p.x} cy={p.y} r="11" fill="#fff0f6" stroke="#cf6b9b" strokeWidth="1.2"/><text x={p.x} y={p.y+.5} textAnchor="middle" dominantBaseline="middle" fontSize={p.name.length>3?8:15} fontWeight="700" fill="#8e3f68">{BODY_GLYPHS[p.name]||p.name.slice(0,2)}</text></g>)}
      <text x={cx} y={cy-8} textAnchor="middle" fontSize="17" fontWeight="800" fill="#4b2b63">{innerName}</text>
      <text x={cx} y={cy+14} textAnchor="middle" fontSize="11" fill="#856b94">inner chart · {outerName} outside</text>
    </svg>
    <p className="muted synastryWheelNote">The inner person’s houses are shown so you can see where the outer person lands. Use “Swap inner chart” to view the house overlay in the other direction.</p>
  </div>;
}
