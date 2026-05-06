"""
FastAPI backend for the NordikBank AML analyst workbench.

Serves index.html as the SPA root and exposes JSON endpoints that replace
the hardcoded CASES array and static figures in the frontend.

Run from the project root:
    uvicorn app.main:app --reload --port 8000
"""

import json
import pickle
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import (
    FEATURES_PATH,
    MODEL_PATH,
    PREDICTIONS_PATH,
    RAW_DIR,
    REPORTS_DIR,
    RESULTS_DIR,
)
from src.data.load_data import load_raw_data
from src.data.preprocess import preprocess

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="NordikBank AML Workbench", version="1.0.0")

APP_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Data loading — done once at startup, cached in module scope
# ---------------------------------------------------------------------------

def _load_scored() -> pd.DataFrame:
    scored_path = RESULTS_DIR / "scored_all.csv"
    if scored_path.exists():
        return pd.read_csv(scored_path)
    raise FileNotFoundError(
        f"scored_all.csv not found at {scored_path}. "
        "Run src/models/evaluate.py::score_all_customers() first."
    )


def _load_features() -> pd.DataFrame:
    if FEATURES_PATH.exists():
        return pd.read_parquet(FEATURES_PATH)
    raise FileNotFoundError(f"features.parquet not found at {FEATURES_PATH}.")


def _load_raw() -> tuple[dict, pd.DataFrame]:
    raw = load_raw_data()
    alert_history = raw["alert_history"]
    return preprocess(raw), alert_history


# Module-level cache — loaded once when the process starts
try:
    _SCORED: pd.DataFrame = _load_scored()
    _FEATURES: pd.DataFrame = _load_features()
    _RAW, _ALERT_HISTORY = _load_raw()
    _CUSTOMERS: pd.DataFrame = _RAW["customers"]
    _APPROVED: pd.DataFrame = _RAW["approved"]
except Exception as e:
    import sys
    print(f"[startup] WARNING: could not load data — {e}", file=sys.stderr)
    _SCORED = _FEATURES = _RAW = _CUSTOMERS = _APPROVED = _ALERT_HISTORY = None


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

_RISK_THRESHOLDS = {"high": 0.60, "moderate": 0.25}


def _prob_to_risk(prob: float) -> str:
    if prob >= _RISK_THRESHOLDS["high"]:
        return "high"
    if prob >= _RISK_THRESHOLDS["moderate"]:
        return "moderate"
    return "low"


def _score_int(prob: float) -> int:
    return min(99, max(1, round(prob * 100)))


def _fmt_dkk(val: float) -> str:
    if val >= 1_000_000:
        return f"DKK {val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"DKK {val/1_000:.0f}k"
    return f"DKK {val:.0f}"


# ---------------------------------------------------------------------------
# Routes — static files and SPA root
# ---------------------------------------------------------------------------

@app.get("/", response_class=FileResponse)
async def serve_spa():
    return FileResponse(APP_DIR / "index.html")


# ---------------------------------------------------------------------------
# /api/queue  — alert queue (replaces hardcoded CASES array)
# ---------------------------------------------------------------------------

@app.get("/api/queue")
async def get_queue(limit: int = 50):
    """
    Return the top-N customers ranked by predicted_probability, enriched with
    alert history so the frontend queue table has all fields it needs.

    Fields match the CASES object shape in index.html:
        id, customer, rule, date, risk, status, progress, analyst,
        time, customer_type, nationality, score
    """
    if _SCORED is None or _CUSTOMERS is None or _ALERT_HISTORY is None:
        raise HTTPException(503, "Data not available — check server logs.")

    # Top-N by predicted probability (all splits — demo shows everyone)
    top = (
        _SCORED
        .sort_values("predicted_probability", ascending=False)
        .head(limit)
        [["customer_id", "predicted_probability", "top_feature_1", "top_feature_2", "top_feature_3"]]
    )

    # Merge customer metadata
    cust_cols = ["customer_id", "customer_type", "nationality", "kyc_risk_rating"]
    top = top.merge(_CUSTOMERS[cust_cols], on="customer_id", how="left")

    # Attach most recent alert per customer (for rule, date, status, analyst, time)
    latest_alert = (
        _ALERT_HISTORY
        .sort_values("alert_date", ascending=False)
        .groupby("customer_id")
        .first()
        .reset_index()
        [["customer_id", "trigger_rule", "alert_date", "analyst_decision", "investigation_time_minutes"]]
    )
    top = top.merge(latest_alert, on="customer_id", how="left")

    cases = []
    for _, row in top.iterrows():
        prob = float(row["predicted_probability"])
        score = _score_int(prob)
        risk = _prob_to_risk(prob)

        # analyst_decision → status label matching what index.html expects
        decision_map = {
            "SAR_filed": "SAR_filed",
            "escalated": "escalated",
            "cleared": "cleared",
        }
        status = decision_map.get(str(row.get("analyst_decision", "")), "cleared")
        alert_date = str(row["alert_date"])[:10] if pd.notna(row.get("alert_date")) else "2024-12-01"
        rule = str(row.get("trigger_rule", "Threshold")).replace("_", " ").title()
        analyst_names = ["Sofia L.", "Marcus T.", "Priya N.", "James B.", "Anika R.", "Tom H."]
        # deterministic analyst assignment from customer id hash
        idx = abs(hash(row["customer_id"])) % len(analyst_names)
        inv_time = int(row["investigation_time_minutes"]) if pd.notna(row.get("investigation_time_minutes")) else 25
        progress = min(100, max(10, int(prob * 100)))

        cases.append({
            "id": f"ALT-{row['customer_id']}",
            "customer": row["customer_id"],
            "rule": rule,
            "date": alert_date,
            "risk": risk,
            "status": status,
            "progress": progress,
            "analyst": analyst_names[idx],
            "time": inv_time,
            "customer_type": str(row.get("customer_type", "personal")),
            "nationality": str(row.get("nationality", "DK")),
            "score": score,
            "predicted_probability": round(prob, 4),
            "top_features": [
                str(row.get("top_feature_1", "")),
                str(row.get("top_feature_2", "")),
                str(row.get("top_feature_3", "")),
            ],
        })

    return JSONResponse({"cases": cases, "total": len(cases)})


# ---------------------------------------------------------------------------
# /api/customer/{customer_id}  — customer detail for investigation view
# ---------------------------------------------------------------------------

@app.get("/api/customer/{customer_id}")
async def get_customer(customer_id: str):
    """
    Full customer profile for the investigation / 360 view:
    demographics, feature values, monthly transaction history,
    alert history, and model score with top driving features.
    """
    if _FEATURES is None or _CUSTOMERS is None or _APPROVED is None:
        raise HTTPException(503, "Data not available.")

    cust_row = _CUSTOMERS[_CUSTOMERS["customer_id"] == customer_id]
    if cust_row.empty:
        raise HTTPException(404, f"Customer {customer_id} not found.")
    cust = cust_row.iloc[0].to_dict()

    feat_row = _FEATURES[_FEATURES["customer_id"] == customer_id]
    feats = feat_row.iloc[0].to_dict() if not feat_row.empty else {}

    scored_row = _SCORED[_SCORED["customer_id"] == customer_id]
    prob = float(scored_row.iloc[0]["predicted_probability"]) if not scored_row.empty else 0.0
    top_features = []
    if not scored_row.empty:
        top_features = [
            scored_row.iloc[0].get("top_feature_1", ""),
            scored_row.iloc[0].get("top_feature_2", ""),
            scored_row.iloc[0].get("top_feature_3", ""),
        ]

    # Monthly transaction volumes (approved only, signed for in/out)
    cust_txns = _APPROVED[_APPROVED["customer_id"] == customer_id].copy()
    cust_txns["month"] = cust_txns["timestamp"].dt.to_period("M").astype(str)
    monthly = (
        cust_txns.groupby("month")
        .agg(volume=("abs_amount", "sum"), count=("transaction_id", "count"))
        .reset_index()
        .sort_values("month")
        .tail(12)
    )
    monthly_data = monthly.to_dict(orient="records")

    # Alert history for this customer
    cust_alerts = (
        _ALERT_HISTORY[_ALERT_HISTORY["customer_id"] == customer_id]
        .sort_values("alert_date", ascending=False)
        .head(10)
    )
    alerts = [
        {
            "alert_id": row["alert_id"],
            "rule": str(row["trigger_rule"]).replace("_", " ").title(),
            "date": str(row["alert_date"])[:10],
            "decision": row["analyst_decision"],
            "time_minutes": int(row["investigation_time_minutes"]),
        }
        for _, row in cust_alerts.iterrows()
    ]

    # Key feature values for the investigation panel
    feature_spotlight = {
        "income_volume_ratio": round(float(feats.get("income_volume_ratio", 0)), 2),
        "structuring_ratio": round(float(feats.get("structuring_ratio", 0)), 4),
        "pct_intl_txns": round(float(feats.get("pct_intl_txns", 0)), 4),
        "pct_intl_high_risk": round(float(feats.get("pct_intl_high_risk", 0)), 4),
        "unique_counterparties": int(feats.get("unique_counterparties", 0)),
        "monthly_vol_cv": round(float(feats.get("monthly_vol_cv", 0)), 4),
        "vol_vs_baseline": round(float(feats.get("vol_vs_baseline", 1)), 4),
        "num_dormant": int(feats.get("num_dormant", 0)),
        "total_volume": round(float(feats.get("total_volume", 0)), 0),
        "inflow_outflow_ratio": round(float(feats.get("inflow_outflow_ratio", 1)), 3),
    }

    return JSONResponse({
        "customer_id": customer_id,
        "profile": {
            "customer_type": cust.get("customer_type", ""),
            "age": cust.get("age"),
            "nationality": cust.get("nationality", ""),
            "residency_country": cust.get("residency_country", ""),
            "occupation_category": cust.get("occupation_category", ""),
            "declared_annual_income": cust.get("declared_annual_income"),
            "declared_annual_turnover": cust.get("declared_annual_turnover"),
            "kyc_risk_rating": cust.get("kyc_risk_rating", ""),
            "pep_status": bool(cust.get("pep_status", False)),
            "sanctions_screening_flag": bool(cust.get("sanctions_screening_flag", False)),
            "num_accounts": int(cust.get("num_accounts", 1)),
            "registration_date": str(cust.get("registration_date", ""))[:10],
        },
        "score": {
            "predicted_probability": round(prob, 4),
            "score_int": _score_int(prob),
            "risk_tier": _prob_to_risk(prob),
            "top_features": top_features,
        },
        "features": feature_spotlight,
        "monthly_transactions": monthly_data,
        "alert_history": alerts,
    })


# ---------------------------------------------------------------------------
# /api/metrics  — model performance stats for the report/dashboard
# ---------------------------------------------------------------------------

@app.get("/api/metrics")
async def get_metrics():
    """Model evaluation metrics from the last training run."""
    metrics_path = REPORTS_DIR / "eval_metrics.json"
    if not metrics_path.exists():
        raise HTTPException(404, "eval_metrics.json not found.")
    with open(metrics_path) as f:
        metrics = json.load(f)
    return JSONResponse(metrics)


# ---------------------------------------------------------------------------
# /api/feature-importance  — top-20 feature importances
# ---------------------------------------------------------------------------

@app.get("/api/feature-importance")
async def get_feature_importance():
    """Top-20 feature importances from the trained gradient boosting model."""
    fi_path = REPORTS_DIR / "feature_importance.csv"
    if not fi_path.exists():
        raise HTTPException(404, "feature_importance.csv not found.")
    fi = pd.read_csv(fi_path, index_col=0)
    fi.index.name = "feature"
    fi = fi.reset_index()
    fi.columns = ["feature", "importance"]
    return JSONResponse(fi.head(20).to_dict(orient="records"))


# ---------------------------------------------------------------------------
# /api/score-distribution  — histogram data for predicted probabilities
# ---------------------------------------------------------------------------

@app.get("/api/score-distribution")
async def get_score_distribution():
    """Histogram of predicted probabilities across all scored customers."""
    if _SCORED is None:
        raise HTTPException(503, "Data not available.")
    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    labels = ["0–10", "10–20", "20–30", "30–40", "40–50",
              "50–60", "60–70", "70–80", "80–90", "90–100"]
    counts, _ = pd.cut(
        _SCORED["predicted_probability"],
        bins=bins, right=False, labels=labels, retbins=False
    ).value_counts(sort=False).reindex(labels, fill_value=0).reset_index().values.T
    return JSONResponse([
        {"bucket": lbl, "count": int(cnt)}
        for lbl, cnt in zip(labels, _SCORED["predicted_probability"]
                            .pipe(lambda s: pd.cut(s, bins=bins, right=False, labels=labels))
                            .value_counts(sort=False)
                            .reindex(labels, fill_value=0)
                            .values)
    ])
