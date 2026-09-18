

import os
import sys
import streamlit as st

# Keep local application packages importable when Streamlit runs from a deployed path.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


from styles.theme import inject_css, SEG_COLORS, GREEN, MUTED
from utils.data_loader import load_clustered, load_properties, DataLoadError
from utils.formatters import fmt_currency, fmt_count
from components.filters import render_filters
from components.kpi_cards import render_kpis
from components import charts

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Parcl · Buyer Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Load data ─────────────────────────────────────────────────────────
try:
    df    = load_clustered("clustered.csv")
    props = load_properties("properties.csv")
except DataLoadError as exc:
    st.error(str(exc))
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────
filtered = render_filters(df)

# ── Header ────────────────────────────────────────────────────────────
# Extra top spacer pushes content fully clear of Streamlit's toolbar.
st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

h1, h2 = st.columns([5, 1])
with h1:
    st.markdown(
        '<p style="font-size:1.65rem; font-weight:800; color:#FFFFFF; '
        'letter-spacing:-0.025em; margin:0 0 0.15rem 0; line-height:1.2;">'
        'Buyer Segmentation &amp; '
        '<span style="color:#00D97E;">Investment Profiling</span>'
        '</p>'
        '<p style="font-size:0.84rem; color:#888888; margin:0;">'
        'Parcl Real Estate Market Intelligence&nbsp;·&nbsp;'
        'Machine Learning Cluster Analysis&nbsp;·&nbsp;2,000 Buyers'
        '</p>',
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        '<div style="display:flex; justify-content:flex-end; '
        'align-items:center; height:100%; padding-top:0.4rem;">'
        '<span style="background:#00D97E; color:#000; font-size:0.68rem; '
        'font-weight:700; padding:0.25rem 0.85rem; border-radius:20px; '
        'letter-spacing:0.05em;">AI-Powered</span>'
        '</div>',
        unsafe_allow_html=True,
    )
st.markdown(
    '<hr style="border:none; border-top:1px solid #2A2A2A; '
    'margin:1rem 0 1.5rem 0;">',
    unsafe_allow_html=True,
)

# ── KPI row ───────────────────────────────────────────────────────────
render_kpis(filtered, props)
st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Segmentation Overview",
    "Investor Behaviour",
    "Geographic Analysis",
    "Segment Insights",
])

# ── Tab 1: Segmentation Overview ──────────────────────────────────────
with tab1:
    col1, col2 = st.columns([1.1, 1])
    with col1:
        charts._card("Buyer Segment Distribution",
                     "K-Means clustering (K=6) identifies six distinct buyer archetypes")
        charts.segment_donut(filtered)
        charts._end()
    with col2:
        charts._card("Segment Size Ranking",
                     "Mid-Market Buyers dominate volume; Portfolio Investors are fewest but highest-value")
        charts.segment_bar(filtered)
        charts._end()

    col3, col4 = st.columns(2)
    with col3:
        charts._card("Acquisition Purpose by Segment",
                     "Investment vs. home purchase split within each buyer archetype")
        charts.purpose_by_segment(filtered)
        charts._end()
    with col4:
        charts._card("Loan Behaviour by Segment",
                     "Financing dependency across buyer types — green = loan applied")
        charts.loan_by_segment(filtered)
        charts._end()

    # Segment legend pills
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    st.markdown("**Segment Key**", unsafe_allow_html=False)
    pills = " ".join(
        f'<span class="seg-pill" style="background:{c}22; color:{c}; border:1px solid {c}66;">{s}</span>'
        for s, c in SEG_COLORS.items()
    )
    st.markdown(pills, unsafe_allow_html=True)

# ── Tab 2: Investor Behaviour ─────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        charts._card("Average Portfolio Spend by Segment",
                     "Portfolio Investors outspend all other segments by 2×+")
        charts.spend_by_segment(filtered)
        charts._end()
    with col2:
        charts._card("Average Units Purchased",
                     "Portfolio Investors acquire 7-8 units vs 3-4 for typical buyers")
        charts.units_by_segment(filtered)
        charts._end()

    charts._card("Price vs. Floor Area by Segment",
                 "Luxury Buyers cluster at high price per sqft; Corporate Buyers spread across area ranges")
    charts.price_vs_area_scatter(filtered)
    charts._end()

    col3, col4 = st.columns(2)
    with col3:
        charts._card("Customer Satisfaction by Segment",
                     "Portfolio Investors rate highest — high-touch service matches high-value relationships")
        charts.satisfaction_segment(filtered)
        charts._end()
    with col4:
        charts._card("Buyer Acquisition by Referral Channel",
                     "Website dominates; Agency brings in higher proportion of premium segments")
        charts.referral_channel(filtered)
        charts._end()

# ── Tab 3: Geographic Analysis ────────────────────────────────────────
with tab3:
    col1, col2 = st.columns([1.2, 1])
    with col1:
        charts._card("Buyer Count by Country",
                     "USA is the dominant buyer market; Canada and Germany are next-largest")
        charts.country_bar(filtered)
        charts._end()
    with col2:
        charts._card("Average Spend by Country",
                     "International buyers from smaller markets often carry higher individual spend")
        charts.spend_by_country(filtered)
        charts._end()

    charts._card("Segment × Country Heatmap",
                 "Distribution of buyer archetypes across the top 8 markets")
    charts.geo_segment_heatmap(filtered)
    charts._end()

    charts._card("Age Distribution by Segment",
                 "Portfolio Investors skew older (avg 62); Corporate Buyers are youngest cohort (avg 46)")
    charts.age_by_segment(filtered)
    charts._end()

# ── Tab 4: Segment Insights ───────────────────────────────────────────
with tab4:
    st.markdown(
        "<p style='color:#888; font-size:0.83rem; margin-bottom:1rem;'>"
        "Normalised radar chart compares segments across six dimensions. "
        "Values scaled 0–1 within each axis so shape shows relative strength, not absolute magnitude.</p>",
        unsafe_allow_html=True,
    )
    charts._card("Segment Profile Radar",
                 "Shape comparison: broader polygon = stronger across more dimensions")
    charts.segment_radar(filtered)
    charts._end()

    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

    # Per-segment stat cards
    st.markdown("**Segment Summary Statistics**", unsafe_allow_html=False)
    segs = filtered["segment_name"].unique()
    rows = [segs[i:i+3] for i in range(0, len(segs), 3)]
    for row in rows:
        cols = st.columns(len(row))
        for col, seg in zip(cols, row):
            sub = filtered[filtered["segment_name"] == seg]
            color = SEG_COLORS.get(seg, "#888")
            with col:
                st.markdown(f"""
                <div class="card">
                    <div style="color:{color}; font-size:0.8rem; font-weight:700;
                                text-transform:uppercase; letter-spacing:0.06em;
                                margin-bottom:0.5rem;">{seg}</div>
                    <table style="width:100%; font-size:0.78rem; border-collapse:collapse;">
                        <tr><td style="color:#888; padding:2px 0;">Buyers</td>
                            <td style="color:#fff; text-align:right;">{len(sub):,}</td></tr>
                        <tr><td style="color:#888; padding:2px 0;">Avg Spend</td>
                            <td style="color:#fff; text-align:right;">{fmt_currency(sub['total_spend'].mean())}</td></tr>
                        <tr><td style="color:#888; padding:2px 0;">Avg Units</td>
                            <td style="color:#fff; text-align:right;">{sub['total_units'].mean():.1f}</td></tr>
                        <tr><td style="color:#888; padding:2px 0;">Avg Age</td>
                            <td style="color:#fff; text-align:right;">{sub['age'].mean():.0f} yrs</td></tr>
                        <tr><td style="color:#888; padding:2px 0;">Loan Rate</td>
                            <td style="color:#fff; text-align:right;">{sub['loan_applied'].eq('Yes').mean()*100:.0f}%</td></tr>
                        <tr><td style="color:#888; padding:2px 0;">Satisfaction</td>
                            <td style="color:#fff; text-align:right;">{sub['satisfaction_score'].mean():.2f}/5</td></tr>
                    </table>
                </div>""", unsafe_allow_html=True)

    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

    # Drill-down table
    charts._card("Buyer Drill-Down",
                 "Full client list for the current filter selection — sorted by total spend")
    if filtered.empty:
        st.info("No buyers match the current selection.")
    else:
        display_cols = ["client_id","segment_name","client_type","country","region",
                       "acquisition_purpose","age","total_units","total_spend",
                       "avg_price","loan_applied","satisfaction_score"]
        disp = filtered[display_cols].copy()
        disp["total_spend"] = disp["total_spend"].apply(lambda x: f"${x:,.0f}")
        disp["avg_price"]   = disp["avg_price"].apply(lambda x: f"${x:,.0f}")
        disp["age"]         = disp["age"].apply(lambda x: f"{x:.0f}")
        st.dataframe(
            disp.sort_values("total_spend", ascending=False),
            width="stretch", height=360,
        )
    charts._end()

st.markdown(
    "<p style='color:#555; font-size:0.74rem; text-align:center; margin-top:2rem;'>"
    "Parcl Buyer Intelligence Platform · K-Means Clustering (K=6) · "
    "2,000 Clients × 10,000 Property Transactions</p>",
    unsafe_allow_html=True,
)
