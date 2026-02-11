from __future__ import annotations

import os
import json
import re
from typing import List, Dict, Optional, Any

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


def _top_aspects(chart: Dict[str, Any], n: int = 10) -> List[Dict[str, Any]]:
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
# NEW: Metadata stripping (works for inline tags too)
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


def _pick_placement_passage(
    passages: List[Dict[str, str]] | None,
    *,
    body: str,
    sign: str,
) -> Optional[str]:
    if not passages or not body or not sign:
        return None

    body_u = body.upper()
    sign_u = sign.upper()

    # strict tag match first
    for p in passages:
        txt = (p.get("text") or "")
        if f"[BODY={body_u}]" in txt and f"[SIGN={sign_u}]" in txt:
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

    if isinstance(cusps, list) and len(cusps) == 12 and isinstance(cusps[0], dict):
        for i, c in enumerate(cusps, start=1):
            sign = c.get("sign")
            deg = c.get("deg_in_sign")
            if sign is None or deg is None:
                out.append(f"- {_ordinal(i)} House: (unavailable)")
            else:
                out.append(f"- {_ordinal(i)} House: {sign} {_deg_str(float(deg))}")
        return out

    if isinstance(signs, list) and len(signs) == 12:
        for i, s in enumerate(signs, start=1):
            out.append(f"- {_ordinal(i)} House: {s}")
        return out

    if isinstance(cusps, list) and len(cusps) == 12 and all(isinstance(v, (int, float)) for v in cusps):
        for i, lon in enumerate(cusps, start=1):
            sign, deg_in_sign = _lon_to_sign_deg(float(lon))
            out.append(f"- {_ordinal(i)} House: {sign} {_deg_str(deg_in_sign)}")
        return out

    for i in range(1, 13):
        out.append(f"- {_ordinal(i)} House: (unavailable)")
    return out


# -----------------------------
# Corpus-only fallback writer (UPDATED: extras included)
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

    sun = planets.get("Sun") or {}
    moon = planets.get("Moon") or {}
    mercury = planets.get("Mercury") or {}
    venus = planets.get("Venus") or {}
    mars = planets.get("Mars") or {}

    # extras (planets dict)
    true_node = planets.get("TrueNode") or {}
    chiron = planets.get("Chiron") or {}
    lilith = planets.get("Lilith") or {}

    # points dict
    asc = points.get("Asc") or {}
    vertex = points.get("Vertex") or {}
    fortune = points.get("Fortune") or {}

    sun_sign = sun.get("sign")
    moon_sign = moon.get("sign")
    asc_sign = asc.get("sign")

    lines: List[str] = []

    # Intro
    if sun_sign and moon_sign and asc_sign:
        lines.append(
            f"Senin haritanda ana vibe: **{sun_sign} Güneş** + **{moon_sign} Ay**, dışarıya ise **{asc_sign} yükselen** gibi akıyor.\n"
            f"Bunu bir cümleyle özetlersek: *özgürlük ihtiyacın var ama bağ kurmak da istiyorsun; zihin hızlı çalışırken kalbi de duymayı öğreniyorsun.*"
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

    # Sun/Moon placement texts
    if sun_sign:
        sun_txt = _pick_placement_passage(retrieved_passages, body="SUN", sign=str(sun_sign))
        if sun_txt:
            lines.append("\n**Sun — Core Identity**")
            lines.append(sun_txt)

    if moon_sign:
        moon_txt = _pick_placement_passage(retrieved_passages, body="MOON", sign=str(moon_sign))
        if moon_txt:
            lines.append("\n**Moon — Emotional Needs**")
            lines.append(moon_txt)

    # 2) Mercury/Venus/Mars
    lines.append("\n### 2) Mercury + Venus + Mars")
    lines.append(_planet_line("Mercury", mercury))
    lines.append(_planet_line("Venus", venus))
    lines.append(_planet_line("Mars", mars))

    for body, title in [
        ("Mercury", "Mercury — Communication"),
        ("Venus", "Venus — Love & Attraction"),
        ("Mars", "Mars — Drive & Action"),
    ]:
        p = planets.get(body) or {}
        sign = p.get("sign")
        if not sign:
            continue
        txt = _pick_placement_passage(retrieved_passages, body=body.upper(), sign=str(sign))
        if txt:
            lines.append(f"\n**{title}**")
            lines.append(txt)

    # 3) Extras (UPDATED)
    lines.append("\n### 3) Nodes + Healing + Extras")
    lines.append(_planet_line("TrueNode", true_node))
    lines.append(_planet_line("Chiron", chiron))
    lines.append(_planet_line("Lilith", lilith))

    # Add their texts if present
    for body, title in [
        ("TRUENODE", "True Node — Direction & Growth"),
        ("CHIRON", "Chiron — Wound & Medicine"),
        ("LILITH", "Lilith — Raw Truth & Boundaries"),
    ]:
        p = planets.get(body.title() if body != "TRUENODE" else "TrueNode") or {}
        sign = p.get("sign")
        if not sign:
            continue
        txt = _pick_placement_passage(retrieved_passages, body=body, sign=str(sign))
        if txt:
            lines.append(f"\n**{title}**")
            lines.append(txt)

    # 4) Angles/points
    def _pt_line(label: str, pt: Dict[str, Any]) -> str:
        if not pt or pt.get("sign") is None or pt.get("deg_in_sign") is None:
            return f"- {label}: (unavailable)"
        return f"- {label}: {pt['sign']} {_deg_str(float(pt['deg_in_sign']))}"

    lines.append("\n### 4) Angles / points")
    lines.append(_pt_line("Asc", points.get("Asc") or {}))
    lines.append(_pt_line("MC", points.get("MC") or {}))
    lines.append(_pt_line("DSC", points.get("DSC") or {}))
    lines.append(_pt_line("IC", points.get("IC") or {}))
    lines.append(_pt_line("Vertex", vertex))
    lines.append(_pt_line("Fortune", fortune))

    # Vertex/Fortune texts (optional)
    for body, title, obj in [
        ("VERTEX", "Vertex — Fated Meetings & Turning Points", vertex),
        ("FORTUNE", "Part of Fortune — Ease, Flow, Sweet Spots", fortune),
    ]:
        sign = (obj or {}).get("sign")
        if not sign:
            continue
        txt = _pick_placement_passage(retrieved_passages, body=body, sign=str(sign))
        if txt:
            lines.append(f"\n**{title}**")
            lines.append(txt)

    # 5) Houses
    lines.append("\n### 5) Houses (12)")
    lines.extend(_houses_12_lines(houses))

    # 6) Aspects
    aspects = _top_aspects(chart, n=10)
    lines.append("\n### 6) Top aspects (tightest first)")
    if aspects:
        for a in aspects:
            p1 = a.get("p1")
            p2 = a.get("p2")
            asp = a.get("aspect")
            orb = a.get("orb")
            if not (p1 and p2 and asp is not None):
                continue
            try:
                orb_f = float(orb)
                orb_s = _deg_str(orb_f)
            except Exception:
                orb_s = str(orb)
            lines.append(f"- {p1} {asp} {p2} (orb {orb_s})")
    else:
        lines.append("- (No aspects available)")

    lines.append("\n**Orb tip (kısa):** 0–2° = çok baskın; 2–4° = güçlü; 4–6° = hissedilir; 6°+ = arka plan (ama tekrar ediyorsa önem kazanır).")

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
        for p in retrieved_passages[:10]:
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
