"""Chronological modeling with leak-resistant features and honest test reporting."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

NUMERIC = ["f_temperature_2m", "f_relative_humidity_2m", "f_apparent_temperature", "f_cloud_cover", "f_wind_speed_10m"]
FEATURES = NUMERIC + ["hour_sin", "hour_cos", "year_sin", "year_cos"]
TARGET = "target_apparent_temperature"

class DataNotReady(ValueError):
    pass

def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    missing = set(["time", TARGET, *NUMERIC]) - set(raw.columns)
    if missing:
        raise DataNotReady(f"Missing required columns: {sorted(missing)}")
    f = raw.copy()
    f["time"] = pd.to_datetime(f["time"], errors="coerce")
    for name in NUMERIC + [TARGET]:
        f[name] = pd.to_numeric(f[name], errors="coerce")
    f = f.dropna(subset=["time", TARGET, *NUMERIC]).sort_values("time").drop_duplicates(subset=["time"])
    if f.empty:
        raise DataNotReady("No complete rows")
    h = f["time"].dt.hour
    d = f["time"].dt.dayofyear
    f["hour_sin"] = np.sin(2 * np.pi * h / 24)
    f["hour_cos"] = np.cos(2 * np.pi * h / 24)
    f["year_sin"] = np.sin(2 * np.pi * d / 365.25)
    f["year_cos"] = np.cos(2 * np.pi * d / 365.25)
    return f.reset_index(drop=True)

def scores(y, yhat) -> dict:
    return {"mae_c": round(float(mean_absolute_error(y, yhat)), 4), "rmse_c": round(float(np.sqrt(mean_squared_error(y, yhat))), 4), "n": int(len(y))}

def chronological_split(f: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split by whole local calendar dates so one date never spans train and test."""
    dates = sorted(f["time"].dt.date.unique())
    if len(dates) < 90:
        raise DataNotReady(f"Need >=90 unique days for demonstration; found {len(dates)}")
    a = int(len(dates) * 0.7)
    b = int(len(dates) * 0.85)
    train = f[f["time"].dt.date.isin(dates[:a])]
    val = f[f["time"].dt.date.isin(dates[a:b])]
    test = f[f["time"].dt.date.isin(dates[b:])]
    if min(len(train), len(val), len(test)) < 100:
        raise DataNotReady("Each split requires at least 100 complete hourly records")
    return train, val, test

def train_and_evaluate(raw: pd.DataFrame, output_dir: Path, provenance: dict | None = None) -> dict:
    f = prepare(raw)
    train, val, test = chronological_split(f)
    # Candidate chosen using VALIDATION ONLY; no test-based hyperparameter tuning.
    candidates = [
        {"max_iter": 100, "max_leaf_nodes": 9, "learning_rate": 0.06, "l2_regularization": 1.0},
        {"max_iter": 160, "max_leaf_nodes": 15, "learning_rate": 0.04, "l2_regularization": 3.0},
    ]
    evaluated = []
    for conf in candidates:
        model = HistGradientBoostingRegressor(random_state=42, min_samples_leaf=20, **conf)
        model.fit(train[FEATURES], train[TARGET])
        evaluated.append((scores(val[TARGET], model.predict(val[FEATURES]))["mae_c"], conf))
    selected_error, selected = min(evaluated, key=lambda t:t[0])
    raw_validation = scores(val[TARGET], val["f_apparent_temperature"])
    should_deploy = bool(selected_error < raw_validation["mae_c"])
    # Refit only on train+validation after fixing hyperparameters/deployment policy.
    fit = pd.concat([train, val], ignore_index=True)
    model = HistGradientBoostingRegressor(random_state=42, min_samples_leaf=20, **selected)
    model.fit(fit[FEATURES], fit[TARGET])
    base_test = scores(test[TARGET], test["f_apparent_temperature"])
    model_test = scores(test[TARGET], model.predict(test[FEATURES]))
    baseline_abs = np.abs(test[TARGET].to_numpy()-test["f_apparent_temperature"].to_numpy())
    ml_abs = np.abs(test[TARGET].to_numpy()-model.predict(test[FEATURES]))
    # illustrative historical worst failure on never-before-seen dates
    worst_indices = np.argsort(ml_abs)[-5:][::-1]
    examples=[]
    pred = model.predict(test[FEATURES])
    for i in worst_indices:
        row=test.iloc[int(i)]
        examples.append({"time": row["time"].isoformat(), "reference_c": round(float(row[TARGET]), 2), "baseline_forecast_c": round(float(row["f_apparent_temperature"]), 2),
                         "ml_forecast_c": round(float(pred[int(i)]), 2), "ml_absolute_error_c": round(float(ml_abs[int(i)]), 2)})
    report = {
        "experiment": "Dubai 24h-lead apparent-temperature forecast correction versus Open-Meteo reanalysis reference",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "data_kind": "real_provider_data" if provenance and provenance.get("forecast_source") else "user_supplied_unverified",
        "reference_caveat": "Historical archive is reanalysis; not direct station observations, may share model dependencies.",
        "train_dates": [str(train["time"].iloc[0].date()), str(train["time"].iloc[-1].date())],
        "validation_dates": [str(val["time"].iloc[0].date()), str(val["time"].iloc[-1].date())],
        "test_dates": [str(test["time"].iloc[0].date()), str(test["time"].iloc[-1].date())],
        "split_counts": {"train": len(train), "validation": len(val), "test": len(test)},
        "validation_baseline": raw_validation,
        "validation_selected_ml_mae_c": selected_error,
        "deploy_ml": should_deploy,
        "selection_policy": "Use ML only if validation MAE strictly beats raw 24h lead forecast; do not select using test scores.",
        "test_baseline": base_test,
        "test_ml": model_test,
        "test_skill_mae_fraction": round(float(1-model_test["mae_c"]/base_test["mae_c"]),4) if base_test["mae_c"] else None,
        "test_ml_improves": model_test["mae_c"] < base_test["mae_c"],
        "test_worst_ml_failures":examples,
        "selected_hyperparams":selected,
        "features":FEATURES,
        "provenance":provenance or {},
        "limitations":["Reference is model-derived historical reanalysis, not independent station observations.", "One city gridpoint is not street-level heat or individual heat illness risk.", "Forecast-vintage features must match real deployment; live forecast horizons vary.", "Single chronological test period; further temporal and geographic validation needed."]
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "deploy_ml":should_deploy,"report":report}, output_dir/"model.joblib")
    (output_dir/"evaluation.json").write_text(json.dumps(report, indent=2))
    return report

def frame_for_live_forecast(hourly: dict) -> pd.DataFrame:
    f = pd.DataFrame(hourly)
    if not all(c in f.columns for c in ["time", "temperature_2m", "relative_humidity_2m", "apparent_temperature", "cloud_cover", "wind_speed_10m"]):
        raise DataNotReady("Forecast missing necessary variables")
    f["time"] = pd.to_datetime(f["time"], errors="coerce")
    for c in NUMERIC:
        f[c] = pd.to_numeric(f[c[2:]], errors="coerce")
    h=f["time"].dt.hour
    day=f["time"].dt.dayofyear
    f["hour_sin"] = np.sin(2*np.pi*h/24)
    f["hour_cos"] = np.cos(2*np.pi*h/24)
    f["year_sin"] = np.sin(2*np.pi*day/365.25)
    f["year_cos"] = np.cos(2*np.pi*day/365.25)
    return f
