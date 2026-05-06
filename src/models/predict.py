"""
Score the 500 held-out test customers and write predictions.csv.
Format required: customer_id, predicted_probability (0.0–1.0).
"""

import pickle

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from src.config import FEATURES_PATH, MODEL_PATH, PREDICTIONS_PATH
from src.features.build_features import get_feature_cols
from src.utils.helpers import get_logger

logger = get_logger(__name__)


def predict(
    features: pd.DataFrame | None = None,
    model: GradientBoostingClassifier | None = None,
) -> pd.DataFrame:
    """
    Score test customers. If features/model are not passed, load from disk.
    Returns the submission DataFrame and writes predictions.csv.
    """
    if features is None:
        features = pd.read_parquet(FEATURES_PATH)

    if model is None:
        with open(MODEL_PATH, "rb") as f:
            bundle = pickle.load(f)
        model        = bundle["model"]
        feature_cols = bundle["feature_cols"]
    else:
        feature_cols = get_feature_cols(features)

    test = features[features["split"] == "test"].copy()
    if len(test) == 0:
        raise ValueError("No test rows found in features DataFrame.")

    X_test = test[feature_cols].fillna(0)
    proba  = model.predict_proba(X_test)[:, 1]

    submission = pd.DataFrame(
        {"customer_id": test["customer_id"].values, "predicted_probability": proba}
    )

    PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    submission.to_csv(PREDICTIONS_PATH, index=False)

    logger.info(
        "predictions.csv written — %d rows, score range [%.4f, %.4f]",
        len(submission), proba.min(), proba.max(),
    )
    return submission
