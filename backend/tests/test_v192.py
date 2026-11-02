from __future__ import annotations
import os
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.accounts import AccountStore
from app.synastry_story import build_directional_house_stories

SAMPLE = {
    "name":"Example", "year":2002,"month":1,"day":25,"hour":9,"minute":30,
    "latitude":40.872,"longitude":35.464,"tz_offset_hours":2.0,
    "timezone":"Europe/Istanbul", "house_system":"P",
}

class V192Tests(unittest.TestCase):
    def test_house_3_concentration_is_explicit_and_directional(self):
        overlay = {
            "a_in_b_houses":[{"planet":"Moon","house":3},{"planet":"Mercury","house":3},{"planet":"Venus","house":3},{"planet":"Saturn","house":7}],
            "b_in_a_houses":[{"planet":"Sun","house":5},{"planet":"Mars","house":5}],
        }
        result = build_directional_house_stories(overlay)
        forward = result["a_to_b"]
        self.assertEqual(forward["chapters"][0]["house"],3)
        text = forward["chapters"][0]["opening"]
        for token in ("Person A", "Person B", "Moon", "Mercury", "Venus", "House 3"):
            self.assertIn(token, text)
        reverse = result["b_to_a"]
        self.assertEqual(reverse["chapters"][0]["house"],5)
        self.assertIn("Person B's",reverse["chapters"][0]["opening"])
        self.assertNotIn("Moon",reverse["chapters"][0]["opening"])

    def test_unknown_time_has_no_fabricated_house_story(self):
        story = build_directional_house_stories({"a_in_b_houses":[], "b_in_a_houses":[]})
        self.assertFalse(story["a_to_b"]["available"])
        self.assertEqual(story["a_to_b"]["chapters"], [])

    def test_endpoint_has_house_stories_in_both_directions(self):
        with TestClient(app) as client:
            response = client.post("/api/chart/synastry", json={"person_a":SAMPLE, "person_b":{**SAMPLE, "name":"Second", "year":2005,"month":11,"day":30}})
            self.assertEqual(response.status_code,200, response.text)
            stories = response.json()["house_stories"]
            self.assertTrue(stories["a_to_b"]["available"])
            self.assertTrue(stories["b_to_a"]["available"])
            self.assertGreater(len(stories["a_to_b"]["chapters"]),0)

    def test_saved_charts_really_persist_and_are_account_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            url = 'sqlite:///' + str(Path(tmp) / 'accounts.sqlite3')
            with patch.dict(os.environ, {"DATABASE_URL":url}, clear=False):
                first = AccountStore()
                alice, token_a = first.register("alice@example.test","strong-password-123", "Alice")
                bob, token_b = first.register("bob@example.test","strong-password-456", "Bob")
                from app.models import BirthData
                saved = first.save_chart(alice["id"], "My lovely chart", BirthData(**SAMPLE))
                self.assertEqual(saved["label"], "My lovely chart")
                new_store = AccountStore()
                own = new_store.list_charts(alice["id"])
                self.assertEqual(len(own),1)
                self.assertEqual(own[0]["birth"]["name"], "Example")
                self.assertEqual(new_store.list_charts(bob["id"]),[])
                self.assertFalse(new_store.delete_chart(bob["id"],saved["id"]))
                self.assertEqual(len(new_store.list_charts(alice["id"])),1)
                self.assertEqual(new_store.user_for_token(token_a)["id"],alice["id"])
                self.assertEqual(new_store.user_for_token(token_b)["id"],bob["id"])

    def test_saved_chart_api_includes_trusted_computed_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///" + str(Path(tmp)/"api.sqlite3")}, clear=False):
                with TestClient(app) as client:
                    auth = client.post("/api/account/register", json={"email":"snapshot@example.test", "password":"longer-password-88", "display_name":"Myla"})
                    self.assertEqual(auth.status_code, 200, auth.text)
                    header = {"Authorization": "Bearer " + auth.json()["token"]}
                    created = client.post("/api/account/charts", headers=header, json={"label":"Favorite person", "birth":SAMPLE})
                    self.assertEqual(created.status_code, 200, created.text)
                    result = created.json()["chart"]
                    self.assertEqual(result["label"], "Favorite person")
                    self.assertIn("chart", result["natal_snapshot"])
                    self.assertIn("Sun", result["natal_snapshot"]["chart"]["planets"])
                    after = client.get("/api/account/me", headers=header)
                    self.assertEqual(after.status_code, 200)
                    self.assertEqual(after.json()["charts"][0]["natal_snapshot"]["chart"]["birth_date"], "2002-01-25")

    def test_migrates_existing_database_without_losing_charts(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "legacy.sqlite3")
            with closing(sqlite3.connect(path)) as conn:
                conn.execute("CREATE TABLE astromyla_saved_charts (id TEXT PRIMARY KEY,user_id TEXT NOT NULL,label TEXT NOT NULL,birth_json TEXT NOT NULL,created_at BIGINT NOT NULL,updated_at BIGINT NOT NULL)")
                conn.commit()
            with patch.dict(os.environ, {"DATABASE_URL":"sqlite:///"+path}, clear=False):
                store = AccountStore()
                from app.models import BirthData
                item = store.save_chart("legacy_user", "Legacy", BirthData(**SAMPLE))
                self.assertIsNone(item["natal_snapshot"])
                self.assertEqual(store.list_charts("legacy_user")[0]["label"], "Legacy")

if __name__ == '__main__': unittest.main()
