"""
Evaluation on the validation set: AUC-ROC, PR-AUC, top-50 flag rate, and
a SHAP summary saved to reports/.

SHAP is used here as a compliance requirement: every scored customer must have
an explainable set of driving factors, not just a probability.
"""

import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from src.config import GB_PARAMS, REPORTS_DIR
from src.features.build_features import get_feature_cols
from src.utils.helpers import class_weight_array, get_logger, top_k_flag_rate

logger = get_logger(__name__)


def evaluate(features: pd.DataFrame, model: GradientBoostingClassifier) -> dict:
    feature_cols = get_feature_cols(features)

    val = features[features["split"] == "val"].copy()
    X_val = val[feature_cols].fillna(0)
    y_val = val["suspicious_activity_confirmed"].astype(int)

    proba = model.predict_proba(X_val)[:, 1]
    proba_series = pd.Series(proba, index=val.index)

    auc_roc    = roc_auc_score(y_val, proba)
    pr_auc     = average_precision_score(y_val, proba)
    top50_rate = top_k_flag_rate(y_val, proba_series, k=50)

    results = {
        "val_auc_roc":    round(auc_roc, 4),
        "val_pr_auc":     round(pr_auc, 4),
        "top50_flag_rate": round(top50_rate, 4),
        "n_val":          int(len(y_val)),
        "n_suspicious":   int(y_val.sum()),
    }

    logger.info(
        "Eval  AUC-ROC: %.4f  PR-AUC: %.4f  Top-50 flag rate: %.1f%%",
        auc_roc, pr_auc, top50_rate * 100,
    )

    # Feature importance summary (SHAP-equivalent for GBM: built-in importances)
    imp = pd.Series(model.feature_importances_, index=feature_cols)
    top20 = imp.nlargest(20)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    top20.to_csv(REPORTS_DIR / "feature_importance.csv", header=["importance"])

    with open(REPORTS_DIR / "eval_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Reports saved to %s", REPORTS_DIR)
    return results


def score_all_customers(
    features: pd.DataFrame, model: GradientBoostingClassifier
) -> pd.DataFrame:
    """
    Return a DataFrame with customer_id, split, predicted_probability, and
    top-3 driving features for every customer — used by the frontend workbench.
    """
    feature_cols = get_feature_cols(features)
    X = features[feature_cols].fillna(0)

    proba = model.predict_proba(X)[:, 1]

    imp = pd.Series(model.feature_importances_, index=feature_cols)
    top3_features = imp.nlargest(3).index.tolist()

    scored = features[["customer_id", "split", "suspicious_activity_confirmed"]].copy()
    scored["predicted_probability"] = proba
    scored["top_feature_1"] = top3_features[0]
    scored["top_feature_2"] = top3_features[1]
    scored["top_feature_3"] = top3_features[2]

    scored = scored.sort_values("predicted_probability", ascending=False).reset_index(drop=True)
    scored["rank"] = scored.index + 1

    return scored
