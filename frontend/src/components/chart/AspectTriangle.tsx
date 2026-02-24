import React, { useMemo } from "react";

type AspectRow = {
  p1: string;
  p2: string;
  aspect: string;
  orb: number;
};

type Props = {
  aspects: AspectRow[];
  bodies: string[];
};

const ABBR: Record<string, string> = {
  Sun: "Su",
  Moon: "Mo",
  Mercury: "Me",
  Venus: "Ve",
  Mars: "Ma",
  Jupiter: "Ju",
  Saturn: "Sa",
  Uranus: "Ur",
  Neptune: "Ne",
  Pluto: "Pl",
  Asc: "ASC",
  DSC: "DSC",
  MC: "MC",
  IC: "IC",
  TrueNode: "NN",
  Lilith: "Lil",
  Chiron: "Chi",
  Vertex: "Vx",
  Fortune: "PoF",
};

function normalizeName(n: string) {
  return String(n || "").trim();
}

function glyphForAspect(a: string) {
  const x = (a || "").toLowerCase();
  if (x === "conjunction" || x === "conj") return "☌";
  if (x === "opposition" || x === "opp") return "☍";
  if (x === "trine") return "△";
  if (x === "square") return "□";
  if (x === "sextile") return "✶";
  return "·";
}

function colorForAspect(a: string) {
  const x = (a || "").toLowerCase();
  if (x === "conjunction" || x === "conj") return "#ff5fa2";
  if (x === "sextile") return "#20c997";
  if (x === "trine") return "#4dabf7";
  if (x === "square") return "#ff922b";
  if (x === "opposition" || x === "opp") return "#845ef7";
  return "rgba(120, 70, 120, 0.45)";
}

function keyPair(a: string, b: string) {
  const p = [normalizeName(a), normalizeName(b)].sort();
  return p[0] + "|" + p[1];
}

export default function AspectTriangle({ aspects, bodies }: Props) {
  const bodyList = useMemo(() => {
    const seen = new Set<string>();
    const out: string[] = [];
    for (const b of bodies || []) {
      const k = normalizeName(b);
      if (!k) continue;
      if (seen.has(k)) continue;
      seen.add(k);
      out.push(k);
    }
    return out;
  }, [bodies]);

  const aspectMap = useMemo(() => {
    const m = new Map<string, AspectRow[]>();
    for (const a of aspects || []) {
      if (!a?.p1 || !a?.p2) continue;
      const kp = keyPair(a.p1, a.p2);
      if (!m.has(kp)) m.set(kp, []);
      m.get(kp)!.push(a);
    }
    return m;
  }, [aspects]);

  function bestAspectBetween(a: string, b: string): AspectRow | null {
    const kp = keyPair(a, b);
    const arr = aspectMap.get(kp) || [];
    if (arr.length === 0) return null;

    // choose the smallest orb
    const sorted = [...arr].sort((x, y) => (x.orb ?? 999) - (y.orb ?? 999));
    return sorted[0] || null;
  }

  return (
    <div className="aspectCard">
      <div className="miniTitle">Aspect Table</div>

      <div className="aspectTableWrap">
        <table className="aspectTable">
          <thead>
            <tr>
              <th className="corner" />
              {bodyList.map((b) => (
                <th key={"h-" + b} className="colHead">
                  {ABBR[b] || b.slice(0, 2)}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {bodyList.map((rowB, i) => (
              <tr key={"r-" + rowB}>
                <th className="rowHead">{rowB}</th>

                {bodyList.map((colB, j) => {
                  if (j >= i) return <td key={`e-${i}-${j}`} className="empty" />;

                  const asp = bestAspectBetween(rowB, colB);
                  if (!asp) return <td key={`n-${i}-${j}`} className="cell mutedCell">·</td>;

                  const g = glyphForAspect(asp.aspect);
                  const c = colorForAspect(asp.aspect);
                  const orb = typeof asp.orb === "number" ? asp.orb : null;

                  return (
                    <td key={`a-${i}-${j}`} className="cell">
                      <div className="aspGlyph" style={{ color: c }}>
                        {g}
                      </div>
                      <div className="aspOrb" style={{ color: "rgba(43,27,59,0.70)" }}>
                        {orb != null ? `${orb.toFixed(1)}°` : ""}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="legend">
        ☌ Conjunction · ☍ Opposition · △ Trine · □ Square · ✶ Sextile
      </div>
    </div>
  );
}