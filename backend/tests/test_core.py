from __future__ import annotations

import math
import unittest

from fastapi.testclient import TestClient

from app.chart import compute_natal_chart, wrap360
from app.main import app
from app.models import BirthData
from app.pdf_report import build_report_pdf
from app.rag import exact_passage, load_index


SAMPLE = dict(
    name="Example",
    year=2002,
    month=1,
    day=25,
    hour=9,
    minute=30,
    latitude=40.872,
    longitude=35.464,
    tz_offset_hours=3.0,
)


class ChartTests(unittest.TestCase):
    def test_planet_house_positions_are_computed(self):
        chart = compute_natal_chart(**SAMPLE, house_system="P")
        for name, body in chart["planets"].items():
            if body.get("available"):
                self.assertIsNotNone(body.get("house"), name)
                self.assertGreaterEqual(body["house"], 1)
                self.assertLessEqual(body["house"], 12)
                self.assertIsNotNone(body.get("house_pos"), name)

    def test_house_system_is_respected(self):
        p = compute_natal_chart(**SAMPLE, house_system="P")
        w = compute_natal_chart(**SAMPLE, house_system="W")
        self.assertEqual(p["house_system"], "P")
        self.assertEqual(w["house_system"], "W")
        self.assertNotEqual(p["houses"]["cusps"], w["houses"]["cusps"])
        for cusp in w["houses"]["cusps"]:
            self.assertAlmostEqual(cusp % 30.0, 0.0, places=7)

    def test_major_aspects_are_not_duplicated_in_other_aspects(self):
        chart = compute_natal_chart(**SAMPLE, house_system="P")
        major = {
            (tuple(sorted((a["p1"], a["p2"]))), a["aspect"])
            for a in chart["aspects"]["planet_aspects"]
        }
        for aspect in chart["aspects"]["other_aspects"]:
            key = (tuple(sorted((aspect["p1"], aspect["p2"]))), aspect["aspect"])
            self.assertNotIn(key, major)


    def test_unknown_time_omits_houses_angles_and_moon_aspects(self):
        chart = compute_natal_chart(**SAMPLE, house_system="P", time_unknown=True)
        self.assertTrue(chart["time_unknown"])
        self.assertEqual(chart["houses"]["cusps"], [])
        self.assertEqual(chart["points"], {})
        self.assertIsNone(chart["house_system"])
        for body in chart["planets"].values():
            if body.get("available"):
                self.assertIsNone(body.get("house"))
                self.assertEqual(body.get("time_precision"), "date_only")
        all_aspects = chart["aspects"]["planet_aspects"] + chart["aspects"]["other_aspects"]
        self.assertTrue(all("Moon" not in {a.get("p1"), a.get("p2")} for a in all_aspects))

    def test_part_of_fortune_switches_day_night_formula(self):
        day = compute_natal_chart(**{**SAMPLE, "hour": 12, "minute": 0}, house_system="P")
        night = compute_natal_chart(**{**SAMPLE, "hour": 0, "minute": 0}, house_system="P")

        for chart in (day, night):
            asc = chart["points"]["Asc"]["lon"]
            sun = chart["planets"]["Sun"]["lon"]
            moon = chart["planets"]["Moon"]["lon"]
            sun_house_pos = chart["planets"]["Sun"]["house_pos"]
            is_day = 7.0 <= sun_house_pos < 13.0
            expected = wrap360(asc + moon - sun) if is_day else wrap360(asc + sun - moon)
            actual = chart["points"]["Fortune"]["lon"]
            self.assertTrue(math.isclose(expected, actual, abs_tol=1e-8))


class ValidationAndApiTests(unittest.TestCase):
    def test_invalid_calendar_date_is_rejected(self):
        with self.assertRaises(Exception):
            BirthData(**{**SAMPLE, "month": 2, "day": 31})


    def test_timezone_is_resolved_from_iana_zone(self):
        client = TestClient(app)
        payload = {
            **SAMPLE,
            "timezone": "Europe/Istanbul",
            "house_system": "P",
            "style": "modern",
            "focus": "general",
        }
        response = client.post("/api/chart/natal", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # Turkey was UTC+2 on 25 Jan 2002; this catches manual-offset drift.
        self.assertEqual(body["timezone"], "Europe/Istanbul")
        self.assertAlmostEqual(body["tz_offset_hours_resolved"], 2.0, places=6)

    def test_unknown_time_api_accepts_checkbox_payload(self):
        client = TestClient(app)
        payload = {
            **SAMPLE,
            "time_unknown": True,
            "timezone": "Europe/Istanbul",
            "house_system": "P",
            "style": "modern",
            "focus": "general",
        }
        response = client.post("/api/chart/natal", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["time_unknown"])
        self.assertEqual(body["points"], {})
        self.assertEqual(body["houses"]["reason"], "birth_time_unknown")

    def test_unknown_time_interpretation_is_explicitly_limited(self):
        client = TestClient(app)
        payload = {
            **SAMPLE,
            "time_unknown": True,
            "timezone": "Europe/Istanbul",
            "house_system": "P",
            "style": "modern",
            "focus": "general",
        }
        response = client.post("/api/interpret/natal", json=payload)
        self.assertEqual(response.status_code, 200)
        text = response.json()["interpretation"]
        self.assertIn("birth time", text.lower())
        self.assertNotIn("**1st House in", text)

    def test_interpretation_endpoint_hides_internal_rag_data_in_production(self):
        client = TestClient(app)
        payload = {
            **SAMPLE,
            "house_system": "W",
            "style": "psychological",
            "focus": "career",
        }
        response = client.post("/api/interpret/natal", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["chart"]["house_system"], "W")
        self.assertIn("interpretation", body)
        self.assertNotIn("retrieval", body)
        self.assertNotIn("query", body)


class ProductionSecurityTests(unittest.TestCase):
    def test_security_headers_are_present(self):
        client = TestClient(app)
        r = client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(r.headers.get("x-frame-options"), "DENY")
        self.assertEqual(r.headers.get("referrer-policy"), "no-referrer")
        self.assertIn("frame-ancestors 'none'", r.headers.get("content-security-policy", ""))

    def test_production_openapi_surface_is_disabled(self):
        client = TestClient(app)
        r = client.get("/openapi.json")
        self.assertEqual(r.status_code, 404)

    def test_production_rebuild_endpoint_is_not_registered(self):
        client = TestClient(app)
        r = client.post("/api/rebuild-index")
        self.assertEqual(r.status_code, 404)

    def test_production_health_does_not_disclose_version(self):
        client = TestClient(app)
        r = client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True})

    def test_declared_oversize_request_is_rejected(self):
        client = TestClient(app)
        payload = b"{}"
        r = client.post("/api/chart/natal", content=payload, headers={"content-type": "application/json", "content-length": "1000001"})
        self.assertEqual(r.status_code, 413)



class RagTests(unittest.TestCase):
    def test_house_corpus_is_indexed(self):
        chunks = load_index()
        self.assertTrue(any(c.source.startswith("houses/") for c in chunks))
        hit = exact_passage(typ="HOUSE", body="HOUSE_1", sign="AQUARIUS")
        self.assertIsNotNone(hit)


class CorpusCoverageTests(unittest.TestCase):
    SIGNS = [
        "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
        "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
    ]

    def test_all_supported_placements_have_all_signs(self):
        bodies = [
            "SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER",
            "SATURN", "URANUS", "NEPTUNE", "PLUTO", "TRUENODE", "CHIRON", "LILITH",
        ]
        missing = []
        for body in bodies:
            for sign in self.SIGNS:
                if exact_passage(typ="PLACEMENT", body=body, sign=sign) is None:
                    missing.append(f"{body}/{sign}")
        self.assertEqual(missing, [])

    def test_all_supported_points_have_all_signs(self):
        bodies = ["ASC", "MC", "DSC", "IC", "VERTEX", "FORTUNE"]
        missing = []
        for body in bodies:
            for sign in self.SIGNS:
                if exact_passage(typ="POINT", body=body, sign=sign) is None:
                    missing.append(f"{body}/{sign}")
        self.assertEqual(missing, [])

    def test_all_house_cusps_have_all_signs(self):
        missing = []
        for house in range(1, 13):
            for sign in self.SIGNS:
                if exact_passage(typ="HOUSE", body=f"HOUSE_{house}", sign=sign) is None:
                    missing.append(f"HOUSE_{house}/{sign}")
        self.assertEqual(missing, [])


class ExtendedSuiteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.a = {
            **SAMPLE,
            "timezone": "Europe/Istanbul",
            "house_system": "P",
            "style": "modern",
            "focus": "general",
            "time_unknown": False,
        }
        self.b = {
            **self.a,
            "name": "Other",
            "year": 2000, "month": 7, "day": 14,
            "hour": 18, "minute": 0,
            "latitude": 39.9334, "longitude": 32.8597,
        }

    def test_synastry_returns_cross_chart_aspects(self):
        r = self.client.post("/api/interpret/synastry", json={"person_a": self.a, "person_b": self.b, "style": "modern"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreater(len(body["synastry"]["aspects"]), 0)
        self.assertIn("interpretation", body)

    def test_synastry_unknown_time_omits_that_persons_moon_and_angles(self):
        unknown = {**self.b, "time_unknown": True}
        r = self.client.post("/api/chart/synastry", json={"person_a": self.a, "person_b": unknown, "style": "modern"})
        self.assertEqual(r.status_code, 200)
        aspects = r.json()["aspects"]
        self.assertTrue(all(a.get("b") != "Moon" for a in aspects))
        self.assertTrue(all(a.get("b") not in {"Asc", "DSC", "MC", "IC", "Vertex"} for a in aspects))

    def test_composite_midpoints_planets_and_house_cusps_when_both_times_known(self):
        r = self.client.post("/api/interpret/composite", json={"person_a": self.a, "person_b": self.b, "style": "modern"})
        self.assertEqual(r.status_code, 200)
        comp = r.json()["composite"]
        self.assertEqual(comp["method"], "zodiacal_midpoint")
        self.assertIn("Sun", comp["planets"])
        self.assertTrue(comp["houses"]["available"])
        self.assertEqual(len(comp["houses"]["cusps"]), 12)
        self.assertIn(comp["planets"]["Sun"]["house"], range(1, 13))

    def test_composite_omits_houses_if_either_birth_time_unknown(self):
        unknown = {**self.b, "time_unknown": True}
        r = self.client.post("/api/interpret/composite", json={"person_a": self.a, "person_b": unknown, "style": "modern"})
        self.assertEqual(r.status_code, 200)
        comp = r.json()["composite"]
        self.assertFalse(comp["houses"]["available"])
        self.assertEqual(comp["houses"]["cusps"], [])

    def test_astrocartography_has_four_angular_line_families(self):
        r = self.client.post("/api/interpret/astrocartography", json=self.a)
        self.assertEqual(r.status_code, 200)
        lines = r.json()["astrocartography"]["lines"]
        sun_angles = {x["angle"] for x in lines if x["planet"] == "Sun"}
        self.assertEqual(sun_angles, {"ASC", "DSC", "MC", "IC"})

    def test_astrocartography_rejects_unknown_birth_time(self):
        r = self.client.post("/api/interpret/astrocartography", json={**self.a, "time_unknown": True})
        self.assertEqual(r.status_code, 422)

    def test_pdf_report_is_a_real_pdf(self):
        syn = self.client.post("/api/interpret/synastry", json={"person_a": self.a, "person_b": self.b, "style": "modern"}).json()
        r = self.client.post("/api/report/pdf", json={
            "kind": "synastry",
            "title": "AstroMYLA Synastry Test",
            "data": syn,
            "interpretation": syn["interpretation"],
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))
        self.assertGreater(len(r.content), 2000)

    def test_premium_pdf_contains_vector_chart_and_long_form_layout(self):
        natal = self.client.post("/api/interpret/natal", json=self.a).json()
        content = build_report_pdf(
            kind="natal",
            title="AstroMYLA Personalized Reading - Example",
            data=natal,
            interpretation=(natal["interpretation"] + "\n\n### A second chapter\n" + natal["interpretation"]),
            tier="personalized",
        )
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertGreater(len(content), 6000)

    def test_public_report_endpoint_rejects_premium_tier(self):
        r = self.client.post("/api/report/pdf", json={
            "kind": "natal",
            "title": "Should Not Bypass Checkout",
            "data": {"chart": {}},
            "interpretation": "test",
            "tier": "deep",
        })
        self.assertEqual(r.status_code, 403)


if __name__ == "__main__":
    unittest.main()
