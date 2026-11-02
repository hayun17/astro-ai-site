"""Directional, evidence-first synastry stories from actual planetary house overlays.

These stories are deliberately deterministic: every named planet and house comes
from the chart calculations, not a free-form generative guess.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any

HOUSE_STORIES = {
    1: ("first impressions & identity", "You notice each other quickly. The house person may feel especially seen, energized or self-conscious around the visitor."),
    2: ("security & values", "You get into what feels dependable: time, money, priorities and even self-worth. Practical consistency matters here."),
    3: ("talking & everyday life", "This is the 'we keep talking' area: texts, little observations, shared jokes and the way you think out loud."),
    4: ("home & emotional safety", "This touches private life, family habits and the need to feel at home with another person."),
    5: ("flirting & fun", "Playfulness, affection and creativity can come alive here. It's often an easy place to notice the spark."),
    6: ("daily routines & showing up", "The relationship starts showing up in ordinary life: support, habits, obligations and how you look after one another."),
    7: ("partnership & commitment", "The house person can experience the visitor through a 'could we be a team?' lens, even when the connection is still new."),
    8: ("trust & vulnerability", "This can feel unusually personal: closeness, boundaries, trust and shared vulnerabilities become harder to ignore."),
    9: ("growth & perspective", "You may pull each other toward different perspectives, study, travel or bigger questions about life."),
    10: ("ambition & being seen", "Career, public life and what each person wants to build can become a meaningful part of the connection."),
    11: ("friendship & future plans", "There's room for shared ideas, friendships, causes and conversations about what's next."),
    12: ("private feelings & blind spots", "Some reactions may be harder to name at first. Gentleness and honest boundaries help more than mind-reading."),
}

PLANET_NOTES = {
    "Sun": "Sun brings attention to identity and confidence",
    "Moon": "Moon brings feelings, habits and the need to feel safe",
    "Mercury": "Mercury brings questions, conversation and mental chemistry",
    "Venus": "Venus brings warmth, pleasure and ways of showing affection",
    "Mars": "Mars brings desire, action and sometimes a little friction",
    "Jupiter": "Jupiter adds encouragement and a bigger-picture outlook",
    "Saturn": "Saturn adds seriousness, responsibility or a need for boundaries",
    "Uranus": "Uranus can shake up familiar patterns and increase the need for freedom",
    "Neptune": "Neptune can bring imagination, softness or ambiguity",
    "Pluto": "Pluto can stir intensity, control questions or deep change",
    "TrueNode": "the Node can put growth and direction in the foreground",
    "Chiron": "Chiron may highlight sensitivities and opportunities for care",
    "Lilith": "Lilith can activate boundaries and less-conventional feelings",
}
PLANET_HOUSE_EXAMPLES = {
    3: {"Moon":"The Moon visitor may make it easier for the house person to speak about everyday feelings.",
        "Mercury":"The Mercury visitor brings questions, messages and the kind of conversation that keeps going after midnight.",
        "Venus":"Venus can soften the tone here: affection may show up as kind words, teasing or remembering small details."},
    4: {"Moon":"Moon can touch the house person's private, familiar side — comfort can deepen, but old sensitivities might surface.",
        "Venus":"Venus may make home and quiet time together feel especially inviting."},
    5: {"Venus":"Venus tends to amplify the playful 'I like being seen by you' quality of this house.",
        "Mars":"Mars can add initiative and flirtation, though the pace needs to feel good to both people.",
        "Sun":"The Sun visitor can make this side of the house person's self-expression feel noticed."},
    7: {"Moon":"The Moon visitor may make the house person think about emotional partnership and daily companionship.",
        "Venus":"Venus can make the visitor feel like a natural candidate for one-to-one affection — not a guarantee of commitment.",
        "Saturn":"Saturn makes expectations, responsibility and long-term boundaries harder to ignore."},
    8: {"Moon":"Moon can bring vulnerability and trust needs into sharp focus.",
        "Venus":"Venus may bring attraction to private, intimate conversations, but trust still has to be earned.",
        "Mars":"Mars can intensify the pull while making boundaries and consent especially important."},
}

IMPORTANT = {"Moon": 10, "Sun": 9, "Venus": 8, "Mars": 8, "Mercury": 7, "Saturn": 7, "Jupiter": 6, "TrueNode": 5, "Pluto": 4, "Uranus": 3, "Neptune": 3, "Chiron": 2, "Lilith": 2}


def _direction(rows: list[dict[str, Any]], visitor: str, host: str) -> dict[str, Any]:
    groups: dict[int, list[str]] = defaultdict(list)
    for item in rows:
        h = item.get("house")
        planet = str(item.get("planet") or "")
        if isinstance(h, int) and 1 <= h <= 12 and planet in PLANET_NOTES and planet not in groups[h]:
            groups[h].append(planet)
    ordered = sorted(groups.items(), key=lambda item: (-len(item[1]), -sum(IMPORTANT.get(p, 0) for p in item[1]), item[0]))
    chapters = []
    for house, planets in ordered[:4]:
        ordered_planets = sorted(planets, key=lambda p: -IMPORTANT.get(p, 0))
        title, theme = HOUSE_STORIES[house]
        pretty = ", ".join(ordered_planets[:-1]) + (" and " if len(ordered_planets)>1 else "") + ordered_planets[-1]
        singular = len(planets) == 1
        intro = (f"{visitor}'s {pretty} lands in {host}'s House {house}. " if singular else
                 f"Look at this: {visitor}'s {pretty} all land in {host}'s House {house}. ")
        if len(planets) > 1:
            intro += f"That's a real concentration in {title} — not just one isolated contact. "
        else:
            intro += f"That's a connection to {title}. "
        specific = [PLANET_HOUSE_EXAMPLES.get(house,{}).get(p) or PLANET_NOTES[p]+"." for p in ordered_planets[:3]]
        body = theme + " " + " ".join(specific)
        chapters.append({
            "house": house, "count": len(planets), "planets": ordered_planets,
            "headline": f"House {house} · {title}", "opening": intro,
            "story": body,
            "question": "Ask yourselves: do you both enjoy the way this area of life comes alive?",
        })
    return {
        "visitor": visitor, "host": host,
        "available": bool(groups), "chapters": chapters,
        "headline": f"What {visitor} brings into {host}'s life",
        "summary": (f"The strongest concentration is House {chapters[0]['house']} ({HOUSE_STORIES[chapters[0]['house']][0]}), with {chapters[0]['count']} planet{'s' if chapters[0]['count']!=1 else ''}. "
                    "And remember: the visitor brings the planets, while the house person experiences that part of life being activated.") if chapters else
                    "House overlays are unavailable for this direction when the receiving person's exact birth time isn't known.",
    }


def build_directional_house_stories(overlays: dict[str, Any] | None, *, a_label: str = "Person A", b_label: str = "Person B") -> dict[str, Any]:
    overlays = overlays or {}
    # Labels are presentation-only and never treated as instructions to an LLM.
    a_to_b = _direction(overlays.get("a_in_b_houses") or [], a_label, b_label)
    b_to_a = _direction(overlays.get("b_in_a_houses") or [], b_label, a_label)
    return {"a_to_b": a_to_b, "b_to_a": b_to_a, "method_note":
            "Planets are placed in the receiving person's natal houses. House interpretations are symbolic, not predictions. Exact receiving birth time is required."}
