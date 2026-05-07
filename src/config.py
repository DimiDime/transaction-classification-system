from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR       = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR    = ROOT / "models" / "saved_models"
REPORTS_DIR   = ROOT / "reports"
DATA_DIR      = ROOT / "data"
RESULTS_DIR   = ROOT / "data" / "results dimi"

FEATURES_PATH    = DATA_DIR / "features.parquet"
PREDICTIONS_PATH = RESULTS_DIR / "predictions.csv"
MODEL_PATH       = MODELS_DIR / "gradient_boosting.pkl"
SCALER_PATH      = MODELS_DIR / "scaler.pkl"

# AML threshold for structuring detection (DKK)
STRUCTURING_THRESHOLD = 15_000
STRUCTURING_BAND_LOW  = 13_000

RANDOM_STATE = 42

# Columns never used as features
NON_FEATURE_COLS = {"customer_id", "suspicious_activity_confirmed", "split"}

GB_PARAMS = dict(
    n_estimators=100,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.8,
    min_samples_leaf=5,
    random_state=RANDOM_STATE,
)
