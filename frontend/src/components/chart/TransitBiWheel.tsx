import React, { useMemo } from "react";
import "./chartStyles.css";

const SIGNS=["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"];
const SIGN_GLYPHS:Record<string,string>={Aries:"♈",Taurus:"♉",Gemini:"♊",Cancer:"♋",Leo:"♌",Virgo:"♍",Libra:"♎",Scorpio:"♏",Sagittarius:"♐",Capricorn:"♑",Aquarius:"♒",Pisces:"♓"};
const BODY_ORDER=["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto","TrueNode","Chiron","Asc","MC","DSC","IC"];
const GLYPHS:Record<string,string>={Sun:"☉",Moon:"☽",Mercury:"☿",Venus:"♀",Mars:"♂",Jupiter:"♃",Saturn:"♄",Uranus:"♅",Neptune:"♆",Pluto:"♇",TrueNode:"☊",Chiron:"⚷",Asc:"ASC",MC:"MC",DSC:"DSC",IC:"IC"};
function wrap(v:number){const x=v%360;return x<0?x+360:x}
function polar(cx:number,cy:number,r:number,d:number){const a=(d-90)*Math.PI/180;return{x:cx+r*Math.cos(a),y:cy+r*Math.sin(a)}}
function style(a:string){const n=(a||"").toLowerCase();if(n==="conjunction")return{stroke:"#d85f9a",w:2.5};if(n==="opposition")return{stroke:"#805ad5",w:2.3};if(n==="square")return{stroke:"#e07a35",w:2.2};if(n==="trine")return{stroke:"#4e8fc7",w:2};return{stroke:"#3c9f80",w:1.8}}
function natalObjects(chart:any){const all={...(chart?.planets||{}),...(chart?.points||{})};return BODY_ORDER.flatMap(name=>{const x=all[name];if(!x||x.available===false||typeof x.lon!=="number")return[];if(chart?.time_unknown&&["Moon","Asc","MC","DSC","IC"].includes(name))return[];return[{name,lon:Number(x.lon)}]})}
function transitObjects(t:any){return BODY_ORDER.flatMap(name=>{const x=t?.planets?.[name];return x&&typeof x.lon==="number"?[{name,lon:Number(x.lon)}]:[]})}

export default function TransitBiWheel({natal,transits}:{natal:any;transits:any}){
  const size=700,cx=350,cy=350,R_OUT=330,R_SIGN=292,R_TRANSIT=276,R_NATAL=232,R_ASPECT=158,R_HOUSE=175;
  const asc=natal?.points?.Asc?.lon??natal?.houses?.ascendant;
  const rot=typeof asc==="number"?wrap(270-asc):0;
  const natalPts=useMemo(()=>natalObjects(natal).map((o,i)=>({...o,...polar(cx,cy,R_NATAL-(i%3)*10,wrap(o.lon+rot))})),[natal,rot]);
  const transitPts=useMemo(()=>transitObjects(transits).map((o,i)=>({...o,...polar(cx,cy,R_TRANSIT-(i%3)*9,wrap(o.lon+rot))})),[transits,rot]);
  const cusps=Array.isArray(natal?.houses?.cusps)&&natal.houses.cusps.length===12?natal.houses.cusps.map(Number):[];
  const lines=(transits?.aspects||[]).slice(0,50).flatMap((a:any,i:number)=>{const t=transits?.planets?.[a.transit];const n=natal?.planets?.[a.natal]||natal?.points?.[a.natal];if(!t||!n||typeof t.lon!=="number"||typeof n.lon!=="number")return[];const p1=polar(cx,cy,R_ASPECT,wrap(Number(t.lon)+rot)),p2=polar(cx,cy,R_ASPECT,wrap(Number(n.lon)+rot));return[{...style(a.aspect),p1,p2,key:`${a.transit}-${a.aspect}-${a.natal}-${i}`}];});
  return <div className="synastryWheelShell transitWheelShell">
    <div className="synastryWheelHeader"><div><strong>Natal + transit bi-wheel</strong><span>Your natal chart inside, current sky outside.</span></div><span className="transitMoment">{transits?.target_utc?new Date(transits.target_utc).toLocaleString():"Current sky"}</span></div>
    <div className="synastryLegend"><span className="legendInner"><i/>Natal · inner + houses</span><span className="legendOuter"><i/>Transits · outer</span><span className="muted">Active transit aspects cross the center</span></div>
    <svg viewBox={`0 0 ${size} ${size}`} className="synastryBiWheel" role="img" aria-label="Natal and current transit bi-wheel">
      <defs><radialGradient id="trBg" cx="50%" cy="45%" r="65%"><stop offset="0%" stopColor="#fffdfd"/><stop offset="75%" stopColor="#f8f7ff"/><stop offset="100%" stopColor="#f5edf8"/></radialGradient></defs>
      <circle cx={cx} cy={cy} r={R_OUT} fill="url(#trBg)" stroke="#b9a0d8" strokeWidth="3"/><circle cx={cx} cy={cy} r={R_SIGN} fill="none" stroke="#c8b7dd" strokeWidth="2"/><circle cx={cx} cy={cy} r="252" fill="none" stroke="#e1d4e9" strokeWidth="1.5"/><circle cx={cx} cy={cy} r="205" fill="none" stroke="#d5c6e4" strokeWidth="1.2"/><circle cx={cx} cy={cy} r={R_ASPECT+8} fill="rgba(255,255,255,.52)" stroke="#eadfea"/>
      {SIGNS.map((sign,i)=>{const a=polar(cx,cy,R_OUT,wrap(i*30+rot)),b=polar(cx,cy,R_SIGN,wrap(i*30+rot)),l=polar(cx,cy,(R_OUT+R_SIGN)/2,wrap(i*30+15+rot));return <g key={sign}><line x1={b.x} y1={b.y} x2={a.x} y2={a.y} stroke="#baa2d3" strokeWidth="1.4"/><text x={l.x} y={l.y} textAnchor="middle" dominantBaseline="middle" fontSize="21" fill="#5c3b70">{SIGN_GLYPHS[sign]}</text></g>})}
      {cusps.map((c:number,i:number)=>{const p1=polar(cx,cy,R_HOUSE,wrap(c+rot)),p2=polar(cx,cy,R_SIGN,wrap(c+rot)),lp=polar(cx,cy,190,wrap(c+rot+8));return <g key={i}><line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke="#a995c2" strokeWidth={i%3===0?2.2:1}/><text x={lp.x} y={lp.y} textAnchor="middle" dominantBaseline="middle" fontSize="10" fill="#7a628b">{i+1}</text></g>})}
      {lines.map((l:any)=><line key={l.key} x1={l.p1.x} y1={l.p1.y} x2={l.p2.x} y2={l.p2.y} stroke={l.stroke} strokeWidth={l.w} opacity=".72"/>)}
      {natalPts.map((p:any)=><g key={`n-${p.name}`}><circle cx={p.x} cy={p.y} r="11" fill="#f1e9ff" stroke="#8766ad"/><text x={p.x} y={p.y+.5} textAnchor="middle" dominantBaseline="middle" fontSize={p.name.length>3?8:15} fontWeight="700" fill="#5c3b70">{GLYPHS[p.name]||p.name.slice(0,2)}</text></g>)}
      {transitPts.map((p:any)=><g key={`t-${p.name}`}><circle cx={p.x} cy={p.y} r="11" fill="#fff0f6" stroke="#cf6b9b"/><text x={p.x} y={p.y+.5} textAnchor="middle" dominantBaseline="middle" fontSize={p.name.length>3?8:15} fontWeight="700" fill="#8e3f68">{GLYPHS[p.name]||p.name.slice(0,2)}</text></g>)}
      <text x={cx} y={cy-8} textAnchor="middle" fontSize="17" fontWeight="800" fill="#4b2b63">Your natal chart</text><text x={cx} y={cy+14} textAnchor="middle" fontSize="11" fill="#856b94">transiting sky outside</text>
    </svg>
  </div>
}
