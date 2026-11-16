import unittest
from datetime import datetime, timezone
from lunaris_choices import (BusinessClaim, BusinessProfile, BusinessEvidenceRepository, ValidatedDataset, ValidationFailure,
                            NotFoundError, assess_area, get_business_evidence)

FIXED = lambda: datetime(2026, 11, 15, 8, 0, tzinfo=timezone.utc)


class BusinessTests(unittest.TestCase):
    def test_fake_verified_status_rejected(self):
        for extra in ({}, {"evidence_url": "https://e.com/x", "reviewer": "R", "reviewed_at": "2026-01-01T00:00:00Z"}):
            with self.assertRaises(ValidationFailure) as cm:
                BusinessClaim.from_dict({"claim_type": "refill", "text": "Offers refills", "status": "independently_verified", **extra})
            self.assertEqual(cm.exception.code, "VERIFIED_STATUS_NOT_SUPPORTED")
        with self.assertRaises(ValidationFailure):
            BusinessClaim.from_dict({"claim_type": "refill", "text": "x", "status": "self_reported", "verifier": "Acme Audit"})

    def test_unknown_status_and_certification_wording(self):
        with self.assertRaises(ValidationFailure):
            BusinessClaim.from_dict({"claim_type": "refill", "text": "x", "status": "certified"})
        for t in ("Certified green cafe", "Best in Dubai", "#1 eco venue", "Accredited recycler"):
            with self.assertRaises(ValidationFailure, msg=t):
                BusinessClaim.from_dict({"claim_type": "other", "text": t, "status": "self_reported"})

    def test_documentation_reviewed_needs_record(self):
        with self.assertRaises(ValidationFailure) as cm:
            BusinessClaim.from_dict({"claim_type": "refill", "text": "x", "status": "documentation_reviewed"})
        self.assertEqual(cm.exception.code, "REVIEW_RECORD_INCOMPLETE")
        ok = BusinessClaim.from_dict({"claim_type": "refill", "text": "x", "status": "documentation_reviewed",
                                      "evidence_url": "https://e.com/doc", "reviewer": "R", "reviewed_at": "2026-01-01T00:00:00Z"})
        self.assertEqual(ok.reviewed_at, "2026-01-01T00:00:00Z")
        with self.assertRaises(ValidationFailure):  # self-report cannot carry a review record
            BusinessClaim.from_dict({"claim_type": "refill", "text": "x", "status": "self_reported", "reviewer": "R"})
        with self.assertRaises(ValidationFailure):  # http not https
            BusinessClaim.from_dict({"claim_type": "refill", "text": "x", "status": "self_reported", "disclosure_url": "http://a.com"})

    def test_profile_demo_labelling_and_no_badge(self):
        r = get_business_evidence("demo-business-001", clock=FIXED)
        codes = [w.code for w in r["warnings"]]
        self.assertIn("DEMO_DATA", codes); self.assertIn("NOT_CERTIFICATION", codes)
        self.assertEqual(r["evidence"][0].data_status, "demo")
        self.assertEqual(r["status_counts"]["independently_verified"], 0)
        self.assertNotIn("badge", r); self.assertNotIn("rank", r)

    def test_unknown_id_and_real_business_blocked(self):
        with self.assertRaises(NotFoundError):
            get_business_evidence("nope")
        with self.assertRaises(ValidationFailure):
            BusinessEvidenceRepository().add(BusinessProfile("real-1", "Real Cafe", False, []))


class ClimEstateTests(unittest.TestCase):
    def test_hidden_risks_for_dubai(self):
        r = assess_area("dubai", "Marina", clock=FIXED)
        self.assertEqual(r["assessment_status"], "not_assessed"); self.assertEqual(r["hazards"], [])
        self.assertEqual(r["reason"], "no_validated_dataset"); self.assertTrue(r["explainer"])

    def test_unsupported_city(self):
        r = assess_area("london", clock=FIXED)
        self.assertEqual(r["support_status"], "unsupported"); self.assertEqual(r["reason"], "city_unsupported")
        self.assertEqual(r["hazards"], []); self.assertIn("UNSUPPORTED_CITY", [w.code for w in r["warnings"]])

    def test_unvalidated_dataset_does_not_open_gate_and_no_scores_ever(self):
        bad = ValidatedDataset("x", "flood", "dubai", "100m", False, None)
        good = ValidatedDataset("y", "flood", "dubai", "100m", True, "https://example.com/report")
        self.assertEqual(assess_area("dubai", registry=[bad], clock=FIXED)["reason"], "no_validated_dataset")
        r = assess_area("dubai", registry=[good], clock=FIXED)
        self.assertEqual(r["reason"], "validated_dataset_present_but_no_hazard_adapter_in_this_release")
        self.assertEqual(r["hazards"], []); self.assertEqual(r["assessment_status"], "not_assessed")


if __name__ == "__main__":
    unittest.main()
