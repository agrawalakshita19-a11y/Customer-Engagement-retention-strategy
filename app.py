import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from theme import (
    PRIMARY, ACCENT, RISK, SAFE, NEUTRAL, BG_CARD, BG_PAGE, SIDEBAR_TEXT,
)

from utils import (
    load_data,
    add_derived_fields,
    kpi_engagement_retention_ratio,
    kpi_product_depth,
    kpi_high_balance_disengagement,
    kpi_credit_card_stickiness,
    kpi_relationship_strength,
)

st.set_page_config(
    page_title="Retention Intelligence | European Bank",
    page_icon="\U0001F3E6",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = f"""
<style>
    .stApp {{
        background-color: {BG_PAGE};
    }}
    [data-testid="stSidebar"] {{
        background-color: {PRIMARY};
    }}
    [data-testid="stSidebar"] * {{
        color: {SIDEBAR_TEXT} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 1.9rem;
        color: {PRIMARY};
    }}
    [data-testid="stMetricLabel"] {{
        font-weight: 600;
        color: {NEUTRAL};
    }}
    .kpi-card {{
        background-color: {BG_CARD};
        border-left: 4px solid {ACCENT};
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
    }}
    h1, h2, h3 {{
        color: {PRIMARY};
        font-family: 'Georgia', serif;
    }}
    .module-eyebrow {{
        color: {ACCENT};
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.78rem;
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_white"
COLOR_RISK_SAFE = {0: SAFE, 1: RISK}

raw_df = load_data("European_Bank.csv")
full_df = add_derived_fields(raw_df)

st.sidebar.markdown("## \U0001F3E6 European Bank")
st.sidebar.markdown("**Retention Intelligence Platform**")
st.sidebar.markdown("---")
st.sidebar.markdown("### Engagement Filters")

geo_filter = st.sidebar.multiselect(
    "Geography", options=sorted(full_df["Geography"].unique()),
    default=sorted(full_df["Geography"].unique())
)
gender_filter = st.sidebar.multiselect(
    "Gender", options=sorted(full_df["Gender"].unique()),
    default=sorted(full_df["Gender"].unique())
)
activity_filter = st.sidebar.radio(
    "Activity status", options=["All", "Active only", "Inactive only"], index=0
)
product_range = st.sidebar.slider(
    "Number of products", min_value=int(full_df["NumOfProducts"].min()),
    max_value=int(full_df["NumOfProducts"].max()),
    value=(int(full_df["NumOfProducts"].min()), int(full_df["NumOfProducts"].max()))
)
balance_range = st.sidebar.slider(
    "Balance range (€)", min_value=float(full_df["Balance"].min()),
    max_value=float(full_df["Balance"].max()),
    value=(float(full_df["Balance"].min()), float(full_df["Balance"].max())),
    step=1000.0, format="€%.0f"
)
salary_range = st.sidebar.slider(
    "Estimated salary range (€)", min_value=float(full_df["EstimatedSalary"].min()),
    max_value=float(full_df["EstimatedSalary"].max()),
    value=(float(full_df["EstimatedSalary"].min()), float(full_df["EstimatedSalary"].max())),
    step=1000.0, format="€%.0f"
)
age_range = st.sidebar.slider(
    "Age range", min_value=int(full_df["Age"].min()), max_value=int(full_df["Age"].max()),
    value=(int(full_df["Age"].min()), int(full_df["Age"].max()))
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Dataset: European_Bank.csv \u2014 10,000 customers across France, "
    "Germany, and Spain. Filters apply to every module below."
)

df = full_df[
    full_df["Geography"].isin(geo_filter)
    & full_df["Gender"].isin(gender_filter)
    & full_df["NumOfProducts"].between(product_range[0], product_range[1])
    & full_df["Balance"].between(balance_range[0], balance_range[1])
    & full_df["EstimatedSalary"].between(salary_range[0], salary_range[1])
    & full_df["Age"].between(age_range[0], age_range[1])
].copy()

if activity_filter == "Active only":
    df = df[df["IsActiveMember"] == 1]
elif activity_filter == "Inactive only":
    df = df[df["IsActiveMember"] == 0]

if len(df) == 0:
    st.warning("No customers match the current filter combination. Loosen a filter in the sidebar to see results.")
    st.stop()

st.markdown('<p class="module-eyebrow">Engagement vs Churn Overview</p>', unsafe_allow_html=True)
st.title("Customer Retention Intelligence")
st.caption(
    f"Showing **{len(df):,}** of {len(full_df):,} customers based on current filters. "
    "Other modules are in the sidebar navigation above this page."
)

overall_churn = df["Exited"].mean()
err = kpi_engagement_retention_ratio(df)
hbd = kpi_high_balance_disengagement(df)
ccss = kpi_credit_card_stickiness(df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Customers in view", f"{len(df):,}")
c2.metric("Overall churn rate", f"{overall_churn:.1%}")
c3.metric("Engagement Retention Ratio", f"{err['ratio']:.2f}\u00d7",
          help="Retention rate of active members \u00f7 retention rate of inactive members. >1 means active members retain better.")
c4.metric("High-Balance Disengagement Rate", f"{hbd['rate']:.1%}",
          help="Share of above-median-balance customers who are inactive.")
c5.metric("Credit Card Stickiness Score", f"{ccss['score']:.2f}\u00d7",
          help="Retention rate of card holders \u00f7 retention rate of non-holders.")

st.markdown("---")

left, right = st.columns([1.1, 1])

with left:
    st.subheader("Churn rate by engagement profile")
    profile_order = [
        "Active Engaged", "Active, Low-Product",
        "Inactive Disengaged", "Inactive, High-Balance",
    ]
    prof_summary = (
        df.groupby("EngagementProfile")["Exited"]
        .agg(["mean", "count"]).reindex(profile_order).reset_index()
    )
    prof_summary.columns = ["Profile", "ChurnRate", "Customers"]
    prof_summary = prof_summary.dropna()

    fig = px.bar(
        prof_summary, x="ChurnRate", y="Profile", orientation="h",
        text=prof_summary["ChurnRate"].map(lambda x: f"{x:.1%}"),
        color="ChurnRate", color_continuous_scale=[SAFE, ACCENT, RISK],
        template=PLOTLY_TEMPLATE,
    )
    fig.update_layout(
        showlegend=False, coloraxis_showscale=False,
        xaxis_tickformat=".0%", yaxis_title=None, xaxis_title="Churn rate",
        height=320, margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "**Active Engaged** customers (active + 2+ products) churn least. "
        "**Inactive, High-Balance** customers churn most \u2014 this is the "
        "silent-churn risk pool the brief calls out."
    )

with right:
    st.subheader("Engagement mix")
    mix = df["EngagementProfile"].value_counts().reindex(profile_order).dropna()
    fig2 = go.Figure(data=[go.Pie(
        labels=mix.index, values=mix.values, hole=0.55,
        marker=dict(colors=[SAFE, ACCENT, NEUTRAL, RISK]),
        textinfo="label+percent",
    )])
    fig2.update_layout(
        showlegend=False, height=320,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")

st.subheader("Activity status: the single strongest engagement signal")
act_col1, act_col2 = st.columns(2)

with act_col1:
    act_churn = df.groupby("IsActiveMember")["Exited"].mean()
    act_churn.index = act_churn.index.map({0: "Inactive", 1: "Active"})
    fig3 = px.bar(
        x=act_churn.index, y=act_churn.values,
        text=[f"{v:.1%}" for v in act_churn.values],
        color=act_churn.index, color_discrete_map={"Active": SAFE, "Inactive": RISK},
        template=PLOTLY_TEMPLATE, labels={"x": "", "y": "Churn rate"},
    )
    fig3.update_layout(showlegend=False, yaxis_tickformat=".0%", height=300,
                        margin=dict(l=10, r=10, t=30, b=10))
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, width="stretch")

with act_col2:
    st.markdown(
        f"""
<div class="kpi-card">
<b>Active members retain at {err['retention_active']:.1%}</b>, compared with
<b>{err['retention_inactive']:.1%} for inactive members</b> \u2014 a retention
gap of {(err['retention_active']-err['retention_inactive'])*100:.1f} points.
<br><br>
This single behavioral signal separates customers more cleanly than any
demographic field in the dataset, supporting the project's core thesis:
<i>engagement, not balance or salary, is the leading indicator of retention.</i>
</div>
""", unsafe_allow_html=True,
    )

st.markdown("---")
st.caption(
    "Navigate to **Product Utilization**, **High-Value Disengaged Detector**, "
    "and **Retention Strength Scoring** using the sidebar page list above "
    "the filters."
)
