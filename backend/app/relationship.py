from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from .chart import ASPECTS, MAJOR_PLANET_NAMES, angular_separation, deg_to_sign, wrap360

SYNASTRY_ORBS = {
    "Conjunction": 6.0,
    "Opposition": 6.0,
    "Trine": 5.0,
    "Square": 5.0,
    "Sextile": 4.0,
}

RELATIONSHIP_BODIES = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "TrueNode", "Lilith", "Chiron",
]
RELATIONSHIP_POINTS = ["Asc", "DSC", "MC", "IC", "Vertex"]


def _eligible_objects(chart: Dict[str, Any], prefix: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    unknown = bool(chart.get("time_unknown"))
    planets = chart.get("planets") or {}
    points = chart.get("points") or {}

    for name in RELATIONSHIP_BODIES:
        body = planets.get(name) or {}
        if body.get("lon") is None or not body.get("available", True):
            continue
        # The Moon can move ~12-15 deg/day; do not use a noon-only Moon in
        # relationship aspects when birth time is unknown.
        if unknown and name == "Moon":
            continue
        out[f"{prefix}:{name}"] = {"lon": float(body["lon"]), "kind": "planet", "name": name}

    if not unknown:
        for name in RELATIONSHIP_POINTS:
            point = points.get(name) or {}
            if point.get("lon") is None:
                continue
            out[f"{prefix}:{name}"] = {"lon": float(point["lon"]), "kind": "point", "name": name}
    return out


def compute_cross_aspects(chart_a: Dict[str, Any], chart_b: Dict[str, Any]) -> List[Dict[str, Any]]:
    a = _eligible_objects(chart_a, "A")
    b = _eligible_objects(chart_b, "B")
    out: List[Dict[str, Any]] = []

    for key_a, obj_a in a.items():
        for key_b, obj_b in b.items():
            sep = angular_separation(float(obj_a["lon"]), float(obj_b["lon"]))
            for aspect_name, exact in ASPECTS.items():
                orb = abs(sep - exact)
                if orb <= SYNASTRY_ORBS[aspect_name]:
                    out.append({
                        "a": obj_a["name"],
                        "b": obj_b["name"],
                        "aspect": aspect_name,
                        "sep": float(sep),
                        "orb": float(orb),
                        "a_kind": obj_a["kind"],
                        "b_kind": obj_b["kind"],
                    })
                    break

    out.sort(key=lambda x: (float(x["orb"]), x["a"], x["b"]))
    return out


def _midpoint_shortest(a: float, b: float) -> float:
    a = wrap360(a)
    b = wrap360(b)
    delta = ((b - a + 540.0) % 360.0) - 180.0
    return wrap360(a + delta / 2.0)


def _numeric_cusps(chart: Dict[str, Any]) -> List[float]:
    cusps = ((chart.get("houses") or {}).get("cusps") or [])
    if isinstance(cusps, list) and len(cusps) == 12 and all(isinstance(v, (int, float)) for v in cusps):
        return [wrap360(float(v)) for v in cusps]
    return []


def _house_from_cusps(lon: float, cusps: List[float]) -> int | None:
    if len(cusps) != 12:
        return None
    x = wrap360(lon)
    for i in range(12):
        start = wrap360(cusps[i])
        end = wrap360(cusps[(i + 1) % 12])
        span = (end - start) % 360.0
        pos = (x - start) % 360.0
        if pos < span or (i == 11 and abs(pos - span) < 1e-9):
            return i + 1
    return None


def compute_composite_chart(chart_a: Dict[str, Any], chart_b: Dict[str, Any]) -> Dict[str, Any]:
    planets_a = chart_a.get("planets") or {}
    planets_b = chart_b.get("planets") or {}
    points_a = chart_a.get("points") or {}
    points_b = chart_b.get("points") or {}
    both_timed = not chart_a.get("time_unknown") and not chart_b.get("time_unknown")

    composite_cusps: List[float] = []
    if both_timed:
        ca, cb = _numeric_cusps(chart_a), _numeric_cusps(chart_b)
        if len(ca) == 12 and len(cb) == 12:
            composite_cusps = [_midpoint_shortest(a, b) for a, b in zip(ca, cb)]

    planets: Dict[str, Dict[str, Any]] = {}
    for name in RELATIONSHIP_BODIES:
        pa, pb = planets_a.get(name) or {}, planets_b.get(name) or {}
        if pa.get("lon") is None or pb.get("lon") is None:
            continue
        if (chart_a.get("time_unknown") or chart_b.get("time_unknown")) and name == "Moon":
            continue
        lon = _midpoint_shortest(float(pa["lon"]), float(pb["lon"]))
        sign, deg = deg_to_sign(lon)
        house = _house_from_cusps(lon, composite_cusps)
        planets[name] = {
            "available": True, "lon": lon, "lat": 0.0, "sign": sign, "deg_in_sign": deg,
            "house": house, "house_pos": None, "retrograde": None,
            "time_precision": "derived_midpoint", "sign_uncertain": False, "possible_signs": [sign],
        }

    points: Dict[str, Dict[str, Any]] = {}
    if both_timed:
        for name in RELATIONSHIP_POINTS:
            pa, pb = points_a.get(name) or {}, points_b.get(name) or {}
            if pa.get("lon") is None or pb.get("lon") is None:
                continue
            lon = _midpoint_shortest(float(pa["lon"]), float(pb["lon"]))
            sign, deg = deg_to_sign(lon)
            points[name] = {"lon": lon, "sign": sign, "deg_in_sign": deg}

    aspect_objects = {name: p for name, p in planets.items() if name in MAJOR_PLANET_NAMES}
    aspects: List[Dict[str, Any]] = []
    names = list(aspect_objects)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p1, p2 = names[i], names[j]
            sep = angular_separation(float(planets[p1]["lon"]), float(planets[p2]["lon"]))
            for aspect_name, exact in ASPECTS.items():
                max_orb = SYNASTRY_ORBS[aspect_name]
                orb = abs(sep - exact)
                if orb <= max_orb:
                    aspects.append({"p1": p1, "p2": p2, "aspect": aspect_name, "exact": exact, "sep": sep, "orb": orb})
                    break
    aspects.sort(key=lambda x: float(x["orb"]))

    if composite_cusps:
        signs = [deg_to_sign(c)[0] for c in composite_cusps]
        houses = {
            "available": True, "cusps": composite_cusps, "signs": signs,
            "system": "midpoint-cusps", "ascendant": (points.get("Asc") or {}).get("lon"),
            "reason": None,
        }
    else:
        houses = {
            "available": False, "cusps": [], "signs": [], "system": None,
            "reason": "both_exact_birth_times_required_for_composite_midpoint_houses",
        }

    return {
        "method": "zodiacal_midpoint",
        "method_note": (
            "Composite planets are shortest-arc zodiacal midpoints between the two natal charts. "
            "When both birth times are known, corresponding natal angles and house cusps are also midpointed "
            "to create symbolic composite houses; they are not a literal event chart for a real place and time."
        ),
        "time_unknown": bool(chart_a.get("time_unknown") or chart_b.get("time_unknown")),
        "house_system": "midpoint-cusps" if composite_cusps else None,
        "planets": planets, "points": points, "houses": houses,
        "aspects": {"planet_aspects": aspects, "other_aspects": []},
    }


_ASPECT_TONE = {
    "Conjunction": "fuses the two functions so they are hard to experience separately",
    "Opposition": "creates a strong polarity that asks for awareness of both sides",
    "Trine": "creates an easy current that can feel natural and supportive",
    "Square": "creates friction, chemistry and a repeated need to adjust",
    "Sextile": "creates a cooperative opening that grows when the pair actively uses it",
}

_BODY_THEME = {
    "Sun": "identity, confidence and life direction", "Moon": "emotional needs, comfort and instinct",
    "Mercury": "communication, interpretation and mental rhythm", "Venus": "affection, attraction and values",
    "Mars": "desire, initiative, conflict and pace", "Jupiter": "encouragement, growth and meaning",
    "Saturn": "commitment, responsibility, fear and durability", "Uranus": "freedom, surprise and change",
    "Neptune": "idealization, empathy, imagination and blurred boundaries", "Pluto": "intensity, power and transformation",
    "TrueNode": "growth direction", "Lilith": "raw boundaries and unfiltered desire", "Chiron": "sensitive spots and repair",
    "Asc": "instinctive style and first impressions", "DSC": "partnership expectations", "MC": "public direction",
    "IC": "private roots and emotional base", "Vertex": "turning-point sensitivity",
}

_HOUSE_THEME = {
    1: "identity, body and immediate self-expression", 2: "money, values and self-worth",
    3: "communication, learning and everyday exchange", 4: "home, family and emotional roots",
    5: "romance, pleasure, creativity and play", 6: "daily life, work habits and care routines",
    7: "partnership, commitment and one-to-one relating", 8: "intimacy, trust, shared resources and vulnerability",
    9: "beliefs, travel, study and perspective", 10: "career, visibility and long-term direction",
    11: "friendship, community and future plans", 12: "privacy, unconscious material, retreat and hidden sensitivities",
}

_SIGN_TONE = {
    "Aries": "direct, fast-moving and willing to initiate",
    "Taurus": "steady, sensory and motivated by consistency",
    "Gemini": "curious, verbal and mentally changeable",
    "Cancer": "protective, emotionally responsive and security-seeking",
    "Leo": "expressive, proud, warm and eager to create something visible",
    "Virgo": "observant, practical and oriented toward adjustment and improvement",
    "Libra": "relational, diplomatic and sensitive to balance and reciprocity",
    "Scorpio": "intense, private and drawn toward depth, trust and transformation",
    "Sagittarius": "open, exploratory and motivated by meaning, truth and possibility",
    "Capricorn": "structured, deliberate and concerned with durability and responsibility",
    "Aquarius": "independent, unconventional and oriented toward freedom and shared ideas",
    "Pisces": "sensitive, imaginative and receptive to emotional atmosphere",
}


def _name(chart: Dict[str, Any], fallback: str) -> str:
    name = str(chart.get("name") or "").strip()
    return name or fallback


def _aspect_sentence(item: Dict[str, Any], a_name: str, b_name: str) -> str:
    a, b, asp = item["a"], item["b"], item["aspect"]
    orb = float(item["orb"])
    ta, tb = _BODY_THEME.get(a, a.lower()), _BODY_THEME.get(b, b.lower())
    tone = _ASPECT_TONE.get(asp, "links the two functions")
    return f"**{a_name} {a} {asp} {b_name} {b}** (orb {orb:.2f}°) connects {ta} with {tb}; the aspect {tone}."


def build_synastry_interpretation(chart_a: Dict[str, Any], chart_b: Dict[str, Any], aspects: List[Dict[str, Any]], overlays: Dict[str, Any] | None = None) -> str:
    a_name, b_name = _name(chart_a, "Person A"), _name(chart_b, "Person B")
    overlays = overlays or {}
    lines = [
        f"### {a_name} × {b_name} — the relationship pattern",
        "Synastry is a comparison of two complete natal charts. It is most useful when you read it as an interaction pattern: what feels easy, what repeatedly activates each person, and where the relationship asks for more awareness. It is not a compatibility score or a verdict on whether a relationship should exist.",
    ]
    if chart_a.get("time_unknown") or chart_b.get("time_unknown"):
        lines.append("One or both birth times are unknown, so time-sensitive Moon contacts, angles and any house overlay that depends on the unknown chart are left out rather than guessed.")
    if not aspects:
        lines.append("\nNo major cross-chart aspects fell inside the configured orbs, so there is not enough reliable inter-aspect data for a detailed synastry reading.")
        return "\n".join(lines)

    lines.append("\n### The strongest threads between you")
    for item in aspects[:8]:
        lines.append("- " + _aspect_sentence(item, a_name, b_name))

    groups = {
        "### Emotional closeness and safety": [x for x in aspects if "Moon" in {x["a"], x["b"]} or "Sun" in {x["a"], x["b"]}],
        "### Communication and being understood": [x for x in aspects if "Mercury" in {x["a"], x["b"]}],
        "### Attraction, desire and chemistry": [x for x in aspects if ({x["a"], x["b"]} & {"Venus","Mars","Pluto","Lilith"}) and ({x["a"], x["b"]} & {"Venus","Mars"})],
        "### Commitment, growth and pressure points": [x for x in aspects if {x["a"], x["b"]} & {"Saturn","Jupiter","Uranus","Neptune","Pluto"}],
    }
    used: set[tuple[str,str,str]] = set()
    for heading, rows in groups.items():
        unique=[]
        for x in rows:
            key=(x["a"],x["aspect"],x["b"])
            if key in used: continue
            used.add(key); unique.append(x)
        if not unique: continue
        lines.append("\n"+heading)
        for x in unique[:5]: lines.append("- "+_aspect_sentence(x,a_name,b_name))

    a_in_b = overlays.get("a_in_b_houses") or []
    b_in_a = overlays.get("b_in_a_houses") or []
    if a_in_b or b_in_a:
        lines.append("\n### Where you enter each other’s lives — house overlays")
        for visitor, host, rows in [(a_name,b_name,a_in_b),(b_name,a_name,b_in_a)]:
            if not rows: continue
            for row in rows[:10]:
                h=int(row["house"]); theme=_HOUSE_THEME.get(h,"this area of life")
                lines.append(f"- **{visitor} {row['planet']} in {host}’s {h}th house** tends to activate {theme}. The planet describes what {visitor} brings; the house describes where {host} is most likely to feel it.")

    lines.extend([
        "\n### What to pay attention to in real life",
        "The tightest aspects usually speak the loudest, but repetition matters just as much: if several contacts keep pointing toward communication, autonomy, reassurance, attraction or boundaries, that repeated theme is more useful than isolating one dramatic aspect.",
        "Notice directionality too. A planet landing in the other person’s house is experienced from two sides: one person brings the planetary function, while the other experiences it in a particular area of life. Swapping the inner/outer chart on the bi-wheel helps you see both perspectives.",
        "The most useful question is not ‘Is this good or bad?’ but ‘What does this connection reliably bring out in each of us, and do we like how we handle that together?’",
    ])
    return "\n".join(lines)


def _placement_line(name: str, p: Dict[str, Any]) -> str | None:
    if not p or not p.get("sign"): return None
    deg=float(p.get("deg_in_sign",0.0)); house=p.get("house")
    hs=f", House {house}" if house else ""
    return f"**Composite {name}: {p['sign']} {deg:.1f}°{hs}**"


def build_composite_interpretation(composite: Dict[str, Any], label: str = "Relationship") -> str:
    planets = composite.get("planets") or {}
    aspects = (composite.get("aspects") or {}).get("planet_aspects") or []
    houses_available = bool((composite.get("houses") or {}).get("available"))

    def describe_body(name: str, role: str) -> str | None:
        p = planets.get(name) or {}
        if not p.get("sign"):
            return None
        sign = str(p["sign"])
        tone = _SIGN_TONE.get(sign, "distinctive")
        house = p.get("house")
        house_phrase = ""
        if house:
            house_phrase = f" Because it falls in the composite {int(house)}th house, this pattern is especially likely to become visible through {_HOUSE_THEME.get(int(house), 'that area of shared life')}."
        return f"**Composite {name} in {sign}** describes {role}. Here the relationship tends to become {tone}.{house_phrase}"

    lines = [
        f"### {label} — the relationship as a third pattern",
        "A midpoint composite is not either person's natal chart and it is not a compatibility score. It is a symbolic chart made from the midpoints between the two natal charts, used to describe the atmosphere that tends to emerge when the relationship operates as a unit: what the bond seems to organize around, how closeness works inside it, and which themes become difficult to ignore.",
    ]
    if houses_available:
        lines.append("Because both birth times are known, the chart also includes midpointed angles and corresponding house cusps. These are symbolic composite houses, not the houses of a literal event chart at a real place and time.")
    else:
        lines.append("Composite houses are omitted because one or both exact birth times are unavailable. The planetary midpoint pattern can still be read without inventing angles or houses.")

    lines.append("\n### Core identity and emotional climate")
    for name, role in [
        ("Sun", "the relationship's central identity, purpose and the kind of 'we' it naturally tries to become"),
        ("Moon", "the emotional climate of the bond: what helps it feel safe, familiar and instinctively connected"),
    ]:
        text = describe_body(name, role)
        if text:
            lines.append(text)

    lines.append("\n### Communication and the shared mental rhythm")
    text = describe_body("Mercury", "how the relationship talks, interprets events, makes decisions and creates a shared narrative")
    if text:
        lines.append(text)
    lines.append("In practice, composite Mercury is useful for noticing what conversations keep returning, whether the pair processes tension by talking, withdrawing, analyzing or acting first, and what kind of language helps both people feel included in the same story.")

    lines.append("\n### Affection, attraction and conflict style")
    for name, role in [
        ("Venus", "how affection, pleasure, tenderness, taste and shared values tend to flow between you"),
        ("Mars", "how the bond pursues desire, handles irritation, takes action and moves through disagreement"),
    ]:
        text = describe_body(name, role)
        if text:
            lines.append(text)
    lines.append("Venus and Mars are most useful when read together: one describes what makes the relationship feel worth enjoying, while the other shows what gives it heat, momentum and sometimes friction.")

    lines.append("\n### Growth, commitment and staying power")
    for name, role in [
        ("Jupiter", "where the relationship tends to seek growth, encouragement, perspective and a sense of possibility"),
        ("Saturn", "where responsibility, limits, fear, commitment and long-term construction become especially important"),
    ]:
        text = describe_body(name, role)
        if text:
            lines.append(text)
    lines.append("Jupiter can show where the pair easily says 'yes' or imagines more, while Saturn shows where the relationship eventually has to become concrete. Neither is automatically good or bad: too much expansion can overpromise, and too much structure can become heavy if it is not chosen consciously.")

    outer_rows = []
    for name, role in [
        ("Uranus", "freedom, disruption, experimentation and the need to keep the bond alive rather than stale"),
        ("Neptune", "imagination, idealization, empathy and the places where clarity or boundaries can become softer"),
        ("Pluto", "intensity, power, vulnerability and the transformations that can change how the relationship understands itself"),
    ]:
        text = describe_body(name, role)
        if text:
            outer_rows.append(text)
    if outer_rows:
        lines.append("\n### Freedom, idealization and deeper transformation")
        lines.extend(outer_rows)
        lines.append("These slower-planet themes often feel less like everyday personality and more like a background pressure or developmental theme. They matter most when repeated by tight aspects or by several placements pointing toward the same issue.")

    if houses_available:
        occupied: dict[int, list[str]] = {}
        for name, p in planets.items():
            h = p.get("house") if isinstance(p, dict) else None
            if isinstance(h, int):
                occupied.setdefault(h, []).append(name)
        if occupied:
            lines.append("\n### Where the relationship concentrates its energy")
            for h, names in sorted(occupied.items()):
                if not names:
                    continue
                joined = ", ".join(names)
                lines.append(f"- **Composite House {h}: {joined}** — this puts repeated attention on {_HOUSE_THEME.get(h, 'this area of shared life')}. The house tells you where the relationship tends to become especially active; the planets tell you what kind of energy is brought there.")

    if aspects:
        lines.append("\n### The aspect stories that shape the bond")
        for a in aspects[:14]:
            t1 = _BODY_THEME.get(a['p1'], a['p1'].lower())
            t2 = _BODY_THEME.get(a['p2'], a['p2'].lower())
            tone = _ASPECT_TONE.get(a['aspect'], "links the two functions")
            lines.append(f"- **{a['p1']} {a['aspect']} {a['p2']}** (orb {float(a['orb']):.2f}°) ties {t1} to {t2}; it {tone}.")

        hard = [a for a in aspects if a.get("aspect") in {"Square", "Opposition"}]
        soft = [a for a in aspects if a.get("aspect") in {"Trine", "Sextile"}]
        conj = [a for a in aspects if a.get("aspect") == "Conjunction"]
        lines.append("\n### Repeating patterns and contradictions")
        if conj:
            lines.append(f"There are {len(conj)} conjunction theme(s), which suggests that some relationship functions are tightly fused and can be hard to separate from one another.")
        if hard:
            lines.append(f"There are {len(hard)} square/opposition theme(s). These are not automatic failure signatures; they are the places where the relationship is most likely to require adjustment, honesty and a workable way to hold two competing needs at once.")
        if soft:
            lines.append(f"There are {len(soft)} trine/sextile theme(s), showing areas where cooperation may feel more available. Easy aspects still need to be used intentionally rather than taken for granted.")
        lines.append("Pay special attention when the same planets appear several times across the tightest aspects. Repetition is usually more informative than treating one dramatic contact as the whole story.")

    lines.extend([
        "\n### How to use this chart with synastry",
        "The composite describes the relationship's internal weather; synastry describes two separate people activating each other. Read them together. A beautiful composite theme does not erase difficult inter-personal contacts, and a tense composite pattern does not automatically make a relationship unhealthy.",
        "A practical way to use the two techniques is to ask three questions: What keeps repeating in the composite? Which synastry contacts trigger that same theme between the two people? And what does the pair actually do with it in real life? That last question matters more than any single symbol.",
    ])
    return "\n".join(lines)

