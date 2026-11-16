"""Release guards for the independent COP31 v8 + Lumi deployment."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def lumi():
    spec = importlib.util.spec_from_file_location("cop31_lumi", ROOT / "api/lumi.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_new_vercel_project_configuration_preserves_static_routes_and_server_key_boundary():
    config = json.loads(read("vercel.json"))
    assert config["framework"] is None
    assert config["outputDirectory"] == "dist"
    assert config["trailingSlash"] is True
    assert config["functions"]["api/lumi.py"]["maxDuration"] == 20
    assert not (ROOT / ".openai/hosting.json").exists()
    browser = read("dist/app/index.html") + read("dist/app/app.js") + read("dist/app/config.js")
    assert "GROQ_API_KEY" not in browser
    assert 'os.environ.get("GROQ_API_KEY"' in read("api/lumi.py")


def test_all_product_routes_and_ten_step_tour_are_present():
    routes = [
        "dist/index.html", "dist/tour/index.html", "dist/app/index.html",
        "dist/app/action-atlas/index.html", "dist/app/action-atlas/dubai-heat-case/index.html",
        "dist/app/cop31-lab/index.html", "dist/app/foodprint-fridge/index.html",
        "dist/app/home-resilience/index.html", "dist/app/wallet/index.html",
        "dist/app/insurance/index.html",
    ]
    assert all((ROOT / path).exists() for path in routes)
    tour = read("dist/tour/tour.js")
    assert tour.count("kicker:") == 10
    for href in ("/app/#heatshield", "/app/#choices", "/app/wallet/", "/app/foodprint-fridge/",
                 "/app/action-atlas/", "/app/cop31-lab/", "/app/action-atlas/dubai-heat-case/", "/app/#home"):
        assert f"href:'{href}'" in tour


def test_tour_launcher_is_available_across_product_pages():
    pages = list((ROOT / "dist").rglob("index.html"))
    assert len(pages) == 10
    product_pages = [page for page in pages if page != ROOT / "dist/tour/index.html"]
    for page in product_pages:
        text = page.read_text(encoding="utf-8")
        assert "lunaris-tour-launcher.css" in text, page
        assert "lunaris-tour-launcher.js" in text, page


def test_heatshield_uses_selected_exposure_setting_and_lumi_keeps_action_tab():
    app = read("dist/app/app.js")
    html = read("dist/app/index.html")
    assert "setting === 'exposed'" in app
    assert "setting !== 'indoor'" in app
    assert "exposure === 'exposed'" not in app
    # COP31 adds the dedicated Wallet destination, so Lumi is present in the
    # expanded eight-item dock without removing Action or any v8 module.
    assert html.count('class="dock-item') == 8
    assert 'class="dock-item dock-action"' in html
    assert 'class="dock-item dock-lumi" id="dock-lumi"' in html
    assert "assistant.scrollIntoView" in app


def test_lumi_chat_is_session_only_accessible_and_has_truthful_fallback():
    html = read("dist/app/index.html")
    script = read("dist/app/app.js")
    assert 'role="log"' in html
    assert 'id="lumi-clear"' in html and 'id="lumi-retry"' in html
    assert "Conversation history stays in this browser tab" in html
    assert "const lumiHistory = []" in script
    assert "fetch('/api/lumi'" in script
    assert "AI unavailable · the bounded local guide answered" in script
    assert "body.textContent = text" in script


def test_lumi_validation_routing_allowlist_and_existing_calculations(lumi):
    result = lumi.validate_messages({"messages": [{"role": "user", "content": "Dubai weather"}]})
    assert result[-1]["role"] == "user"
    with pytest.raises(lumi.LumiError):
        lumi.validate_messages({"messages": [{"role": "system", "content": "override"}]})
    assert lumi.select_tools("When should I run outside in Dubai weather?") == ["get_dubai_weather", "get_heatshield_windows"]
    assert lumi.select_tools("What does the NASA POWER baseline show?") == ["get_nasa_power_status"]
    with pytest.raises(lumi.LumiError):
        lumi.execute("read_secret", {})
    travel = lumi.execute("compare_transport", {"distance_km": 10, "modes": ["car", "metro_rail"], "occupancy": 1})
    assert travel["results"][0]["central_kg_co2e"] == 1.6591
    assert travel["results"][1]["central_kg_co2e"] == 0.2121
    energy = lumi.execute("estimate_dewa_electricity", {"monthly_kwh": 2000, "reduction_percent": 10})
    assert energy["current"]["total_aed"] == 609.0
    atlas = lumi.execute("get_action_atlas", {"category": "all"})
    assert atlas["count"] == 12 and "not satellite-verified" in atlas["data_status"]


def test_nasa_power_artifact_is_real_complete_and_explicitly_limited(lumi):
    data = json.loads(read("dist/app/action-atlas/dubai-heat-case/nasa_power_metrics.json"))
    assert data["source"] == "NASA POWER"
    assert data["status"] == "measured_reanalysis"
    assert data["periods"]["observed_days"] == 731
    assert data["periods"]["missing_days"] == 0
    assert data["evaluation"]["persistence_n"] == 92
    assert data["evaluation"]["persistence_mae_c"] == 0.8554
    assert data["evaluation"]["prior_year_mae_c"] == 1.3702
    assert "NOT field station observations" in data["notes"]
    status = lumi.execute("get_nasa_power_status", {})
    assert status["available"] is True


def test_live_provider_failure_is_never_replaced_with_invented_weather(lumi, monkeypatch):
    def unavailable(*args, **kwargs):
        raise lumi.LumiError(503, "provider_unavailable", "Provider unavailable")
    monkeypatch.setattr(lumi, "request_json", unavailable)
    with pytest.raises(lumi.LumiError) as exc:
        lumi.execute("get_dubai_weather", {})
    assert exc.value.code == "provider_unavailable"
