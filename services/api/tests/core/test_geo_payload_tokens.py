import math
import unittest

from lunaris_api.core import geo
from lunaris_api.core.payload import PayloadError, check_json_payload
from lunaris_api.core.tokens import hash_token, new_token
from lunaris_api.cities_data import CITIES


class GeoTests(unittest.TestCase):
    def test_coarsen(self):
        self.assertEqual(geo.coarsen(25.204849, 55.270783), (25.2, 55.27))

    def test_rejects_bad(self):
        for bad in [(91, 0), (0, 181), (math.nan, 0), (0, math.inf)]:
            with self.assertRaises(ValueError):
                geo.coarsen(*bad)

    def test_radius(self):
        dubai = next(c for c in CITIES if c["id"] == "dubai")
        self.assertTrue(geo.within_radius(25.2, 55.27, dubai["center_lat"], dubai["center_lon"]))
        self.assertFalse(geo.within_radius(51.5, -0.12, dubai["center_lat"], dubai["center_lon"]))
        # Abu Dhabi is ~120 km away: outside the default 80 km plausibility radius
        self.assertFalse(geo.within_radius(24.4539, 54.3773, dubai["center_lat"], dubai["center_lon"]))


class PayloadTests(unittest.TestCase):
    def test_ok(self):
        check_json_payload({"a": [1, 2.5, "x", None, True], "b": {"c": 1}})

    def test_rejects(self):
        for bad in [{"a": float("nan")}, {"a": float("inf")}, {"a": "x" * 5000},
                    {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": 1}}}}}}}}}},
                    {"a": [0] * 5000}, {"a": object()}]:
            with self.assertRaises(PayloadError):
                check_json_payload(bad)


class TokenTests(unittest.TestCase):
    def test_hash_is_keyed_and_deterministic(self):
        t = new_token()
        self.assertGreaterEqual(len(t), 40)
        self.assertEqual(hash_token("s1", t), hash_token("s1", t))
        self.assertNotEqual(hash_token("s1", t), hash_token("s2", t))
        self.assertNotIn(t, hash_token("s1", t))


class CityRegistryTests(unittest.TestCase):
    def test_only_dubai_supported_no_fake_coverage(self):
        supported = [c["id"] for c in CITIES if c["support_status"] == "supported"]
        self.assertEqual(supported, ["dubai"])
        self.assertEqual(next(c for c in CITIES if c["id"] == "dubai")["timezone"], "Asia/Dubai")
        self.assertEqual(len({c["id"] for c in CITIES}), len(CITIES))


if __name__ == "__main__":
    unittest.main()
