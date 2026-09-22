# AstroMYLA Premium Report Design - v1.5.0

## Design goal

The paid PDF should feel like a keepsake reading, not a raw software export. The reader should be able to see the natal chart first, then move into a calm long-form narrative where placements, houses and aspects are synthesized rather than listed one by one.

## Opening page

1. AstroMYLA brand line
2. Reading tier: Personalized Reading or Deep Personal Reading
3. Reader name
4. Birth date, time, birthplace and timezone when available
5. Short editorial line: *The chart is the map. The reading is the conversation.*
6. Vector natal chart wheel
7. Sun / Moon / Rising strip

The wheel plots the ten major planets on the cover for legibility. Node, Lilith and Chiron remain in the detailed position table and interpretation.

## Writing brief - Personalized Reading

The premium generator is instructed to create a substantial whole-chart reading, usually around 2,500-4,000 words when the chart supports it. It should cover:

- The shape of the chart / strongest repeating themes
- Big Three synthesis
- Mind and communication
- Love, closeness and attraction
- Desire, courage and boundaries
- Home, roots and emotional safety
- Work, vocation and visibility
- Growth edges and long lessons
- Private/inner patterns where supported
- Strongest aspect stories
- Practical reflection points
- A warm closing note

## Writing brief - Deep Personal Reading

The deep tier expands toward roughly 4,000-6,000 words when the chart supports it and adds:

- Contradictions that make the person interesting
- Deeper relationship/autonomy/boundary synthesis
- Up to three customer-supplied questions/themes
- More explicit synthesis of repeating patterns across houses, planets and aspects

## Tone rules

- Warm and intimate, but not overfamiliar
- Specific to the chart, not generic affirmation copy
- Varied transitions; avoid every paragraph starting with the same formula
- No deterministic fate claims
- No diagnoses or fear-based language
- No invented transits, placements, houses or aspects
- Unknown birth time must remain visibly limited
- Astrology is framed as reflective/interpretive rather than scientific certainty

## Reliability rule

Paid generation is strict. If the configured model is unavailable, the protected premium endpoint returns an error instead of silently delivering the shorter free fallback.
