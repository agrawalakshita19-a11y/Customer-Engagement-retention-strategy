import streamlit as st
import pandas as pd
import plotly.express as px
from theme import PRIMARY, ACCENT, RISK, SAFE, BG_CARD

from utils import load_data, add_derived_fields, get_at_risk_premium_customers

st.set_page_config(page_title="Disengaged Customer Detector | European Bank", page_icon="\U0001F50D", layout="wide")

PLOTLY_TEMPLATE = "plotly_white"

st.markdown(f"""<style>
h1, h2, h3 {{ color:{PRIMARY}; font-family:'Georgia', serif; }}
.module-eyebrow {{ color:{ACCENT}; font-weight:700; letter-spacing:.08em; text-transform:uppercase; font-size:.78rem; }}
.insight-box {{ background-color:{BG_CARD}; border-left:4px solid {RISK}; border-radius:6px; padding:1rem 1.2rem; }}
</style>""", unsafe_allow_html=True)

full_df = add_derived_fields(load_data("European_Bank.csv"))

st.markdown('<p class="module-eyebrow">Core Module</p>', unsafe_allow_html=True)
st.title("High-Value Disengaged Customer Detector")
st.caption(
    "Customers who look financially strong on paper but show no active "
    "relationship with the bank \u2014 the highest silent-churn risk."
)

st.subheader("Define \u201cpremium\u201d and \u201cdisengaged\u201d for this search")
c1, c2, c3 = st.columns(3)
with c1:
    balance_pct = st.slider(
        "Balance percentile threshold", min_value=50, max_value=99, value=50, step=5,
        help="Customers above this balance percentile are considered high-balance."
    )
with c2:
    salary_pct = st.slider(
        "Salary percentile threshold", min_value=0, max_value=99, value=0, step=5,
        help="Set above 0 to also require high estimated salary, not just high balance."
    )
with c3:
    activity_req = st.selectbox(
        "Engagement requirement", options=["Inactive only", "Active or inactive"], index=0
    )

balance_cut = full_df["Balance"].quantile(balance_pct / 100)
salary_cut = full_df["EstimatedSalary"].quantile(salary_pct / 100)

mask = (full_df["Balance"] > balance_cut) & (full_df["EstimatedSalary"] > salary_cut)
if activity_req == "Inactive only":
    mask &= full_df["IsActiveMember"] == 0

detected = full_df[mask].copy()
detected = detected.sort_values("Balance", ascending=False)

st.markdown("---")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Customers detected", f"{len(detected):,}")
m2.metric("Share of full customer base", f"{len(detected)/len(full_df):.1%}")
m3.metric("Churn rate in this segment", f"{detected['Exited'].mean():.1%}" if len(detected) else "\u2014")
m4.metric("Total balance at risk", f"\u20ac{detected['Balance'].sum():,.0f}")

if len(detected) == 0:
    st.info("No customers match these thresholds. Loosen the percentile cutoffs above.")
    st.stop()

st.markdown(f"""
<div class="insight-box">
At default thresholds (balance above median, fully inactive), <b>{(full_df['AtRiskPremium'].sum()):,} customers</b>
({full_df['AtRiskPremium'].mean():.1%} of the base) qualify as at-risk premium
customers, churning at <b>{full_df.loc[full_df.AtRiskPremium, 'Exited'].mean():.1%}</b> \u2014
well above the bank-wide average of {full_df['Exited'].mean():.1%}. These
customers are not flight risks because they lack means; they are flight
risks because the bank has stopped earning their attention.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

left, right = st.columns([1.1, 1])
with left:
    st.subheader("Where are they?")
    geo_dist = detected["Geography"].value_counts().reset_index()
    geo_dist.columns = ["Geography", "Customers"]
    fig = px.bar(
        geo_dist, x="Geography", y="Customers", color="Geography",
        color_discrete_sequence=[PRIMARY, ACCENT, RISK],
        template=PLOTLY_TEMPLATE,
    )
    fig.update_layout(showlegend=False, height=320)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Balance distribution of detected segment")
    fig2 = px.histogram(
        detected, x="Balance", nbins=30, color_discrete_sequence=[RISK],
        template=PLOTLY_TEMPLATE,
    )
    fig2.update_layout(height=320, yaxis_title="Customers")
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")

st.subheader("Salary\u2013balance mismatch: high earners parking little with this bank")
mismatch_n = full_df["SalaryBalanceMismatch"].sum()
mismatch_churn = full_df.loc[full_df["SalaryBalanceMismatch"], "Exited"].mean() if mismatch_n else float("nan")
st.caption(
    f"{mismatch_n:,} customers earn above-median salary but hold a zero "
    f"balance with the bank \u2014 churning at {mismatch_churn:.1%}. These "
    "customers likely treat this bank as secondary, with their primary "
    "relationship elsewhere."
)

st.markdown("---")
st.subheader("Detected customer list")
st.caption("Sorted by balance, descending. Use this list to prioritize outreach.")

display_cols = [
    "CustomerId", "Surname", "Geography", "Age", "Tenure", "Balance",
    "EstimatedSalary", "NumOfProducts", "HasCrCard", "IsActiveMember",
    "RelationshipStrengthIndex", "RSI_Tier", "Exited",
]
st.dataframe(
    detected[display_cols].style.format({
        "Balance": "\u20ac{:,.0f}", "EstimatedSalary": "\u20ac{:,.0f}",
        "RelationshipStrengthIndex": "{:.1f}",
    }),
    width="stretch", height=420,
)

csv = detected[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    "Download detected segment as CSV", data=csv,
    file_name="at_risk_premium_customers.csv", mime="text/csv",
)
