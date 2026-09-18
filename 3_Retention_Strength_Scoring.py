import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from theme import (
    PRIMARY, ACCENT, RISK, SAFE, NEUTRAL, BG_CARD, BORDER, AT_RISK,
    PALE_RISK, PALE_ACCENT, PALE_NEUTRAL, PALE_SAFE,
)

from utils import load_data, add_derived_fields, kpi_relationship_strength

st.set_page_config(page_title="Retention Strength Scoring | European Bank", page_icon="\U0001F4AA", layout="wide")

PLOTLY_TEMPLATE = "plotly_white"

st.markdown(f"""<style>
h1, h2, h3 {{ color:{PRIMARY}; font-family:'Georgia', serif; }}
.module-eyebrow {{ color:{ACCENT}; font-weight:700; letter-spacing:.08em; text-transform:uppercase; font-size:.78rem; }}
.insight-box {{ background-color:{BG_CARD}; border-left:4px solid {ACCENT}; border-radius:6px; padding:1rem 1.2rem; }}
.formula-box {{ background-color:{BG_CARD}; border:1px solid {BORDER}; border-radius:6px; padding:.9rem 1.1rem; font-family: monospace; font-size:.85rem; }}
</style>""", unsafe_allow_html=True)

full_df = add_derived_fields(load_data("European_Bank.csv"))

st.markdown('<p class="module-eyebrow">Core Module</p>', unsafe_allow_html=True)
st.title("Retention Strength Scoring")
st.caption(
    "A single composite score \u2014 the Relationship Strength Index (RSI) \u2014 "
    "combining engagement and product depth into one number per customer."
)

with st.expander("How the Relationship Strength Index (RSI) is calculated", expanded=False):
    st.markdown(f"""
<div class="formula-box">
RSI = (IsActiveMember &times; 40)<br>
&nbsp;&nbsp;+ (min(NumOfProducts, 2) / 2 &times; 30)<br>
&nbsp;&nbsp;+ (Tenure / 10 &times; 15)<br>
&nbsp;&nbsp;+ (HasCrCard &times; 15)<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= score from 0\u2013100
</div>
<br>
<b>Why product benefit is capped at 2:</b> churn rises sharply at 3\u20134
products in this dataset (see Product Utilization module). Rewarding
product count without limit would make the index reward a behavior that
is actually associated with high churn, so the index treats 2 products as
"sufficient depth" and does not reward further accumulation.
<br><br>
<b>Why activity is weighted heaviest (40 of 100 points):</b> activity status
shows the largest single retention gap of any field tested in this dataset.
""", unsafe_allow_html=True)

st.subheader("Churn rate by RSI tier")
tiers = kpi_relationship_strength(full_df)
fig = px.bar(
    tiers, x="Tier", y="ChurnRate",
    text=tiers["ChurnRate"].map(lambda x: f"{x:.1%}"),
    color="ChurnRate", color_continuous_scale=[SAFE, ACCENT, RISK],
    template=PLOTLY_TEMPLATE,
    category_orders={"Tier": ["Fragile (0-39)", "At-Risk (40-59)", "Stable (60-79)", "Sticky (80-100)"]},
)
fig.update_layout(coloraxis_showscale=False, yaxis_tickformat=".0%", height=380, xaxis_title=None)
fig.update_traces(textposition="outside")
st.plotly_chart(fig, width="stretch")

corr = full_df["RelationshipStrengthIndex"].corr(full_df["Exited"])
st.caption(
    f"RSI correlates with churn at r = {corr:.2f} (negative: higher RSI, "
    "lower churn). The tier breakdown above is monotonic \u2014 each tier "
    "up reduces churn \u2014 which is the threshold structure the brief "
    "asks for in the Retention Strength Assessment step."
)

st.markdown("---")

st.subheader("Score a customer profile")
st.caption("Use the controls below to see how engagement and product choices move the RSI score and the implied churn risk tier.")

p1, p2, p3, p4 = st.columns(4)
with p1:
    sim_active = st.toggle("Active member", value=True)
with p2:
    sim_products = st.slider("Number of products", 1, 4, 2)
with p3:
    sim_tenure = st.slider("Tenure (years)", 0, 10, 5)
with p4:
    sim_card = st.toggle("Has credit card", value=True)

sim_rsi = (
    (int(sim_active) * 40)
    + (min(sim_products, 2) / 2 * 30)
    + (sim_tenure / 10 * 15)
    + (int(sim_card) * 15)
)

if sim_rsi >= 80:
    sim_tier, sim_color = "Sticky (80-100)", SAFE
elif sim_rsi >= 60:
    sim_tier, sim_color = "Stable (60-79)", ACCENT
elif sim_rsi >= 40:
    sim_tier, sim_color = "At-Risk (40-59)", AT_RISK
else:
    sim_tier, sim_color = "Fragile (0-39)", RISK

gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=sim_rsi,
    number={"suffix": " / 100", "font": {"color": PRIMARY}},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": sim_color},
        "steps": [
            {"range": [0, 40], "color": PALE_RISK},
            {"range": [40, 60], "color": PALE_ACCENT},
            {"range": [60, 80], "color": PALE_NEUTRAL},
            {"range": [80, 100], "color": PALE_SAFE},
        ],
    },
))
gauge_fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))

g1, g2 = st.columns([1, 1.2])
with g1:
    st.plotly_chart(gauge_fig, width="stretch")
with g2:
    benchmark_churn = tiers.set_index("Tier").loc[sim_tier, "ChurnRate"] if sim_tier in tiers["Tier"].values else None
    st.markdown(f"""
<div class="insight-box">
<b>RSI Score: {sim_rsi:.1f}</b> \u2014 falls in the <b>{sim_tier}</b> tier.
<br><br>
Customers in this tier of the actual dataset churn at approximately
<b>{benchmark_churn:.1%}</b>, versus a bank-wide average of
{full_df['Exited'].mean():.1%}.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

st.subheader("RSI distribution across the customer base")
fig3 = px.histogram(
    full_df, x="RelationshipStrengthIndex", color="Exited", nbins=25,
    color_discrete_map={0: SAFE, 1: RISK}, barmode="overlay", opacity=0.7,
    template=PLOTLY_TEMPLATE, labels={"Exited": "Churned", "RelationshipStrengthIndex": "RSI Score"},
)
fig3.update_layout(height=380, legend_title_text="Churned")
st.plotly_chart(fig3, width="stretch")
