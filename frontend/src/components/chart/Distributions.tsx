import React, { useMemo } from "react";

type Props = {
  planets: any; // chart.planets object
};

const ELEMENT_BY_SIGN: Record<string, "Fire" | "Earth" | "Air" | "Water"> = {
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

const MODALITY_BY_SIGN: Record<string, "Cardinal" | "Fixed" | "Mutable"> = {
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

const MAJORS = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"];

export default function Distributions({ planets }: Props) {
  const { elements, modalities, counted } = useMemo(() => {
    const el: Record<string, number> = { Fire: 0, Earth: 0, Air: 0, Water: 0 };
    const mo: Record<string, number> = { Cardinal: 0, Fixed: 0, Mutable: 0 };
    let n = 0;

    for (const k of MAJORS) {
      const p = planets?.[k];
      const sign = p?.sign;
      if (!sign) continue;

      const e = ELEMENT_BY_SIGN[sign];
      const m = MODALITY_BY_SIGN[sign];
      if (e) el[e] += 1;
      if (m) mo[m] += 1;
      n += 1;
    }

    return { elements: el, modalities: mo, counted: n };
  }, [planets]);

  const pct = (x: number) => {
    if (!counted) return "0%";
    return `${Math.round((x / counted) * 100)}%`;
  };

  return (
    <div className="distCard">
      <div className="miniTitle">Distributions</div>

      <div className="distGrid">
        <div className="distBlock">
          <div className="distHead">Elements</div>
          {Object.entries(elements).map(([k, v]) => (
            <div className="distRow" key={k}>
              <div className="distKey">{k}</div>
              <div className="distVal">
                {v} <span className="distPct">{pct(v)}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="distBlock">
          <div className="distHead">Modalities</div>
          {Object.entries(modalities).map(([k, v]) => (
            <div className="distRow" key={k}>
              <div className="distKey">{k}</div>
              <div className="distVal">
                {v} <span className="distPct">{pct(v)}</span>
              </div>
            </div>
          ))}
          <div className="distNote">Counted: Sun → Pluto</div>
        </div>
      </div>
    </div>
  );
}