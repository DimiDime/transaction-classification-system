"""
End-to-end pipeline:
  load → preprocess → build_features → train → evaluate → predict

Run from the project root:
  python run_pipeline.py
"""

import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from src.data.load_data import load_raw_data
from src.data.preprocess import preprocess
from src.features.build_features import build_features
from src.models.evaluate import evaluate, score_all_customers
from src.models.predict import predict
from src.models.train import train
from src.utils.helpers import get_logger

logger = get_logger("pipeline")


def main():
    logger.info("=== Step 1/5  Load raw data ===")
    raw = load_raw_data()

    logger.info("=== Step 2/5  Preprocess ===")
    data = preprocess(raw)

    logger.info("=== Step 3/5  Build features ===")
    features = build_features(data)

    logger.info("=== Step 4/5  Train model ===")
    final_model, val_model = train(features)

    logger.info("=== Step 5a   Evaluate on val (val_model, trained on train only) ===")
    metrics = evaluate(features, val_model)

    logger.info("=== Step 5b   Score test customers → predictions.csv ===")
    submission = predict(features, final_model)

    logger.info("Done. Val AUC-ROC: %.4f  |  Submission rows: %d", metrics["val_auc_roc"], len(submission))

    # Also write scored_all.csv for the frontend workbench (use final model)
    from src.config import RESULTS_DIR
    scored = score_all_customers(features, final_model)
    scored.to_csv(RESULTS_DIR / "scored_all.csv", index=False)
    logger.info("scored_all.csv written — %d customers ranked", len(scored))


if __name__ == "__main__":
    main()
