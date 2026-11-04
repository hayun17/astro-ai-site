"""Deterministic, evidence-anchored transit interpretations.

Every statement in the structured story points to a calculated transit aspect
or a documented natal-house placement. No prediction or hidden LLM dependency.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

PLANET_ACTION: dict[str, str] = {
    "Sun": "attention, motivation and what feels important right now",
    "Moon": "the emotional temperature and day-to-day instincts",
    "Mercury": "conversation, thinking and the details you're processing",
    "Venus": "connection, pleasure, affection and values",
    "Mars": "initiative, confidence, desire and what gets under your skin",
    "Jupiter": "room to grow, possibilities and the bigger picture",
    "Saturn": "limits, commitments, patience and what needs structure",
    "Uranus": "the need for change, freedom and a different approach",
    "Neptune": "idealism, sensitivity and the need for clear boundaries",
    "Pluto": "deeper change, power dynamics and what you're ready to outgrow",
    "TrueNode": "questions about direction, belonging and future choices",
    "Chiron": "an old sensitivity and the chance to approach it more gently",
}
NATAL_TOPICS: dict[str, str] = {
    "Sun": "your confidence, identity and sense of direction",
    "Moon": "your comfort, emotional needs and instinctive reactions",
    "Mercury": "how you think, listen and say what you mean",
    "Venus": "your relationships, pleasure and personal values",
    "Mars": "your drive, boundaries, anger and appetite for action",
    "Jupiter": "your beliefs, hope and appetite for growth",
    "Saturn": "the responsibilities and long-term promises you carry",
    "Uranus": "your individual streak and need for freedom",
    "Neptune": "your ideals, imagination and sensitivity",
    "Pluto": "your relationship with power and transformation",
    "TrueNode": "what a meaningful next step might look like",
    "Chiron": "a vulnerable place where self-compassion matters",
    "Asc": "how you show up and let people meet you",
    "DSC": "how you negotiate closeness and partnership",
    "MC": "your work, visibility and public direction",
    "IC": "your private world, roots and feeling of home",
    "Vertex": "the meaning you make of significant encounters",
}
ASPECT_TONE = {
    "Conjunction": (
        "turns up the volume on", "This can feel hard to ignore, so notice what wants your attention without reacting on autopilot"
    ),
    "Opposition": (
        "pulls against", "You may notice two competing needs; you don't have to choose a winner immediately"
    ),
    "Square": (
        "puts some productive friction around", "If something feels irritating, treat it as useful information rather than a signal to force an outcome"
    ),
    "Trine": (
        "opens an easier route into", "This is the kind of opening you can actually use, not just wait for"
    ),
    "Sextile": (
        "offers a small opening around", "A little initiative can help you make something of this opportunity"
    ),
}
# Hand-written, real-life angles for the most commonly felt contacts.
# Each is only used when the matching calculated moving and natal bodies exist.
PAIR_SCENES = {
    ("Saturn", "Sun"): "It may be easier to see which habits are helping you become the person you want to be. Big promises aren't necessary here; small commitments kept consistently may say more.",
    ("Saturn", "Moon"): "You might feel torn between being responsible and having room for your own feelings. Support doesn't always mean pushing through—sometimes it's admitting what you've been carrying.",
    ("Saturn", "Venus"): "You might start caring less about grand gestures and more about who actually shows up. Consistency, boundaries and the price of emotional effort can become useful questions.",
    ("Saturn", "Mercury"): "Your thoughts may feel more serious or deliberate. Give yourself permission to check the facts and find the right words rather than rushing a conversation.",
    ("Saturn", "MC"): "Career questions may be asking for structure rather than instant certainty. Think next steps, real responsibilities and a pace you can sustain.",
    ("Saturn", "Mars"): "Your desire to move quickly may meet a practical limit. Instead of seeing the limit as defeat, ask what would make your next move stronger.",
    ("Jupiter", "Sun"): "This can be a moment to notice where you've made yourself too small. There's room to explore a bigger version of your goals without committing to every opportunity.",
    ("Jupiter", "Venus"): "Generosity, warmth and saying yes to the good things may feel especially appealing. Enjoy the openness, while still paying attention to what feels truly reciprocal.",
    ("Jupiter", "Moon"): "You might want a little more emotional space—more honesty, more connection or simply a better perspective on what's weighing you down.",
    ("Jupiter", "MC"): "A bigger vision for your work might be tempting. Notice where genuine possibilities exist, and give those ideas a realistic next step.",
    ("Uranus", "Sun"): "You may feel curious about a version of yourself that doesn't fit old expectations. Experimenting with a small change can teach you more than making an overnight declaration.",
    ("Uranus", "Moon"): "Your usual emotional routine may feel a little restrictive. There's a difference between needing freedom and needing to disappear; see which one is actually true.",
    ("Uranus", "Venus"): "You might be craving a different kind of closeness—more spontaneity, space or honesty. Newness is exciting, but it doesn't have to erase what already matters.",
    ("Neptune", "Venus"): "It's easy to fall in love with what a connection could become. Enjoy the tenderness, and make space to notice what's being shown to you in real life.",
    ("Neptune", "Moon"): "Feelings can be a little harder to name. A quiet moment, good boundaries and checking your assumptions may help more than a dramatic conclusion.",
    ("Neptune", "Sun"): "Your sense of direction might feel more intuitive than concrete. You don't have to solve the whole future today; try separating inspiration from certainty.",
    ("Pluto", "Sun"): "A deeper question about identity or control may be surfacing. You can look honestly at an old pattern without deciding your entire life needs to change.",
    ("Pluto", "Moon"): "An old emotional response may be asking to be understood instead of managed. Be curious about where the intensity comes from, without treating it as destiny.",
    ("Pluto", "Venus"): "Closeness may bring up questions about trust, control or the fear of losing something important. Honesty and consent matter more than intensity alone.",
    ("Mars", "Moon"): "A little impatience could spill into your mood even when the real issue is feeling unheard. Try noticing the feeling before it turns into a reaction.",
    ("Mars", "Mercury"): "Words may come fast, and so might the urge to win the point. You can say the honest thing without turning it into a fight.",
    ("Mars", "Venus"): "Attraction and irritation can sometimes live close together. Notice whether you're leaning into genuine chemistry or simply enjoying the rush.",
    ("Mars", "Sun"): "The urge to move, decide or take charge may be stronger. Choose a direction for that energy instead of scattering it across every irritation.",
    ("Venus", "Moon"): "Comfort and affection can feel more worth tending to. A small act of care may say more than a polished declaration.",
    ("Venus", "Venus"): "It's a nice chance to revisit what you enjoy and who you want to share it with. Make room for pleasure without turning it into an obligation.",
    ("Venus", "Mars"): "Desire and warmth may be easier to notice together. What matters is whether the attention feels mutual and respectful.",
    ("Mercury", "Moon"): "You might find it helpful to put a feeling into actual words. Not every emotion needs fixing; sometimes it just needs to be heard.",
    ("Mercury", "Mercury"): "Conversations and ideas can spark quickly. If something matters, a little clarity now can save a lot of second-guessing later.",
    ("Moon", "Venus"): "Something small may remind you what feels comforting in love or friendship. You don't have to make a big story out of a passing mood.",
    ("Sun", "MC"): "Your public direction or work can feel a little more visible. Pick one practical thing you'd like people to understand about your contribution.",
    ("TrueNode", "Mercury"): "You might be rethinking the story you're telling yourself about where you're heading. A conversation or new idea could help you check whether your words still match your priorities.",
}
GENERIC_SCENES = {
    "Moon": "Your need for comfort, security and feeling understood may be easier to notice than usual. See what you need before assuming someone else should guess.",
    "Venus": "Your relationships and values are a useful place to check in. Pay attention to the difference between something exciting and something nourishing.",
    "Mercury": "A conversation or decision may benefit from a little extra clarity. You don't have to know the perfect thing to say to begin honestly.",
    "Sun": "Questions about confidence, self-expression or direction may be taking up more space. You can learn something by noticing what you keep returning to.",
    "Mars": "Your drive and boundaries are worth noticing. An urge to act might carry useful information, even if you choose not to act immediately.",
    "MC": "Work, ambition or being visible may be on your mind. Check whether your next move fits your real priorities rather than someone else's timetable.",
    "DSC": "One-to-one relationships may reflect something important back to you. Notice where give-and-take feels easy and where you need clearer agreements.",
    "Asc": "The way you're showing up may want a little adjustment. You can try a different approach without losing who you are.",
    "IC": "Your home base and emotional foundations may deserve attention. Something as simple as a quieter boundary or supportive routine can matter.",
    "Saturn": "The commitments you carry may be asking to be reviewed. What is genuinely yours to hold, and what is habit or pressure?",
    "Jupiter": "Your beliefs or future plans may be inviting a wider perspective. Stay open while keeping one foot on the ground.",
    "Uranus": "The pull toward freedom or change may be noticeable. A thoughtful experiment is often easier to learn from than a dramatic leap.",
    "Neptune": "An ideal or expectation may be coloring how you see the situation. Keep the inspiration, but check the practical details too.",
    "Pluto": "A deeper pattern around intensity or control may be worth exploring without judging yourself for having it.",
    "TrueNode": "Questions about what matters next may be coming into focus. You don't need an instant answer to move thoughtfully.",
    "Chiron": "A tender subject may be worth approaching with compassion rather than pressure to fix it.",
}
ASPECT_ADVICE = {
    "Conjunction": "This is an emphasized contact: give it attention without assuming it has to take over the whole day.",
    "Opposition": "There may be two real needs pulling in different directions. You can hold both before making a choice.",
    "Square": "A square can feel uncomfortable, but the friction can show you what needs an adjustment—not necessarily a fight.",
    "Trine": "A trine suggests a smoother opening. It still helps to take one small step rather than waiting for something to happen by itself.",
    "Sextile": "A sextile suggests a subtler opportunity. A bit of initiative may be what makes it useful.",
}
HOUSE_FOCUS = {
    1:"identity, confidence and how you take up space",2:"resources, money and self-worth",
    3:"texts, conversations, learning and everyday movement",4:"home, family and feeling emotionally safe",
    5:"romance, flirting, creative expression and having fun",6:"your daily routine, workload and how you care for yourself",
    7:"close relationships, agreements and finding fair give-and-take",8:"trust, intimacy, shared responsibilities and sensitive conversations",
    9:"education, travel and the bigger ideas shaping your perspective",10:"work, public goals and how you want to be seen",
    11:"friendships, networks and what you're building for the future",12:"rest, closure and things that need quiet time to settle",
}

REFLECTION = {
    "Sun": "What deserves your energy today, and what doesn't?",
    "Moon": "What would make you feel steadier or more at ease?",
    "Mercury": "Is there a conversation you could make clearer and kinder?",
    "Venus": "Which connection or pleasure feels genuinely mutual?",
    "Mars": "Where could you be more direct without becoming reactive?",
    "Jupiter": "What possibility is worth exploring without overpromising?",
    "Saturn": "Which commitment needs a realistic next step?",
    "Uranus": "Where might a little flexibility change the whole feeling?",
    "Neptune": "What needs a boundary, a fact-check or more time?",
    "Pluto": "What pattern is worth understanding rather than controlling?",
    "TrueNode": "What would moving toward your values look like?",
    "Chiron": "How can you respond to a sensitive spot with less judgment?",
}
HOUSE_PROMPTS = {
    1: "How do you want to show up in the room?",
    2: "What feels worth your time and resources?",
    3: "Which conversation or small learning moment matters?",
    4: "What would help your home life feel more supportive?",
    5: "Can you make room for play, creativity or affection?",
    6: "Which everyday habit would make your week easier?",
    7: "What makes a one-to-one connection feel fair?",
    8: "Where is trust asking for an honest conversation?",
    9: "What new perspective is worth taking seriously?",
    10: "What do you want your work to say about you?",
    11: "Who helps you feel part of something bigger?",
    12: "Where do you need quiet or a gentler pace?",
}
SLOW = {"Saturn", "Jupiter", "Uranus", "Neptune", "Pluto", "Chiron", "TrueNode"}


def _human_aspect(row: dict[str, Any]) -> str:
    return f"{row['transit']} {str(row['aspect']).lower()} your natal {row['natal']}"


def _aspect_story(row: dict[str, Any]) -> dict[str, Any]:
    moving = str(row.get("transit") or "")
    receiving = str(row.get("natal") or "")
    name = str(row.get("aspect") or "")
    orb = float(row.get("orb", 0))
    approaching = bool(row.get("applying"))
    movement = (
        "It's moving closer to exactness over the next six hours."
        if approaching else "It's moving away from exactness over the next six hours."
    )
    scope = "a longer-running background theme" if moving in SLOW else "a shorter-lived nudge"
    scene = PAIR_SCENES.get((moving, receiving), GENERIC_SCENES.get(receiving,
            f"You may want to reflect on {NATAL_TOPICS.get(receiving, 'a personal theme')} at your own pace."))
    emphasis = ASPECT_ADVICE.get(name, "Notice what this contact brings up.")
    summary = f"{scene} {emphasis}"

    return {
        "title": f"{moving} {name.lower()} your natal {receiving}",
        "transit": moving,
        "natal": receiving,
        "aspect": name,
        "orb": round(orb, 2),
        "motion": "Getting closer" if approaching else "Moving apart",
        "movement_note": movement,
        "scope": scope,
        "summary": summary,
        "try_this": REFLECTION.get(receiving, "What feels useful to notice today?"),
    }


def build_transit_reading(data: dict[str, Any], natal: dict[str, Any]) -> dict[str, Any]:
    """Provide readable chart-specific insight whether or not an LLM API is configured."""
    raw_rows = data.get("top_aspects") or []
    aspect_stories = [_aspect_story(row) for row in raw_rows[:5]]
    first = aspect_stories[0] if aspect_stories else None
    date_iso = str(data.get("target_utc") or "")
    try:
        day = datetime.fromisoformat(date_iso.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        day = "Selected day"
    if first:
        headline = {
            "Sun": "A closer look at your own direction",
            "Moon": "Give your feelings some room",
            "Mercury": "There's something worth talking through",
            "Venus": "A little honesty about connection",
            "Mars": "Where your energy wants to go",
            "MC": "Your next move matters more than the noise",
            "DSC": "Your one-to-one connections are in focus",
            "Saturn": "Finding your own sustainable pace",
        }.get(first["natal"], "Here's what stands out in your sky")
        lede = (
            f"The strongest contact for {day} is {first['title']} ({first['orb']:.2f}° orb). "
            "That tells us which part of your natal chart is most activated right now. "
            "Let's translate it into something you might actually recognize in everyday life."
        )
    else:
        headline = "A quieter transit picture today"
        lede = (
            "No major transit-to-natal aspects fall within the tighter orbs used by AstroMYLA right now. "
            "That doesn't mean nothing is happening; it just means this particular filter isn't flagging a dominant contact."
        )
    raw_houses = data.get("house_overlays") or []
    priority = {"Sun": 0, "Moon": 1, "Venus": 2, "Mars": 3, "Mercury": 4, "Jupiter": 5, "Saturn": 6}
    ranked_houses = sorted(raw_houses, key=lambda h: (priority.get(h.get("planet"), 7), str(h.get("planet"))))
    house_stories = []
    for h in ranked_houses[:4]:
        planet = str(h.get("planet") or "")
        house = int(h.get("house") or 0)
        if not 1 <= house <= 12:
            continue
        theme = str(h.get("theme") or "that part of your life")
        house_label = f"{house}{'st' if house == 1 else 'nd' if house == 2 else 'rd' if house == 3 else 'th'}"
        house_stories.append({
            "title": f"{planet} in your natal {house_label} house",
            "planet": planet,
            "house": house,
            "summary": f"{planet} is passing through the {house_label} house of your natal chart, putting some emphasis on {HOUSE_FOCUS.get(house, theme)}. It doesn't promise an event; it suggests where paying a little more attention could be useful.",
            "prompt": HOUSE_PROMPTS.get(house, "What could use your attention?"),
        })
    return {
        "date": day,
        "headline": headline,
        "intro": lede,
        "key_aspects": aspect_stories,
        "house_stories": house_stories,
        "birth_time_note": (
            "Your birth time is unknown, so houses, angles and time-sensitive natal Moon contacts are left out rather than guessed."
            if natal.get("time_unknown") else ""
        ),
        "closing": "Take what feels useful, leave what doesn't. A transit is a symbolic lens, not a verdict or a scientific forecast.",
    }


def render_transit_reading(reading: dict[str, Any]) -> str:
    parts = ["### Your sky, explained", str(reading["intro"])]
    aspects = reading.get("key_aspects") or []
    if aspects:
        parts.append("\n### The strongest contacts")
        for item in aspects:
            parts.extend([
                f"**{item['title']}** — orb {float(item['orb']):.2f}° · {item['motion'].lower()}.",
                item["summary"],
                f"Try asking yourself: {item['try_this']}",
            ])
    houses = reading.get("house_stories") or []
    if houses:
        parts.append("\n### Where this touches everyday life")
        for h in houses:
            parts.extend([f"**{h['title']}**", h["summary"], h["prompt"]])
    if reading.get("birth_time_note"):
        parts.extend(["\n### About your birth-time precision", reading["birth_time_note"]])
    parts.extend(["\n### A reminder", reading["closing"]])
    return "\n\n".join(parts)
