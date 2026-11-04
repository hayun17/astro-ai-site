"""Regression tests for v1.10.1 transit reading visibility and fidelity."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.transit_reading import build_transit_reading, render_transit_reading
from app.transits import compute_personal_transits
from app.models import BirthData
from app.chart import compute_natal_chart
from datetime import date

BIRTH = {"name": "Example", "year": 2005, "month": 11, "day": 30,
         "hour": 9, "minute": 37, "latitude": 37.87, "longitude": 32.49,
         "timezone": "Europe/Istanbul", "tz_offset_hours": 2, "house_system": "P"}

class TransitReadingTests(unittest.TestCase):
    def test_real_api_returns_actual_reading_and_transit_aspect(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with TestClient(app) as client:
                response = client.post("/api/interpret/daily", json={"birth": BIRTH, "target_date": "2026-11-04", "style":"modern"})
                self.assertEqual(response.status_code, 200, response.text)
                data = response.json()
        reading = data["transits"]["reading"]
        self.assertEqual(reading["date"], "2026-11-04")
        self.assertGreaterEqual(len(reading["key_aspects"]), 1)
        first = reading["key_aspects"][0]
        actual = data["transits"]["top_aspects"][0]
        self.assertEqual((first["transit"], first["aspect"], first["natal"]),
                         (actual["transit"], actual["aspect"], actual["natal"]))
        self.assertEqual(first["orb"], round(actual["orb"], 2))
        self.assertGreater(len(first["summary"]), 110)
        self.assertIn("### Your sky, explained", data["interpretation"])

    def test_personal_house_stories_match_actual_overlays(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with TestClient(app) as client:
                data = client.post("/api/interpret/daily", json={"birth":BIRTH,"target_date":"2026-11-04"}).json()
        overlays = {(x["planet"], x["house"]) for x in data["transits"]["house_overlays"]}
        house_stories = data["transits"]["reading"]["house_stories"]
        self.assertTrue(house_stories)
        for h in house_stories:
            self.assertIn((h["planet"], h["house"]), overlays)
            self.assertIn("house", h["summary"].lower())

    def test_unknown_birth_time_does_not_invent_houses_or_moon(self):
        birth = {**BIRTH,"time_unknown":True}
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with TestClient(app) as client:
                response = client.post("/api/interpret/daily", json={"birth":birth,"target_date":"2026-11-04"})
                self.assertEqual(response.status_code,200,response.text)
                data = response.json()
        reading = data["transits"]["reading"]
        self.assertFalse(reading["house_stories"])
        self.assertTrue(reading["birth_time_note"])
        self.assertNotIn("your natal Moon", " ".join(i["title"] for i in reading["key_aspects"]))

    def test_curated_mars_moon_story_and_orb_are_evidence_based(self):
        data = {"target_utc":"2026-11-04T12:00:00+00:00", "top_aspects":[
            {"transit":"Mars","natal":"Moon","aspect":"Square","orb":0.41,"applying":True}
        ], "house_overlays":[{"planet":"Venus","house":7,"theme":"partnership"}]}
        result = build_transit_reading(data, {"time_unknown":False})
        item = result["key_aspects"][0]
        self.assertIn("Mars square your natal Moon",item["title"])
        self.assertIn("impatience",item["summary"])
        self.assertEqual(item["orb"],0.41)
        self.assertIn("7th house",result["house_stories"][0]["title"])
        longform = render_transit_reading(result)
        self.assertIn("Mars square your natal Moon",longform)
        self.assertIn("Venus in your natal 7th house",longform)

    def test_quiet_period_is_honest_about_orb_filter(self):
        result = build_transit_reading({"target_utc":"2026-11-04T12:00:00+00:00","top_aspects":[],"house_overlays":[]}, {"time_unknown":True})
        self.assertFalse(result["key_aspects"])
        self.assertIn("No major transit-to-natal aspects",result["intro"])
        self.assertIn("unknown",result["birth_time_note"])
