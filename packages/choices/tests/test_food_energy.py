import json, unittest
from datetime import datetime, timezone
from lunaris_choices import compare_food, calculate_energy, list_categories, ValidationFailure

FIXED = lambda: datetime(2026, 11, 15, 8, 0, tzinfo=timezone.utc)


class FoodTests(unittest.TestCase):
    def test_comparison_and_units(self):
        r = compare_food({"item_a": {"category": "beef_beef_herd", "quantity_g": 150}, "item_b": {"category": "peas", "quantity_g": 150}}, clock=FIXED)
        a, b = r.alternatives
        self.assertAlmostEqual(a["emissions_kg_co2e"]["central"], 99.48 * 0.15, places=3)
        self.assertEqual(a["emissions_unit"], "kg CO2e"); self.assertEqual(a["factor_unit"], "kg CO2e per kg of product")
        self.assertTrue(r.estimated_impacts[0]["equal_quantities"])
        self.assertIn("Farm-to-retail", a["boundary"])
        self.assertTrue(r.evidence[0].source_url.startswith("https://ourworldindata.org"))
        codes = [w.code for w in r.warnings]
        for c in ("CATEGORY_AVERAGE", "RANGE_NOT_ENCODED"):
            self.assertIn(c, codes)
        self.assertNotIn("FACTORS_UNVERIFIED", codes)
        self.assertIsNone(a["emissions_kg_co2e"]["low"])  # ranges not invented

    def test_unequal_quantities_warns(self):
        r = compare_food({"item_a": {"category": "rice", "quantity_g": 100}, "item_b": {"category": "cheese", "quantity_g": 30}}, clock=FIXED)
        self.assertIn("UNEQUAL_QUANTITIES", [w.code for w in r.warnings])

    def test_brand_or_restaurant_rejected(self):
        for cat in ("McDonald's Big Mac", "burger", "", None, 5):
            with self.assertRaises(ValidationFailure, msg=str(cat)):
                compare_food({"item_a": {"category": cat, "quantity_g": 100}, "item_b": {"category": "rice", "quantity_g": 100}})
        with self.assertRaises(ValidationFailure):
            compare_food({"item_a": {"category": "rice", "quantity_g": 100, "brand": "X"}, "item_b": {"category": "rice", "quantity_g": 100}})

    def test_bad_quantities(self):
        for q in (-1, 0, "100", None, float("nan"), 1e9):
            with self.assertRaises(ValidationFailure, msg=str(q)):
                compare_food({"item_a": {"category": "rice", "quantity_g": q}, "item_b": {"category": "peas", "quantity_g": 100}})

    def test_label_is_not_used(self):
        r = compare_food({"item_a": {"category": "rice", "quantity_g": 100, "label": "Some Brand rice"}, "item_b": {"category": "peas", "quantity_g": 100}}, clock=FIXED)
        self.assertIn("LABEL_NOT_USED", [w.code for w in r.warnings])

    def test_categories_listed(self):
        self.assertGreaterEqual(len(list_categories()), 10)


def sc(**kw):
    d = {"name": "AC", "power_w": 1500, "hours_per_use": 8, "uses_per_week": 7}
    d.update(kw); return d


class EnergyTests(unittest.TestCase):
    def test_kwh_and_cost(self):
        r = calculate_energy({"scenarios": [sc()], "tariff_aed_per_kwh": 0.3, "period_days": 7}, clock=FIXED)
        row = r.alternatives[0]
        self.assertAlmostEqual(row["energy_kwh"], 1.5 * 8 * 7, places=3)
        self.assertAlmostEqual(row["cost_aed"], 1.5 * 56 * 0.3, places=2)
        self.assertEqual(row["cost_status"], "custom_assumption")
        self.assertTrue(any("custom assumption" in a for a in r.assumptions))

    def test_unknown_price_no_cost(self):
        r = calculate_energy({"scenarios": [sc()]}, clock=FIXED)
        self.assertIsNone(r.alternatives[0]["cost_aed"]); self.assertEqual(r.alternatives[0]["cost_status"], "unknown")
        self.assertIn("UNKNOWN_PRICE", [w.code for w in r.warnings]); self.assertIn("NO_METER_DATA", [w.code for w in r.warnings])
        self.assertIsNone(r.alternatives[0]["emissions_kg_co2e"])

    def test_duty_cycle_and_comparison(self):
        r = calculate_energy({"scenarios": [sc(name="old", power_w=1500), sc(name="new", power_w=1000, duty_cycle=0.5)], "tariff_aed_per_kwh": 0.3, "period_days": 30}, clock=FIXED)
        imp = r.estimated_impacts[0]
        self.assertLess(imp["energy_kwh_difference"], 0); self.assertLess(imp["cost_aed_difference"], 0)

    def test_grid_factor_optional(self):
        r = calculate_energy({"scenarios": [sc()], "grid_kg_per_kwh": 0.4, "period_days": 7}, clock=FIXED)
        self.assertAlmostEqual(r.alternatives[0]["emissions_kg_co2e"], 84 * 0.4, places=3)

    def test_invalid(self):
        bad = [sc(power_w=-5), sc(power_w=0), sc(hours_per_use=25), sc(hours_per_use=24, uses_per_week=8), sc(duty_cycle=1.5), sc(name=""), sc(power_w="1500")]
        for s in bad:
            with self.assertRaises(ValidationFailure, msg=str(s)):
                calculate_energy({"scenarios": [s]})
        for extra in ({"tariff_aed_per_kwh": -0.1}, {"period_days": 0}, {"grid_kg_per_kwh": -1}, {"smart_meter_id": "x"}):
            with self.assertRaises(ValidationFailure, msg=str(extra)):
                calculate_energy({"scenarios": [sc()], **extra})
        with self.assertRaises(ValidationFailure):
            calculate_energy({"scenarios": []})
        json.dumps(calculate_energy({"scenarios": [sc()]}).to_dict())


if __name__ == "__main__":
    unittest.main()
