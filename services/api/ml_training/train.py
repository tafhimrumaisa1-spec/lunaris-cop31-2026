"""Run `python -m scripts.train --start 2024-03-01 --end 2026-10-31`."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from lunaris_climate.sources import fetch_training_data
from lunaris_climate.ml import train_and_evaluate
from lunaris_climate.config import MODEL_DIR, ROOT

def main():
    p=argparse.ArgumentParser(description="Train 24h-ahead forecast correction for Dubai using real archived API records")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--out",default=str(MODEL_DIR))
    p.add_argument("--cache-dir",default=str(ROOT/"data"/"cache"))
    a=p.parse_args()
    raw, provenance=fetch_training_data(a.start,a.end,Path(a.cache_dir))
    # Do not silently train on mocked provider data
    if raw.empty:
        raise SystemExit("Provider returned no records")
    report=train_and_evaluate(raw,Path(a.out),provenance)
    print(json.dumps({"train":report["split_counts"], "baseline":report["test_baseline"], "ml":report["test_ml"],"deploy_ml":report["deploy_ml"]},indent=2))
if __name__ == "__main__":
    main()
