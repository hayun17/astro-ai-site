import React from "react";

type Chapter = { house: number; headline: string; planets: string[]; count: number; opening: string; story: string; question: string };
type Direction = { visitor: string; host: string; available: boolean; summary: string; chapters: Chapter[] };

function DirectionPanel({ direction, visitor, host }: { direction: Direction | undefined; visitor: string; host: string }) {
  const chapters = direction?.chapters || [];
  return <article className="houseStoryDirection">
    <div className="houseStoryDirectionHeading"><span>✧ {visitor} → {host}</span><h4>What {visitor} brings into {host}'s world</h4></div>
    {!direction?.available ? <p className="muted">We can't reliably map {visitor}'s planets into {host}'s houses without {host}'s exact birth time. We won't guess.</p> : <>
      <p className="houseStorySummary">{direction.summary}</p>
      {chapters.map((ch, i) => <div className={`houseStoryChapter ${i === 0 ? "houseStoryLead" : ""}`} key={ch.house}>
        <span className="houseNumber">HOUSE {ch.house} {i === 0 ? "· THE BIGGEST EMPHASIS" : ""}</span>
        <h5>{ch.headline.split(" · ")[1] || ch.headline}</h5>
        <p><strong>{ch.opening}</strong> {ch.story}</p>
        <div className="houseStoryPlanets">{ch.planets.map(p => <span key={p}>{p}</span>)}</div>
      </div>)}
    </>}
  </article>;
}
export default function HouseOverlayStories({ stories, personA, personB }: { stories: any; personA: string; personB: string }) {
  if (!stories) return null;
  const a = personA.trim() || "Person A", b = personB.trim() || "Person B";
  return <section className="houseStories" aria-label="Detailed two-way synastry house stories">
    <div className="houseStoriesIntro"><span className="premiumKicker">INSIDE YOUR CONNECTION ✨</span><h3>Where you change each other's world</h3><p>Here's the interesting bit: the very same relationship can feel different from each side. Let's look at which parts of life each person's planets light up — with actual houses and planets, not generic compatibility advice.</p></div>
    <div className="houseStoriesGrid">
      <DirectionPanel direction={stories.a_to_b} visitor={a} host={b}/>
      <DirectionPanel direction={stories.b_to_a} visitor={b} host={a}/>
    </div>
    <p className="muted houseStoriesFootnote">House placements are symbolic relationship themes, not a prediction of how someone will behave. The receiving person's birth time needs to be known.</p>
  </section>;
}
