from __future__ import annotations

import json
from typing import Any


def premium_prompt(*, chart: dict[str, Any], tier: str, style: str, focus: str, questions: list[str]) -> tuple[str, str, int]:
    """Build a long-form, calculation-grounded premium natal-reading prompt.

    The chart JSON remains the sole source of astronomical facts.  The model is
    asked to synthesize rather than enumerate, and to keep a warm, editorial
    voice suitable for a paid PDF report.
    """
    tier = "deep" if tier == "deep" else "personalized"
    max_tokens = 9000 if tier == "deep" else 6500

    length_note = (
        "Aim for a substantial long-form reading, usually around 4,000-6,000 words when the chart supports it."
        if tier == "deep"
        else "Aim for a substantial but focused reading, usually around 2,500-4,000 words when the chart supports it."
    )
    question_note = ""
    if tier == "deep" and questions:
        question_note = (
            "\nThe reader supplied personal questions. Give each question its own clearly titled section near the end. "
            "Answer only through patterns actually supported by the supplied natal chart; do not claim certainty or predict guaranteed events.\n"
            + "\n".join(f"- Question {i+1}: {q}" for i, q in enumerate(questions[:3]))
        )

    system = (
        "You are AstroMYLA's premium astrology writer. Create an elegant, intimate, highly personalized natal reading in warm, polished English. "
        "The supplied chart JSON is the ONLY source of astronomical facts. Never invent a placement, house, aspect, angle, retrograde state, or timing technique. "
        "Synthesize repeating themes across placements, houses and aspects instead of writing disconnected encyclopedia entries. "
        "Write like a thoughtful human astrologer speaking directly to one person: gentle, perceptive, specific, occasionally playful, but never melodramatic or patronizing. "
        "Avoid deterministic claims, diagnoses, fear language, soul-contract certainty, guaranteed relationship outcomes, or medical/legal/financial advice. "
        "Do not use compatibility scores or fake precision. When the birth time is unknown, explicitly respect the missing houses/angles and do not reconstruct them. "
        "Use Markdown headings beginning with ### and short paragraphs. Bold may be used sparingly for a phrase that genuinely matters. "
        "Do not begin every section with the same formula. Vary rhythm and transitions so the report feels editorial rather than templated. "
        + length_note
    )

    structure = [
        "A soft opening note that tells the reader how to use the report without sounding like a disclaimer.",
        "### The shape of your chart - a whole-chart overview and the 3-5 strongest repeating themes.",
        "### Your core self - Sun, Moon and Ascendant when available, woven together rather than treated separately.",
        "### Your mind and voice - Mercury plus the houses/aspects that materially change how it works.",
        "### Love, closeness and attraction - Venus, the 5th/7th/8th houses when available, and relevant aspects.",
        "### Desire, courage and boundaries - Mars and the chart patterns that modify drive, anger, initiative and self-protection.",
        "### Home, roots and emotional safety - Moon/IC/4th-house themes when available.",
        "### Work, vocation and visibility - MC/10th/6th/2nd-house themes and relevant planets/aspects when available.",
        "### Growth edges and long lessons - Jupiter, Saturn, Nodes and only the strongest supporting aspects.",
        "### The private room inside you - 8th/12th-house, Pluto, Neptune, Lilith or Chiron themes only when those data are actually available.",
        "### Your strongest aspect stories - explain several tight aspects as living patterns, including how apparently contradictory parts can coexist.",
        "### What gets easier when you know this - practical, non-prescriptive reflection points grounded in the chart.",
    ]
    if tier == "deep":
        structure.insert(10, "### The contradictions that make you interesting - explicitly synthesize tensions between different chart signatures rather than trying to flatten them.")
        structure.insert(11, "### Relationship patterns in depth - how closeness, autonomy, needs and conflict styles may interact, without predicting outcomes.")
    structure.append("### A note to keep - a warm closing that feels personal and concise, not generic inspiration.")

    user = (
        f"Premium tier: {tier}\n"
        f"Style preference: {style}\n"
        f"Focus preference: {focus}\n"
        "Use this editorial structure as a guide; merge sections naturally if the chart lacks the required time-sensitive data:\n- "
        + "\n- ".join(structure)
        + question_note
        + "\n\nChart data:\n"
        + json.dumps(chart, ensure_ascii=False)
    )
    return system, user, max_tokens
