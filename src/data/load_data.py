import pandas as pd
from src.config import RAW_DIR


def load_raw_data() -> dict[str, pd.DataFrame]:
    """Load all six raw CSVs and return them keyed by name."""
    customers = pd.read_csv(
        RAW_DIR / "customers.csv",
        parse_dates=["registration_date"],
    )
    transactions = pd.read_csv(
        RAW_DIR / "transactions.csv",
        parse_dates=["timestamp"],
    )
    accounts = pd.read_csv(
        RAW_DIR / "accounts.csv",
        parse_dates=["opening_date"],
    )
    baselines    = pd.read_csv(RAW_DIR / "baselines.csv")
    alert_history = pd.read_csv(
        RAW_DIR / "alert_history.csv",
        parse_dates=["alert_date"],
    )
    country_risk = pd.read_csv(RAW_DIR / "country_risk.csv")

    return {
        "customers":     customers,
        "transactions":  transactions,
        "accounts":      accounts,
        "baselines":     baselines,
        "alert_history": alert_history,
        "country_risk":  country_risk,
    }
