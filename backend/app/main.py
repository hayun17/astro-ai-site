from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import BirthData
from .chart import compute_natal_chart
from .rag import retrieve, build_index
from .llm import generate_interpretation

app = FastAPI(title="AstroAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------- helpers ----------
def _read_text_if_exists(fp: Path) -> str | None:
    if not fp.exists():
        return None
    t = fp.read_text(encoding="utf-8", errors="ignore").strip()
    return t or None


def _find_placement_file(body: str, sign: str) -> str | None:
    """
    Look for placement files like:
      backend/data/corpus/placements/chiron/chiron_in_pisces.txt
      backend/data/corpus/placements/true_node/true_node_in_aries.txt
    """
    if not body or not sign:
        return None

    base = Path(__file__).resolve().parent.parent  # backend/
    corpus_dir = base / "data" / "corpus" / "placements"

    b = body.lower()
    s = sign.lower()

    candidates = [
        corpus_dir / b / f"{b}_in_{s}.txt",
        corpus_dir / b / f"{b}_in_{s}.corpus.txt",
    ]

    for fp in candidates:
        txt = _read_text_if_exists(fp)
        if txt:
            return txt
    return None


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/rebuild-index")
def rebuild_index_route():
    chunks = build_index()
    return {"chunks": len(chunks)}


@app.post("/api/chart/natal")
def natal_chart(birth: BirthData):
    chart = compute_natal_chart(
        name=birth.name,
        year=birth.year,
        month=birth.month,
        day=birth.day,
        hour=birth.hour,
        minute=birth.minute,
        latitude=birth.latitude,
        longitude=birth.longitude,
        tz_offset_hours=birth.tz_offset_hours,
        house_system="P",
    )
    return chart


@app.post("/api/interpret/natal")
def interpret_natal(birth: BirthData):
    chart = compute_natal_chart(
        name=birth.name,
        year=birth.year,
        month=birth.month,
        day=birth.day,
        hour=birth.hour,
        minute=birth.minute,
        latitude=birth.latitude,
        longitude=birth.longitude,
        tz_offset_hours=birth.tz_offset_hours,
        house_system=getattr(birth, "house_system", "P"),
    )

    planets = chart.get("planets", {}) or {}
    points = chart.get("points", {}) or {}

    def _psign(p: str) -> str | None:
        return (planets.get(p, {}) or {}).get("sign")

    def _xsign_point(k: str) -> str | None:
        return (points.get(k, {}) or {}).get("sign")

    # ---- signs we care about ----
    sun_sign = _psign("Sun")
    moon_sign = _psign("Moon")
    mercury_sign = _psign("Mercury")
    venus_sign = _psign("Venus")
    mars_sign = _psign("Mars")

    true_node_sign = _psign("TrueNode")
    chiron_sign = _psign("Chiron")
    lilith_sign = _psign("Lilith")

    vertex_sign = _xsign_point("Vertex")
    fortune_sign = _xsign_point("Fortune")

    # aspects summary for query
    aspects = chart.get("aspects", {}) or {}
    planet_aspects = aspects.get("planet_aspects", []) or []
    other_aspects = aspects.get("other_aspects", []) or []
    all_aspects = sorted((planet_aspects + other_aspects), key=lambda x: x.get("orb", 999.0))
    top_aspects = all_aspects[:20]

    # ---- build query ----
    q = "natal chart interpretation "

    # planet+sign tokens
    for p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "TrueNode", "Chiron", "Lilith"]:
        s = (planets.get(p, {}) or {}).get("sign")
        if s:
            q += f"{p} {s} "

    # points tokens
    for k in ["Asc", "MC", "Vertex", "Fortune"]:
        s = (points.get(k, {}) or {}).get("sign")
        if s:
            q += f"{k} {s} "

    # add strong anchors (match your corpus tags)
    def _anchor(body_tag: str, sign: str | None, key: str):
        nonlocal q
        if sign:
            q += f" | [BODY={body_tag}] [SIGN={str(sign).upper()}] | KEY={key} "

    _anchor("SUN", sun_sign, f"sun_in_{str(sun_sign).lower()}" if sun_sign else "sun_in_x")
    _anchor("MOON", moon_sign, f"moon_in_{str(moon_sign).lower()}" if moon_sign else "moon_in_x")
    _anchor("MERCURY", mercury_sign, f"mercury_in_{str(mercury_sign).lower()}" if mercury_sign else "mercury_in_x")
    _anchor("VENUS", venus_sign, f"venus_in_{str(venus_sign).lower()}" if venus_sign else "venus_in_x")
    _anchor("MARS", mars_sign, f"mars_in_{str(mars_sign).lower()}" if mars_sign else "mars_in_x")

    _anchor("TRUENODE", true_node_sign, f"true_node_in_{str(true_node_sign).lower()}" if true_node_sign else "true_node_in_x")
    _anchor("CHIRON", chiron_sign, f"chiron_in_{str(chiron_sign).lower()}" if chiron_sign else "chiron_in_x")
    _anchor("LILITH", lilith_sign, f"lilith_in_{str(lilith_sign).lower()}" if lilith_sign else "lilith_in_x")

    _anchor("VERTEX", vertex_sign, f"vertex_in_{str(vertex_sign).lower()}" if vertex_sign else "vertex_in_x")
    _anchor("FORTUNE", fortune_sign, f"fortune_in_{str(fortune_sign).lower()}" if fortune_sign else "fortune_in_x")

    # aspects tokens
    q += " | " + " ".join(
        f"{a.get('p1')} {a.get('aspect')} {a.get('p2')}"
        for a in top_aspects
        if a.get("p1") and a.get("p2") and a.get("aspect")
    )

    # ---- retrieval ----
    passages = retrieve(q, k=40)

    # ---- OPTIONAL: Force key placement files to always be present (top) ----
    forced: list[dict] = []

    def _force(body_folder: str, sign: str | None):
        if not sign:
            return
        txt = _find_placement_file(body_folder, str(sign))
        if txt:
            forced.append({"source": f"FORCED | placements/{body_folder}/{body_folder}_in_{str(sign).lower()}.txt", "text": txt})

    _force("sun", sun_sign)
    _force("moon", moon_sign)
    _force("mercury", mercury_sign)
    _force("venus", venus_sign)
    _force("mars", mars_sign)

    _force("chiron", chiron_sign)
    _force("true_node", true_node_sign)
    _force("lilith", lilith_sign)

    # (Vertex/Fortune are points, only force if you actually created those folders/files)
    _force("vertex", vertex_sign)
    _force("fortune", fortune_sign)

    if forced:
        forced_texts = {f["text"] for f in forced}
        tail = [p for p in passages if (p.get("text") or "") not in forced_texts]
        passages = forced + tail

    # ---- generate ----
    text = generate_interpretation(
        system_prompt="You are a professional astrology interpreter.",
        user_prompt=f"Chart data:\n{chart}",
        retrieved_passages=passages,
    )

    return {
        "chart": chart,
        "interpretation": text,
        "retrieval": passages,
    }
