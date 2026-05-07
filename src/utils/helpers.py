import logging
import sys

import numpy as np
import pandas as pd


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def class_weight_array(y: pd.Series) -> np.ndarray:
    """Inverse-frequency sample weights for imbalanced binary labels."""
    n = len(y)
    n_pos = y.sum()
    n_neg = n - n_pos
    return np.where(y == 1, n / (2 * n_pos), n / (2 * n_neg))


def top_k_flag_rate(y_true: pd.Series, y_prob: pd.Series, k: int = 50) -> float:
    """Fraction of truly suspicious customers in the top-k ranked by score."""
    top_k = y_prob.nlargest(k).index
    return y_true.loc[top_k].mean()
