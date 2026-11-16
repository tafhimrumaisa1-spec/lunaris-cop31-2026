import unittest

from lunaris_api.core.cache import TTLCache
from lunaris_api.core.ratelimit import SlidingWindowLimiter


class Clock:
    def __init__(self): self.t = 1000.0
    def __call__(self): return self.t


class LimiterTests(unittest.TestCase):
    def test_blocks_then_recovers(self):
        c = Clock(); lim = SlidingWindowLimiter(c)
        for _ in range(3):
            self.assertTrue(lim.check("k", 3, 60)[0])
        ok, retry = lim.check("k", 3, 60)
        self.assertFalse(ok); self.assertGreaterEqual(retry, 1)
        c.t += 61
        self.assertTrue(lim.check("k", 3, 60)[0])

    def test_keys_independent(self):
        lim = SlidingWindowLimiter(Clock())
        self.assertTrue(lim.check("a", 1, 60)[0])
        self.assertFalse(lim.check("a", 1, 60)[0])
        self.assertTrue(lim.check("b", 1, 60)[0])

    def test_denied_hits_not_recorded(self):
        c = Clock(); lim = SlidingWindowLimiter(c)
        lim.check("k", 1, 10)
        for _ in range(50):
            lim.check("k", 1, 10)
        c.t += 10.5
        self.assertTrue(lim.check("k", 1, 10)[0])


class CacheTests(unittest.TestCase):
    def test_fresh_stale_expired(self):
        c = Clock(); cache = TTLCache(monotonic=c)
        cache.put("k", "v")
        c.t += 100
        self.assertIsNone(cache.get("k", 50))
        hit = cache.get("k", 200)
        self.assertEqual(hit.value, "v"); self.assertAlmostEqual(hit.age_seconds, 100)
        self.assertIsNone(cache.get("missing", 200))

    def test_zero_ttl_is_always_a_cache_bypass(self):
        cache = TTLCache(monotonic=lambda: 10.0)
        cache.put("k", "v")
        self.assertIsNone(cache.get("k", 0))

    def test_eviction(self):
        c = Clock(); cache = TTLCache(max_entries=2, monotonic=c)
        cache.put("a", 1); c.t += 1; cache.put("b", 2); c.t += 1; cache.put("c", 3)
        self.assertIsNone(cache.get("a", 1e9))
        self.assertIsNotNone(cache.get("c", 1e9))


if __name__ == "__main__":
    unittest.main()
