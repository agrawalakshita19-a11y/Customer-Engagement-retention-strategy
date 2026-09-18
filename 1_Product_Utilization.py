import streamlit as st
import pandas as pd
import plotly.express as px
from theme import PRIMARY, ACCENT, RISK, SAFE, BG_CARD

from utils import load_data, add_derived_fields, kpi_product_depth

st.set_page_config(page_title="Product Utilization | European Bank", page_icon="\U0001F4E6", layout="wide")

PLOTLY_TEMPLATE = "plotly_white"

st.markdown(f"""<style>
h1, h2, h3 {{ color:{PRIMARY}; font-family:'Georgia', serif; }}
.module-eyebrow {{ color:{ACCENT}; font-weight:700; letter-spacing:.08em; text-transform:uppercase; font-size:.78rem; }}
.insight-box {{ background-color:{BG_CARD}; border-left:4px solid {ACCENT}; border-radius:6px; padding:1rem 1.2rem; }}
</style>""", unsafe_allow_html=True)

full_df = add_derived_fields(load_data("European_Bank.csv"))

st.sidebar.header("Product Filters")
prod_select = st.sidebar.multiselect(
    "Number of products", options=sorted(full_df["NumOfProducts"].unique()),
    default=sorted(full_df["NumOfProducts"].unique())
)
geo_select = st.sidebar.multiselect(
    "Geography", options=sorted(full_df["Geography"].unique()),
    default=sorted(full_df["Geography"].unique())
)

df = full_df[full_df["NumOfProducts"].isin(prod_select) & full_df["Geography"].isin(geo_select)]
if len(df) == 0:
    st.warning("No customers match this filter combination.")
    st.stop()

st.markdown('<p class="module-eyebrow">Core Module</p>', unsafe_allow_html=True)
st.title("Product Utilization Impact Analysis")
st.caption(
    "Does holding more products make a customer stickier? The data says: "
    "only up to a point \u2014 and then sharply not."
)

pdi = kpi_product_depth(df)
st.subheader("Churn rate by number of products held")

fig = px.bar(
    pdi, x="NumOfProducts", y="ChurnRate",
    text=pdi["ChurnRate"].map(lambda x: f"{x:.1%}"),
    color="ChurnRate", color_continuous_scale=[SAFE, ACCENT, RISK],
    template=PLOTLY_TEMPLATE,
)
fig.update_layout(
    coloraxis_showscale=False, yaxis_tickformat=".0%",
    xaxis=dict(tickmode="linear", title="Number of products"),
    yaxis_title="Churn rate", height=380,
)
fig.update_traces(textposition="outside")
st.plotly_chart(fig, width="stretch")

two_plus = pdi[pdi.NumOfProducts == 2]["ChurnRate"].values
one_val = pdi[pdi.NumOfProducts == 1]["ChurnRate"].values
three_plus_n = df[df.NumOfProducts >= 3].shape[0]
three_plus_churn = df[df.NumOfProducts >= 3]["Exited"].mean() if three_plus_n else float("nan")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f"""
<div class="insight-box">
<b>Two products is the retention sweet spot.</b> Single-product customers churn
at {one_val[0]:.1%} if shown, while two-product customers churn at the lowest
rate in the dataset ({two_plus[0]:.1%} if shown). Beyond two products, churn
rises sharply \u2014 customers holding 3 or more products churn at
{three_plus_churn:.1%} (n={three_plus_n:,}).
<br><br>
This is <b>not</b> a simple "more products = more loyalty" story. It looks
more like two distinct populations: customers who <i>chose</i> a second
product (genuine cross-sell success), versus customers pushed into 3-4
products \u2014 possibly via aggressive bundling, complaint resolution offers,
or product consolidation after a service issue \u2014 who are leaving anyway.
</div>
""", unsafe_allow_html=True)

with col2:
    st.subheader("Single vs. multi-product retention")
    df["ProductTier"] = df["NumOfProducts"].apply(lambda x: "Single product" if x == 1 else "Multi-product (2+)")
    tier_churn = df.groupby("ProductTier")["Exited"].agg(["mean", "count"])
    fig2 = px.bar(
        tier_churn.reset_index(), x="ProductTier", y="mean",
        text=tier_churn["mean"].map(lambda x: f"{x:.1%}").values,
        color="ProductTier", color_discrete_map={"Single product": ACCENT, "Multi-product (2+)": PRIMARY},
        template=PLOTLY_TEMPLATE, labels={"mean": "Churn rate", "ProductTier": ""},
    )
    fig2.update_layout(showlegend=False, yaxis_tickformat=".0%", height=320)
    fig2.update_traces(textposition="outside")
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")

st.subheader("Product depth and engagement, combined")
st.caption("Does activity status change the product-count story? Yes — and the cliff at 3-4 products holds regardless of activity.")

cross = df.groupby(["NumOfProducts", "IsActiveMember"])["Exited"].mean().reset_index()
cross["Activity"] = cross["IsActiveMember"].map({0: "Inactive", 1: "Active"})
fig3 = px.bar(
    cross, x="NumOfProducts", y="Exited", color="Activity", barmode="group",
    color_discrete_map={"Active": SAFE, "Inactive": RISK},
    template=PLOTLY_TEMPLATE, labels={"Exited": "Churn rate", "NumOfProducts": "Number of products"},
)
fig3.update_layout(yaxis_tickformat=".0%", height=380, xaxis=dict(tickmode="linear"))
st.plotly_chart(fig3, width="stretch")

st.markdown("---")

with st.expander("View underlying product-tier data table"):
    st.dataframe(
        pdi.style.format({"ChurnRate": "{:.1%}", "RetentionRate": "{:.1%}", "Customers": "{:,}"}),
        width="stretch",
    )
