import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def load_data(path: str = "European_Bank.csv") -> pd.DataFrame:
    """Load and validate the bank customer dataset."""
    df = pd.read_csv(path)

    expected_binary = ["HasCrCard", "IsActiveMember", "Exited"]
    for col in expected_binary:
        bad = ~df[col].isin([0, 1])
        if bad.any():
            df = df[~bad]

    expected_geo = {"France", "Spain", "Germany"}
    df = df[df["Geography"].isin(expected_geo)]

    expected_gender = {"Male", "Female"}
    df = df[df["Gender"].isin(expected_gender)]

    df = df[(df["Age"] >= 18) & (df["Age"] <= 100)]
    df = df[df["NumOfProducts"].between(1, 4)]
    df = df[df["Balance"] >= 0]
    df = df[df["EstimatedSalary"] >= 0]

    df = df.drop_duplicates(subset="CustomerId")

    df = df.reset_index(drop=True)
    return df


def add_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add engagement profile, financial segments, and the Relationship
    Strength Index (RSI) to the dataframe. Pure function — does not mutate
    the cached original."""
    df = df.copy()

    median_balance = df["Balance"].median()
    median_salary = df["EstimatedSalary"].median()

    df["HasBalance"] = df["Balance"] > 0
    df["HighBalance"] = df["Balance"] > median_balance
    df["HighSalary"] = df["EstimatedSalary"] > median_salary
    df["LowProduct"] = df["NumOfProducts"] == 1
    df["MultiProduct"] = df["NumOfProducts"] >= 2
    df["OverLeveragedProduct"] = df["NumOfProducts"] >= 3  # churn-cliff zone

    def classify(row):
        active = row["IsActiveMember"] == 1
        if active and row["MultiProduct"]:
            return "Active Engaged"
        if active and row["LowProduct"]:
            return "Active, Low-Product"
        if (not active) and row["HighBalance"]:
            return "Inactive, High-Balance"
        return "Inactive Disengaged"

    df["EngagementProfile"] = df.apply(classify, axis=1)

    df["SalaryBalanceMismatch"] = df["HighSalary"] & (~df["HasBalance"])

    df["AtRiskPremium"] = (
        df["HighBalance"] & df["HighSalary"] & (df["IsActiveMember"] == 0)
    )

    df["RelationshipStrengthIndex"] = (
        (df["IsActiveMember"] * 40)
        + (df["NumOfProducts"].clip(upper=2) / 2 * 30)
        + (df["Tenure"] / 10 * 15)
        + (df["HasCrCard"] * 15)
    ).round(1)

    def rsi_tier(score):
        if score >= 80:
            return "Sticky (80-100)"
        elif score >= 60:
            return "Stable (60-79)"
        elif score >= 40:
            return "At-Risk (40-59)"
        else:
            return "Fragile (0-39)"

    df["RSI_Tier"] = df["RelationshipStrengthIndex"].apply(rsi_tier)

    return df

def kpi_engagement_retention_ratio(df: pd.DataFrame) -> dict:
    """Retention rate of active members vs inactive members (ratio > 1
    means active members retain better)."""
    ret_active = 1 - df.loc[df.IsActiveMember == 1, "Exited"].mean()
    ret_inactive = 1 - df.loc[df.IsActiveMember == 0, "Exited"].mean()
    ratio = ret_active / ret_inactive if ret_inactive > 0 else np.nan
    return {
        "ratio": ratio,
        "retention_active": ret_active,
        "retention_inactive": ret_inactive,
    }


def kpi_product_depth(df: pd.DataFrame) -> pd.DataFrame:
    """Churn and retention rate by number of products held."""
    g = df.groupby("NumOfProducts")["Exited"].agg(["mean", "count"]).reset_index()
    g.columns = ["NumOfProducts", "ChurnRate", "Customers"]
    g["RetentionRate"] = 1 - g["ChurnRate"]
    return g


def kpi_high_balance_disengagement(df: pd.DataFrame) -> dict:
    """Of high-balance customers, what fraction are inactive (disengaged)?
    And what is the churn rate within that disengaged-premium group?"""
    hb = df[df["HighBalance"]]
    if len(hb) == 0:
        return {"rate": np.nan, "segment_churn": np.nan, "segment_n": 0}
    disengaged = hb[hb["IsActiveMember"] == 0]
    rate = len(disengaged) / len(hb)
    seg_churn = disengaged["Exited"].mean() if len(disengaged) else np.nan
    return {"rate": rate, "segment_churn": seg_churn, "segment_n": len(disengaged)}


def kpi_credit_card_stickiness(df: pd.DataFrame) -> dict:
    """Retention rate of card holders vs non-holders."""
    ret_card = 1 - df.loc[df.HasCrCard == 1, "Exited"].mean()
    ret_nocard = 1 - df.loc[df.HasCrCard == 0, "Exited"].mean()
    score = ret_card / ret_nocard if ret_nocard > 0 else np.nan
    return {"score": score, "retention_card": ret_card, "retention_nocard": ret_nocard}


def kpi_relationship_strength(df: pd.DataFrame) -> pd.DataFrame:
    """Churn rate by RSI tier — should be monotonically decreasing if the
    index is well-constructed."""
    order = ["Fragile (0-39)", "At-Risk (40-59)", "Stable (60-79)", "Sticky (80-100)"]
    g = df.groupby("RSI_Tier")["Exited"].agg(["mean", "count"]).reindex(order).reset_index()
    g.columns = ["Tier", "ChurnRate", "Customers"]
    return g


def get_at_risk_premium_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Return the high-value disengaged customer detector result set."""
    cols = [
        "CustomerId", "Surname", "Geography", "Age", "Tenure",
        "Balance", "EstimatedSalary", "NumOfProducts", "HasCrCard",
        "IsActiveMember", "RelationshipStrengthIndex", "RSI_Tier", "Exited",
    ]
    return df[df["AtRiskPremium"]][cols].sort_values("Balance", ascending=False)
