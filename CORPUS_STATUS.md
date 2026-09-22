# Corpus Coverage Status — v1.2.0

The local AstroMYLA interpretation corpus is now complete for every chart element that the current backend can retrieve by sign.

## Placement coverage

All of the following are **12/12 signs**:

- Sun
- Moon
- Mercury
- Venus
- Mars
- Jupiter
- Saturn
- Uranus
- Neptune
- Pluto
- True Node
- Chiron
- Lilith

## Point / angle coverage

All of the following are **12/12 signs**:

- Ascendant (ASC)
- Midheaven (MC)
- Descendant (DSC)
- IC
- Vertex
- Part of Fortune

## House-cusp coverage

Every house from **House 1 through House 12** now contains an interpretation for **all 12 signs**.

- 12 houses × 12 signs = **144/144 house-cusp texts**

The previously missing `House 1 in Taurus` file is included, while the original supplied House 1 texts are preserved.

## Tone

New corpus text is written in warm, conversational English and follows `rules/tone_rules.txt`:

- second-person voice
- emotionally intelligent, grounded language
- no clinical claims
- no guaranteed predictions
- no deterministic “this means you are…” framing
- symbolic points such as Vertex / Node / Lilith are treated as interpretive themes, not fate

## Chiron calculation note

The interpretation corpus has complete Chiron text, but the astronomical Chiron position still requires Swiss Ephemeris asteroid data. If deployment does not include the necessary ephemeris files, Chiron remains unavailable for that chart and its corpus passage is not used.
