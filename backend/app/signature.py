from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List

ELEMENT_BY_SIGN = {
    "Aries":"Fire","Leo":"Fire","Sagittarius":"Fire",
    "Taurus":"Earth","Virgo":"Earth","Capricorn":"Earth",
    "Gemini":"Air","Libra":"Air","Aquarius":"Air",
    "Cancer":"Water","Scorpio":"Water","Pisces":"Water",
}
MODALITY_BY_SIGN = {
    "Aries":"Cardinal","Cancer":"Cardinal","Libra":"Cardinal","Capricorn":"Cardinal",
    "Taurus":"Fixed","Leo":"Fixed","Scorpio":"Fixed","Aquarius":"Fixed",
    "Gemini":"Mutable","Virgo":"Mutable","Sagittarius":"Mutable","Pisces":"Mutable",
}
RULER_BY_SIGN = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon","Leo":"Sun","Virgo":"Mercury",
    "Libra":"Venus","Scorpio":"Pluto","Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Uranus","Pisces":"Neptune",
}
SIGN_TRAITS = {
    "Aries":["direct","self-starting","energetic"], "Taurus":["steady","sensual","consistent"],
    "Gemini":["curious","verbal","adaptable"], "Cancer":["protective","tender","emotionally attentive"],
    "Leo":["warm","expressive","confident"], "Virgo":["observant","practical","thoughtful"],
    "Libra":["relational","fair-minded","graceful"], "Scorpio":["intense","private","loyal"],
    "Sagittarius":["open-minded","adventurous","frank"], "Capricorn":["reliable","mature","goal-oriented"],
    "Aquarius":["independent","original","mentally stimulating"], "Pisces":["empathetic","imaginative","gentle"],
}
ELEMENT_NEEDS = {
    "Fire":"warm, direct and alive", "Earth":"steady, dependable and grounded",
    "Air":"mentally responsive, curious and communicative", "Water":"emotionally attuned, gentle and safe",
}
ELEMENT_COMMUNICATION = {
    "Fire":"clear, candid and willing to address things quickly", "Earth":"concrete, consistent and willing to follow through",
    "Air":"curious, articulate and able to keep a conversation moving", "Water":"emotionally perceptive and able to hear what is underneath the words",
}
ELEMENT_REPAIR = {
    "Fire":"name the issue directly, clear the air, then reconnect through action", "Earth":"slow the pace, make the next step concrete, and rebuild trust through consistency",
    "Air":"talk it through without cornering either person, then agree on what each person actually means",
    "Water":"lower the emotional temperature first, acknowledge the feeling, and only then solve the problem",
}
MODALITY_STYLE = {
    "Cardinal":"initiating", "Fixed":"consistent", "Mutable":"flexible",
}
HOUSE_THEMES = {
    1:"identity and first impressions", 2:"values, security and resources", 3:"communication and everyday exchange",
    4:"home, family and emotional roots", 5:"romance, pleasure and creativity", 6:"daily life, care and practical routines",
    7:"partnership and one-to-one relating", 8:"intimacy, trust and transformation", 9:"beliefs, travel and perspective",
    10:"career, visibility and direction", 11:"friendship, community and future plans", 12:"privacy, vulnerability and the unconscious",
}


def _body(chart: Dict[str, Any], name: str) -> Dict[str, Any]:
    return (chart.get("planets") or {}).get(name) or {}


def _point(chart: Dict[str, Any], name: str) -> Dict[str, Any]:
    return (chart.get("points") or {}).get(name) or {}


def _sign(chart: Dict[str, Any], name: str) -> str | None:
    if name in (chart.get("planets") or {}):
        obj = _body(chart, name)
    else:
        obj = _point(chart, name)
    sign = obj.get("sign")
    return str(sign) if sign else None


def _all_aspects(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    a = chart.get("aspects") or {}
    return list(a.get("planet_aspects") or []) + list(a.get("other_aspects") or [])


def _aspect_rows(chart: Dict[str, Any], body: str) -> List[Dict[str, Any]]:
    rows = [r for r in _all_aspects(chart) if r.get("p1") == body or r.get("p2") == body]
    return sorted(rows, key=lambda r: float(r.get("orb") or 99.0))


def _unique(values: Iterable[str], limit: int = 5) -> List[str]:
    out: List[str] = []
    for value in values:
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def _element(sign: str | None) -> str:
    return ELEMENT_BY_SIGN.get(sign or "", "Air")


def _modality(sign: str | None) -> str:
    return MODALITY_BY_SIGN.get(sign or "", "Mutable")


def _trait_scores(chart: Dict[str, Any]) -> tuple[dict[str,float], dict[str,float]]:
    element = defaultdict(float)
    modality = defaultdict(float)
    weights = {"Sun":2.2,"Moon":2.2,"Mercury":1.2,"Venus":1.5,"Mars":1.5,"Jupiter":0.7,"Saturn":1.0,"Uranus":0.45,"Neptune":0.45,"Pluto":0.45}
    for name, weight in weights.items():
        sign = _sign(chart, name)
        if sign:
            element[_element(sign)] += weight
            modality[_modality(sign)] += weight
    asc = _sign(chart, "Asc")
    if asc:
        element[_element(asc)] += 1.8
        modality[_modality(asc)] += 1.8
    return dict(element), dict(modality)


def _top_key(values: dict[str,float], fallback: str) -> str:
    return max(values, key=values.get) if values else fallback


def _signature_headline(element: str, modality: str) -> str:
    adjectives = {"Fire":"Magnetic","Earth":"Grounded","Air":"Electric","Water":"Intuitive"}
    nouns = {"Cardinal":"Initiator","Fixed":"Anchor","Mutable":"Explorer"}
    return f"The {adjectives.get(element,'Layered')} {nouns.get(modality,'Explorer')}"


def _aspect_watchouts(chart: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    hard = {"Square","Opposition"}
    for row in sorted(_all_aspects(chart), key=lambda r: float(r.get("orb") or 99.0)):
        if row.get("aspect") not in hard or float(row.get("orb") or 99.0) > 5.0:
            continue
        pair = {str(row.get("p1")), str(row.get("p2"))}
        if "Moon" in pair and "Pluto" in pair:
            out.append("feelings can become all-or-nothing when trust feels uncertain")
        elif "Venus" in pair and "Neptune" in pair:
            out.append("romantic idealization can outrun the available evidence")
        elif "Mercury" in pair and "Saturn" in pair:
            out.append("you may edit yourself too heavily before saying what you mean")
        elif "Sun" in pair and "Saturn" in pair:
            out.append("self-expectations can become harsher than the situation requires")
        elif "Mars" in pair and "Jupiter" in pair:
            out.append("momentum can turn into overextension before you notice the limit")
        elif "Moon" in pair and "Uranus" in pair:
            out.append("closeness and independence may need conscious pacing")
        elif "Venus" in pair and "Pluto" in pair:
            out.append("attraction can intensify quickly and make boundaries especially important")
        if len(out) >= 3:
            break
    return _unique(out or ["you may need both closeness and enough room to stay fully yourself"], 3)


def build_astromyla_signature(chart: Dict[str, Any]) -> Dict[str, Any]:
    elem, mod = _trait_scores(chart)
    top_elem, top_mod = _top_key(elem, "Air"), _top_key(mod, "Mutable")
    sun, moon, asc = _sign(chart,"Sun"), _sign(chart,"Moon"), _sign(chart,"Asc")
    core = []
    for sign in (sun, moon, asc):
        core.extend(SIGN_TRAITS.get(sign or "", []))
    core = _unique(core, 5)
    needs = []
    if moon:
        needs.extend([ELEMENT_NEEDS[_element(moon)], *SIGN_TRAITS.get(moon, [])[:2]])
    if _sign(chart,"Venus"):
        needs.extend(SIGN_TRAITS[_sign(chart,"Venus")][:2])
    return {
        "headline": _signature_headline(top_elem, top_mod),
        "core_energy": _unique(core, 4),
        "needs": _unique(needs, 4),
        "watch_outs": _aspect_watchouts(chart),
        "dominant_element": top_elem,
        "dominant_modality": top_mod,
        "summary": f"A {top_elem.lower()}-leaning, {MODALITY_STYLE.get(top_mod, 'flexible')} chart signature: you tend to do best when your individuality and emotional needs can coexist rather than compete.",
        "evidence": _unique([f"Sun in {sun}" if sun else "", f"Moon in {moon}" if moon else "", f"Ascendant in {asc}" if asc else "", f"{top_elem} emphasis", f"{top_mod} emphasis"], 5),
        "method_note": "This is a descriptive AstroMYLA synthesis from the chart's major placements, angles, elemental/modality emphasis and tight aspects. It is not a personality diagnosis.",
    }


def _seventh_house_context(chart: Dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    if chart.get("time_unknown"):
        return None, None, None
    signs = (chart.get("houses") or {}).get("signs") or []
    seventh = str(signs[6]) if isinstance(signs, list) and len(signs) >= 7 and signs[6] else _sign(chart, "DSC")
    ruler = RULER_BY_SIGN.get(seventh or "")
    ruler_sign = _sign(chart, ruler) if ruler else None
    return seventh, ruler, ruler_sign


def build_partner_blueprint(chart: Dict[str, Any]) -> Dict[str, Any]:
    moon, mercury, venus, mars, saturn = (_sign(chart,n) for n in ("Moon","Mercury","Venus","Mars","Saturn"))
    seventh, ruler, ruler_sign = _seventh_house_context(chart)

    emotional = ELEMENT_NEEDS[_element(moon)] if moon else "emotionally respectful and responsive"
    communication = ELEMENT_COMMUNICATION[_element(mercury)] if mercury else "clear and responsive"
    attraction_traits = _unique((SIGN_TRAITS.get(venus or "", []) + SIGN_TRAITS.get(mars or "", []) + SIGN_TRAITS.get(seventh or "", [])), 4)
    long_term_traits = _unique((SIGN_TRAITS.get(seventh or "", []) + SIGN_TRAITS.get(ruler_sign or "", []) + SIGN_TRAITS.get(saturn or "", [])), 4)
    best = _unique([*SIGN_TRAITS.get(moon or "", [])[:2], *SIGN_TRAITS.get(seventh or "", [])[:2], *SIGN_TRAITS.get(ruler_sign or "", [])[:2]], 4)

    evidence = [f"Moon in {moon}" if moon else "", f"Venus in {venus}" if venus else "", f"Mars in {mars}" if mars else ""]
    if seventh:
        evidence.append(f"7th-house cusp / Descendant in {seventh}")
    if ruler and ruler_sign:
        evidence.append(f"7th-house ruler {ruler} in {ruler_sign}")

    return {
        "headline": "Your Ideal Partner Blueprint",
        "emotional_style": emotional,
        "communication": communication,
        "attraction": attraction_traits,
        "long_term": long_term_traits,
        "best_match_energy": best,
        "summary": "This profile describes relationship qualities your chart is more likely to work well with; it does not name one destined sign or guarantee compatibility.",
        "evidence": _unique(evidence, 6),
        "time_note": None if seventh else "Birth time is unknown, so the 7th house and its ruler are intentionally excluded from this profile.",
    }


def build_attract_vs_need(chart: Dict[str, Any]) -> Dict[str, Any]:
    moon, venus, mars, saturn = (_sign(chart,n) for n in ("Moon","Venus","Mars","Saturn"))
    seventh, ruler, ruler_sign = _seventh_house_context(chart)
    attract = _unique([
        *SIGN_TRAITS.get(venus or "", []),
        *SIGN_TRAITS.get(mars or "", []),
        *SIGN_TRAITS.get(seventh or "", [])[:2],
    ], 5)
    need = _unique([
        *SIGN_TRAITS.get(moon or "", []),
        *SIGN_TRAITS.get(ruler_sign or "", [])[:2],
        *SIGN_TRAITS.get(saturn or "", [])[:2],
    ], 5)
    return {
        "attract": attract,
        "need": need,
        "summary": "Attraction and sustainable compatibility are not always the same pattern. AstroMYLA separates the qualities that spark interest from the qualities that tend to support emotional steadiness over time.",
        "evidence": _unique([f"Venus in {venus}" if venus else "", f"Mars in {mars}" if mars else "", f"Moon in {moon}" if moon else "", f"7th-house ruler {ruler} in {ruler_sign}" if ruler and ruler_sign else "", f"Saturn in {saturn}" if saturn else ""], 6),
    }


def build_emotional_manual(chart: Dict[str, Any]) -> Dict[str, Any]:
    moon, mercury, venus = (_sign(chart,n) for n in ("Moon","Mercury","Venus"))
    moon_el, mercury_el = _element(moon), _element(mercury)
    helps = _unique([
        ELEMENT_NEEDS[moon_el],
        f"communication that feels {ELEMENT_COMMUNICATION[mercury_el]}",
        *(SIGN_TRAITS.get(venus or "", [])[:2]),
    ], 4)
    avoid = _aspect_watchouts(chart)
    repair = ELEMENT_REPAIR[moon_el]
    reassurance = {
        "Fire":"show enthusiasm, honesty and active presence rather than vague reassurance",
        "Earth":"show reliability through concrete follow-through and predictable care",
        "Air":"keep communication open and make room for questions without treating them as distance",
        "Water":"name the emotional reality gently and create enough safety for vulnerability",
    }[moon_el]
    return {
        "headline":"Your Emotional Manual",
        "helps":helps,
        "avoid":avoid,
        "repair_style":repair,
        "reassurance":reassurance,
        "evidence":_unique([f"Moon in {moon}" if moon else "", f"Mercury in {mercury}" if mercury else "", f"Venus in {venus}" if venus else ""], 4),
    }


def build_natal_signature_suite(chart: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "signature": build_astromyla_signature(chart),
        "partner_blueprint": build_partner_blueprint(chart),
        "attract_vs_need": build_attract_vs_need(chart),
        "emotional_manual": build_emotional_manual(chart),
    }


def _pair_has(row: Dict[str, Any], a: str, b: str) -> bool:
    return {str(row.get("a")), str(row.get("b"))} == {a,b}


def _theme_from_aspect(row: Dict[str, Any]) -> tuple[str,str] | None:
    a,b,asp = str(row.get("a")),str(row.get("b")),str(row.get("aspect"))
    pair={a,b}
    tone = "easy flow" if asp in {"Trine","Sextile"} else "strong activation" if asp == "Conjunction" else "growth-producing tension"
    if {"Venus","Mars"} <= pair: return "Magnetic chemistry", f"Venus–Mars contact creates {tone} around attraction, desire and pacing."
    if "Moon" in pair and "Venus" in pair: return "Emotional warmth", f"Moon–Venus contact creates {tone} between comfort needs and affection."
    if "Moon" in pair and "Saturn" in pair: return "Security vs pressure", f"Moon–Saturn contact makes reliability, emotional pacing and responsibility a major theme."
    if "Mercury" in pair: return "Mental exchange", f"Mercury contact creates {tone} in how the pair talks, interprets and repairs misunderstandings."
    if "Saturn" in pair: return "Commitment lessons", f"Saturn contact makes boundaries, endurance, timing and responsibility difficult to ignore."
    if "Pluto" in pair: return "Transformative intensity", f"Pluto contact can make the connection psychologically intense and boundary-sensitive."
    if "Uranus" in pair: return "Freedom & electricity", f"Uranus contact adds novelty, unpredictability and a need for breathing room."
    if "Neptune" in pair: return "Idealization & sensitivity", f"Neptune contact heightens imagination and empathy, while making clarity especially valuable."
    if "Sun" in pair or "Moon" in pair: return "Core recognition", f"A luminary contact creates {tone} around identity and emotional recognition."
    return None


def _overlay_theme(house: int) -> tuple[str,str] | None:
    mapping = {
        1:("Identity activation","The visitor strongly affects self-perception, presence and first-impression chemistry."),
        4:("Home-body pull","The overlay reaches private life, emotional roots, family patterns and the feeling of home."),
        5:("Romantic spark","The overlay emphasizes attraction, play, pleasure, creativity and being noticed romantically."),
        7:("Partnership mirror","The overlay lands directly in the relationship axis, making one-to-one relating hard to treat casually."),
        8:("Deep-bond intensity","The overlay emphasizes intimacy, trust, vulnerability, shared resources and transformation."),
        10:("Public direction","The connection strongly touches ambition, visibility, achievement or long-term direction."),
        11:("Friendship & future","The connection emphasizes friendship, community, shared plans and the future."),
        12:("Private undertow","The overlay can feel subtle, private or difficult to name, so assumptions and projection need extra care."),
    }
    return mapping.get(house)


def build_myla_match(aspects: List[Dict[str, Any]], overlays: Dict[str, Any] | None = None) -> Dict[str, Any]:
    themes: List[Dict[str, Any]] = []
    seen=set()
    for row in sorted(aspects, key=lambda r: float(r.get("orb") or 99.0)):
        found=_theme_from_aspect(row)
        if not found or found[0] in seen: continue
        themes.append({"title":found[0],"description":found[1],"evidence":f"{row.get('a')} {row.get('aspect')} {row.get('b')} · orb {float(row.get('orb') or 0):.2f}°"})
        seen.add(found[0])
        if len(themes)>=3: break
    overlays=overlays or {}
    for direction,label in ((overlays.get("a_activates_b") or [],"Person A → Person B"),(overlays.get("b_activates_a") or [],"Person B → Person A")):
        for row in direction[:4]:
            h=int(row.get("house") or 0)
            found=_overlay_theme(h)
            if not found or found[0] in seen: continue
            themes.append({"title":found[0],"description":found[1],"evidence":f"{label}: House {h} activated by {int(row.get('count') or 0)} planet(s)"})
            seen.add(found[0])
            if len(themes)>=5: break
        if len(themes)>=5: break
    if not themes:
        themes=[{"title":"Subtle connection","description":"No single major theme dominates the configured synastry orbs; the relationship may be better understood through the full pattern rather than one headline contact.","evidence":"Configured major aspects and available house overlays"}]
    headline=" · ".join(t["title"] for t in themes[:3])
    return {
        "headline": headline,
        "themes": themes,
        "summary": "Myla Match highlights the strongest repeating relationship themes from tight cross-chart aspects and two-way house activation. It is not a success score or prediction.",
        "method_note": "Themes are selected deterministically from the tightest major synastry aspects and the most activated receiving houses in both directions.",
    }
