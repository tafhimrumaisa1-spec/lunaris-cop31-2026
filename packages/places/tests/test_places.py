import json, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from lunaris_choices import ValidationFailure
from lunaris_places import Place, PlaceService, load_curated

NOW = datetime(2026, 11, 15, 8, 0, tzinfo=timezone.utc)  # 12:00 Asia/Dubai, a Sunday
CLOCK = lambda: NOW
iso = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")

REAL = {"id": "r1", "name": "Sample Venue", "city_id": "dubai", "categories": ["cafe"], "setting": "indoor", "is_demo": False,
        "description": "Test fixture standing in for a licensed record.", "map_link": "https://maps.example/x",
        "source_name": "Test licensed dataset", "source_url": "https://example.com/data", "license_note": "test licence",
        "retrieved_at": "2026-11-01T00:00:00Z", "verified_by": "tester"}


def demo(i, cats, setting):
    return Place.from_dict({"id": f"demo-{i}", "name": f"DEMO {i}", "city_id": "dubai", "categories": cats, "setting": setting,
                            "is_demo": True, "description": "d"})


def wx(**kw):
    d = {"apparent_temperature_c": 30, "precip_probability_percent": 10, "retrieved_at": iso(NOW - timedelta(minutes=30)), "data_status": "live"}
    d.update(kw); return d


class ProvenanceTests(unittest.TestCase):
    def test_missing_provenance_rejected(self):
        for k in ("source_name", "source_url", "license_note", "retrieved_at", "verified_by"):
            d = dict(REAL); d.pop(k)
            with self.assertRaises(ValidationFailure, msg=k) as cm:
                Place.from_dict(d)
            self.assertEqual(cm.exception.code, "MISSING_PROVENANCE")
        Place.from_dict(REAL)

    def test_demo_must_be_labelled_and_flag_explicit(self):
        with self.assertRaises(ValidationFailure):
            Place.from_dict({**REAL, "is_demo": True, "name": "Totally Real Cafe"})
        d = dict(REAL); d.pop("is_demo")
        with self.assertRaises(ValidationFailure):
            Place.from_dict(d)

    def test_bad_fields(self):
        for bad in ({"source_url": "http://x.com"}, {"categories": ["spa"]}, {"setting": "underwater"}, {"rating": 5}, {"map_link": "javascript:alert(1)"}):
            with self.assertRaises(ValidationFailure, msg=str(bad)):
                Place.from_dict({**REAL, **bad})

    def test_loader_rejects_real_entry_without_provenance(self):
        bad = dict(REAL); bad.pop("source_url")
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "c.json"; p.write_text(json.dumps({"entries": [bad]}))
            with self.assertRaises(ValidationFailure):
                load_curated(p)

    def test_shipped_file_is_demo_only(self):
        entries = load_curated()
        self.assertTrue(entries and all(e.is_demo for e in entries))

    def test_verified_evidence_for_curated(self):
        r = PlaceService([Place.from_dict(REAL)], CLOCK).list_places({})
        ev = r["places"][0]["evidence"]
        self.assertEqual(ev["data_status"], "verified"); self.assertEqual(ev["source_url"], "https://example.com/data")
        self.assertNotIn("DEMO_ENTRIES", [w["code"] for w in r["warnings"]])


class ServiceTests(unittest.TestCase):
    def svc(self):
        return PlaceService([demo("walk", ["walk"], "outdoor"), demo("cafe", ["cafe"], "indoor"), demo("gallery", ["culture", "indoor"], "indoor")], CLOCK)

    def test_unsupported_city(self):
        for c in ("london", "", "DUBAI-XX"):
            try:
                r = self.svc().list_places({"city_id": c or "x"})
            except ValidationFailure:
                continue
            self.assertEqual(r["places"], []); self.assertEqual(r["support_status"], "unsupported")
            self.assertIn("UNSUPPORTED_CITY", [w["code"] for w in r["warnings"]])
        self.assertEqual(self.svc().list_places({"city_id": "Dubai"})["support_status"], "supported")

    def test_category_and_activity_filter(self):
        names = lambda r: [p["id"] for p in r["places"]]
        self.assertEqual(names(self.svc().list_places({"categories": ["cafe"]})), ["demo-cafe"])
        self.assertEqual(names(self.svc().list_places({"activities": ["walking"]})), ["demo-walk"])
        r = self.svc().list_places({"activities": ["scuba"]})
        self.assertIn("UNKNOWN_ACTIVITY", [w["code"] for w in r["warnings"]]); self.assertEqual(len(r["places"]), 3)

    def test_ordering_alphabetical_no_ranking(self):
        r = self.svc().list_places({})
        self.assertEqual(r["ordering"], "alphabetical")
        self.assertEqual([p["name"] for p in r["places"]], sorted(p["name"] for p in r["places"]))
        self.assertIn("NO_RANKING", [w["code"] for w in r["warnings"]])

    def test_weather_rain_excludes_outdoor_only(self):
        r = self.svc().list_places({"weather": wx(precip_probability_percent=80)})
        self.assertEqual({p["id"] for p in r["places"]}, {"demo-cafe", "demo-gallery"}); self.assertEqual(r["excluded_by_weather_count"], 1)

    def test_weather_comfort_range(self):
        r = self.svc().list_places({"weather": wx(apparent_temperature_c=41), "comfort_max_c": 29, "comfort_min_c": 19})
        self.assertNotIn("demo-walk", [p["id"] for p in r["places"]])
        r = self.svc().list_places({"weather": wx(apparent_temperature_c=25), "comfort_max_c": 29, "comfort_min_c": 19})
        self.assertIn("demo-walk", [p["id"] for p in r["places"]])
        with self.assertRaises(ValidationFailure):
            self.svc().list_places({"comfort_max_c": 19, "comfort_min_c": 29})

    def test_weather_skipped_when_quality_insufficient(self):
        for bad in (wx(data_status="demo"), wx(data_status="historical"), wx(retrieved_at=iso(NOW - timedelta(hours=5))),
                    wx(precip_probability_percent=None), wx(apparent_temperature_c=None), wx(retrieved_at=iso(NOW + timedelta(hours=2)))):
            r = self.svc().list_places({"weather": bad, "comfort_max_c": 20})
            self.assertEqual(len(r["places"]), 3, msg=str(bad))
            self.assertEqual(r["skipped_filters"][0]["filter"], "weather")
            self.assertIn("WEATHER_FILTER_SKIPPED", [w["code"] for w in r["warnings"]])

    def test_weather_input_validation(self):
        for bad in (wx(precip_probability_percent=120), wx(apparent_temperature_c="hot"), wx(retrieved_at="2026-11-15T08:00:00"), wx(extra=1)):
            with self.assertRaises(ValidationFailure):
                self.svc().list_places({"weather": bad})

    def test_open_now_unknown_without_fresh_hours(self):
        r = self.svc().list_places({})
        self.assertTrue(all(p["open_now"] is None and p["open_now_note"] for p in r["places"]))
        hours = {d: [["09:00", "17:00"]] for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")}
        base = {**REAL, "hours": hours}
        fresh = Place.from_dict({**base, "hours_verified_at": iso(NOW - timedelta(days=3))})
        stale = Place.from_dict({**base, "hours_verified_at": iso(NOW - timedelta(days=90))})
        self.assertTrue(fresh.open_now(NOW))                                   # 12:00 Dubai
        self.assertFalse(fresh.open_now(NOW + timedelta(hours=8)))              # 20:00 Dubai
        self.assertIsNone(stale.open_now(NOW))
        with self.assertRaises(ValidationFailure):
            Place.from_dict({**base})  # hours with no verification date

    def test_overnight_hours(self):
        h = {d: [["20:00", "02:00"]] for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")}
        p = Place.from_dict({**REAL, "hours": h, "hours_verified_at": iso(NOW)})
        self.assertTrue(p.open_now(datetime(2026, 11, 15, 20, 0, tzinfo=timezone.utc)))   # 00:00 Dubai next day
        self.assertFalse(p.open_now(NOW))

    def test_unknown_query_field_rejected(self):
        with self.assertRaises(ValidationFailure):
            self.svc().list_places({"sort": "best"})


if __name__ == "__main__":
    unittest.main()
