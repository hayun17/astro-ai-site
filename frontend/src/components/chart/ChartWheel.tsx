import React, { useMemo } from "react";
import "./chartStyles.css";
import ChartBackground from "./ChartBackground.png";

type Props = {
  chart: any; // backend chart json
};

const SIGNS = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
];

const SIGN_GLYPHS: Record<string, string> = {
  Aries: "♈", Taurus: "♉", Gemini: "♊", Cancer: "♋", Leo: "♌", Virgo: "♍",
  Libra: "♎", Scorpio: "♏", Sagittarius: "♐", Capricorn: "♑", Aquarius: "♒", Pisces: "♓",
};

const BODY_ORDER = [
  "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
  "TrueNode", "Lilith", "Chiron", "Vertex", "Fortune",
  "Asc", "MC", "DSC", "IC",
];

const BODY_GLYPHS: Record<string, string> = {
  Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂", Jupiter: "♃", Saturn: "♄",
  Uranus: "♅", Neptune: "♆", Pluto: "♇",
  TrueNode: "☊",
  Lilith: "⚸",
  Chiron: "⚷",
  Vertex: "Vx",
  Fortune: "⊗",
  Asc: "ASC",
  MC: "MC",
  DSC: "DSC",
  IC: "IC",
};

function wrap360(d: number) {
  const x = d % 360;
  return x < 0 ? x + 360 : x;
}

function astroDegToSvgRad(astroDeg: number) {
  return (astroDeg - 90) * (Math.PI / 180);
}

function polar(cx: number, cy: number, r: number, astroDeg: number) {
  const a = astroDegToSvgRad(astroDeg);
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

function degToDegMin(deg: number) {
  const d = Math.floor(deg);
  const m = Math.round((deg - d) * 60);
  const mm = m === 60 ? 0 : m;
  const dd = m === 60 ? d + 1 : d;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${dd}°${pad(mm)}′`;
}

function lonToSignDeg(lon: number) {
  const L = wrap360(lon);
  const signIndex = Math.floor(L / 30);
  const degInSign = L - signIndex * 30;
  return { sign: SIGNS[signIndex], degInSign };
}

type AspectRow = {
  p1: string;
  p2: string;
  aspect: string;
  orb: number;
};

function aspectStyle(aspect: string) {
  const a = aspect.toLowerCase();
  const harmonious = a === "trine" || a === "sextile";
  const challenging = a === "square" || a === "opposition";

  if (harmonious) return { stroke: "#ff86b8", width: 2.8, opacity: 0.87 };
  if (challenging) return { stroke: "#9f7cff", width: 2.8, opacity: 0.87 };
  return { stroke: "#d8c8ff", width: 2.4, opacity: 0.55 };
}

export default function ChartWheel({ chart }: Props) {
  const { ascDeg, cusps, bodies, titleName, aspects } = useMemo(() => {
    const asc =
      chart?.houses?.ascendant ??
      chart?.points?.Asc?.lon ??
      chart?.points?.ASC?.lon ??
      null;

    const cuspsArr: number[] = chart?.houses?.cusps ?? chart?.houses?.house_cusps ?? [];
    const planetsObj = chart?.planets ?? {};
    const pointsObj = chart?.points ?? {};
    const aspectsObj = chart?.aspects ?? {};

    const merged: any = { ...planetsObj };
    for (const k of Object.keys(pointsObj || {})) {
      merged[k] = { ...pointsObj[k], available: true };
    }

    return {
      ascDeg: typeof asc === "number" ? wrap360(asc) : null,
      cusps: Array.isArray(cuspsArr)
        ? cuspsArr.map((v: any) => Number(v)).filter((n) => Number.isFinite(n))
        : [],
      bodies: merged,
      titleName: chart?.name ? String(chart.name) : "",
      aspects: aspectsObj,
    };
  }, [chart]);

  const rot = useMemo(() => {
    if (ascDeg == null) return 0;
    return wrap360(270 - ascDeg);
  }, [ascDeg]);

  const size = 620;
  const cx = size / 2;
  const cy = size / 2;

  // ✅ senin bulduğun hizalama
  const R_OUT = 292;
  const R_SIGN_IN = 262;

  const R_HOUSE = 205;
  const R_PLANET = 245;
  const R_ASPECT = 165;
  const R_CENTER = 125;

  const BG_PAD = 36;
  const BG_OPACITY = 0.95;

  /**
   * ✅ KATMAN KATMAN OFFSET SİSTEMİ
   * Her şeyi ayrı ayrı oynat.
   */
  const OUTER_DX = 7, OUTER_DY = 0;     // en dış çember
  const SIGN_DX  = 8, SIGN_DY  = 4;     // 2. ring + sign lines + sign labels
  const HOUSE_DX = 0, HOUSE_DY = 0;     // house çizgileri + numaralar
  const GUIDE_DX = 0, GUIDE_DY = 0;     // guide circle (aspect guide vs)
  const ASPECT_DX = 0, ASPECT_DY = 0;   // açı çizgileri (planet ile senkronlanacak)
  const ASC_DX = 0, ASC_DY = 0;         // ASC çizgisi/yazısı
  const PLANET_DX = 0, PLANET_DY = 0;   // gezegenler + degree label
  const CENTER_DX = 0, CENTER_DY = 0;   // center circle + title

  // ✅ görünürlük/kontrast arttırılmış palette
  const theme = {
    stroke1: "#bfa6ff",
    stroke2: "#b79dff",
    text: "#4b2b63",
    softText: "#7b5f95",
    planetDot: "#ff93bf",
    houseLine: "#a88cff",
    signLine: "#9f84ff",
    houseNumber: "#3e2158",
  };

  // ✅ house numaraları için ayar (okunurluk)
  const HOUSE_NUM_FONT = 12.5;
  const HOUSE_NUM_WEIGHT: React.CSSProperties["fontWeight"] = 800;
  const HOUSE_NUM_OPACITY = 1;
  const HOUSE_NUM_BG = true;
  const HOUSE_NUM_BG_R = 10.5;
  const HOUSE_NUM_BG_FILL = "rgba(255,255,255,0.78)";
  const HOUSE_NUM_BG_STROKE = "rgba(191,166,255,0.55)";
  const HOUSE_NUM_BG_STROKE_W = 1;

  // ✅ sign ring stroke (house çizgilerini burada bitiriyorduk)
  const SIGN_RING_STROKE = 10;
  const HOUSE_END_R = R_SIGN_IN + SIGN_RING_STROKE / 2 - 1;

  const signLines = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => {
      const deg = wrap360(i * 30 + rot);
      const p1 = polar(cx, cy, R_SIGN_IN, deg);
      const p2 = polar(cx, cy, R_OUT, deg);
      return { deg, p1, p2 };
    });
  }, [cx, cy, rot, R_SIGN_IN, R_OUT]);

  const signLabels = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => {
      const deg = wrap360(i * 30 + 15 + rot);
      const p = polar(cx, cy, (R_OUT + R_SIGN_IN) / 2, deg);
      const sign = SIGNS[i];
      return { sign, glyph: SIGN_GLYPHS[sign], x: p.x, y: p.y };
    });
  }, [cx, cy, rot, R_OUT, R_SIGN_IN]);

  const houseLines = (cusps?.length === 12 ? cusps : []).map((c, idx) => {
    const deg = wrap360(c + rot);
    const p1 = polar(cx, cy, R_CENTER - 6, deg);
    const p2 = polar(cx, cy, HOUSE_END_R, deg);
    return { idx: idx + 1, deg, p1, p2 };
  });

  const ascLine =
    ascDeg != null
      ? (() => {
          const deg = wrap360(ascDeg + rot);
          const p1 = polar(cx, cy, R_CENTER - 6, deg);
          const p2 = polar(cx, cy, R_OUT, deg);
          const labelP = polar(cx, cy, R_OUT + 16, deg);
          return { deg, p1, p2, labelP };
        })()
      : null;

  const planetPoints = useMemo(() => {
    if (!bodies) return [];

    const pts: Array<{
      name: string;
      lon: number;
      x: number;
      y: number;
      label: string;
      degMin: string;
    }> = [];

    let placed = 0;

    for (const name of BODY_ORDER) {
      const d = bodies[name];
      if (!d) continue;
      if (d.available === false) continue;

      const lon = d.lon;
      if (typeof lon !== "number" || Number.isNaN(lon)) continue;

      const r = R_PLANET - (placed % 3) * 12;
      const deg = wrap360(lon + rot);
      const p = polar(cx, cy, r, deg);

      const glyph = BODY_GLYPHS[name] || name.slice(0, 2);
      const degInSign =
        typeof d.deg_in_sign === "number" ? d.deg_in_sign : lonToSignDeg(lon).degInSign;

      pts.push({
        name,
        lon,
        x: p.x,
        y: p.y,
        label: glyph,
        degMin: degToDegMin(degInSign),
      });

      placed += 1;
    }

    return pts;
  }, [bodies, rot, cx, cy, R_PLANET]);

  const pointByName = useMemo(() => {
    const map = new Map<string, { x: number; y: number; lon: number }>();
    for (const p of planetPoints) map.set(p.name, { x: p.x, y: p.y, lon: p.lon });
    return map;
  }, [planetPoints]);

  // ✅ AÇI ÇİZGİLERİ: içte kalması için güvenli radius (center'dan küçük)
  const R_ASPECT_DRAW = Math.min(R_ASPECT, R_CENTER - 10);

  const aspectLines = useMemo(() => {
    const out: Array<{
      key: string;
      x1: number; y1: number; x2: number; y2: number;
      stroke: string; width: number; opacity: number;
    }> = [];

    const maxOrb = 6.0;
    const maxLines = 30;

    const planetAs: AspectRow[] = Array.isArray(aspects?.planet_aspects) ? aspects.planet_aspects : [];
    const otherAs: AspectRow[] = Array.isArray(aspects?.other_aspects) ? aspects.other_aspects : [];
    const merged = [...planetAs, ...otherAs];

    const seen = new Set<string>();

    for (const a of merged) {
      if (!a?.p1 || !a?.p2 || !a?.aspect) continue;
      const orb = typeof a.orb === "number" ? a.orb : 999;
      if (orb > maxOrb) continue;

      const keyRaw = [a.p1, a.p2].sort().join("|") + "|" + a.aspect;
      if (seen.has(keyRaw)) continue;
      seen.add(keyRaw);

      const p1 = pointByName.get(a.p1);
      const p2 = pointByName.get(a.p2);
      if (!p1 || !p2) continue;

      const d1 = wrap360(p1.lon + rot);
      const d2 = wrap360(p2.lon + rot);

      // ✅ iç çemberde çiz
      const q1 = polar(cx, cy, R_ASPECT_DRAW, d1);
      const q2 = polar(cx, cy, R_ASPECT_DRAW, d2);

      const st = aspectStyle(a.aspect);

      out.push({
        key: keyRaw,
        x1: q1.x, y1: q1.y,
        x2: q2.x, y2: q2.y,
        stroke: st.stroke,
        width: st.width,
        opacity: st.opacity,
      });

      if (out.length >= maxLines) break;
    }

    return out;
  }, [aspects, pointByName, rot, cx, cy, R_ASPECT_DRAW]);

  return (
    <div
      className="chartWheelWrap"
      style={{
        width: "100%",
        height: "100%",
        borderRadius: 18,
        border: `1px solid ${theme.stroke1}`,
        background:
          "radial-gradient(900px 600px at 20% 10%, rgba(255,234,244,0.32) 0%, rgba(255,234,244,0) 60%)," +
          "radial-gradient(900px 600px at 80% 0%, rgba(232,244,255,0.22) 0%, rgba(232,244,255,0) 60%)," +
          "rgba(255,255,255,0.78)",
        boxShadow: "0 10px 30px rgba(0,0,0,0.06)",
        padding: 6,
      }}
    >
      <svg
        viewBox={`0 0 ${size} ${size}`}
        width="100%"
        height="100%"
        role="img"
        aria-label="Natal chart wheel"
        style={{ display: "block" }}
      >
        <defs>
          <clipPath id="wheelClip">
            <circle cx={cx} cy={cy} r={R_OUT - 1} />
          </clipPath>

          <radialGradient id="bgTint" cx="50%" cy="40%" r="70%">
            <stop offset="0%" stopColor="rgba(255, 214, 234, 0.18)" />
            <stop offset="55%" stopColor="rgba(208, 196, 255, 0.16)" />
            <stop offset="100%" stopColor="rgba(255, 255, 255, 0.10)" />
          </radialGradient>
        </defs>

        {/* Background */}
        <g clipPath="url(#wheelClip)">
          <image
            href={ChartBackground}
            x={-BG_PAD}
            y={-BG_PAD}
            width={size + BG_PAD * 2}
            height={size + BG_PAD * 2}
            preserveAspectRatio="xMidYMid slice"
            opacity={BG_OPACITY}
            style={{
              filter: "saturate(0.75) contrast(0.90) brightness(1.06) hue-rotate(-10deg)",
            }}
          />
          <rect x={0} y={0} width={size} height={size} fill="url(#bgTint)" />
        </g>

        {/* OUTER ring (separate move) */}
        <g transform={`translate(${OUTER_DX}, ${OUTER_DY})`}>
          <circle
            cx={cx}
            cy={cy}
            r={R_OUT}
            fill="rgba(255,230,242,0.18)"
            stroke={theme.stroke1}
            strokeWidth={6}
            opacity={0.98}
          />
        </g>

        {/* SIGN system (2nd ring + sign lines + sign labels) */}
        <g transform={`translate(${SIGN_DX}, ${SIGN_DY})`}>
          <circle
            cx={cx}
            cy={cy}
            r={R_SIGN_IN}
            fill="rgba(245,241,255,0.14)"
            stroke={theme.stroke2}
            strokeWidth={SIGN_RING_STROKE}
            opacity={0.98}
          />

          {signLines.map((l, i) => (
            <line
              key={`sign-${i}`}
              x1={l.p1.x}
              y1={l.p1.y}
              x2={l.p2.x}
              y2={l.p2.y}
              stroke={theme.signLine}
              strokeWidth={2.6}
              opacity={0.95}
            />
          ))}

          {signLabels.map((s) => (
            <text
              key={s.sign}
              x={s.x}
              y={s.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="22"
              fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto"
              fill={theme.text}
              opacity={0.92}
            >
              {s.glyph}
            </text>
          ))}
        </g>

        {/* GUIDE ring(s) like aspect guide circle */}
        <g transform={`translate(${GUIDE_DX}, ${GUIDE_DY})`}>
          <circle
            cx={cx}
            cy={cy}
            r={R_ASPECT}
            fill="none"
            stroke="rgba(217,204,255,0.22)"
            strokeWidth={1}
          />
        </g>

        {/* HOUSE lines + numbers */}
        <g transform={`translate(${HOUSE_DX}, ${HOUSE_DY})`}>
          {houseLines.map((l) => {
            const numP = polar(cx, cy, R_HOUSE - 20, wrap360(l.deg + 8));
            return (
              <g key={`house-${l.idx}`}>
                <line
                  x1={l.p1.x}
                  y1={l.p1.y}
                  x2={l.p2.x}
                  y2={l.p2.y}
                  stroke={theme.houseLine}
                  strokeWidth={l.idx === 1 ? 3.4 : 2.4}
                  opacity={l.idx === 1 ? 0.94 : 0.90}
                />

                {HOUSE_NUM_BG && (
                  <circle
                    cx={numP.x}
                    cy={numP.y}
                    r={HOUSE_NUM_BG_R}
                    fill={HOUSE_NUM_BG_FILL}
                    stroke={HOUSE_NUM_BG_STROKE}
                    strokeWidth={HOUSE_NUM_BG_STROKE_W}
                  />
                )}

                <text
                  x={numP.x}
                  y={numP.y + 0.3}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={HOUSE_NUM_FONT}
                  fill={theme.houseNumber}
                  opacity={HOUSE_NUM_OPACITY}
                  fontFamily="ui-sans-serif, system-ui"
                  style={{ fontWeight: HOUSE_NUM_WEIGHT }}
                >
                  {l.idx}
                </text>
              </g>
            );
          })}
        </g>

        {/* ✅ FIX: CENTER CIRCLE önce (açıların altında kalmasın diye) */}
        <g transform={`translate(${CENTER_DX}, ${CENTER_DY})`}>
          <circle
            cx={cx}
            cy={cy}
            r={R_CENTER}
            fill="rgba(255,255,255,0.98)"
            stroke={theme.stroke2}
            strokeWidth={2}
            opacity={0.98}
          />
        </g>

        {/* ✅ FIX: ASPECT lines gezegenlerle senkron translate */}
        <g transform={`translate(${PLANET_DX + ASPECT_DX}, ${PLANET_DY + ASPECT_DY})`}>
          {aspectLines.map((a) => (
            <line
              key={a.key}
              x1={a.x1}
              y1={a.y1}
              x2={a.x2}
              y2={a.y2}
              stroke={a.stroke}
              strokeWidth={a.width}
              opacity={a.opacity}
              strokeLinecap="round"
            />
          ))}
        </g>

        {/* ASC line */}
        <g transform={`translate(${ASC_DX}, ${ASC_DY})`}>
          {ascLine && (
            <g>
              <line
                x1={ascLine.p1.x}
                y1={ascLine.p1.y}
                x2={ascLine.p2.x}
                y2={ascLine.p2.y}
                stroke="#ff7fb8"
                strokeWidth={3.2}
                opacity={0.95}
              />
              <text
                x={ascLine.labelP.x}
                y={ascLine.labelP.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="12"
                fill="#ff5aa6"
                fontFamily="ui-sans-serif, system-ui"
              >
                ASC
              </text>
            </g>
          )}
        </g>

        {/* PLANETS */}
        <g transform={`translate(${PLANET_DX}, ${PLANET_DY})`}>
          {planetPoints.map((p) => (
            <g key={p.name}>
              <circle
                cx={p.x}
                cy={p.y}
                r={13}
                fill="rgba(255,255,255,0.98)"
                stroke={theme.planetDot}
                strokeWidth={3}
                opacity={0.98}
              />
              <text
                x={p.x}
                y={p.y + 0.5}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="14"
                fill={theme.text}
                fontFamily="ui-sans-serif, system-ui"
              >
                {p.label}
              </text>
              <text
                x={p.x}
                y={p.y + 22}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="10"
                fill={theme.softText}
                fontFamily="ui-sans-serif, system-ui"
                opacity={0.92}
              >
                {p.degMin}
              </text>
            </g>
          ))}
        </g>

        {/* ✅ FIX: CENTER TEXT en sonda (hep üstte kalsın) */}
        <g transform={`translate(${CENTER_DX}, ${CENTER_DY})`}>
          <text
            x={cx}
            y={cy - 6}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="20"
            fill={theme.text}
            fontFamily="ui-serif, Georgia, 'Times New Roman', serif"
            style={{ fontWeight: 800, letterSpacing: 0.6 }}
          >
            Natal Chart
          </text>
          <text
            x={cx}
            y={cy + 20}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="12"
            fill={theme.softText}
            fontFamily="ui-sans-serif, system-ui"
          >
            {titleName}
          </text>
        </g>
      </svg>

      <div style={{ marginTop: 10, fontSize: 12, color: "#533a6b" }}>
        <span style={{ opacity: 0.9 }}>
          Burçlar ♈–♓, gezegenler sembollerle. Açı çizgileri: pembe (uyumlu), mor (zorlayıcı).
        </span>
      </div>
    </div>
  );
}
