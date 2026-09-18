import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_gen.generator import END_DATE, START_DATE, load_data
from theme.charts import COLOR_BLOCKCHAIN, COLOR_BRIDGE, SYMBOL_COLORS, STATUS, apply_default_layout, register_template
from theme.style import inject_css, kpi_grid, period_badge, section_header

st.set_page_config(page_title="Blockchain · PixFlow", layout="wide", page_icon="🔗")
inject_css()
register_template()

st.title("🔗 Blockchain & Bridge")

data = load_data()
chain = data["chain"].copy()

st.sidebar.header("Filters")
symbol_options = ["All"] + sorted(chain["symbol"].unique().tolist())
symbol_sel = st.sidebar.selectbox("Symbol", symbol_options)
type_options = ["All", "BLOCKCHAIN", "BRIDGE"]
type_sel = st.sidebar.selectbox("Type", type_options)
status_options = ["All"] + sorted(chain["status"].unique().tolist())
status_sel = st.sidebar.selectbox("Status", status_options)
date_range = st.sidebar.date_input("Date range", value=(START_DATE, END_DATE),
                                    min_value=START_DATE, max_value=END_DATE)
start, end = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (START_DATE, END_DATE)
if start > end:
    start, end = end, start

df = chain[(chain["timestamp"].dt.date >= start) & (chain["timestamp"].dt.date <= end)]
if symbol_sel != "All":
    df = df[df["symbol"] == symbol_sel]
if type_sel != "All":
    df = df[df["type"] == type_sel]
if status_sel != "All":
    df = df[df["status"] == status_sel]

df["month"] = df["timestamp"].dt.to_period("M")
df["year"] = df["timestamp"].dt.year
df["month_num"] = df["timestamp"].dt.month

period_badge(f"{start:%m/%d/%Y} — {end:%m/%d/%Y}")

kpi_grid(
    [
        {"icon": "💠", "label": "Total value", "value": f"{df['value'].sum():,.0f}"},
        {"icon": "🧮", "label": "Average value", "value": f"{df['value'].mean():,.2f}" if len(df) else "0.00"},
        {"icon": "⛽", "label": "Total fee", "value": f"{df['tx_fee'].sum():,.2f}"},
        {"icon": "🔢", "label": "Transactions", "value": f"{len(df):,}"},
    ]
)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔄 Year-over-Year", "🧪 Status & Correlation", "📋 Data"])

with tab1:
    section_header("📊", "Monthly volume — Blockchain vs Bridge")
    monthly = df.groupby(["month", "type"])["value"].sum().reset_index()
    monthly["month"] = monthly["month"].astype(str)
    fig = px.bar(monthly, x="month", y="value", color="type", barmode="group",
                 color_discrete_map={"BLOCKCHAIN": COLOR_BLOCKCHAIN, "BRIDGE": COLOR_BRIDGE},
                 labels={"value": "Value", "month": "Month", "type": "Type"})
    apply_default_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

    section_header("🪙", "Volume by symbol")
    by_symbol = df.groupby("symbol")["value"].sum().reset_index().sort_values("value", ascending=False)
    fig_s = px.bar(by_symbol, x="symbol", y="value", color="symbol",
                   color_discrete_map=SYMBOL_COLORS, labels={"value": "Value", "symbol": "Symbol"})
    fig_s.update_layout(showlegend=False)
    apply_default_layout(fig_s, height=320)
    st.plotly_chart(fig_s, use_container_width=True)

with tab2:
    section_header("🔄", "Year-over-year comparison — value by type")
    for tx_type in ("BLOCKCHAIN", "BRIDGE"):
        sub = df[df["type"] == tx_type]
        if sub.empty:
            continue
        pivot = sub.groupby(["month_num", "year"])["value"].sum().unstack(fill_value=0)
        fig2 = go.Figure()
        for year in pivot.columns:
            fig2.add_trace(go.Scatter(x=pivot.index, y=pivot[year], name=str(year), mode="lines+markers"))
        apply_default_layout(fig2, title=f"{tx_type.title()} — monthly value by year", height=340)
        fig2.update_layout(xaxis=dict(tickmode="array", tickvals=list(range(1, 13))))
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        section_header("🧪", "Status distribution")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig3 = px.pie(status_counts, values="Count", names="Status", hole=0.55,
                      color="Status", color_discrete_map=STATUS)
        apply_default_layout(fig3, height=320)
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        section_header("🔗", "Value × Fee")
        sample = df.sample(min(len(df), 3000), random_state=42) if len(df) else df
        fig4 = px.scatter(sample, x="value", y="tx_fee", trendline="ols", opacity=0.5,
                          labels={"value": "Value", "tx_fee": "Fee"})
        fig4.update_traces(marker=dict(color=COLOR_BLOCKCHAIN))
        apply_default_layout(fig4, height=320)
        st.plotly_chart(fig4, use_container_width=True)

with tab4:
    section_header("📋", "Raw data (sample)")
    display_df = df.copy()
    display_df["tx_hash"] = display_df["tx_hash"].str[:18] + "..."
    st.dataframe(display_df.head(300), use_container_width=True)
