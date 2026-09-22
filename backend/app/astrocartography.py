from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import swisseph as swe

from .chart import MAJOR_PLANET_NAMES, PLANETS, wrap360


def _norm180(x: float) -> float:
    return ((float(x) + 180.0) % 360.0) - 180.0


def _equatorial_position(jd_ut: float, pid: int) -> Tuple[float, float]:
    flags = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
    try:
        xx, _ = swe.calc_ut(jd_ut, pid, flags)
    except swe.Error:
        xx, _ = swe.calc_ut(jd_ut, pid, swe.FLG_MOSEPH | swe.FLG_EQUATORIAL)
    return wrap360(float(xx[0])), float(xx[1])


def _split_dateline(points: List[List[float]]) -> List[List[List[float]]]:
    if not points:
        return []
    segments: List[List[List[float]]] = [[points[0]]]
    for prev, cur in zip(points, points[1:]):
        if abs(cur[0] - prev[0]) > 180.0:
            segments.append([cur])
        else:
            segments[-1].append(cur)
    return [seg for seg in segments if len(seg) >= 2]


def _rising_setting_points(ra_deg: float, dec_deg: float, gst_deg: float, rising: bool) -> List[List[float]]:
    points: List[List[float]] = []
    dec = math.radians(dec_deg)
    # Limit to a useful, readable map range and avoid numerical singularities
    # at the geographic poles.
    for lat in range(-75, 76, 2):
        phi = math.radians(lat)
        cos_h = -math.tan(phi) * math.tan(dec)
        if cos_h < -1.0 or cos_h > 1.0:
            continue  # circumpolar / never rises at this latitude
        h0 = math.degrees(math.acos(max(-1.0, min(1.0, cos_h))))
        lst = ra_deg - h0 if rising else ra_deg + h0
        lon = _norm180(lst - gst_deg)
        points.append([lon, float(lat)])
    return points


def compute_astrocartography(jd_ut: float) -> Dict[str, Any]:
    """Compute basic geocentric astrocartography angular lines.

    The result contains MC/IC meridians plus ASC/DSC curves for the major
    planets. It intentionally does not claim to include parans, local-space
    azimuths, relocated houses, or topocentric corrections.
    """
    gst_deg = float(swe.sidtime(jd_ut)) * 15.0
    lines: List[Dict[str, Any]] = []
    bodies: Dict[str, Dict[str, float]] = {}

    for name in MAJOR_PLANET_NAMES:
        pid = PLANETS[name]
        try:
            ra, dec = _equatorial_position(jd_ut, pid)
        except swe.Error:
            continue
        bodies[name] = {"ra": ra, "dec": dec}

        mc_lon = _norm180(ra - gst_deg)
        ic_lon = _norm180(mc_lon + 180.0)
        lines.append({
            "planet": name,
            "angle": "MC",
            "kind": "meridian",
            "segments": [[[mc_lon, -80.0], [mc_lon, 80.0]]],
        })
        lines.append({
            "planet": name,
            "angle": "IC",
            "kind": "meridian",
            "segments": [[[ic_lon, -80.0], [ic_lon, 80.0]]],
        })

        asc_pts = _rising_setting_points(ra, dec, gst_deg, True)
        dsc_pts = _rising_setting_points(ra, dec, gst_deg, False)
        asc_segments = _split_dateline(asc_pts)
        dsc_segments = _split_dateline(dsc_pts)
        if asc_segments:
            lines.append({"planet": name, "angle": "ASC", "kind": "curve", "segments": asc_segments})
        if dsc_segments:
            lines.append({"planet": name, "angle": "DSC", "kind": "curve", "segments": dsc_segments})

    return {
        "method": "geocentric_angular_lines",
        "jd_ut": float(jd_ut),
        "greenwich_sidereal_time_deg": gst_deg,
        "bodies": bodies,
        "lines": lines,
        "coverage_note": (
            "Shows planetary ASC/DSC rising-setting curves and MC/IC meridians. "
            "Parans, local-space lines and relocated-house calculations are not included in this version."
        ),
    }


def build_astrocartography_interpretation(data: Dict[str, Any]) -> str:
    planet_themes = {
        "Sun": ("visibility, vitality and confidence", "being seen and taking up space"),
        "Moon": ("belonging, emotion and instinct", "home-feeling, care and sensitivity"),
        "Mercury": ("learning, movement and communication", "conversation, study, writing and networking"),
        "Venus": ("connection, pleasure, aesthetics and ease", "relationships, social warmth and what you enjoy"),
        "Mars": ("drive, courage, friction and action", "initiative, competition, sexuality and sharper boundaries"),
        "Jupiter": ("growth, opportunity and perspective", "expansion, confidence, teaching and broader horizons"),
        "Saturn": ("responsibility, structure and endurance", "commitment, boundaries, work and long-term building"),
        "Uranus": ("freedom, disruption and reinvention", "experimentation, independence and sudden change"),
        "Neptune": ("imagination, spirituality and permeability", "inspiration, idealization and the need for clear boundaries"),
        "Pluto": ("intensity, power and transformation", "deep change, control themes and psychological depth"),
    }
    angle_meaning = {
        "ASC": "On the ASC, the planet is read through identity, body, beginnings and the way you meet the environment.",
        "DSC": "On the DSC, the planet is read through partners, clients, collaborators and the kinds of people or dynamics you meet one-to-one.",
        "MC": "On the MC, the planet is read through career, reputation, visibility, ambition and the direction of public life.",
        "IC": "On the IC, the planet is read through home, family, privacy, roots and the inner base from which you operate.",
    }
    lines = [
        "### How to read your astrocartography map",
        "Astrocartography takes the planets from one birth moment and maps the places on Earth where each planet was rising (ASC), setting (DSC), culminating overhead (MC), or at the lower meridian (IC). The line does not make a city automatically good or bad; it describes which planetary theme is emphasized and through which area of life.",
        "",
        "### The four angles",
    ]
    for angle in ["ASC", "DSC", "MC", "IC"]:
        lines.append(f"- **{angle}** — {angle_meaning[angle]}")

    primary = ["Sun", "Moon", "Venus", "Mars", "Jupiter", "Saturn", "Mercury", "Uranus", "Neptune", "Pluto"]
    for planet in primary:
        theme, lived = planet_themes[planet]
        lines.append(f"\n### {planet} lines — {theme}")
        lines.append(f"A {planet} line tends to bring more attention to {lived}. How that feels depends on the angle:")
        lines.append(f"- **{planet}–ASC:** the {planet.lower()} theme becomes personal and immediate — something you may feel through identity, body, pace and the way you start things.")
        lines.append(f"- **{planet}–DSC:** the {planet.lower()} theme often arrives through other people — partners, clients, rivals, collaborators or people who mirror it back to you.")
        lines.append(f"- **{planet}–MC:** the {planet.lower()} theme becomes more public — visible through work, reputation, ambition, leadership or the direction you are known for.")
        lines.append(f"- **{planet}–IC:** the {planet.lower()} theme moves inward — home, family, private life, belonging and the emotional foundation of a place can carry more of it.")

    lines.extend([
        "\n### Comparing two places without oversimplifying",
        "Pick the place first, then look at which lines are actually near it. Compare the planet and the angle together: Venus–DSC and Venus–MC are both Venus lines, but one emphasizes one-to-one relating while the other emphasizes public/social visibility. Mars–ASC can feel very different from Mars–IC for the same reason.",
        "If several lines cluster near the same region, read them as a combination rather than choosing one winner. A place can be energizing and demanding at the same time. For a serious relocation decision, the next layer is a relocated chart; parans and local-space techniques can add still more context.",
        "Astrocartography is interpretive. Use it as a map for questions and comparisons, not as a guarantee that a location will produce a specific event.",
    ])
    note = data.get("coverage_note")
    if note:
        lines.append(f"\n### Technical scope\n{note}")
    return "\n".join(lines)

