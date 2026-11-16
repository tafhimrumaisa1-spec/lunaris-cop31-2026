import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from lunaris_climate.ml import prepare, chronological_split, train_and_evaluate, DataNotReady
from lunaris_climate.recommendations import Preferences, rank_hours
from lunaris_climate.api import app

@pytest.fixture
def synthetic_dataset():
    """Artificial math test fixture ONLY. Never used to make claims about Dubai accuracy."""
    rng=np.random.default_rng(11)
    dates=pd.date_range("2025-01-01",periods=110*24,freq="h")
    f=32+7*np.sin(np.arange(len(dates))*2*np.pi/24)+rng.normal(0,2,len(dates))
    return pd.DataFrame({"time":dates, "f_temperature_2m":f,
        "f_relative_humidity_2m":rng.uniform(20,80,len(dates)),
        "f_apparent_temperature":f+2,
        "f_cloud_cover":rng.uniform(0,100,len(dates)),
        "f_wind_speed_10m":rng.uniform(0,30,len(dates)),
        "target_apparent_temperature":f+1+rng.normal(0,0.4,len(dates))})

def test_date_split_no_leakage(synthetic_dataset):
    x=prepare(synthetic_dataset)
    a,b,c=chronological_split(x)
    assert a.time.max().date()<b.time.min().date()<c.time.min().date()
    assert set(a.time.dt.date).isdisjoint(set(c.time.dt.date))

def test_training_writes_artifacts_with_synthetic_label(synthetic_dataset,tmp_path):
    report=train_and_evaluate(synthetic_dataset,tmp_path,{"fixture":"synthetic TEST DATA ONLY"})
    assert report["data_kind"]=="user_supplied_unverified"
    assert report["test_ml"]["n"]>0
    assert (tmp_path/"model.joblib").exists()
    assert (tmp_path/"evaluation.json").exists()
    assert len(report["test_worst_ml_failures"])==5

def test_requires_sufficient_history():
    with pytest.raises(DataNotReady):
        chronological_split(pd.DataFrame({"time":pd.date_range("2025-01-01",periods=200,freq="h")}))

def test_preference_validation():
    with pytest.raises(ValueError):
        Preferences(min_comfort_c=31,max_comfort_c=20)

def test_heat_window_score_and_cautions():
    p=Preferences(min_comfort_c=20,max_comfort_c=28,prefers_clouds=True,activity="running")
    out=rank_hours([
        {"time":"2026-11-16T17:00:00+04:00","apparent_temperature_c":26,"cloud_cover_pct":75,"precipitation_mm":0,"relative_humidity_pct":40},
        {"time":"2026-11-16T12:00:00+04:00","apparent_temperature_c":41,"cloud_cover_pct":0,"precipitation_mm":0,"relative_humidity_pct":45}],p)
    assert out[0]["preference_match_score"]>out[1]["preference_match_score"]
    assert out[1]["cautions"]

def test_untrained_status():
    r=TestClient(app).get("/v1/climate-ai/health")
    assert r.status_code==200
    assert r.json()["city"]=="Dubai"

def test_live_failure_is_503(monkeypatch):
    import lunaris_climate.api as api
    from lunaris_climate.sources import ProviderError
    def failure(*args,**kwargs): raise ProviderError("offline")
    monkeypatch.setattr(api,"get_live_forecast",failure)
    response=TestClient(app).post("/v1/heatshield/ai-windows",json={"preferences":{"min_comfort_c":19,"max_comfort_c":30}})
    assert response.status_code==503
    assert "no fallback numbers invented" in response.json()["detail"]
