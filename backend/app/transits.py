from __future__ import annotations

from datetime import date, datetime, time as dt_time, timezone
from typing import Any

import swisseph as swe

from .chart import ASPECTS, angular_separation, compute_all_bodies, compute_object_house, deg_to_sign, wrap360

TRANSIT_BODIES = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "TrueNode", "Chiron",
]
NATAL_TARGETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "TrueNode", "Chiron",
    "Asc", "MC", "DSC", "IC", "Vertex",
]
TRANSIT_ORBS = {
    "Conjunction": 3.0,
    "Opposition": 3.0,
    "Trine": 2.5,
    "Square": 2.5,
    "Sextile": 2.0,
}
ASPECT_WEIGHT = {"Conjunction": 1.0, "Opposition": .95, "Square": .9, "Trine": .8, "Sextile": .68}
TRANSIT_WEIGHT = {"Pluto":1.0,"Neptune":.95,"Uranus":.95,"Saturn":.95,"Jupiter":.8,"Mars":.75,"Venus":.55,"Mercury":.5,"Sun":.5,"Moon":.35,"TrueNode":.7,"Chiron":.65}
TARGET_WEIGHT = {"Sun":1.0,"Moon":1.0,"Asc":1.0,"MC":.95,"Venus":.9,"Mars":.85,"Mercury":.8,"Saturn":.8,"Jupiter":.7,"DSC":.9,"IC":.85,"TrueNode":.75,"Chiron":.7,"Uranus":.55,"Neptune":.55,"Pluto":.55,"Vertex":.6}

HOUSE_THEMES = {
    1:"identity, body, presence and self-direction", 2:"money, resources, values and self-worth",
    3:"communication, learning, siblings and local movement", 4:"home, family, roots and emotional foundations",
    5:"romance, creativity, pleasure and self-expression", 6:"work routines, health habits and daily responsibilities",
    7:"partnership, attraction, agreements and one-to-one dynamics", 8:"intimacy, trust, shared resources and deep change",
    9:"travel, higher learning, belief and perspective", 10:"career, visibility, reputation and long-range direction",
    11:"friendships, networks, community and future goals", 12:"rest, closure, private life, intuition and unconscious patterns",
}


def _dt_to_jd(dt: datetime) -> float:
    dt = dt.astimezone(timezone.utc)
    hour = dt.hour + dt.minute / 60 + dt.second / 3600
    return swe.julday(dt.year, dt.month, dt.day, hour, swe.GREG_CAL)


def resolve_transit_datetime(target_date: date | None = None) -> datetime:
    if target_date is None:
        return datetime.now(timezone.utc)
    return datetime.combine(target_date, dt_time(hour=12), tzinfo=timezone.utc)


def _objects(chart: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    out.update(chart.get("planets") or {})
    out.update(chart.get("points") or {})
    return out


def _aspect_rows(natal: dict[str, Any], transit_bodies: dict[str, Any], future_bodies: dict[str, Any]) -> list[dict[str, Any]]:
    natal_objects = _objects(natal)
    rows: list[dict[str, Any]] = []
    for t_name in TRANSIT_BODIES:
        t = transit_bodies.get(t_name) or {}
        ft = future_bodies.get(t_name) or {}
        if t.get("lon") is None or not t.get("available", True):
            continue
        for n_name in NATAL_TARGETS:
            n = natal_objects.get(n_name) or {}
            if n.get("lon") is None:
                continue
            if natal.get("time_unknown") and n_name in {"Moon","Asc","MC","DSC","IC","Vertex"}:
                continue
            sep = angular_separation(float(t["lon"]), float(n["lon"]))
            for aspect, exact in ASPECTS.items():
                max_orb = TRANSIT_ORBS[aspect]
                orb = abs(sep - exact)
                if orb <= max_orb:
                    future_orb = orb
                    if ft.get("lon") is not None:
                        future_sep = angular_separation(float(ft["lon"]), float(n["lon"]))
                        future_orb = abs(future_sep - exact)
                    applying = future_orb < orb
                    closeness = max(0.0, 1.0 - orb / max_orb)
                    importance = closeness * ASPECT_WEIGHT[aspect] * TRANSIT_WEIGHT.get(t_name,.5) * TARGET_WEIGHT.get(n_name,.5)
                    rows.append({
                        "transit": t_name, "natal": n_name, "aspect": aspect,
                        "orb": float(orb), "separation": float(sep), "applying": bool(applying),
                        "transit_sign": t.get("sign"), "transit_deg_in_sign": t.get("deg_in_sign"),
                        "score": round(float(importance) * 100, 1),
                    })
                    break
    rows.sort(key=lambda x: (-float(x["score"]), float(x["orb"]), x["transit"], x["natal"]))
    return rows


def _house_overlays(natal: dict[str, Any], birth: Any, transit_bodies: dict[str, Any]) -> list[dict[str, Any]]:
    if natal.get("time_unknown"):
        return []
    rows: list[dict[str, Any]] = []
    for name in TRANSIT_BODIES:
        body = transit_bodies.get(name) or {}
        if body.get("lon") is None or not body.get("available", True):
            continue
        try:
            house = compute_object_house(
                jd_ut=float(natal["jd_ut"]), latitude=float(birth.latitude), longitude=float(birth.longitude),
                house_system=str(natal.get("house_system") or birth.house_system), obj_lon=float(body["lon"]),
                obj_lat=float(body.get("lat") or 0.0),
            )
        except Exception:
            continue
        rows.append({"planet": name, "house": house, "theme": HOUSE_THEMES.get(house, "this area of life")})
    return rows


def compute_personal_transits(natal: dict[str, Any], birth: Any, target_date: date | None = None) -> dict[str, Any]:
    dt = resolve_transit_datetime(target_date)
    jd = _dt_to_jd(dt)
    future_jd = jd + 0.25
    bodies = compute_all_bodies(jd)
    future = compute_all_bodies(future_jd)
    aspects = _aspect_rows(natal, bodies, future)
    houses = _house_overlays(natal, birth, bodies)
    public_bodies = {k:v for k,v in bodies.items() if k in TRANSIT_BODIES and v.get("available", True) and v.get("lon") is not None}
    return {
        "target_utc": dt.isoformat(),
        "jd_ut": jd,
        "planets": public_bodies,
        "aspects": aspects,
        "house_overlays": houses,
        "top_aspects": aspects[:10],
        "method_note": "Transiting planetary longitudes are calculated with Swiss Ephemeris and compared with the natal chart using tighter transit orbs. Applying/separating status is estimated from the aspect's change over the next six hours.",
    }


def build_daily_transit_interpretation(data: dict[str, Any], natal: dict[str, Any]) -> str:
    rows = data.get("top_aspects") or []
    houses = data.get("house_overlays") or []
    lines = [
        "### Your current sky",
        "This is a timing snapshot, not a prediction of fixed events. The strongest entries are the closest and most astrologically weighted contacts active around the selected day.",
    ]
    if not rows:
        lines.append("No major transit-to-natal aspects are especially tight inside the current transit orbs.")
    else:
        lines.append("\n### Strongest active transits")
        for row in rows[:8]:
            motion = "applying" if row.get("applying") else "separating"
            lines.append(f"- **Transit {row['transit']} {row['aspect']} natal {row['natal']}** — orb {float(row['orb']):.2f}° · {motion}.")
    if houses:
        lines.append("\n### Where the sky is landing in your chart")
        for row in houses[:10]:
            lines.append(f"- **{row['planet']} through your {row['house']}th house** emphasizes {row['theme']}.")
    if natal.get("time_unknown"):
        lines.append("\nBecause the birth time is unknown, natal houses and angles are intentionally excluded from this daily reading.")
    lines.extend([
        "\n### How to use this",
        "Outer-planet transits usually describe longer chapters; faster planets often act as short-term triggers or mood/attention shifts. Repeated themes matter more than any single contact.",
    ])
    return "\n".join(lines)
