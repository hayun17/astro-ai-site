from __future__ import annotations

import os
from typing import Dict, List, Tuple, Optional, Any

import swisseph as swe

# ----------------------------
# EPHEMERIS PATH (SAFE)
# ----------------------------
# 1) Eğer kullanıcı ortam değişkeni verdiyse onu kullan (istersen sonra ekleriz)
# 2) Yoksa: backend/ephe klasörü varsa onu kullan
# 3) Yoksa: "." (mevcut klasör) - ama biz zaten file yoksa MOSEPH fallback yapacağız
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EPHE = os.path.normpath(os.path.join(HERE, "..", "ephe"))
EPHE_PATH = os.environ.get("SE_EPHE_PATH") or (DEFAULT_EPHE if os.path.isdir(DEFAULT_EPHE) else ".")
swe.set_ephe_path(EPHE_PATH)

# ----------------------------
# CONSTANTS
# ----------------------------

PLANETS: Dict[str, int] = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "TrueNode": swe.TRUE_NODE,
}

# Extras (bazıları ephe dosyası isteyebilir; yoksa crash yerine skip yapacağız)
EXTRA_BODIES: Dict[str, int] = {
    "Chiron": swe.CHIRON,
    "Lilith": swe.MEAN_APOG,  # Mean Black Moon
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ASPECTS = {
    "Conjunction": 0,
    "Opposition": 180,
    "Trine": 120,
    "Square": 90,
    "Sextile": 60,
}

DEFAULT_ORBS = {
    "Conjunction": 8.0,
    "Opposition": 8.0,
    "Trine": 6.0,
    "Square": 6.0,
    "Sextile": 4.0,
}

MAJOR_PLANET_NAMES = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
]

# ----------------------------
# HELPERS
# ----------------------------

def wrap360(deg: float) -> float:
    d = deg % 360.0
    return d + 360.0 if d < 0 else d

def angular_separation(a: float, b: float) -> float:
    d = abs(wrap360(a) - wrap360(b))
    return min(d, 360.0 - d)

def deg_to_sign(deg: float) -> Tuple[str, float]:
    deg = wrap360(deg)
    sign_idx = int(deg // 30)
    within = deg - 30 * sign_idx
    return SIGNS[sign_idx], within

def opposite_deg(x: float) -> float:
    return wrap360(x + 180.0)

def to_julian_day_ut(year: int, month: int, day: int, hour: int, minute: int, tz_offset_hours: float) -> float:
    h_local = hour + minute / 60.0
    h_ut = h_local - tz_offset_hours
    return swe.julday(year, month, day, h_ut, swe.GREG_CAL)

def _hs_bytes(house_system: str) -> bytes:
    hs = (house_system or "P")[0].encode("ascii", errors="ignore")
    return hs if len(hs) == 1 else b"P"

def _safe_calc_ut(jd_ut: float, pid: int) -> Optional[Tuple[List[float], int]]:
    """
    Önce SWIEPH (dosyalı) dener.
    Ephe dosyası yoksa MOSEPH (dosyasız) dener.
    Yine olmazsa None döner.
    """
    try:
        xx, retflag = swe.calc_ut(jd_ut, pid, swe.FLG_SWIEPH)
        return xx, retflag
    except swe.Error:
        # dosya yoksa / bulunamazsa: MOSEPH fallback (major planets için çok işe yarar)
        try:
            xx, retflag = swe.calc_ut(jd_ut, pid, swe.FLG_MOSEPH)
            return xx, retflag
        except swe.Error:
            return None

# ----------------------------
# COMPUTE BODIES / HOUSES
# ----------------------------

def compute_all_bodies(jd_ut: float) -> Dict[str, Dict[str, Any]]:
    """
    Planets + extras. Ephe dosyası yoksa bazı extras (örn. Chiron) otomatik skip edilir.
    """
    bodies: Dict[str, Dict[str, Any]] = {}
    merged: Dict[str, int] = {}
    merged.update(PLANETS)
    merged.update(EXTRA_BODIES)

    for name, pid in merged.items():
        res = _safe_calc_ut(jd_ut, pid)
        if res is None:
            # Crash yok: sadece işaretle/skip
            bodies[name] = {
                "available": False,
                "lon": None,
                "lat": None,
                "sign": None,
                "deg_in_sign": None,
                "lon_speed": None,
            }
            continue

        xx, _ = res
        lon, lat, lon_speed = float(xx[0]), float(xx[1]), float(xx[3])
        lon = wrap360(lon)
        sign, within = deg_to_sign(lon)

        bodies[name] = {
            "available": True,
            "lon": lon,
            "lat": lat,
            "sign": sign,
            "deg_in_sign": float(within),
            "lon_speed": lon_speed,
        }

    return bodies

def compute_houses(jd_ut: float, latitude: float, longitude: float, house_system: str = "P") -> Dict[str, object]:
    hs = _hs_bytes(house_system)
    cusps, ascmc = swe.houses(jd_ut, latitude, longitude, hs)

    cusp_list = (
        [wrap360(float(c)) for c in cusps[1:13]] if len(cusps) >= 13
        else [wrap360(float(c)) for c in cusps[:12]]
    )

    asc = wrap360(float(ascmc[0])) if len(ascmc) > 0 else None
    mc = wrap360(float(ascmc[1])) if len(ascmc) > 1 else None

    return {"cusps": cusp_list, "ascendant": asc, "midheaven": mc}

def compute_planet_houses(
    jd_ut: float,
    latitude: float,
    longitude: float,
    house_system: str,
    bodies: Dict[str, Dict[str, Any]]
) -> None:
    hs = _hs_bytes(house_system)

    for name, d in bodies.items():
        if not d.get("available") or d.get("lon") is None:
            d["house"] = None
            d["house_pos"] = None
            continue

        lon = float(d["lon"])
        lat = float(d.get("lat") or 0.0)

        try:
            hpos = swe.house_pos(jd_ut, latitude, longitude, hs, lon, lat)
        except Exception:
            hpos = None

        if hpos is None:
            d["house"] = None
            d["house_pos"] = None
        else:
            d["house_pos"] = float(hpos)
            d["house"] = int(float(hpos))

def compute_angles_and_points(
    jd_ut: float,
    latitude: float,
    longitude: float,
    house_system: str = "P",
) -> Dict[str, Dict[str, float]]:
    hs = _hs_bytes(house_system)
    cusps, ascmc = swe.houses(jd_ut, latitude, longitude, hs)

    asc = wrap360(float(ascmc[0])) if len(ascmc) > 0 else None
    mc = wrap360(float(ascmc[1])) if len(ascmc) > 1 else None
    vertex = wrap360(float(ascmc[3])) if len(ascmc) > 3 else None

    dsc = opposite_deg(asc) if asc is not None else None
    ic = opposite_deg(mc) if mc is not None else None

    # Sun/Moon for Fortune (safe)
    sun_res = _safe_calc_ut(jd_ut, swe.SUN)
    moon_res = _safe_calc_ut(jd_ut, swe.MOON)
    if sun_res is None or moon_res is None or asc is None:
        fortune = None
        sun_lon = None
        moon_lon = None
        is_day = True
    else:
        xx_sun, _ = sun_res
        xx_moon, _ = moon_res
        sun_lon = wrap360(float(xx_sun[0]))
        moon_lon = wrap360(float(xx_moon[0]))

        try:
            sun_house_pos = swe.house_pos(jd_ut, latitude, longitude, hs, sun_lon, float(xx_sun[1]))
            is_day = (sun_house_pos is not None and float(sun_house_pos) <= 6.0)
        except Exception:
            is_day = True

        if is_day:
            fortune = wrap360(asc + moon_lon - sun_lon)
        else:
            fortune = wrap360(asc + sun_lon - moon_lon)

    def pack(lon: Optional[float]) -> Optional[Dict[str, float]]:
        if lon is None:
            return None
        sign, within = deg_to_sign(lon)
        return {"lon": float(lon), "sign": sign, "deg_in_sign": float(within)}

    points: Dict[str, Dict[str, float]] = {}
    for k, v in [("Asc", asc), ("MC", mc), ("DSC", dsc), ("IC", ic), ("Vertex", vertex), ("Fortune", fortune)]:
        pv = pack(v)
        if pv:
            points[k] = pv

    return points

# ----------------------------
# ASPECTS
# ----------------------------

def compute_aspects_between(objects: Dict[str, Dict[str, Any]]) -> List[Dict[str, float]]:
    names = [k for k, v in objects.items() if v.get("lon") is not None]
    res: List[Dict[str, float]] = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p1, p2 = names[i], names[j]
            a, b = float(objects[p1]["lon"]), float(objects[p2]["lon"])
            sep = angular_separation(a, b)
            for asp_name, asp_deg in ASPECTS.items():
                orb = abs(sep - float(asp_deg))
                if orb <= DEFAULT_ORBS[asp_name]:
                    res.append({
                        "p1": p1,
                        "p2": p2,
                        "aspect": asp_name,
                        "exact": float(asp_deg),
                        "sep": float(sep),
                        "orb": float(orb),
                    })
                    break

    res.sort(key=lambda x: x["orb"])
    return res

# ----------------------------
# PUBLIC API
# ----------------------------

def compute_natal_chart(
    *,
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    latitude: float,
    longitude: float,
    tz_offset_hours: float = 3.0,
    house_system: str = "P",
) -> Dict[str, object]:
    jd_ut = to_julian_day_ut(year, month, day, hour, minute, tz_offset_hours)

    bodies = compute_all_bodies(jd_ut)
    houses = compute_houses(jd_ut, latitude, longitude, house_system=house_system)
    points = compute_angles_and_points(jd_ut, latitude, longitude, house_system=house_system)

    compute_planet_houses(jd_ut, latitude, longitude, house_system, bodies)

    # Planet aspects: only major planets that are available
    major_planets = {k: bodies[k] for k in MAJOR_PLANET_NAMES if k in bodies and bodies[k].get("lon") is not None}
    planet_aspects = compute_aspects_between(major_planets)

    # Other aspects: points + extras + major planets
    other_objects: Dict[str, Dict[str, Any]] = {}
    other_objects.update(points)

    for k in ["TrueNode", "Chiron", "Lilith"]:
        if k in bodies and bodies[k].get("lon") is not None:
            other_objects[k] = bodies[k]

    other_objects.update(major_planets)
    other_aspects = compute_aspects_between(other_objects)

    return {
        "name": name,
        "jd_ut": jd_ut,
        "planets": bodies,     # includes extras; unavailable ones have available=False
        "houses": houses,
        "points": points,
        "aspects": {
            "planet_aspects": planet_aspects,
            "other_aspects": other_aspects,
        },
    }
