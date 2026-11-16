"""Contract conformance: served OpenAPI vs contracts/openapi-target.yaml, models vs data-models.json."""
import pytest

from lunaris_contracts import contract_fields, enum_values, load_openapi_paths
from lunaris_api import schemas


def test_every_target_path_and_method_is_served(client):
    served = client.get("/openapi.json").json()["paths"]
    for path, ops in load_openapi_paths().items():
        assert path in served, f"missing path {path}"
        for method in ops:
            assert method in served[path], f"missing {method.upper()} {path}"


def test_documented_status_codes_present(client):
    served = client.get("/openapi.json").json()["paths"]
    assert "503" in served["/v1/weather/dubai"]["get"]["responses"]
    assert "201" in served["/v1/missions/{id}/interest"]["post"]["responses"]
    for path, ops in load_openapi_paths().items():
        for method, spec in ops.items():
            for code in spec["responses"]:
                assert str(code) in served[path][method]["responses"], f"{method.upper()} {path} missing {code}"


CONTRACT_MODELS = {
    "City": schemas.City, "UserPreferences": schemas.UserPreferences, "Evidence": schemas.Evidence,
    "HourConditions": schemas.HourConditions, "ActivityWindow": schemas.ActivityWindow,
    "ChoiceComparison": schemas.ChoiceComparison, "CommunityMission": schemas.CommunityMission,
    "ImpactRecord": schemas.ImpactRecord,
}


@pytest.mark.parametrize("name", sorted(CONTRACT_MODELS))
def test_models_contain_every_contract_field(name):
    missing = contract_fields(name) - set(CONTRACT_MODELS[name].model_fields)
    assert not missing, f"{name} lacks contract fields {missing}"


def test_extra_fields_are_only_the_documented_additions():
    allowed = {
        "Evidence": {"license_note", "location_precision", "model_id", "assumptions", "uncertainty"},
        "CommunityMission": {"summary"},
    }
    for name, model in CONTRACT_MODELS.items():
        extra = set(model.model_fields) - contract_fields(name)
        assert extra <= allowed.get(name, set()), f"{name} has undocumented extra fields {extra}"


def test_literal_types_match_contract_enums():
    from typing import get_args
    ev = schemas.Evidence.model_fields["data_status"].annotation
    assert set(get_args(ev)) == enum_values("Evidence", "data_status")
    assert set(get_args(schemas.ActivityWindow.model_fields["heat_caution"].annotation)) == enum_values("ActivityWindow", "heat_caution")
    assert set(get_args(schemas.CommunityMission.model_fields["status"].annotation)) == enum_values("CommunityMission", "status")
    assert set(get_args(schemas.ImpactRecord.model_fields["verification_status"].annotation)) == enum_values("ImpactRecord", "verification_status")
