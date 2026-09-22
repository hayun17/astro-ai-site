from __future__ import annotations

import math
import unittest

from fastapi.testclient import TestClient

from app.chart import compute_all_bodies, to_julian_day_ut
from app.main import app


class PublishedEphemerisReferenceTests(unittest.TestCase):
    """Regression checks against a published 25-Jan-2002 00:00 UT ephemeris.

    The source values are published to the nearest arcminute, so the tolerance
    is one arcminute. The application keeps substantially more precision than
    the display/reference table.
    """

    # Tropical geocentric zodiac, 2002-01-25 00:00 UT, degree within sign.
    REFERENCE = {
        "Sun": 4 + 50 / 60,
        "Moon": 12 + 50 / 60,
        "Mercury": 10 + 59 / 60,
        "Venus": 7 + 21 / 60,
        "Mars": 4 + 24 / 60,
        "Jupiter": 7 + 39 / 60,
        "Saturn": 8 + 13 / 60,
        "Uranus": 23 + 42 / 60,
        "Neptune": 8 + 20 / 60,
        "Pluto": 16 + 49 / 60,
    }

    def test_planet_degrees_match_published_ephemeris_to_arcminute(self):
        jd = to_julian_day_ut(2002, 1, 25, 0, 0, 0.0)
        bodies = compute_all_bodies(jd)
        for name, expected in self.REFERENCE.items():
            actual = float(bodies[name]["deg_in_sign"])
            difference_arcmin = abs(actual - expected) * 60.0
            self.assertLessEqual(
                difference_arcmin,
                1.0,
                f"{name}: {actual:.6f}° differs from published {expected:.6f}° by {difference_arcmin:.3f} arcmin",
            )


class HistoricalTimezoneRegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.base = {
            "name": "Reference",
            "year": 2002,
            "month": 1,
            "day": 25,
            "hour": 9,
            "minute": 30,
            "latitude": 40.872,
            "longitude": 35.464,
            "tz_offset_hours": 3.0,  # intentionally wrong manual fallback
            "timezone": "Europe/Istanbul",
            "house_system": "P",
            "style": "modern",
            "focus": "general",
            "time_unknown": False,
        }

    def test_istanbul_winter_2002_resolves_utc_plus_two(self):
        response = self.client.post("/api/chart/natal", json=self.base)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(math.isclose(float(body["tz_offset_hours_resolved"]), 2.0, abs_tol=1e-9))
        # Regression guard: +2 gives an Aries Ascendant here. Using a modern
        # hard-coded +3 would move it back into Pisces.
        self.assertEqual(body["points"]["Asc"]["sign"], "Aries")
        self.assertAlmostEqual(float(body["points"]["Asc"]["deg_in_sign"]), 4.1829, places=3)

    def test_istanbul_summer_2002_resolves_utc_plus_three(self):
        payload = {**self.base, "month": 7, "day": 25}
        response = self.client.post("/api/chart/natal", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(math.isclose(float(response.json()["tz_offset_hours_resolved"]), 3.0, abs_tol=1e-9))

    def test_istanbul_after_2016_is_utc_plus_three_year_round(self):
        payload = {**self.base, "year": 2017, "month": 1, "day": 25}
        response = self.client.post("/api/chart/natal", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(math.isclose(float(response.json()["tz_offset_hours_resolved"]), 3.0, abs_tol=1e-9))


if __name__ == "__main__":
    unittest.main()
