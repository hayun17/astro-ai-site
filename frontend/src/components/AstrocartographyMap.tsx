import React, { useMemo, useState } from "react";

type Segment = number[][];
type Line = {
  planet: string;
  angle: "ASC" | "DSC" | "MC" | "IC";
  kind: string;
  segments: Segment[];
};

type Props = {
  data: any;
};

const PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"];

const PLANET_GUIDE: Record<string, { theme: string; watch: string }> = {
  Sun: { theme: "visibility, vitality and confidence", watch: "pressure to perform or over-identify with being seen" },
  Moon: { theme: "belonging, home-feeling and emotional sensitivity", watch: "moodiness, nostalgia or absorbing the atmosphere too strongly" },
  Mercury: { theme: "learning, movement, writing and conversation", watch: "mental overload, restlessness or living too much in your head" },
  Venus: { theme: "connection, pleasure, aesthetics and social ease", watch: "people-pleasing, overspending or avoiding necessary friction" },
  Mars: { theme: "drive, courage, sexuality and decisive action", watch: "conflict, impatience or running at a pace your body cannot sustain" },
  Jupiter: { theme: "growth, opportunity, teaching and wider horizons", watch: "overconfidence, overcommitment or assuming bigger always means better" },
  Saturn: { theme: "structure, responsibility, boundaries and long-term building", watch: "loneliness, heaviness or turning discipline into self-punishment" },
  Uranus: { theme: "freedom, reinvention and experimentation", watch: "instability, abrupt decisions or change for its own sake" },
  Neptune: { theme: "imagination, spirituality, creativity and sensitivity", watch: "idealization, confusion or porous boundaries" },
  Pluto: { theme: "intensity, power and deep transformation", watch: "control struggles, obsession or feeling everything has to become all-or-nothing" },
};

const ANGLE_GUIDE: Record<string, string> = {
  ASC: "You tend to feel the planet through identity, body, beginnings and the way you meet the environment.",
  DSC: "The planet is often encountered through partners, clients, collaborators and one-to-one dynamics.",
  MC: "The planet becomes more visible through career, reputation, ambition and public direction.",
  IC: "The planet is felt more privately through home, family, roots, rest and emotional foundations.",
};

const COLORS: Record<string, string> = {
  Sun: "#d07a24",
  Moon: "#6b78a8",
  Mercury: "#5c8b69",
  Venus: "#b45f85",
  Mars: "#ba4a4a",
  Jupiter: "#8a63b8",
  Saturn: "#6d665c",
  Uranus: "#4d8e9f",
  Neptune: "#5377bd",
  Pluto: "#7f4a72",
};

function xFor(lon: number) {
  return ((lon + 180) / 360) * 1000;
}
function yFor(lat: number) {
  return ((80 - lat) / 160) * 500;
}
function pathFor(seg: Segment) {
  return seg.map((p, i) => `${i === 0 ? "M" : "L"}${xFor(p[0]).toFixed(2)},${yFor(p[1]).toFixed(2)}`).join(" ");
}

export default function AstrocartographyMap({ data }: Props) {
  const [planet, setPlanet] = useState("Sun");
  const [angles, setAngles] = useState<Record<string, boolean>>({ ASC: true, DSC: true, MC: true, IC: true });
  const lines: Line[] = Array.isArray(data?.lines) ? data.lines : [];
  const shown = useMemo(
    () => lines.filter((line) => line.planet === planet && angles[line.angle]),
    [lines, planet, angles]
  );
  const birthplace = data?.birthplace;

  return (
    <div className="astroMapCard">
      <div className="astroMapToolbar">
        <label>
          Planet
          <select value={planet} onChange={(e) => setPlanet(e.target.value)}>
            {PLANETS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </label>
        <div className="angleToggles" aria-label="Astrocartography line filters">
          {(["ASC", "DSC", "MC", "IC"] as const).map((angle) => (
            <label key={angle}>
              <input
                type="checkbox"
                checked={angles[angle]}
                onChange={(e) => setAngles({ ...angles, [angle]: e.target.checked })}
              />
              <span>{angle}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="astroMapViewport">
        <img src="/world-outline.svg" alt="World map outline" className="worldMapImage" />
        <svg viewBox="0 0 1000 500" className="astroMapOverlay" role="img" aria-label={`${planet} astrocartography angular lines`}>
          {shown.flatMap((line, lineIdx) =>
            (line.segments || []).map((seg, segIdx) => (
              <path
                key={`${line.angle}-${lineIdx}-${segIdx}`}
                d={pathFor(seg)}
                fill="none"
                stroke={COLORS[planet] || "#76558f"}
                strokeWidth={line.angle === "MC" || line.angle === "IC" ? 2.3 : 1.8}
                strokeDasharray={line.angle === "DSC" ? "8 5" : line.angle === "IC" ? "3 5" : undefined}
                opacity={0.9}
              />
            ))
          )}
          {birthplace && Number.isFinite(Number(birthplace.longitude)) && Number.isFinite(Number(birthplace.latitude)) && (
            <g>
              <circle cx={xFor(Number(birthplace.longitude))} cy={yFor(Number(birthplace.latitude))} r="6" fill="#ffffff" stroke="#6e4c82" strokeWidth="2.5" />
              <circle cx={xFor(Number(birthplace.longitude))} cy={yFor(Number(birthplace.latitude))} r="2.3" fill="#6e4c82" />
            </g>
          )}
        </svg>
      </div>
      <div className="astroMapLegend">
        <span><b>ASC</b> rising / self</span>
        <span><b>DSC</b> setting / relationships</span>
        <span><b>MC</b> culmination / public life</span>
        <span><b>IC</b> lower meridian / roots</span>
      </div>
      <div className="astroLineGuide">
        <strong>{planet} lines · {PLANET_GUIDE[planet]?.theme}</strong>
        <p>Turn individual angle filters on and off to compare how the same planet changes by angle.</p>
        <div className="astroAngleGuideGrid">
          {(["ASC", "DSC", "MC", "IC"] as const).map((angle) => (
            <div key={angle} className={angles[angle] ? "active" : ""}><b>{planet}–{angle}</b><span>{ANGLE_GUIDE[angle]}</span></div>
          ))}
        </div>
        <p className="astroWatch"><b>Worth watching:</b> {PLANET_GUIDE[planet]?.watch}.</p>
      </div>
      <p className="muted astroMapNote">{data?.coverage_note}</p>
    </div>
  );
}
