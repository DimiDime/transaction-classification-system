import pandas as pd


def preprocess(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Clean raw data and return enriched dict.

    Key decisions:
    - Keep only 'approved' transactions: declined txns show attempted amounts but
      no funds moved, so they distort volume/velocity features. We track declined
      count separately as a risk signal.
    - Cast boolean columns to int for sklearn compatibility.
    - Coerce label column to float, preserving NaN for test rows (no label).
    """
    customers    = data["customers"].copy()
    transactions = data["transactions"].copy()
    accounts     = data["accounts"].copy()
    baselines    = data["baselines"].copy()
    country_risk = data["country_risk"].copy()

    # --- customers ---
    customers["pep_status"]               = customers["pep_status"].astype(int)
    customers["sanctions_screening_flag"] = customers["sanctions_screening_flag"].astype(int)
    customers["suspicious_activity_confirmed"] = pd.to_numeric(
        customers["suspicious_activity_confirmed"], errors="coerce"
    )

    # --- transactions ---
    transactions["abs_amount"] = transactions["amount"].abs()

    approved = transactions[transactions["status"] == "approved"].copy()
    declined = transactions[transactions["status"] == "declined"].copy()

    # --- accounts ---
    accounts["is_dormant"] = (
        (accounts["avg_monthly_balance_6m"] == 0)
        & (accounts["avg_monthly_inflow_6m"] == 0)
        & (accounts["avg_monthly_outflow_6m"] == 0)
    ).astype(int)

    return {
        "customers":    customers,
        "transactions": transactions,
        "approved":     approved,
        "declined":     declined,
        "accounts":     accounts,
        "baselines":    baselines,
        "country_risk": country_risk,
    }
