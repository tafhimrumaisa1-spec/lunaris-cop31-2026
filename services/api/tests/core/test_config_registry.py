import sys
import types
import unittest

from lunaris_api.config import ConfigError, Settings, normalize_database_url
from lunaris_api.core.scheduler import NullScheduler, SchedulerNotConfigured
from lunaris_api.integrations.registry import ProviderLoadError, load_entrypoint, load_providers


PROD = {
    "LUNARIS_ENV": "production",
    "LUNARIS_DATABASE_URL": "postgresql://u:p@db/lunaris",
    "LUNARIS_SESSION_SECRET": "s" * 40,
    "LUNARIS_CORS_ALLOW_ORIGINS": "https://app.example.org",
}


class ConfigTests(unittest.TestCase):
    def test_dev_defaults_are_safe(self):
        s = Settings.from_env({})
        self.assertEqual(s.env, "development")
        self.assertTrue(s.is_sqlite)
        self.assertGreaterEqual(len(s.session_secret), 32)  # ephemeral
        self.assertFalse(s.seed_demo_data)
        self.assertEqual(s.cors_allow_origins, ("http://localhost:3000",))

    def test_production_ok(self):
        s = Settings.from_env(PROD)
        self.assertEqual(s.database_url, "postgresql+psycopg://u:p@db/lunaris")
        self.assertFalse(s.docs_enabled)
        self.assertFalse(s.auto_create_schema)

    def test_production_rejections(self):
        for k, v in [("LUNARIS_DATABASE_URL", "sqlite:///x.db"), ("LUNARIS_SESSION_SECRET", "short"),
                     ("LUNARIS_CORS_ALLOW_ORIGINS", "*"), ("LUNARIS_CORS_ALLOW_ORIGINS", "http://evil.example")]:
            with self.assertRaises(ConfigError, msg=k + v):
                Settings.from_env({**PROD, k: v})
        env = dict(PROD); del env["LUNARIS_SESSION_SECRET"]
        with self.assertRaises(ConfigError):
            Settings.from_env(env)

    def test_star_cors_rejected_everywhere(self):
        with self.assertRaises(ConfigError):
            Settings.from_env({"LUNARIS_CORS_ALLOW_ORIGINS": "*"})

    def test_email_auth_not_claimed(self):
        with self.assertRaises(ConfigError):
            Settings.from_env({"LUNARIS_AUTH_MODE": "email"})

    def test_bad_ints_and_bools(self):
        with self.assertRaises(ConfigError):
            Settings.from_env({"LUNARIS_SESSION_TTL_DAYS": "abc"})
        with self.assertRaises(ConfigError):
            Settings.from_env({"LUNARIS_TRUST_PROXY_HEADERS": "maybe"})

    def test_url_normalisation(self):
        self.assertEqual(normalize_database_url("postgres://a@b/c"), "postgresql+psycopg://a@b/c")
        self.assertEqual(normalize_database_url("sqlite://"), "sqlite://")


class RegistryTests(unittest.TestCase):
    def setUp(self):
        mod = types.ModuleType("fake_provider_mod")

        class W:
            def fetch_hourly(self, **kw): return []
        mod.W = W
        mod.instance = W()
        sys.modules["fake_provider_mod"] = mod

    def tearDown(self):
        sys.modules.pop("fake_provider_mod", None)

    def test_unset_means_not_integrated(self):
        p = load_providers(Settings.for_tests())
        self.assertEqual(set(p.status().values()), {"not_integrated"})

    def test_bind_class_and_instance(self):
        p = load_providers(Settings.for_tests(weather_provider="fake_provider_mod:W", choices_engine="fake_provider_mod:instance"))
        self.assertEqual(p.status()["weather"], "bound")
        self.assertEqual(p.status()["choices"], "bound")
        self.assertEqual(p.status()["climate"], "not_integrated")

    def test_fail_fast(self):
        for bad in ["nocolon", "does_not_exist_mod:X", "fake_provider_mod:Nope"]:
            with self.assertRaises(ProviderLoadError):
                load_entrypoint(bad)


class SchedulerTests(unittest.TestCase):
    def test_null_scheduler_never_fakes_jobs(self):
        from datetime import timedelta
        s = NullScheduler()
        self.assertEqual(s.jobs(), [])
        with self.assertRaises(SchedulerNotConfigured):
            s.register("refresh", lambda: None, timedelta(hours=1))


if __name__ == "__main__":
    unittest.main()
