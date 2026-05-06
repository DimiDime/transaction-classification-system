"""
Train a GradientBoostingClassifier on train+val combined, then save it.

Two-stage strategy (mirrors the notebook):
  1. Evaluate on val-only to pick hyper-parameters and report honest AUC.
  2. Retrain on train+val so the final model has seen all labelled data before
     scoring the 500 held-out test customers.
"""

import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from src.config import GB_PARAMS, MODEL_PATH, MODELS_DIR
from src.features.build_features import get_feature_cols
from src.utils.helpers import class_weight_array, get_logger

logger = get_logger(__name__)


def _split(features: pd.DataFrame, feature_cols: list[str]):
    train = features[features["split"] == "train"]
    val   = features[features["split"] == "val"]

    X_train = train[feature_cols].fillna(0)
    y_train = train["suspicious_activity_confirmed"].astype(int)
    X_val   = val[feature_cols].fillna(0)
    y_val   = val["suspicious_activity_confirmed"].astype(int)
    return X_train, y_train, X_val, y_val


def train(features: pd.DataFrame) -> tuple[GradientBoostingClassifier, GradientBoostingClassifier]:
    feature_cols = get_feature_cols(features)

    X_train, y_train, X_val, y_val = _split(features, feature_cols)

    logger.info(
        "Train: %d rows (%d suspicious, %.1f%%)  |  Val: %d rows (%d suspicious, %.1f%%)",
        len(X_train), y_train.sum(), y_train.mean() * 100,
        len(X_val),   y_val.sum(),   y_val.mean()   * 100,
    )

    # --- val-only model for honest evaluation ---
    sw_train = class_weight_array(y_train)
    gb_val = GradientBoostingClassifier(**GB_PARAMS)
    gb_val.fit(X_train, y_train, sample_weight=sw_train)

    val_proba = gb_val.predict_proba(X_val)[:, 1]
    auc_roc   = roc_auc_score(y_val, val_proba)
    pr_auc    = average_precision_score(y_val, val_proba)
    logger.info("Val AUC-ROC: %.4f  |  PR-AUC: %.4f", auc_roc, pr_auc)

    # --- final model on train + val ---
    train_val = features[features["split"].isin(["train", "val"])]
    X_tv = train_val[feature_cols].fillna(0)
    y_tv = train_val["suspicious_activity_confirmed"].astype(int)
    sw_tv = class_weight_array(y_tv)

    final_model = GradientBoostingClassifier(**GB_PARAMS)
    final_model.fit(X_tv, y_tv, sample_weight=sw_tv)
    logger.info("Final model trained on %d customers", len(X_tv))

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": final_model, "feature_cols": feature_cols}, f)
    logger.info("Model saved to %s", MODEL_PATH)

    # Return both: val_model for honest evaluation, final_model for prediction
    return final_model, gb_val
