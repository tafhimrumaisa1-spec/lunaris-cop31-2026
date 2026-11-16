from pathlib import Path
import os
DUBAI_LAT = 25.2048
DUBAI_LON = 55.2708
DUBAI_TZ = "Asia/Dubai"
ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = Path(os.getenv("LUNARIS_MODEL_DIR", ROOT / "artifacts"))
MODEL_FILE = MODEL_DIR / "model.joblib"
REPORT_FILE = MODEL_DIR / "evaluation.json"
ALLOWED_ORIGINS = [v.strip() for v in os.getenv("LUNARIS_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if v.strip()]
