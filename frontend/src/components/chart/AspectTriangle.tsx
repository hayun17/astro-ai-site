import React, { useMemo } from "react";

type AspectItem = {
  p1: string;
  p2: string;
  aspect: string;
  orb: number;
};

const PLANETS = [
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

// (Optional) If backend later includes these in planet aspects, you can enable:
// const EXTRA_POINTS = ["Asc", "MC", "North Node", "Chiron"];

const ASPECT_GLYPH: Record<string, string> = {
  Conjunction: "☌",
  Opposition: "☍",
  Trine: "△",
  Square: "□",
  Sextile: "✶",
};

function key(a: string, b: string) {
  return [a, b].sort().join("__");
}

function aspectClass(name?: string) {
  switch (name) {
    case "Conjunction":
      return "asp asp-conj";
    case "Opposition":
      return "asp asp-opp";
    case "Trine":
      return "asp asp-trine";
    case "Square":
      return "asp asp-square";
    case "Sextile":
      return "asp asp-sextile";
    default:
      return "asp asp-other";
  }
}

export default function AspectTriangle({ aspects }: { aspects: AspectItem[] }) {
  const map = useMemo(() => {
    const m = new Map<string, AspectItem>();
    (aspects || []).forEach((a) => {
      if (!a?.p1 || !a?.p2) return;
      m.set(key(a.p1, a.p2), a);
    });
    return m;
  }, [aspects]);

  return (
    <div className="aspectCard">
      <div className="miniTitle">Aspect Table</div>

      <div className="aspectTableWrap">
        <table className="aspectTable">
          <thead>
            <tr>
              <th className="corner"></th>
              {PLANETS.map((p) => (
                <th key={p} className="colHead">
                  {p.slice(0, 2)}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {PLANETS.map((rowP, i) => (
              <tr key={rowP}>
                <th className="rowHead">{rowP}</th>

                {PLANETS.map((colP, j) => {
                  if (j >= i) return <td key={colP} className="empty"></td>;

                  const a = map.get(key(rowP, colP));
                  if (!a) return <td key={colP} className="cell mutedCell">·</td>;

                  const glyph = ASPECT_GLYPH[a.aspect] || "•";
                  const orb = Number.isFinite(a.orb) ? a.orb : 0;

                  return (
                    <td key={colP} className={`cell ${aspectClass(a.aspect)}`}>
                      <div className="aspGlyph">{glyph}</div>
                      <div className="aspOrb">{orb.toFixed(1)}°</div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="legend">
        ☌ Conj · ☍ Opp · △ Trine · □ Square · ✶ Sextile
      </div>
    </div>
  );
}