"""
Customer-level feature engineering for AML scoring.

Each _feat_* function takes the preprocessed data dict and returns a DataFrame
with customer_id plus the feature columns it owns. All are left-joined onto the
customer spine at the end so every customer gets a row regardless of activity.

Feature groups:
  1. identity       — KYC risk, PEP/sanctions flags, customer type, tenure
  2. income         — income-to-volume ratio (key deviation signal)
  3. velocity       — total transaction counts/volumes, declined ratio
  4. structuring    — cash txns near the 15K DKK internal threshold
  5. cash           — cash deposit vs withdrawal split, ratios
  6. counterparty   — counterparty diversity, concentration, recurring share
  7. geo            — international exposure, high-risk country links
  8. accounts       — dormant accounts, foreign currency, balance/flow ratio
  9. temporal       — monthly volume/count CV (erratic = suspicious)
 10. baselines      — 6-month behavioral aggregates from baselines.csv
 11. deviation      — actual vs baseline (relative, not absolute)
 12. type_mix       — transaction type share vector
"""

import numpy as np
import pandas as pd

from src.config import (
    FEATURES_PATH,
    STRUCTURING_BAND_LOW,
    STRUCTURING_THRESHOLD,
)


# ---------------------------------------------------------------------------
# 1. Identity
# ---------------------------------------------------------------------------

def _feat_identity(customers: pd.DataFrame) -> pd.DataFrame:
    f = customers[
        [
            "customer_id",
            "customer_type",
            "kyc_risk_rating",
            "pep_status",
            "sanctions_screening_flag",
            "nationality",
            "residency_country",
            "num_accounts",
            "registration_date",
        ]
    ].copy()

    f["kyc_medium"] = (f["kyc_risk_rating"] == "medium").astype(int)
    f["kyc_high"]   = (f["kyc_risk_rating"] == "high").astype(int)

    # Nationality ≠ residency is a mild AML indicator
    f["nationality_mismatch"] = (f["nationality"] != f["residency_country"]).astype(int)

    # Customer tenure in years — newer customers have less established profiles
    ref_date = pd.Timestamp("2025-01-01")
    f["tenure_years"] = (ref_date - f["registration_date"]).dt.days / 365.25

    return f.drop(columns=["kyc_risk_rating", "nationality", "residency_country", "registration_date"])


# ---------------------------------------------------------------------------
# 2. Income vs volume
# ---------------------------------------------------------------------------

def _feat_income(customers: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    inc = customers[
        ["customer_id", "customer_type", "declared_annual_income", "declared_annual_turnover"]
    ].copy()

    # Use turnover for business entities, income for personal
    inc["declared_annual"] = np.where(
        inc["customer_type"].isin(["corporate", "SME", "sole_trader"]),
        inc["declared_annual_turnover"],
        inc["declared_annual_income"],
    )

    vol = baselines[["customer_id", "avg_monthly_volume"]].copy()
    vol["annual_volume_proxy"] = vol["avg_monthly_volume"] * 12

    f = inc[["customer_id", "declared_annual"]].merge(
        vol[["customer_id", "annual_volume_proxy"]], on="customer_id", how="left"
    )

    # >1 means transacting more than declared — core AML red flag
    f["income_volume_ratio"] = f["annual_volume_proxy"] / (f["declared_annual"] + 1)
    f["income_missing"]      = f["declared_annual"].isna().astype(int)

    return f[["customer_id", "income_volume_ratio", "income_missing"]]


# ---------------------------------------------------------------------------
# 3. Velocity
# ---------------------------------------------------------------------------

def _feat_velocity(
    customers: pd.DataFrame, approved: pd.DataFrame, declined: pd.DataFrame
) -> pd.DataFrame:
    txn_agg = approved.groupby("customer_id").agg(
        txn_count_total   = ("transaction_id", "count"),
        total_volume      = ("abs_amount", "sum"),
        avg_txn_amount    = ("abs_amount", "mean"),
        max_single_txn    = ("abs_amount", "max"),
        std_txn_amount    = ("abs_amount", "std"),
    ).reset_index()

    declined_counts = (
        declined.groupby("customer_id").size().reset_index(name="declined_txn_count")
    )

    f = customers[["customer_id"]].merge(txn_agg, on="customer_id", how="left")
    f = f.merge(declined_counts, on="customer_id", how="left")

    f["txn_count_total"]   = f["txn_count_total"].fillna(0)
    f["declined_txn_count"] = f["declined_txn_count"].fillna(0)
    f["total_volume"]      = f["total_volume"].fillna(0)
    f["avg_txn_amount"]    = f["avg_txn_amount"].fillna(0)
    f["max_single_txn"]    = f["max_single_txn"].fillna(0)
    f["std_txn_amount"]    = f["std_txn_amount"].fillna(0)

    f["declined_ratio"] = f["declined_txn_count"] / (f["txn_count_total"] + 1)

    return f


# ---------------------------------------------------------------------------
# 4. Structuring
# ---------------------------------------------------------------------------

def _feat_structuring(customers: pd.DataFrame, approved: pd.DataFrame) -> pd.DataFrame:
    cash = approved[
        approved["transaction_type"].isin(["cash_deposit", "cash_withdrawal"])
    ].copy()

    cash["in_structuring_band"] = (
        (cash["abs_amount"] >= STRUCTURING_BAND_LOW)
        & (cash["abs_amount"] < STRUCTURING_THRESHOLD)
    ).astype(int)

    struct_agg = cash.groupby("customer_id").agg(
        cash_txn_count     = ("transaction_id", "count"),
        structuring_count  = ("in_structuring_band", "sum"),
        cash_total_volume  = ("abs_amount", "sum"),
    ).reset_index()

    struct_agg["structuring_ratio"] = (
        struct_agg["structuring_count"] / struct_agg["cash_txn_count"]
    )

    f = customers[["customer_id"]].merge(struct_agg, on="customer_id", how="left")
    for col in ["cash_txn_count", "structuring_count", "cash_total_volume", "structuring_ratio"]:
        f[col] = f[col].fillna(0)

    return f[["customer_id", "structuring_count", "structuring_ratio"]]


# ---------------------------------------------------------------------------
# 5. Cash direction split
# ---------------------------------------------------------------------------

def _feat_cash(
    customers: pd.DataFrame, approved: pd.DataFrame, feat_velocity: pd.DataFrame
) -> pd.DataFrame:
    cash_dir = approved[
        approved["transaction_type"].isin(["cash_deposit", "cash_withdrawal"])
    ].copy()

    cash_by_dir = (
        cash_dir.groupby(["customer_id", "transaction_type"])
        .agg(count=("transaction_id", "count"), volume=("abs_amount", "sum"))
        .unstack(fill_value=0)
    )
    cash_by_dir.columns = ["_".join(c) for c in cash_by_dir.columns]
    cash_by_dir = cash_by_dir.reset_index()

    f = customers[["customer_id"]].merge(cash_by_dir, on="customer_id", how="left")
    f = f.merge(
        feat_velocity[["customer_id", "txn_count_total", "total_volume"]],
        on="customer_id",
        how="left",
    )

    for col in [c for c in f.columns if c != "customer_id"]:
        f[col] = f[col].fillna(0)

    deposit_col    = "count_cash_deposit"    if "count_cash_deposit"    in f.columns else None
    withdrawal_col = "count_cash_withdrawal" if "count_cash_withdrawal" in f.columns else None

    if deposit_col:
        f["pct_cash_deposit"]    = f[deposit_col]    / (f["txn_count_total"] + 1)
    else:
        f["pct_cash_deposit"] = 0.0

    if withdrawal_col:
        f["pct_cash_withdrawal"] = f[withdrawal_col] / (f["txn_count_total"] + 1)
    else:
        f["pct_cash_withdrawal"] = 0.0

    keep = ["customer_id", "pct_cash_deposit", "pct_cash_withdrawal"]
    if "volume_cash_deposit"    in f.columns: keep.append("volume_cash_deposit")
    if "volume_cash_withdrawal" in f.columns: keep.append("volume_cash_withdrawal")

    return f[keep]


# ---------------------------------------------------------------------------
# 6. Counterparty
# ---------------------------------------------------------------------------

def _feat_counterparty(customers: pd.DataFrame, approved: pd.DataFrame) -> pd.DataFrame:
    cp_agg = approved.groupby("customer_id").agg(
        unique_counterparties = ("counterparty_id", "nunique"),
        recurring_txn_count   = ("is_recurring", "sum"),
        total_txns            = ("transaction_id", "count"),
    ).reset_index()

    cp_agg["pct_recurring"] = cp_agg["recurring_txn_count"] / (cp_agg["total_txns"] + 1)

    # Max share any single counterparty represents — high concentration = potential
    # shell-company routing
    cp_share = (
        approved.groupby(["customer_id", "counterparty_id"])
        .size()
        .reset_index(name="cp_count")
    )
    cp_total = approved.groupby("customer_id").size().reset_index(name="total")
    cp_share = cp_share.merge(cp_total, on="customer_id")
    cp_share["share"] = cp_share["cp_count"] / cp_share["total"]
    cp_conc = (
        cp_share.groupby("customer_id")["share"].max().reset_index(name="max_cp_concentration")
    )

    f = customers[["customer_id"]].merge(cp_agg, on="customer_id", how="left")
    f = f.merge(cp_conc, on="customer_id", how="left")

    f["unique_counterparties"]  = f["unique_counterparties"].fillna(0)
    f["pct_recurring"]          = f["pct_recurring"].fillna(0)
    f["max_cp_concentration"]   = f["max_cp_concentration"].fillna(1.0)  # 1 counterparty = 100%

    return f[["customer_id", "unique_counterparties", "pct_recurring", "max_cp_concentration"]]


# ---------------------------------------------------------------------------
# 7. Geographic / international
# ---------------------------------------------------------------------------

def _feat_geo(
    customers: pd.DataFrame, approved: pd.DataFrame, country_risk: pd.DataFrame
) -> pd.DataFrame:
    intl = approved[approved["counterparty_bank_country"].notna()].copy()
    intl = intl.merge(
        country_risk, left_on="counterparty_bank_country", right_on="country_code", how="left"
    )

    intl_agg = intl.groupby("customer_id").agg(
        intl_txn_count        = ("transaction_id", "count"),
        intl_volume           = ("abs_amount", "sum"),
        high_risk_country_txns= ("eu_high_risk_list", "sum"),
        min_cpi               = ("corruption_perception_index", "min"),
        unique_countries      = ("counterparty_bank_country", "nunique"),
    ).reset_index()

    total_txns = approved.groupby("customer_id").size().reset_index(name="total_txns")
    intl_agg = intl_agg.merge(total_txns, on="customer_id", how="left")

    intl_agg["pct_intl_txns"]      = intl_agg["intl_txn_count"] / (intl_agg["total_txns"] + 1)
    intl_agg["pct_intl_high_risk"] = (
        intl_agg["high_risk_country_txns"] / (intl_agg["intl_txn_count"] + 1)
    )

    f = customers[["customer_id"]].merge(intl_agg, on="customer_id", how="left")

    for col in ["intl_txn_count", "intl_volume", "high_risk_country_txns",
                "unique_countries", "pct_intl_txns", "pct_intl_high_risk"]:
        f[col] = f[col].fillna(0)

    # Unknown CPI = median (unknown ≠ safe)
    median_cpi = f["min_cpi"].median()
    f["min_cpi"] = f["min_cpi"].fillna(median_cpi)

    return f[[
        "customer_id", "intl_txn_count", "intl_volume", "pct_intl_txns",
        "pct_intl_high_risk", "min_cpi", "unique_countries",
    ]]


# ---------------------------------------------------------------------------
# 8. Accounts
# ---------------------------------------------------------------------------

def _feat_accounts(customers: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    acc_agg = accounts.groupby("customer_id").agg(
        num_accounts          = ("account_id", "count"),
        num_dormant           = ("is_dormant", "sum"),
        has_foreign_currency  = ("currency", lambda x: int((x != "DKK").any())),
        total_balance         = ("avg_monthly_balance_6m", "sum"),
        total_inflow          = ("avg_monthly_inflow_6m", "sum"),
        total_outflow         = ("avg_monthly_outflow_6m", "sum"),
    ).reset_index()

    acc_agg["pct_dormant_accounts"] = acc_agg["num_dormant"] / (acc_agg["num_accounts"] + 1)

    # Flow asymmetry: large inflow relative to outflow can signal layering
    acc_agg["inflow_outflow_ratio"] = acc_agg["total_inflow"] / (acc_agg["total_outflow"] + 1)

    f = customers[["customer_id"]].merge(acc_agg, on="customer_id", how="left")
    for col in ["num_dormant", "pct_dormant_accounts", "has_foreign_currency",
                "inflow_outflow_ratio"]:
        f[col] = f[col].fillna(0)

    return f[[
        "customer_id", "num_dormant", "pct_dormant_accounts",
        "has_foreign_currency", "total_balance", "total_inflow",
        "total_outflow", "inflow_outflow_ratio",
    ]]


# ---------------------------------------------------------------------------
# 9. Temporal / erratic behaviour
# ---------------------------------------------------------------------------

def _feat_temporal(customers: pd.DataFrame, approved: pd.DataFrame) -> pd.DataFrame:
    approved = approved.copy()
    approved["month"] = approved["timestamp"].dt.to_period("M")

    monthly_vol = (
        approved.groupby(["customer_id", "month"])["abs_amount"].sum().reset_index()
    )
    monthly_stats = (
        monthly_vol.groupby("customer_id")["abs_amount"]
        .agg(["mean", "std"])
        .reset_index()
    )
    monthly_stats.columns = ["customer_id", "monthly_vol_mean", "monthly_vol_std"]
    monthly_stats["monthly_vol_cv"] = monthly_stats["monthly_vol_std"] / (
        monthly_stats["monthly_vol_mean"] + 1
    )

    monthly_cnt = (
        approved.groupby(["customer_id", "month"]).size().reset_index(name="cnt")
    )
    cnt_stats = (
        monthly_cnt.groupby("customer_id")["cnt"]
        .agg(["mean", "std"])
        .reset_index()
    )
    cnt_stats.columns = ["customer_id", "monthly_cnt_mean", "monthly_cnt_std"]
    cnt_stats["monthly_cnt_cv"] = cnt_stats["monthly_cnt_std"] / (
        cnt_stats["monthly_cnt_mean"] + 1
    )

    f = customers[["customer_id"]].merge(monthly_stats, on="customer_id", how="left")
    f = f.merge(cnt_stats, on="customer_id", how="left")

    for col in ["monthly_vol_cv", "monthly_cnt_cv", "monthly_vol_mean", "monthly_cnt_mean"]:
        f[col] = f[col].fillna(0)

    return f[[
        "customer_id", "monthly_vol_cv", "monthly_cnt_cv",
        "monthly_vol_mean", "monthly_cnt_mean",
    ]]


# ---------------------------------------------------------------------------
# 10. Baselines (6-month behavioural aggregates)
# ---------------------------------------------------------------------------

def _feat_baselines(customers: pd.DataFrame, baselines: pd.DataFrame) -> pd.DataFrame:
    f = customers[["customer_id"]].merge(baselines, on="customer_id", how="left")
    return f


# ---------------------------------------------------------------------------
# 11. Deviation from baseline
# ---------------------------------------------------------------------------

def _feat_deviation(
    feat_velocity: pd.DataFrame, baselines: pd.DataFrame
) -> pd.DataFrame:
    dev = feat_velocity[["customer_id", "total_volume", "txn_count_total"]].merge(
        baselines[
            ["customer_id", "avg_monthly_volume", "avg_monthly_transaction_count",
             "max_single_transaction_6m"]
        ],
        on="customer_id",
        how="left",
    )

    dev["baseline_annual_vol"]   = dev["avg_monthly_volume"] * 12
    dev["baseline_annual_count"] = dev["avg_monthly_transaction_count"] * 12

    # Ratio >1: customer is more active than their 6-month baseline suggests
    dev["vol_vs_baseline"]   = dev["total_volume"]       / (dev["baseline_annual_vol"]   + 1)
    dev["count_vs_baseline"] = dev["txn_count_total"]    / (dev["baseline_annual_count"] + 1)

    return dev[["customer_id", "vol_vs_baseline", "count_vs_baseline"]]


# ---------------------------------------------------------------------------
# 12. Transaction type mix
# ---------------------------------------------------------------------------

def _feat_type_mix(customers: pd.DataFrame, approved: pd.DataFrame) -> pd.DataFrame:
    type_counts = (
        approved.groupby(["customer_id", "transaction_type"])
        .size()
        .unstack(fill_value=0)
    )
    type_counts.columns = [f"txn_type_{c}" for c in type_counts.columns]
    type_counts = type_counts.reset_index()

    type_cols = [c for c in type_counts.columns if c.startswith("txn_type_")]
    row_totals = type_counts[type_cols].sum(axis=1)
    type_counts[type_cols] = type_counts[type_cols].div(row_totals, axis=0)

    f = customers[["customer_id"]].merge(type_counts, on="customer_id", how="left").fillna(0)
    return f


# ---------------------------------------------------------------------------
# Master builder
# ---------------------------------------------------------------------------

def build_features(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Assemble all feature groups into a single customer-level DataFrame and
    save it to data/features.parquet.
    """
    customers    = data["customers"]
    approved     = data["approved"]
    declined     = data["declined"]
    accounts     = data["accounts"]
    baselines    = data["baselines"]
    country_risk = data["country_risk"]

    feat_identity    = _feat_identity(customers)
    feat_income      = _feat_income(customers, baselines)
    feat_velocity    = _feat_velocity(customers, approved, declined)
    feat_structuring = _feat_structuring(customers, approved)
    feat_cash        = _feat_cash(customers, approved, feat_velocity)
    feat_counterparty= _feat_counterparty(customers, approved)
    feat_geo         = _feat_geo(customers, approved, country_risk)
    feat_accounts    = _feat_accounts(customers, accounts)
    feat_temporal    = _feat_temporal(customers, approved)
    feat_baselines   = _feat_baselines(customers, baselines)
    feat_deviation   = _feat_deviation(feat_velocity, baselines)
    feat_type_mix    = _feat_type_mix(customers, approved)

    feature_groups = [
        feat_identity, feat_income, feat_velocity, feat_structuring,
        feat_cash, feat_counterparty, feat_geo, feat_accounts,
        feat_temporal, feat_baselines, feat_deviation, feat_type_mix,
    ]

    spine = customers[["customer_id", "suspicious_activity_confirmed", "split"]].copy()

    features = spine
    for grp in feature_groups:
        features = features.merge(grp, on="customer_id", how="left")

    # Drop duplicate num_accounts columns if both feat_identity and feat_accounts contributed
    if "num_accounts_x" in features.columns and "num_accounts_y" in features.columns:
        features = features.rename(columns={"num_accounts_x": "num_accounts"})
        features = features.drop(columns=["num_accounts_y"])

    # Drop any remaining object columns (non-feature metadata), but keep split
    obj_cols = [
        c for c in features.columns
        if features[c].dtype == object and c not in {"customer_id", "split"}
    ]
    features = features.drop(columns=obj_cols)

    # Bool → int for sklearn
    bool_cols = features.select_dtypes(include="bool").columns.tolist()
    features[bool_cols] = features[bool_cols].astype(int)

    FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(FEATURES_PATH, index=False)

    feature_cols = [
        c for c in features.columns
        if c not in {"customer_id", "suspicious_activity_confirmed", "split"}
    ]
    print(f"Saved features.parquet — {len(features)} customers, {len(feature_cols)} features")
    return features


def get_feature_cols(features: pd.DataFrame) -> list[str]:
    return [
        c for c in features.columns
        if c not in {"customer_id", "suspicious_activity_confirmed", "split"}
        and features[c].dtype != object
    ]
