from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

# ----------------------------
# EPHEMERIS PATH
# ----------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EPHE = os.path.normpath(os.path.join(HERE, "..", "ephe"))
EPHE_PATH = os.environ.get("SE_EPHE_PATH") or (DEFAULT_EPHE if os.path.isdir(DEFAULT_EPHE) else ".")
swe.set_ephe_path(EPHE_PATH)


class ChartComputationError(ValueError):
    """Raised when Swiss Ephemeris cannot compute the requested chart."""


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

# Chiron needs asteroid ephemeris files. If they are unavailable we mark it as
# unavailable instead of fabricating a position. Lilith here is Mean Black Moon.
EXTRA_BODIES: Dict[str, int] = {
    "Chiron": swe.CHIRON,
    "Lilith": swe.MEAN_APOG,
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ASPECTS = {
    "Conjunction": 0.0,
    "Opposition": 180.0,
    "Trine": 120.0,
    "Square": 90.0,
    "Sextile": 60.0,
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

VALID_HOUSE_SYSTEMS = {"P", "W", "K", "R", "C", "E"}

# ----------------------------
# HELPERS
# ----------------------------

def wrap360(deg: float) -> float:
    return float(deg) % 360.0


def angular_separation(a: float, b: float) -> float:
    d = abs(wrap360(a) - wrap360(b))
    return min(d, 360.0 - d)


def deg_to_sign(deg: float) -> Tuple[str, float]:
    deg = wrap360(deg)
    sign_idx = int(deg // 30.0)
    within = deg - 30.0 * sign_idx
    return SIGNS[sign_idx], within


def opposite_deg(x: float) -> float:
    return wrap360(x + 180.0)


def to_julian_day_ut(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    tz_offset_hours: float,
) -> float:
    h_local = hour + minute / 60.0
    h_ut = h_local - tz_offset_hours
    return swe.julday(year, month, day, h_ut, swe.GREG_CAL)


def _hs_bytes(house_system: str) -> bytes:
    hs = (house_system or "P").upper()[:1]
    if hs not in VALID_HOUSE_SYSTEMS:
        raise ChartComputationError(f"Unsupported house system: {house_system!r}")
    return hs.encode("ascii")


def _safe_calc_ut(jd_ut: float, pid: int) -> Optional[Tuple[Tuple[float, ...], int]]:
    """Try Swiss Ephemeris first, then Moshier, always requesting speed."""
    try:
        return swe.calc_ut(jd_ut, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)
    except swe.Error:
        try:
            return swe.calc_ut(jd_ut, pid, swe.FLG_MOSEPH | swe.FLG_SPEED)
        except swe.Error:
            return None


def _houses_raw(jd_ut: float, latitude: float, longitude: float, hs: bytes):
    try:
        return swe.houses(jd_ut, latitude, longitude, hs)
    except swe.Error as exc:
        raise ChartComputationError(
            "The selected house system cannot be calculated for these coordinates. "
            "Try Whole Sign (W) or Equal (E), especially at extreme latitudes."
        ) from exc


def _true_obliquity(jd_ut: float) -> float:
    try:
        xx, _ = swe.calc_ut(jd_ut, swe.ECL_NUT, swe.FLG_SWIEPH)
        return float(xx[0])
    except swe.Error:
        xx, _ = swe.calc_ut(jd_ut, swe.ECL_NUT, swe.FLG_MOSEPH)
        return float(xx[0])


def _house_pos(
    *,
    jd_ut: float,
    latitude: float,
    longitude: float,
    house_system: str,
    obj_lon: float,
    obj_lat: float,
) -> float:
    """Return Swiss Ephemeris house position in [1, 13)."""
    hs = _hs_bytes(house_system)
    _, ascmc = _houses_raw(jd_ut, latitude, longitude, hs)
    armc = float(ascmc[2])
    eps = _true_obliquity(jd_ut)
    try:
        return float(swe.house_pos(armc, latitude, eps, (obj_lon, obj_lat), hs))
    except swe.Error as exc:
        raise ChartComputationError("Could not calculate a house position.") from exc


# ----------------------------
# COMPUTE BODIES / HOUSES
# ----------------------------

def compute_all_bodies(jd_ut: float) -> Dict[str, Dict[str, Any]]:
    bodies: Dict[str, Dict[str, Any]] = {}
    merged: Dict[str, int] = {**PLANETS, **EXTRA_BODIES}

    for name, pid in merged.items():
        res = _safe_calc_ut(jd_ut, pid)
        if res is None:
            bodies[name] = {
                "available": False,
                "lon": None,
                "lat": None,
                "sign": None,
                "deg_in_sign": None,
                "lon_speed": None,
                "retrograde": None,
            }
            continue

        xx, _ = res
        lon = wrap360(float(xx[0]))
        lat = float(xx[1])
        lon_speed = float(xx[3])
        sign, within = deg_to_sign(lon)

        bodies[name] = {
            "available": True,
            "lon": lon,
            "lat": lat,
            "sign": sign,
            "deg_in_sign": float(within),
            "lon_speed": lon_speed,
            "retrograde": lon_speed < 0.0,
        }

    return bodies


def compute_houses(
    jd_ut: float,
    latitude: float,
    longitude: float,
    house_system: str = "P",
) -> Dict[str, object]:
    hs = _hs_bytes(house_system)
    cusps, ascmc = _houses_raw(jd_ut, latitude, longitude, hs)

    cusp_list = [wrap360(float(c)) for c in tuple(cusps)[:12]]
    cusp_signs = [deg_to_sign(c)[0] for c in cusp_list]

    asc = wrap360(float(ascmc[0])) if len(ascmc) > 0 else None
    mc = wrap360(float(ascmc[1])) if len(ascmc) > 1 else None

    return {
        "system": house_system.upper()[:1],
        "cusps": cusp_list,
        "signs": cusp_signs,
        "ascendant": asc,
        "midheaven": mc,
    }


def compute_planet_houses(
    jd_ut: float,
    latitude: float,
    longitude: float,
    house_system: str,
    bodies: Dict[str, Dict[str, Any]],
) -> None:
    hs = _hs_bytes(house_system)
    _, ascmc = _houses_raw(jd_ut, latitude, longitude, hs)
    armc = float(ascmc[2])
    eps = _true_obliquity(jd_ut)

    for d in bodies.values():
        if not d.get("available") or d.get("lon") is None:
            d["house"] = None
            d["house_pos"] = None
            continue

        lon = float(d["lon"])
        lat = float(d.get("lat") or 0.0)
        try:
            hpos = float(swe.house_pos(armc, latitude, eps, (lon, lat), hs))
        except swe.Error:
            d["house"] = None
            d["house_pos"] = None
            continue

        # Swiss Ephemeris returns [1, 13). Keep the fractional position for
        # diagnostics and expose the conventional integer house number.
        d["house_pos"] = hpos
        d["house"] = max(1, min(12, int(hpos)))


def compute_angles_and_points(
    jd_ut: float,
    latitude: float,
    longitude: float,
    house_system: str = "P",
) -> Dict[str, Dict[str, Any]]:
    hs = _hs_bytes(house_system)
    _, ascmc = _houses_raw(jd_ut, latitude, longitude, hs)

    asc = wrap360(float(ascmc[0])) if len(ascmc) > 0 else None
    mc = wrap360(float(ascmc[1])) if len(ascmc) > 1 else None
    vertex = wrap360(float(ascmc[3])) if len(ascmc) > 3 else None

    dsc = opposite_deg(asc) if asc is not None else None
    ic = opposite_deg(mc) if mc is not None else None

    # Part of Fortune: day chart = ASC + Moon - Sun; night chart = ASC + Sun - Moon.
    sun_res = _safe_calc_ut(jd_ut, swe.SUN)
    moon_res = _safe_calc_ut(jd_ut, swe.MOON)
    fortune: Optional[float] = None

    if sun_res is not None and moon_res is not None and asc is not None:
        xx_sun, _ = sun_res
        xx_moon, _ = moon_res
        sun_lon = wrap360(float(xx_sun[0]))
        moon_lon = wrap360(float(xx_moon[0]))
        try:
            sun_hpos = _house_pos(
                jd_ut=jd_ut,
                latitude=latitude,
                longitude=longitude,
                house_system=house_system,
                obj_lon=sun_lon,
                obj_lat=float(xx_sun[1]),
            )
            # Houses 7–12 are above the horizon; 1–6 are below it.
            is_day = 7.0 <= sun_hpos < 13.0
        except ChartComputationError:
            is_day = True

        fortune = wrap360(asc + moon_lon - sun_lon) if is_day else wrap360(asc + sun_lon - moon_lon)

    def pack(lon: Optional[float]) -> Optional[Dict[str, Any]]:
        if lon is None:
            return None
        sign, within = deg_to_sign(lon)
        return {"lon": float(lon), "sign": sign, "deg_in_sign": float(within)}

    points: Dict[str, Dict[str, Any]] = {}
    for key, value in [
        ("Asc", asc),
        ("MC", mc),
        ("DSC", dsc),
        ("IC", ic),
        ("Vertex", vertex),
        ("Fortune", fortune),
    ]:
        packed = pack(value)
        if packed:
            points[key] = packed

    return points


# ----------------------------
# ASPECTS
# ----------------------------

def compute_aspects_between(objects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    names = [k for k, v in objects.items() if v.get("lon") is not None]
    result: List[Dict[str, Any]] = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p1, p2 = names[i], names[j]
            a, b = float(objects[p1]["lon"]), float(objects[p2]["lon"])
            sep = angular_separation(a, b)
            for aspect_name, aspect_deg in ASPECTS.items():
                orb = abs(sep - aspect_deg)
                if orb <= DEFAULT_ORBS[aspect_name]:
                    result.append({
                        "p1": p1,
                        "p2": p2,
                        "aspect": aspect_name,
                        "exact": aspect_deg,
                        "sep": float(sep),
                        "orb": float(orb),
                    })
                    break

    result.sort(key=lambda x: x["orb"])
    return result


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
    time_unknown: bool = False,
) -> Dict[str, object]:
    # With an unknown birth time we use local noon only as a neutral reference
    # for date-based planetary positions. We deliberately do NOT fabricate
    # houses, angles, Part of Fortune, or planet-house placements.
    calc_hour = 12 if time_unknown else hour
    calc_minute = 0 if time_unknown else minute
    jd_ut = to_julian_day_ut(year, month, day, calc_hour, calc_minute, tz_offset_hours)

    bodies = compute_all_bodies(jd_ut)

    if time_unknown:
        # Detect sign changes across the local calendar date. This matters most
        # for the Moon. If a sign can change that day, downstream RAG/LLM code
        # will avoid presenting one noon sign as certain.
        jd_start = to_julian_day_ut(year, month, day, 0, 0, tz_offset_hours)
        jd_end = to_julian_day_ut(year, month, day, 23, 59, tz_offset_hours)
        start_bodies = compute_all_bodies(jd_start)
        end_bodies = compute_all_bodies(jd_end)
        for key, body in bodies.items():
            body["house"] = None
            body["house_pos"] = None
            body["time_precision"] = "date_only"
            start_sign = (start_bodies.get(key) or {}).get("sign")
            end_sign = (end_bodies.get(key) or {}).get("sign")
            uncertain = bool(start_sign and end_sign and start_sign != end_sign)
            body["sign_uncertain"] = uncertain
            body["possible_signs"] = list(dict.fromkeys([s for s in [start_sign, end_sign] if s]))

        houses: Dict[str, object] = {
            "system": None,
            "cusps": [],
            "signs": [],
            "ascendant": None,
            "midheaven": None,
            "available": False,
            "reason": "birth_time_unknown",
        }
        points: Dict[str, Dict[str, Any]] = {}
    else:
        houses = compute_houses(jd_ut, latitude, longitude, house_system=house_system)
        points = compute_angles_and_points(jd_ut, latitude, longitude, house_system=house_system)
        compute_planet_houses(jd_ut, latitude, longitude, house_system, bodies)
        for body in bodies.values():
            body["time_precision"] = "exact_time"
            body["sign_uncertain"] = False
            body["possible_signs"] = [body.get("sign")] if body.get("sign") else []

    # Moon aspects can move materially during a date. In unknown-time mode we
    # omit them rather than turning a noon-only aspect into a false certainty.
    major_planets = {
        k: bodies[k]
        for k in MAJOR_PLANET_NAMES
        if k in bodies
        and bodies[k].get("lon") is not None
        and not (time_unknown and k == "Moon")
    }
    planet_aspects = compute_aspects_between(major_planets)

    # Build the expanded aspect graph, then remove major-major pairs because
    # they are already present in planet_aspects. This prevents duplicate rows
    # and duplicate weighting in downstream interpretation logic.
    expanded_objects: Dict[str, Dict[str, Any]] = dict(major_planets)
    for key in ["TrueNode", "Chiron", "Lilith"]:
        if key in bodies and bodies[key].get("lon") is not None:
            expanded_objects[key] = bodies[key]
    expanded_objects.update(points)

    major_names = set(major_planets)
    other_aspects = [
        a for a in compute_aspects_between(expanded_objects)
        if not (a["p1"] in major_names and a["p2"] in major_names)
    ]

    return {
        "name": name,
        "jd_ut": jd_ut,
        "time_unknown": bool(time_unknown),
        "time_reference": "local_noon" if time_unknown else "birth_time",
        "time_note": (
            "Birth time was marked unknown. Planet positions use local noon as a reference; "
            "houses, angles, Part of Fortune, and Moon aspects are intentionally omitted."
            if time_unknown else None
        ),
        "house_system": None if time_unknown else house_system.upper()[:1],
        "planets": bodies,
        "houses": houses,
        "points": points,
        "aspects": {
            "planet_aspects": planet_aspects,
            "other_aspects": other_aspects,
        },
    }


def compute_object_house(
    *,
    jd_ut: float,
    latitude: float,
    longitude: float,
    house_system: str,
    obj_lon: float,
    obj_lat: float = 0.0,
) -> int:
    """Public helper for relationship overlays: return host-chart house 1..12."""
    hpos = _house_pos(
        jd_ut=jd_ut,
        latitude=latitude,
        longitude=longitude,
        house_system=house_system,
        obj_lon=obj_lon,
        obj_lat=obj_lat,
    )
    return max(1, min(12, int(hpos)))
