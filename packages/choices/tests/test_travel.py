import math, unittest
from datetime import datetime, timezone
from lunaris_choices import compare_travel, ValidationFailure

FIXED = lambda: datetime(2026, 11, 15, 8, 0, tzinfo=timezone.utc)


def req(**kw):
    base = {"distance_km": 10, "modes": [{"mode": "car"}, {"mode": "bus"}, {"mode": "walk"}]}
    base.update(kw)
    return base


def alt(res, mode):
    return next(a for a in res.alternatives if a["mode"] == mode)


class TravelTests(unittest.TestCase):
    def test_units_and_arithmetic(self):
        r = compare_travel(req(), clock=FIXED)
        car = alt(r, "car")
        self.assertEqual(car["unit"], "kg CO2e")
        self.assertAlmostEqual(car["emissions_kg_co2e"]["central"], 10 * 0.16591, places=4)
        self.assertAlmostEqual(alt(r, "bus")["emissions_kg_co2e"]["central"], 10 * 0.10151, places=4)
        e = car["emissions_kg_co2e"]
        self.assertLessEqual(e["low"], e["central"]); self.assertLessEqual(e["central"], e["high"])

    def test_round_trip_doubles(self):
        one = alt(compare_travel(req(), clock=FIXED), "car")["emissions_kg_co2e"]["central"]
        two = alt(compare_travel(req(round_trip=True), clock=FIXED), "car")["emissions_kg_co2e"]["central"]
        self.assertAlmostEqual(two, 2 * one, places=4)

    def test_occupancy_divides_vehicle_modes_only(self):
        r = compare_travel(req(modes=[{"mode": "car", "occupancy": 4}, {"mode": "bus", "occupancy": 4}]), clock=FIXED)
        self.assertAlmostEqual(alt(r, "car")["emissions_kg_co2e"]["central"], 10 * 0.16591 / 4, places=4)
        self.assertAlmostEqual(alt(r, "bus")["emissions_kg_co2e"]["central"], 10 * 0.10151, places=4)
        self.assertIn("OCCUPANCY_IGNORED", [w.code for w in r.warnings])

    def test_default_occupancy_is_disclosed(self):
        r = compare_travel(req(), clock=FIXED)
        self.assertTrue(any("occupancy not given" in a for a in r.assumptions))

    def test_bad_occupancy(self):
        for occ in (0, 0.5, -1, 10, "2", True, float("nan")):
            with self.assertRaises(ValidationFailure, msg=str(occ)):
                compare_travel(req(modes=[{"mode": "car", "occupancy": occ}]), clock=FIXED)
        with self.assertRaises(ValidationFailure):
            compare_travel(req(modes=[{"mode": "motorbike", "occupancy": 3}]), clock=FIXED)

    def test_negative_zero_and_nonfinite_distance(self):
        for d in (-5, 0, float("inf"), float("nan"), "10", None, True, 25000):
            with self.assertRaises(ValidationFailure, msg=str(d)):
                compare_travel(req(distance_km=d), clock=FIXED)
        try:
            compare_travel(req(distance_km=-1), clock=FIXED)
        except ValidationFailure as e:
            self.assertEqual(e.code, "NEGATIVE_VALUE")

    def test_country_proxy_assumption(self):
        ae = compare_travel(req(country_code="ae"), clock=FIXED)
        self.assertIn("JURISDICTION_PROXY", [w.code for w in ae.warnings])
        gb = compare_travel(req(country_code="GB"), clock=FIXED)
        self.assertNotIn("JURISDICTION_PROXY", [w.code for w in gb.warnings])
        with self.assertRaises(ValidationFailure):
            compare_travel(req(country_code="UAE"), clock=FIXED)

    def test_walk_is_zero_operational_with_lifecycle_note(self):
        w = alt(compare_travel(req(), clock=FIXED), "walk")
        self.assertEqual(w["emissions_kg_co2e"]["central"], 0.0)
        self.assertTrue(any("lifecycle" in n.lower() for n in w["notes"]))

    def test_no_routing_and_no_invented_time(self):
        r = compare_travel(req(), clock=FIXED)
        self.assertTrue(all(a["time_minutes"] is None for a in r.alternatives))
        self.assertIn("NO_ROUTING", [w.code for w in r.warnings])
        r2 = compare_travel(req(modes=[{"mode": "bus", "avg_speed_kmh": 20}]), clock=FIXED)
        self.assertAlmostEqual(r2.alternatives[0]["time_minutes"], 30.0)
        with self.assertRaises(ValidationFailure) as cm:
            compare_travel({"origin": "A", "destination": "B", "modes": [{"mode": "car"}]})
        self.assertEqual(cm.exception.code, "ROUTING_DISABLED")

    def test_electric_requires_user_grid_factor(self):
        r = compare_travel(req(modes=[{"mode": "electric_car"}, {"mode": "car"}]), clock=FIXED)
        self.assertEqual(alt(r, "electric_car")["status"], "excluded")
        self.assertIn("EV_INPUT_MISSING", [w.code for w in r.warnings])
        r = compare_travel(req(modes=[{"mode": "electric_car", "ev_kwh_per_km": 0.2, "grid_kg_per_kwh": 0.4}]), clock=FIXED)
        self.assertAlmostEqual(r.alternatives[0]["emissions_kg_co2e"]["central"], 10 * 0.2 * 0.4, places=4)

    def test_interval_overlap_flag_and_baseline(self):
        r = compare_travel(req(modes=[{"mode": "bus"}, {"mode": "metro_rail"}, {"mode": "car"}], baseline_mode="bus"), clock=FIXED)
        self.assertTrue(all(i["baseline_mode"] == "bus" for i in r.estimated_impacts))
        with self.assertRaises(ValidationFailure):
            compare_travel(req(baseline_mode="bicycle"), clock=FIXED)

    def test_duplicates_unknown_modes_unknown_fields(self):
        for bad in (req(modes=[{"mode": "car"}, {"mode": "car"}]), req(modes=[{"mode": "helicopter"}]), req(modes=[]), req(foo=1), req(modes="car")):
            with self.assertRaises(ValidationFailure):
                compare_travel(bad, clock=FIXED)

    def test_evidence_and_warnings_present_and_serialisable(self):
        r = compare_travel(req(), clock=FIXED)
        ev = r.evidence[0]
        self.assertEqual(ev.data_status, "modeled"); self.assertTrue(ev.source_url); self.assertEqual(ev.retrieved_at, "2026-11-15T08:00:00Z")
        self.assertNotIn("FACTORS_UNVERIFIED", [w.code for w in r.warnings])
        d = r.to_dict()
        import json; json.dumps(d)
        self.assertEqual(d["comparison_type"], "travel")

    def test_deterministic_id(self):
        self.assertEqual(compare_travel(req(), clock=FIXED).choice_id, compare_travel(req(), clock=FIXED).choice_id)


if __name__ == "__main__":
    unittest.main()
