from __future__ import annotations

from pathlib import Path
import os
import json
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import BirthData
from .chart import compute_natal_chart
from .rag import retrieve, build_index
from .llm import generate_interpretation

app = FastAPI(title="AstroAI API", version="1.0.0")

# =========================
# Security / Env
# =========================
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()  # "development" | "production"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")  # set in Render backend env

# =========================
# CORS
# =========================
if ENVIRONMENT == "development":
    allowed_origins = ["*"]
else:
    allowed_origins = [
        "https://astromyla.com",
        "https://www.astromyla.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------- helpers ----------
_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

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


def _lon_to_sign(lon: float) -> str:
    x = float(lon) % 360.0
    idx = int(x // 30.0)
    return _SIGNS[idx]


def _get_house_cusp_signs(chart: dict) -> list[str | None]:
    """
    Returns list of 12 cusp signs for houses 1..12.
    Supports:
      houses.cusps = [float,...]  length 12
      houses.cusps = [{"lon":..,"sign":..},...] length 12
      houses.signs = [sign,...] length 12
    """
    houses = chart.get("houses", {}) or {}

    # case 1: houses.signs
    signs = houses.get("signs")
    if isinstance(signs, list) and len(signs) == 12:
        return [str(s) if s else None for s in signs]

    cusps = houses.get("cusps")
    if isinstance(cusps, list) and len(cusps) == 12:
        # case 2: list[dict]
        if isinstance(cusps[0], dict):
            out: list[str | None] = []
            for c in cusps:
                s = c.get("sign")
                if s:
                    out.append(str(s))
                else:
                    lon = c.get("lon")
                    out.append(_lon_to_sign(float(lon)) if lon is not None else None)
            return out

        # case 3: list[float]
        if all(isinstance(v, (int, float)) for v in cusps):
            return [_lon_to_sign(float(v)) for v in cusps]

    return [None] * 12


def build_rag_query(chart: dict) -> str:
    """
    CRITICAL: Retrieval query scope.
    Includes:
      - Sun..Pluto + TrueNode + Lilith + Chiron (if sign exists)
      - Asc/MC/DSC/IC/Vertex/Fortune (if exists)
      - House cusp signs 1..12 (if exists)
      - Top aspects tokens (for extra anchoring)
      - Strong tag-like anchors to match your corpus headers
    """
    planets = chart.get("planets", {}) or {}
    points = chart.get("points", {}) or {}

    def psign(p: str) -> str | None:
        return (planets.get(p, {}) or {}).get("sign")

    def xsign_point(k: str) -> str | None:
        return (points.get(k, {}) or {}).get("sign")

    # aspects summary for query
    aspects = chart.get("aspects", {}) or {}
    planet_aspects = aspects.get("planet_aspects", []) or []
    other_aspects = aspects.get("other_aspects", []) or []
    all_aspects = sorted((planet_aspects + other_aspects), key=lambda x: x.get("orb", 999.0))
    top_aspects = all_aspects[:25]

    # ---- base query ----
    q_parts: list[str] = []
    q_parts.append("natal chart interpretation")

    # ---- planet + sign tokens ----
    for p in [
        "Sun","Moon","Mercury","Venus","Mars",
        "Jupiter","Saturn","Uranus","Neptune","Pluto",
        "TrueNode","Chiron","Lilith"
    ]:
        s = psign(p)
        if s:
            q_parts.append(f"{p} {s}")
            q_parts.append(f"{p} in {s}")

    # ---- points tokens (include DSC/IC too) ----
    for k in ["Asc", "MC", "DSC", "IC", "Vertex", "Fortune"]:
        s = xsign_point(k)
        if s:
            q_parts.append(f"{k} {s}")
            q_parts.append(f"{k} in {s}")

    # ---- house cusp signs ----
    house_signs = _get_house_cusp_signs(chart)
    ords = ["1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th","11th","12th"]
    for i, s in enumerate(house_signs, start=1):
        if not s:
            continue
        q_parts.append(f"{ords[i-1]} House {s}")
        q_parts.append(f"{ords[i-1]} House in {s}")
        # anchor-y tokens for your future house corpus tags
        q_parts.append(f"HOUSE_{i} {s}")
        q_parts.append(f"[TYPE=HOUSE] [BODY=HOUSE_{i}] [SIGN={str(s).upper()}]")

    # ---- strong anchors for existing PLACEMENT corpus tags ----
    # These match the header style you showed:
    # [TYPE=PLACEMENT] [BODY=MARS] [SIGN=ARIES] [KEY=mars_in_aries]
    def anchor(typ: str, body_tag: str, sign: str | None, key: str):
        if sign:
            q_parts.append(f"[TYPE={typ}] [BODY={body_tag}] [SIGN={str(sign).upper()}] [KEY={key}]")

    # placements
    for body_tag, pkey, folder in [
        ("SUN", "Sun", "sun"),
        ("MOON", "Moon", "moon"),
        ("MERCURY", "Mercury", "mercury"),
        ("VENUS", "Venus", "venus"),
        ("MARS", "Mars", "mars"),
        ("JUPITER", "Jupiter", "jupiter"),
        ("SATURN", "Saturn", "saturn"),
        ("URANUS", "Uranus", "uranus"),
        ("NEPTUNE", "Neptune", "neptune"),
        ("PLUTO", "Pluto", "pluto"),
        ("TRUENODE", "TrueNode", "true_node"),
        ("CHIRON", "Chiron", "chiron"),
        ("LILITH", "Lilith", "lilith"),
    ]:
        s = psign(pkey)
        if s:
            anchor("PLACEMENT", body_tag, s, f"{folder}_in_{str(s).lower()}")

    # points (optional corpus tags if you add later)
    for body_tag, k in [
        ("ASC", "Asc"),
        ("MC", "MC"),
        ("DSC", "DSC"),
        ("IC", "IC"),
        ("VERTEX", "Vertex"),
        ("FORTUNE", "Fortune"),
    ]:
        s = xsign_point(k)
        if s:
            anchor("POINT", body_tag, s, f"{body_tag.lower()}_in_{str(s).lower()}")

    # ---- aspects tokens ----
    asp_tokens = []
    for a in top_aspects:
        p1 = a.get("p1")
        p2 = a.get("p2")
        asp = a.get("aspect")
        if p1 and p2 and asp:
            asp_tokens.append(f"{p1} {asp} {p2}")
    if asp_tokens:
        q_parts.append(" | " + " ".join(asp_tokens))

    # join
    return " ".join(q_parts)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "environment": ENVIRONMENT,
        "admin_token_configured": bool(ADMIN_TOKEN),
        "cors_allow_origins": allowed_origins,
    }


# 🔒 Admin protected rebuild-index
@app.post("/api/rebuild-index")
def rebuild_index_route(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    # In production, require token
    if ENVIRONMENT != "development":
        if not ADMIN_TOKEN:
            raise HTTPException(status_code=500, detail="ADMIN_TOKEN is not configured on server")
        if x_admin_token != ADMIN_TOKEN:
            raise HTTPException(status_code=403, detail="Unauthorized")

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

    # ---- build retrieval query (UPDATED: includes houses + outer + full angles) ----
    q = build_rag_query(chart)

    # ---- retrieval ----
    passages = retrieve(q, k=60)

    # ---- OPTIONAL: Force key placement files to always be present (top) ----
    forced: list[dict] = []

    def _force(body_folder: str, sign: str | None):
        if not sign:
            return
        txt = _find_placement_file(body_folder, str(sign))
        if txt:
            forced.append(
                {"source": f"FORCED | placements/{body_folder}/{body_folder}_in_{str(sign).lower()}.txt", "text": txt}
            )

    # planets
    for folder, key in [
        ("sun", "Sun"),
        ("moon", "Moon"),
        ("mercury", "Mercury"),
        ("venus", "Venus"),
        ("mars", "Mars"),
        ("jupiter", "Jupiter"),
        ("saturn", "Saturn"),
        ("uranus", "Uranus"),
        ("neptune", "Neptune"),
        ("pluto", "Pluto"),
        ("chiron", "Chiron"),
        ("true_node", "TrueNode"),
        ("lilith", "Lilith"),
    ]:
        _force(folder, _psign(key))

    # points
    _force("vertex", _xsign_point("Vertex"))
    _force("fortune", _xsign_point("Fortune"))

    if forced:
        forced_texts = {f["text"] for f in forced}
        tail = [p for p in passages if (p.get("text") or "") not in forced_texts]
        passages = forced + tail

    # ---- generate ----
    text = generate_interpretation(
        system_prompt="You are a professional astrology interpreter.",
        user_prompt=f"Chart data:\n{json.dumps(chart, ensure_ascii=False)}",
        retrieved_passages=passages,
    )

    return {
        "chart": chart,
        "interpretation": text,
        "retrieval": passages,
        "query": q,
    }