import logging
import unittest

from lunaris_api.core.redaction import RedactingFilter, JsonFormatter, redact_text, redact_value


class RedactionTests(unittest.TestCase):
    def test_email_and_bearer(self):
        out = redact_text("user a.b+c@example.com sent Authorization: Bearer abcdefghijklmnop1234")
        self.assertNotIn("example.com", out)
        self.assertNotIn("abcdefghijklmnop1234", out)

    def test_precise_coordinates(self):
        out = redact_text("at 25.204849, 55.270783")
        self.assertNotIn("25.204849", out)
        self.assertNotIn("55.270783", out)

    def test_coarse_coordinates_and_small_decimals_survive(self):
        self.assertEqual(redact_text("took 12.5 ms"), "took 12.5 ms")

    def test_long_token(self):
        tok = "A" * 43
        self.assertNotIn(tok, redact_text(f"session {tok} created"))

    def test_phone(self):
        self.assertNotIn("971", redact_text("call +971 50 123 4567 now"))

    def test_mapping_keys(self):
        d = redact_value({"email": "x@y.zz", "ok": 1, "nested": {"latitude": 25.2, "note": "mail me z@q.io"}})
        self.assertEqual(d["email"], "[REDACTED]")
        self.assertEqual(d["nested"]["latitude"], "[REDACTED]")
        self.assertNotIn("q.io", d["nested"]["note"])
        self.assertEqual(d["ok"], 1)

    def test_logging_filter_and_json(self):
        rec = logging.LogRecord("lunaris.t", logging.INFO, __file__, 1, "login %s", ("me@example.org",), None)
        rec.session_token = "secretvalue"
        RedactingFilter().filter(rec)
        line = JsonFormatter().format(rec)
        self.assertNotIn("me@example.org", line)
        self.assertNotIn("secretvalue", line)


if __name__ == "__main__":
    unittest.main()
