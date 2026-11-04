import React from "react";

type TransitInsight = {
  title: string;
  transit: string;
  natal: string;
  aspect: string;
  orb: number;
  motion: string;
  scope: string;
  summary: string;
  try_this: string;
};

type HouseInsight = { title: string; planet: string; house: number; summary: string; prompt: string };

type TransitReadingData = {
  date?: string;
  headline?: string;
  intro?: string;
  key_aspects?: TransitInsight[];
  house_stories?: HouseInsight[];
  birth_time_note?: string;
  closing?: string;
};

export default function TransitReading({ reading }: { reading?: TransitReadingData | null }) {
  if (!reading) {
    return (
      <section className="transitStory" aria-label="Your personal transit interpretation">
        <div className="transitStoryLead"><span className="transitStoryEyebrow">YOUR SKY, EXPLAINED ✦</span><h3>Reading unavailable</h3>
          <p>The planetary positions loaded, but their written interpretation did not arrive. Try generating the transits again.</p></div>
      </section>
    );
  }
  const aspects = reading.key_aspects || [];
  const main = aspects[0];
  const rest = aspects.slice(1);
  const houses = reading.house_stories || [];

  return (
    <section className="transitStory" aria-label="Your personal transit interpretation">
      <div className="transitStoryLead">
        <div className="transitStoryTop"><span className="transitStoryEyebrow">✦ ASTROMYLA · YOUR PERSONAL SKY</span><span className="transitStoryDate">{reading.date}</span></div>
        <h3>{reading.headline || "Let's read your current sky"}</h3>
        <p>{reading.intro}</p>
      </div>

      {main && (
        <article className="transitMainInsight">
          <div className="transitInsightTitle"><span className="transitInsightIndex">01 / MAIN THEME</span><span className="transitMotion">{main.motion}</span></div>
          <h4>{main.title}</h4>
          <div className="transitInsightMeta"><span>{Number(main.orb).toFixed(2)}° orb</span><span>{main.scope}</span></div>
          <p>{main.summary}</p>
          <div className="transitTry"><span>♡ A QUESTION FOR YOU</span><p>{main.try_this}</p></div>
        </article>
      )}

      {rest.length > 0 && (
        <div className="transitMore">
          <div className="transitStorySectionTitle"><span>MORE GOING ON</span><h4>The other conversations in your chart</h4></div>
          <div className="transitDetailsStack">
            {rest.map((item, index) => (
              <details key={`${item.transit}-${item.natal}-${item.aspect}-${index}`} className="transitStoryDetail">
                <summary><span className="transitDetailNumber">{String(index + 2).padStart(2, "0")}</span><span className="transitDetailName">{item.title}<small>{Number(item.orb).toFixed(2)}° orb · {item.motion.toLowerCase()}</small></span><span aria-hidden="true" className="transitDetailToggle">+</span></summary>
                <div className="transitDetailBody"><p>{item.summary}</p><p className="transitReflection">♡ {item.try_this}</p></div>
              </details>
            ))}
          </div>
        </div>
      )}

      {houses.length > 0 && (
        <div className="transitHousesStory">
          <div className="transitStorySectionTitle"><span>WHERE IT SHOWS UP</span><h4>The areas of life getting a little louder</h4></div>
          <div className="transitHouseCards">
            {houses.slice(0, 3).map((item) => (
              <article key={`${item.planet}-${item.house}`} className="transitHouseCard">
                <span className="transitHouseNumber">HOUSE {item.house}</span>
                <h5>{item.title}</h5>
                <p>{item.summary}</p>
                <small>{item.prompt}</small>
              </article>
            ))}
          </div>
        </div>
      )}

      {reading.birth_time_note && <p className="transitPrecisionNote">✧ {reading.birth_time_note}</p>}
      <p className="transitDisclaimer">{reading.closing || "Astrology is symbolic and interpretive, not a prediction of events."}</p>
    </section>
  );
}
