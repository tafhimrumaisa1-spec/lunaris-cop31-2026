"""Fails if enums in lunaris_api.enums drift from contracts/data-models.json."""
import unittest

from lunaris_api import enums

try:
    from lunaris_contracts import ContractNotFound, contract_fields, enum_values, find_contracts_dir
    find_contracts_dir()
    HAVE = True
except Exception:  # noqa: BLE001
    HAVE = False


@unittest.skipUnless(HAVE, "contracts/data-models.json not found (set LUNARIS_CONTRACTS_DIR)")
class ContractEnumTests(unittest.TestCase):
    CASES = [
        ("Evidence", "data_status", enums.DATA_STATUSES),
        ("City", "support_status", enums.SUPPORT_STATUSES),
        ("ActivityWindow", "heat_caution", enums.HEAT_CAUTIONS),
        ("ChoiceComparison", "comparison_type", enums.COMPARISON_TYPES),
        ("CommunityMission", "status", enums.MISSION_STATUSES),
        ("CommunityMission", "permission_status", enums.PERMISSION_STATUSES),
        ("CommunityMission", "verification_status", enums.MISSION_VERIFICATION_STATUSES),
        ("ImpactRecord", "verification_status", enums.IMPACT_VERIFICATION_STATUSES),
    ]

    def test_enum_members_match(self):
        for model, field, ours in self.CASES:
            with self.subTest(f"{model}.{field}"):
                self.assertEqual(set(ours), enum_values(model, field))

    def test_documented_ambiguities_still_hold(self):
        # DATA_AND_EVIDENCE.md uses a DIFFERENT 3-level vocabulary for business disclosure than any
        # contract enum. If the contract ever gains it, this fails and the handoff note must be updated.
        for model, field, _ in self.CASES:
            self.assertFalse(enums.BUSINESS_DISCLOSURE_STATUSES <= enum_values(model, field))
        # Evidence.data_status includes 'verified'/'self_reported' (also used for user records).
        self.assertTrue({"verified", "self_reported"} <= enum_values("Evidence", "data_status"))

    def test_surface_allowlists_are_subsets(self):
        for s in (enums.WEATHER_ALLOWED_DATA_STATUS, enums.WINDOW_ALLOWED_DATA_STATUS, enums.CHOICES_ALLOWED_DATA_STATUS):
            self.assertTrue(s <= enums.DATA_STATUSES)
            self.assertFalse({"verified", "self_reported"} & s)

    def test_contract_has_expected_models(self):
        for m in ("City", "UserPreferences", "Evidence", "HourConditions", "ActivityWindow",
                  "ChoiceComparison", "CommunityMission", "ImpactRecord"):
            self.assertTrue(contract_fields(m))


if __name__ == "__main__":
    unittest.main()
