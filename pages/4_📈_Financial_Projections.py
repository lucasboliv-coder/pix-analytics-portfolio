import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_gen.financials import (
    COMPANIES,
    COST_BREAKDOWN_KPIS,
    HEADLINE_KPIS,
    SCENARIOS,
    STOCK_KPIS,
    YEARS,
    load_financials,
)
from theme.charts import COLOR_COMPANY_A, COLOR_COMPANY_B, SCENARIO_COLORS, apply_default_layout, register_template
from theme.style import inject_css, kpi_grid, section_header

st.set_page_config(page_title="Financial Projections · PixFlow", layout="wide", page_icon="📈")
inject_css()
register_template()

st.title("📈 Financial Projections")

st.info(
    "⚠️ **Unlike the rest of this app, this page is not synthetic data.** "
    "It's derived from real multi-year financial models I built professionally "
    "for the two companies of a payments/fintech group. Company names and "
    "product lines are fictionalized, and every figure has additionally been "
    "scaled by an undisclosed, per-company factor before publishing — so "
    "growth rates and cost/revenue ratios closely track the real model "
    "(aside from rounding), but the absolute dollar and client-count values "
    "do not.",
    icon="⚠️",
)

data = load_financials()
yearly, scenario = data["yearly"], data["scenario"]

COMPANY_COLOR = {COMPANIES[0]: COLOR_COMPANY_A, COMPANIES[1]: COLOR_COMPANY_B}


def fmt_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:,.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:,.2f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:,.1f}K"
    return f"{sign}${value:,.0f}"


def fmt_num(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"


def kpi_value(df: pd.DataFrame, company: str, kpi: str, year: int) -> float:
    row = df[(df["company"] == company) & (df["kpi"] == kpi) & (df["year"] == year)]
    return float(row["value"].iloc[0]) if len(row) else 0.0


st.sidebar.header("Filters")
primary_company = st.sidebar.selectbox("Company (KPI cards)", COMPANIES)

# ---------------------------------------------------------------------------
# KPIs — first vs. last forecast year, for the sidebar-selected company
# ---------------------------------------------------------------------------
revenue_first = kpi_value(yearly, primary_company, "Gross Revenue", YEARS[0])
revenue_last = kpi_value(yearly, primary_company, "Gross Revenue", YEARS[-1])
ebitda_last = kpi_value(yearly, primary_company, "Estimated EBITDA", YEARS[-1])
clients_last = kpi_value(yearly, primary_company, "Retail Clients (EoP)", YEARS[-1])
revenue_growth = ((revenue_last / revenue_first) - 1) * 100 if revenue_first else 0

section_header("📊", f"{primary_company} — {YEARS[0]} → {YEARS[-1]} (base forecast)")
kpi_grid(
    [
        {"icon": "💰", "label": f"Gross Revenue ({YEARS[-1]})", "value": fmt_money(revenue_last),
         "delta": f"{revenue_growth:,.0f}% vs {YEARS[0]}", "positive": revenue_growth >= 0},
        {"icon": "📈", "label": f"Estimated EBITDA ({YEARS[-1]})", "value": fmt_money(ebitda_last)},
        {"icon": "👥", "label": f"Retail Clients ({YEARS[-1]})", "value": fmt_num(clients_last)},
        {"icon": "🎯", "label": "Scenarios modeled", "value": " / ".join(SCENARIOS)},
    ]
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 5-Year Trend", "🎯 Scenario Comparison", "🧾 Cost Breakdown", "👥 Clients & Volume", "📋 Data"]
)

# ---------------------------------------------------------------------------
with tab1:
    section_header("📈", "Base forecast — both companies")
    kpi_sel = st.selectbox("KPI", HEADLINE_KPIS, key="trend_kpi")
    df = yearly[yearly["kpi"] == kpi_sel]
    fig = go.Figure()
    for company in COMPANIES:
        sub = df[df["company"] == company].sort_values("year")
        fig.add_trace(go.Scatter(x=sub["year"], y=sub["value"], name=company, mode="lines+markers",
                                  line=dict(color=COMPANY_COLOR[company], width=3)))
    apply_default_layout(fig, height=380)
    fig.update_layout(xaxis=dict(tickmode="array", tickvals=YEARS))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Estimated EBITDA = Gross Revenue − Total Costs; not an audited P&L line.")

# ---------------------------------------------------------------------------
with tab2:
    section_header("🎯", "Conservative / Pessimistic / Optimistic — 2025-2029")
    kpi_sel2 = st.selectbox("KPI", HEADLINE_KPIS, key="scenario_kpi")
    is_stock = kpi_sel2 in STOCK_KPIS
    df2 = scenario[scenario["kpi"] == kpi_sel2]
    fig2 = px.bar(df2, x="scenario", y="value", color="company", barmode="group",
                  category_orders={"scenario": SCENARIOS},
                  color_discrete_map=COMPANY_COLOR,
                  labels={"value": kpi_sel2, "scenario": "Scenario"})
    apply_default_layout(fig2, height=380)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(
        f"{'Client counts are the modeled level at end of 2029 under each scenario.' if is_stock else 'Revenue/cost/volume figures are cumulative totals over 2025-2029 under each scenario.'}"
    )

# ---------------------------------------------------------------------------
with tab3:
    section_header("🧾", "Cost breakdown by year")
    cost_company = st.radio("Company", COMPANIES, horizontal=True, key="cost_company")
    cost_kpis = COST_BREAKDOWN_KPIS[cost_company]
    df3 = yearly[(yearly["company"] == cost_company) & (yearly["kpi"].isin(cost_kpis))]
    fig3 = px.bar(df3, x="year", y="value", color="kpi", barmode="stack",
                  labels={"value": "Expense", "year": "Year", "kpi": "Category"})
    apply_default_layout(fig3, height=380)
    fig3.update_layout(xaxis=dict(tickmode="array", tickvals=YEARS))
    st.plotly_chart(fig3, use_container_width=True)

    total_cost_last = kpi_value(yearly, cost_company, "Total Costs", YEARS[-1])
    kpi_grid([{"icon": "🧾", "label": f"Total Costs ({YEARS[-1]})", "value": fmt_money(total_cost_last)}])

# ---------------------------------------------------------------------------
with tab4:
    section_header("👥", "Clients & volume")
    cv_company = st.radio("Company", COMPANIES, horizontal=True, key="cv_company")
    col1, col2 = st.columns(2)
    with col1:
        df4 = yearly[(yearly["company"] == cv_company) & (yearly["kpi"].isin(["Retail Clients (EoP)", "Institutional Clients (EoP)"]))]
        fig4 = px.line(df4, x="year", y="value", color="kpi", markers=True,
                       labels={"value": "Clients", "year": "Year", "kpi": ""})
        apply_default_layout(fig4, title="Client growth", height=340)
        fig4.update_layout(xaxis=dict(tickmode="array", tickvals=YEARS))
        st.plotly_chart(fig4, use_container_width=True)
    with col2:
        df5 = yearly[(yearly["company"] == cv_company) & (yearly["kpi"] == "Volume Processed")]
        fig5 = px.bar(df5, x="year", y="value", labels={"value": "Volume", "year": "Year"})
        fig5.update_traces(marker_color=COMPANY_COLOR[cv_company])
        apply_default_layout(fig5, title="Volume processed", height=340)
        fig5.update_layout(xaxis=dict(tickmode="array", tickvals=YEARS))
        st.plotly_chart(fig5, use_container_width=True)

# ---------------------------------------------------------------------------
with tab5:
    section_header("📋", "Raw data")
    data_company = st.selectbox("Company", COMPANIES, key="data_company")
    st.markdown(f"**{YEARS[0]}-{YEARS[-1]} base forecast**")
    yearly_pivot = yearly[yearly["company"] == data_company].pivot(index="kpi", columns="year", values="value")
    st.dataframe(yearly_pivot.style.format("{:,.0f}"), use_container_width=True)

    st.markdown("**5-year scenarios**")
    scenario_pivot = scenario[scenario["company"] == data_company].pivot(index="kpi", columns="scenario", values="value")
    scenario_pivot = scenario_pivot[SCENARIOS]
    st.dataframe(scenario_pivot.style.format("{:,.0f}"), use_container_width=True)
