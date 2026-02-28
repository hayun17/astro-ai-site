from __future__ import annotations

import os
import json
import re
from typing import List, Dict, Optional, Any, Tuple

from openai import OpenAI


# -----------------------------
# OpenAI client
# -----------------------------
def get_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


# -----------------------------
# Helpers: parse chart from prompt
# -----------------------------
def _extract_chart_from_user_prompt(user_prompt: str) -> Optional[Dict[str, Any]]:
    if not user_prompt:
        return None

    m = re.search(r"Chart data:\s*(\{.*\})\s*$", user_prompt, flags=re.DOTALL)
    if not m:
        return None

    raw = m.group(1).strip()

    # Strategy 1: JSON parse directly
    try:
        return json.loads(raw)
    except Exception:
        pass

    # Strategy 2: best-effort coerce Python dict repr -> JSON
    coerced = raw
    coerced = coerced.replace(": None", ": null").replace(": True", ": true").replace(": False", ": false")
    coerced = re.sub(r"'", '"', coerced)

    try:
        return json.loads(coerced)
    except Exception:
        return None


def _deg_str(deg: float) -> str:
    d = int(deg)
    mins = int(round((deg - d) * 60))
    if mins == 60:
        d += 1
        mins = 0
    return f"{d}°{mins:02d}′"


def _planet_line(name: str, p: Dict[str, Any]) -> str:
    sign = p.get("sign")
    deg = p.get("deg_in_sign")
    house = p.get("house")
    if sign is None or deg is None:
        return f"- {name}: (unavailable)"
    hs = f", House {house}" if house is not None else ""
    return f"- {name}: {sign} {_deg_str(float(deg))}{hs}"


def _top_aspects(chart: Dict[str, Any], n: int = 12) -> List[Dict[str, Any]]:
    aspects = (chart.get("aspects") or {})
    planet_aspects = aspects.get("planet_aspects") or []
    other_aspects = aspects.get("other_aspects") or []
    all_aspects = [a for a in (planet_aspects + other_aspects) if isinstance(a, dict)]

    def orb_val(a: Dict[str, Any]) -> float:
        try:
            return float(a.get("orb", 999.0))
        except Exception:
            return 999.0

    return sorted(all_aspects, key=orb_val)[:n]


# -----------------------------
# Metadata stripping (works for inline tags too)
# -----------------------------
_TAG_INLINE_RE = re.compile(r"\[(TYPE|BODY|SIGN|KEY)=[^\]]+\]\s*", re.IGNORECASE)

def _strip_metadata(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    t = _TAG_INLINE_RE.sub("", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def _pick_passage_by_tags(
    passages: List[Dict[str, str]] | None,
    *,
    body: str,
    sign: str,
    typ: str | None = None,
) -> Optional[str]:
    """
    Finds a corpus passage by strict tag match:
      [BODY=XXX] [SIGN=YYY] and optionally [TYPE=...]
    Falls back to "Body in Sign" (case-insensitive).
    """
    if not passages or not body or not sign:
        return None

    body_u = body.upper()
    sign_u = sign.upper()
    typ_u = (typ or "").upper()

    # strict tag match first
    for p in passages:
        txt = (p.get("text") or "")
        if f"[BODY={body_u}]" in txt and f"[SIGN={sign_u}]" in txt:
            if typ_u:
                if f"[TYPE={typ_u}]" in txt:
                    return _strip_metadata(txt)
            else:
                return _strip_metadata(txt)

    # fallback: "Body in Sign" match
    needle = f"{body.title()} in {sign.title()}"
    for p in passages:
        txt = (p.get("text") or "")
        if needle.lower() in txt.lower():
            return _strip_metadata(txt)

    return None


# -----------------------------
# Houses: convert absolute degrees (0-360) -> sign + deg_in_sign
# -----------------------------
_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def _lon_to_sign_deg(lon: float) -> tuple[str, float]:
    x = float(lon) % 360.0
    sign_idx = int(x // 30.0)
    sign = _SIGNS[sign_idx]
    deg_in_sign = x - 30.0 * sign_idx
    return sign, deg_in_sign


def _ordinal(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _houses_12_lines(houses: Dict[str, Any]) -> List[str]:
    cusps = houses.get("cusps")
    signs = houses.get("signs")

    out: List[str] = []

    # If cusps are dicts (sign/deg_in_sign)
    if isinstance(cusps, list) and len(cusps) == 12 and isinstance(cusps[0], dict):
        for i, c in enumerate(cusps, start=1):
            sign = c.get("sign")
            deg = c.get("deg_in_sign")
            if sign is None or deg is None:
                out.append(f"- {_ordinal(i)} House: (unavailable)")
            else:
                out.append(f"- {_ordinal(i)} House: {sign} {_deg_str(float(deg))}")
        return out

    # If signs list
    if isinstance(signs, list) and len(signs) == 12:
        for i, s in enumerate(signs, start=1):
            out.append(f"- {_ordinal(i)} House: {s}")
        return out

    # If cusps are floats (0..360)
    if isinstance(cusps, list) and len(cusps) == 12 and all(isinstance(v, (int, float)) for v in cusps):
        for i, lon in enumerate(cusps, start=1):
            sign, deg_in_sign = _lon_to_sign_deg(float(lon))
            out.append(f"- {_ordinal(i)} House: {sign} {_deg_str(deg_in_sign)}")
        return out

    for i in range(1, 13):
        out.append(f"- {_ordinal(i)} House: (unavailable)")
    return out


def _houses_12_signs(houses: Dict[str, Any]) -> List[Optional[str]]:
    """
    Returns house cusp signs [1..12] as list of 12 items.
    """
    cusps = houses.get("cusps")
    signs = houses.get("signs")

    if isinstance(signs, list) and len(signs) == 12:
        return [str(s) if s else None for s in signs]

    if isinstance(cusps, list) and len(cusps) == 12 and isinstance(cusps[0], dict):
        out: List[Optional[str]] = []
        for c in cusps:
            out.append(str(c.get("sign")) if c.get("sign") else None)
        return out

    if isinstance(cusps, list) and len(cusps) == 12 and all(isinstance(v, (int, float)) for v in cusps):
        out: List[Optional[str]] = []
        for lon in cusps:
            sign, _ = _lon_to_sign_deg(float(lon))
            out.append(sign)
        return out

    return [None] * 12


# -----------------------------
# Corpus-only fallback writer (UPDATED: outer planets + house interpretations)
# -----------------------------
def _corpus_only_interpretation(
    *,
    user_prompt: str,
    retrieved_passages: List[Dict[str, str]] | None,
) -> str:
    chart = _extract_chart_from_user_prompt(user_prompt) or {}
    planets = chart.get("planets") or {}
    points = chart.get("points") or {}
    houses = chart.get("houses") or {}

    # core
    sun = planets.get("Sun") or {}
    moon = planets.get("Moon") or {}
    mercury = planets.get("Mercury") or {}
    venus = planets.get("Venus") or {}
    mars = planets.get("Mars") or {}

    # outer planets
    jupiter = planets.get("Jupiter") or {}
    saturn = planets.get("Saturn") or {}
    uranus = planets.get("Uranus") or {}
    neptune = planets.get("Neptune") or {}
    pluto = planets.get("Pluto") or {}

    # extras
    true_node = planets.get("TrueNode") or {}
    chiron = planets.get("Chiron") or {}
    lilith = planets.get("Lilith") or {}

    # points
    asc = points.get("Asc") or {}
    mc = points.get("MC") or {}
    dsc = points.get("DSC") or {}
    ic = points.get("IC") or {}
    vertex = points.get("Vertex") or {}
    fortune = points.get("Fortune") or {}

    sun_sign = sun.get("sign")
    moon_sign = moon.get("sign")
    asc_sign = asc.get("sign")

    lines: List[str] = []

    # Intro (samimi)
    if sun_sign and moon_sign and asc_sign:
        lines.append(
            f"Senin haritanda ana vibe: **{sun_sign} Güneş** + **{moon_sign} Ay**, dışarıya ise **{asc_sign} yükselen** gibi akıyor. "
            f"Bir cümleyle: *içgüdün derin, hedeflerin net; ama ruhun nefes almak için özgürlüğe de ihtiyaç duyuyor.*"
        )
    else:
        lines.append("Senin haritanda genel vibe: (veri eksik olduğu için kısa özet).")

    # 1) Big 3
    lines.append("\n### 1) Big 3 (placements)")
    lines.append(_planet_line("Sun", sun))
    lines.append(_planet_line("Moon", moon))
    if asc_sign and asc.get("deg_in_sign") is not None:
        lines.append(f"- Asc: {asc_sign} {_deg_str(float(asc.get('deg_in_sign')))}")
    else:
        lines.append("- Asc: (unavailable)")

    # Sun/Moon texts
    if sun_sign:
        sun_txt = _pick_passage_by_tags(retrieved_passages, body="SUN", sign=str(sun_sign), typ="PLACEMENT")
        if sun_txt:
            lines.append("\n**Sun — Core Identity**")
            lines.append(sun_txt)

    if moon_sign:
        moon_txt = _pick_passage_by_tags(retrieved_passages, body="MOON", sign=str(moon_sign), typ="PLACEMENT")
        if moon_txt:
            lines.append("\n**Moon — Emotional Needs**")
            lines.append(moon_txt)

    # 2) Mercury/Venus/Mars
    lines.append("\n### 2) Mercury + Venus + Mars")
    lines.append(_planet_line("Mercury", mercury))
    lines.append(_planet_line("Venus", venus))
    lines.append(_planet_line("Mars", mars))

    for body, title in [
        ("MERCURY", "Mercury — Communication"),
        ("VENUS", "Venus — Love & Attraction"),
        ("MARS", "Mars — Drive & Action"),
    ]:
        p = planets.get(body.title()) if body != "MERCURY" else planets.get("Mercury")
        if body == "VENUS":
            p = planets.get("Venus")
        if body == "MARS":
            p = planets.get("Mars")
        p = p or {}
        sign = p.get("sign")
        if not sign:
            continue
        txt = _pick_passage_by_tags(retrieved_passages, body=body, sign=str(sign), typ="PLACEMENT")
        if txt:
            lines.append(f"\n**{title}**")
            lines.append(txt)

    # 3) Outer planets (NEW)
    lines.append("\n### 3) Outer planets (Jupiter → Pluto)")
    lines.append(_planet_line("Jupiter", jupiter))
    lines.append(_planet_line("Saturn", saturn))
    lines.append(_planet_line("Uranus", uranus))
    lines.append(_planet_line("Neptune", neptune))
    lines.append(_planet_line("Pluto", pluto))

    for body, title in [
        ("JUPITER", "Jupiter — Growth & Luck"),
        ("SATURN", "Saturn — Lessons & Mastery"),
        ("URANUS", "Uranus — Change & Awakening"),
        ("NEPTUNE", "Neptune — Dreams & Sensitivity"),
        ("PLUTO", "Pluto — Power & Transformation"),
    ]:
        p = planets.get(body.title()) if body not in ["URANUS", "NEPTUNE"] else planets.get(body.title().capitalize())
        # safer:
        p = planets.get(body.title().capitalize()) or planets.get(body.title()) or planets.get(body.capitalize()) or {}
        sign = (p or {}).get("sign")
        if not sign:
            continue
        txt = _pick_passage_by_tags(retrieved_passages, body=body, sign=str(sign), typ="PLACEMENT")
        if txt:
            lines.append(f"\n**{title}**")
            lines.append(txt)

    # 4) Nodes + Healing + Extras
    lines.append("\n### 4) Nodes + Healing + Extras")
    lines.append(_planet_line("TrueNode", true_node))
    lines.append(_planet_line("Chiron", chiron))
    lines.append(_planet_line("Lilith", lilith))

    for body, title, key in [
        ("TRUENODE", "True Node — Direction & Growth", "TrueNode"),
        ("CHIRON", "Chiron — Wound & Medicine", "Chiron"),
        ("LILITH", "Lilith — Raw Truth & Boundaries", "Lilith"),
    ]:
        p = planets.get(key) or {}
        sign = p.get("sign")
        if not sign:
            continue
        txt = _pick_passage_by_tags(retrieved_passages, body=body, sign=str(sign), typ="PLACEMENT")
        if txt:
            lines.append(f"\n**{title}**")
            lines.append(txt)

    # 5) Angles / points (NEW: optionally interpret if corpus exists)
    def _pt_line(label: str, pt: Dict[str, Any]) -> str:
        if not pt or pt.get("sign") is None or pt.get("deg_in_sign") is None:
            return f"- {label}: (unavailable)"
        return f"- {label}: {pt['sign']} {_deg_str(float(pt['deg_in_sign']))}"

    lines.append("\n### 5) Angles / points")
    lines.append(_pt_line("Asc", asc))
    lines.append(_pt_line("MC", mc))
    lines.append(_pt_line("DSC", dsc))
    lines.append(_pt_line("IC", ic))
    lines.append(_pt_line("Vertex", vertex))
    lines.append(_pt_line("Fortune", fortune))

    for body, title, obj in [
        ("ASC", "Ascendant — How you show up", asc),
        ("MC", "Midheaven — Public path & career vibe", mc),
        ("DSC", "Descendant — Relationship mirror", dsc),
        ("IC", "IC — Inner roots & emotional base", ic),
        ("VERTEX", "Vertex — Fated meetings & turning points", vertex),
        ("FORTUNE", "Part of Fortune — Ease, flow, sweet spots", fortune),
    ]:
        sign = (obj or {}).get("sign")
        if not sign:
            continue
        txt = _pick_passage_by_tags(retrieved_passages, body=body, sign=str(sign), typ="POINT")
        if txt:
            lines.append(f"\n**{title}**")
            lines.append(txt)

    # 6) Houses (12) + house interpretations (NEW)
    lines.append("\n### 6) Houses (12)")
    lines.extend(_houses_12_lines(houses))

    house_signs = _houses_12_signs(houses)

    lines.append("\n### 7) House interpretations (sign on each house cusp)")
    any_house_text = False
    for i, sign in enumerate(house_signs, start=1):
        if not sign:
            continue

        # Expected corpus tags:
        # [TYPE=HOUSE]
        # [BODY=HOUSE_1]
        # [SIGN=CAPRICORN]
        body = f"HOUSE_{i}"
        txt = _pick_passage_by_tags(retrieved_passages, body=body, sign=str(sign), typ="HOUSE")
        if txt:
            any_house_text = True
            lines.append(f"\n**{_ordinal(i)} House in {sign}**")
            lines.append(txt)

    if not any_house_text:
        lines.append("- (House corpus metni yoksa burada görünmez; dosyaları ekleyince otomatik basacak.)")

    # 8) Aspects
    aspects = _top_aspects(chart, n=12)
    lines.append("\n### 8) Top aspects (tightest first)")
    if aspects:
        seen = set()
        for a in aspects:
            p1 = a.get("p1")
            p2 = a.get("p2")
            asp = a.get("aspect")
            orb = a.get("orb")
            if not (p1 and p2 and asp is not None):
                continue
            k = (str(p1), str(asp), str(p2), str(orb))
            if k in seen:
                continue
            seen.add(k)
            try:
                orb_f = float(orb)
                orb_s = _deg_str(orb_f)
            except Exception:
                orb_s = str(orb)
            lines.append(f"- {p1} {asp} {p2} (orb {orb_s})")
    else:
        lines.append("- (No aspects available)")

    lines.append("\n**Orb tip:** 0–2° çok baskın; 2–4° güçlü; 4–6° hissedilir; 6°+ arka plan (ama tekrar ediyorsa önem kazanır).")

    return "\n".join(lines).strip()


def _looks_like_quota_error(msg: str) -> bool:
    s = (msg or "").lower()
    return ("insufficient_quota" in s) or ("exceeded your current quota" in s) or ("status code: 429" in s) or ("rate limit" in s)


# -----------------------------
# Main entry
# -----------------------------
def generate_interpretation(
    *,
    system_prompt: str,
    user_prompt: str,
    retrieved_passages: List[Dict[str, str]] | None = None,
    model: str | None = None,
    max_tokens: int = 2500,
) -> str:
    client = get_client()

    # No key OR quota etc -> corpus-only
    if client is None:
        return _corpus_only_interpretation(user_prompt=user_prompt, retrieved_passages=retrieved_passages)

    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Build context for model
    context = ""
    if retrieved_passages:
        lines = []
        for p in retrieved_passages[:12]:
            src = p.get("source", "")
            txt = p.get("text", "")
            if not txt:
                continue
            lines.append(f"[source: {src}] {txt}")
        context = "\n\n".join(lines)

    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append({
            "role": "system",
            "content": (
                "Use the following reference passages as anchors.\n"
                "Do NOT copy sentences verbatim; paraphrase and produce original text.\n\n"
                + context
            )
        })
    messages.append({"role": "user", "content": user_prompt})

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

    except Exception as e:
        msg = str(e)
        if _looks_like_quota_error(msg) or "401" in msg or "403" in msg or "connection" in msg.lower():
            return _corpus_only_interpretation(user_prompt=user_prompt, retrieved_passages=retrieved_passages)

        return _corpus_only_interpretation(user_prompt=user_prompt, retrieved_passages=retrieved_passages)