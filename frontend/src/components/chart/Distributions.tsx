import React, { useMemo } from "react";

type Planet = {
  sign?: string;
  available?: boolean;
};

type PlanetsDict = Record<string, Planet>;

const MAJOR = [
  "Sun",
  "Moon",
  "Mercury",
  "Venus",
  "Mars",
  "Jupiter",
  "Saturn",
  "Uranus",
  "Neptune",
  "Pluto",
];

const ELEMENTS: Record<string, "Fire" | "Earth" | "Air" | "Water"> = {
  Aries: "Fire",
  Leo: "Fire",
  Sagittarius: "Fire",
  Taurus: "Earth",
  Virgo: "Earth",
  Capricorn: "Earth",
  Gemini: "Air",
  Libra: "Air",
  Aquarius: "Air",
  Cancer: "Water",
  Scorpio: "Water",
  Pisces: "Water",
};

const MODALITIES: Record<string, "Cardinal" | "Fixed" | "Mutable"> = {
  Aries: "Cardinal",
  Cancer: "Cardinal",
  Libra: "Cardinal",
  Capricorn: "Cardinal",
  Taurus: "Fixed",
  Leo: "Fixed",
  Scorpio: "Fixed",
  Aquarius: "Fixed",
  Gemini: "Mutable",
  Virgo: "Mutable",
  Sagittarius: "Mutable",
  Pisces: "Mutable",
};

function pct(n: number, total: number) {
  if (!total) return "0%";
  return `${Math.round((n / total) * 100)}%`;
}

export default function Distributions({ planets }: { planets?: PlanetsDict }) {
  const { elementCount, modalityCount, total } = useMemo(() => {
    const e: Record<string, number> = { Fire: 0, Earth: 0, Air: 0, Water: 0 };
    const m: Record<string, number> = { Cardinal: 0, Fixed: 0, Mutable: 0 };

    if (!planets) return { elementCount: e, modalityCount: m, total: 0 };

    let t = 0;

    for (const name of MAJOR) {
      const p = planets[name];
      if (!p?.sign) continue;
      if (p.available === false) continue;

      const el = ELEMENTS[p.sign];
      const mo = MODALITIES[p.sign];
      if (!el || !mo) continue;

      e[el] += 1;
      m[mo] += 1;
      t += 1;
    }

    return { elementCount: e, modalityCount: m, total: t };
  }, [planets]);

  if (!planets) return null;

  return (
    <div className="distCard">
      <div className="miniTitle">Distributions</div>

      <div className="distGrid">
        <div className="distBlock">
          <div className="distHead">Elements</div>
          {(["Fire", "Earth", "Air", "Water"] as const).map((k) => (
            <div key={k} className="distRow">
              <span className="distKey">{k}</span>
              <span className="distVal">
                {elementCount[k]} <span className="distPct">{pct(elementCount[k], total)}</span>
              </span>
            </div>
          ))}
        </div>

        <div className="distBlock">
          <div className="distHead">Modalities</div>
          {(["Cardinal", "Fixed", "Mutable"] as const).map((k) => (
            <div key={k} className="distRow">
              <span className="distKey">{k}</span>
              <span className="distVal">
                {modalityCount[k]} <span className="distPct">{pct(modalityCount[k], total)}</span>
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="distNote">Counted: Sun → Pluto</div>
    </div>
  );
}