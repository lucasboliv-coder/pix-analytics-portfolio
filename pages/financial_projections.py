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
from theme.charts import COLOR_COMPANY_A, COLOR_COMPANY_B, SCENARIO_COLORS, apply_default_layout
from theme.icons import ICON, mi
from theme.narrative import escape_dollar
from theme.style import kpi_grid, section_header

st.title(f"{mi(ICON['financials_page'])} Financial Projections")

st.info(
    "**Unlike the rest of this app, this page is not synthetic data.** "
    "It's derived from real multi-year financial models I built professionally "
    "for the two companies of a payments/fintech group. Company names and "
    "product lines are fictionalized, and every figure has additionally been "
    "transformed by an undisclosed, per-company operation before publishing — so "
    "growth rates and cost/revenue ratios closely track the real model "
    "(aside from rounding), but the absolute dollar and client-count values "
    "do not.",
    icon=mi(ICON["warning"]),
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


_MONEY_KPIS = {"Gross Revenue", "Total Costs", "Estimated EBITDA"}


def fmt_kpi(value: float, kpi: str) -> str:
    return fmt_money(value) if kpi in _MONEY_KPIS else fmt_num(value)


def trend_stats(sub: pd.DataFrame) -> dict:
    """First/last/peak stats + CAGR for one company's KPI series, sorted by year."""
    sub = sub.sort_values("year")
    years, values = sub["year"].tolist(), sub["value"].tolist()
    first_year, last_year = years[0], years[-1]
    first, last = values[0], values[-1]
    span = last_year - first_year
    peak_i = max(range(len(values)), key=lambda i: values[i])
    # A negative (or zero) starting value makes "% growth" meaningless — e.g. a
    # loss turning into a profit isn't a "-400% increase". trend_story() reads
    # this flag and switches to a loss/profit sentence instead of a percentage.
    valid_growth = first > 0
    total_growth = (last / first - 1) * 100 if valid_growth else 0.0
    cagr = ((last / first) ** (1 / span) - 1) * 100 if valid_growth and span else 0.0
    yoy = pd.Series(values).pct_change().dropna() * 100
    return {
        "first_year": first_year, "last_year": last_year, "first": first, "last": last,
        "peak_year": years[peak_i], "peak_value": values[peak_i], "peak_is_last": peak_i == len(values) - 1,
        "total_growth": total_growth, "cagr": cagr, "valid_growth": valid_growth,
        "accelerating": len(yoy) >= 2 and yoy.iloc[-1] > yoy.iloc[0],
    }


def trend_story(stats: dict, kpi: str) -> str:
    """One sentence reading the trajectory — growing-to-the-end vs. peak-then-easing,
    described in the most constructive terms the actual numbers support."""
    return escape_dollar(_trend_story_raw(stats, kpi))


def _trend_story_raw(stats: dict, kpi: str) -> str:
    fmt = lambda v: fmt_kpi(v, kpi)
    if not stats["valid_growth"]:
        if stats["last"] > 0:
            return (
                f"swings from a loss of {fmt(abs(stats['first']))} in {stats['first_year']} to a profit of "
                f"{fmt(stats['last'])} by {stats['last_year']} — the clearest sign in the model that the "
                f"underlying unit economics work once the business reaches scale."
            )
        return (
            f"narrows from a loss of {fmt(abs(stats['first']))} in {stats['first_year']} to a loss of "
            f"{fmt(abs(stats['last']))} by {stats['last_year']} — moving the right direction, though not "
            f"yet profitable within the forecast window."
        )
    if stats["last"] >= stats["first"] and stats["peak_is_last"]:
        pace = (
            "and the pace is still building — the strongest year-over-year gain lands right at the end of the window"
            if stats["accelerating"]
            else "at a steady, repeatable clip across the full five years"
        )
        return (
            f"climbs from {fmt(stats['first'])} in {stats['first_year']} to {fmt(stats['last'])} in "
            f"{stats['last_year']} — a {stats['total_growth']:,.0f}% increase, compounding at roughly "
            f"{stats['cagr']:.1f}% a year, {pace}."
        )
    change_from_peak = (stats["last"] / stats["peak_value"] - 1) * 100 if stats["peak_value"] else 0.0
    return (
        f"builds to a peak of {fmt(stats['peak_value'])} in {stats['peak_year']}, then settles to "
        f"{fmt(stats['last'])} by {stats['last_year']} ({change_from_peak:+.0f}% off the peak) — a sign of a "
        f"market finding its natural size after the early land-grab phase, not of momentum breaking down."
    )


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

section_header(ICON["overview"], f"{primary_company} — {YEARS[0]} → {YEARS[-1]} (base forecast)")
kpi_grid(
    [
        {"icon": ICON["revenue"], "label": f"Gross Revenue ({YEARS[-1]})", "value": fmt_money(revenue_last),
         "delta": f"{revenue_growth:,.0f}% vs {YEARS[0]}", "positive": revenue_growth >= 0},
        {"icon": ICON["ebitda"], "label": f"Estimated EBITDA ({YEARS[-1]})", "value": fmt_money(ebitda_last)},
        {"icon": ICON["clients"], "label": f"Retail Clients ({YEARS[-1]})", "value": fmt_num(clients_last)},
        {"icon": ICON["scenario"], "label": "Scenarios modeled", "value": " / ".join(SCENARIOS)},
    ]
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"{mi(ICON['growth'])} 5-Year Trend",
    f"{mi(ICON['scenario'])} Scenario Comparison",
    f"{mi(ICON['costs'])} Cost Breakdown",
    f"{mi(ICON['clients'])} Clients & Volume",
    f"{mi(ICON['data'])} Data",
])

# ---------------------------------------------------------------------------
with tab1:
    section_header(ICON["growth"], "Base forecast — both companies")
    kpi_sel = st.selectbox("KPI", HEADLINE_KPIS, key="trend_kpi")
    df = yearly[yearly["kpi"] == kpi_sel]
    stats_by_company = {}
    fig = go.Figure()
    for company in COMPANIES:
        sub = df[df["company"] == company].sort_values("year")
        stats_by_company[company] = trend_stats(sub)
        color = COMPANY_COLOR[company]  # always "#rrggbb" (theme.charts.CATEGORICAL)
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["value"], name=company, mode="lines+markers",
            line=dict(color=color, width=3, shape="spline", smoothing=0.3),
            marker=dict(size=7),
            fill="tozeroy", fillcolor=color + "14",  # 8-digit hex: ~8% alpha
        ))
    apply_default_layout(fig, height=380)
    fig.update_layout(xaxis=dict(tickmode="array", tickvals=YEARS))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Estimated EBITDA = Gross Revenue − Total Costs; not an audited P&L line.")

    # ---- Trajectory read-out: CAGR stat cards + a plain-language take on the
    # shape of each curve, instead of leaving the chart to speak for itself.
    section_header(ICON["overview"], f"What the {kpi_sel.lower()} trajectory shows")
    def _cagr_card(company: str) -> dict:
        s = stats_by_company[company]
        label = f"{company} — CAGR '{str(YEARS[0])[2:]}–'{str(YEARS[-1])[2:]}"
        if not s["valid_growth"]:
            # A negative starting value makes CAGR/total-growth undefined —
            # "0.0%/yr" would misread as flat when it's actually the biggest
            # swing on the page (loss to profit, or a shrinking loss).
            return {
                "icon": ICON["growth"], "label": label,
                "value": "Turned profitable" if s["last"] > 0 else "Still negative",
                "delta": None,
            }
        return {
            "icon": ICON["growth"], "label": label,
            "value": f"{s['cagr']:.1f}%/yr",
            "delta": f"{s['total_growth']:,.0f}% total", "positive": s["total_growth"] >= 0,
        }

    kpi_grid([_cagr_card(company) for company in COMPANIES])
    col_a, col_b = st.columns(2)
    for col, company in zip((col_a, col_b), COMPANIES):
        with col:
            st.markdown(f"**{company}** {trend_story(stats_by_company[company], kpi_sel)}")

    both_valid = all(stats_by_company[c]["valid_growth"] for c in COMPANIES)
    leader = max(COMPANIES, key=lambda c: stats_by_company[c]["cagr"]) if both_valid else None
    laggard = COMPANIES[1 - COMPANIES.index(leader)] if leader and len(COMPANIES) == 2 else None
    if laggard and stats_by_company[leader]["cagr"] > stats_by_company[laggard]["cagr"]:
        st.markdown(
            f"**Takeaway:** both companies head the same direction over the forecast window, but "
            f"**{leader}** compounds faster in percentage terms ({stats_by_company[leader]['cagr']:.1f}%/yr "
            f"vs. {stats_by_company[laggard]['cagr']:.1f}%/yr for {laggard}) — the smaller base has more "
            f"room to run, while {laggard}'s scale still delivers the larger absolute gain."
        )

# ---------------------------------------------------------------------------
with tab2:
    section_header(ICON["scenario"], "Conservative / Pessimistic / Optimistic — 2025-2029")
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
    section_header(ICON["costs"], "Cost breakdown by year")
    cost_company = st.radio("Company", COMPANIES, horizontal=True, key="cost_company")
    cost_kpis = COST_BREAKDOWN_KPIS[cost_company]
    df3 = yearly[(yearly["company"] == cost_company) & (yearly["kpi"].isin(cost_kpis))]
    fig3 = px.bar(df3, x="year", y="value", color="kpi", barmode="stack",
                  labels={"value": "Expense", "year": "Year", "kpi": "Category"})
    apply_default_layout(fig3, height=380)
    fig3.update_layout(xaxis=dict(tickmode="array", tickvals=YEARS))
    st.plotly_chart(fig3, use_container_width=True)

    total_cost_last = kpi_value(yearly, cost_company, "Total Costs", YEARS[-1])
    kpi_grid([{"icon": ICON["costs"], "label": f"Total Costs ({YEARS[-1]})", "value": fmt_money(total_cost_last)}])

# ---------------------------------------------------------------------------
with tab4:
    section_header(ICON["clients"], "Clients & volume")
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
    section_header(ICON["data"], "Raw data")
    data_company = st.selectbox("Company", COMPANIES, key="data_company")
    st.markdown(f"**{YEARS[0]}-{YEARS[-1]} base forecast**")
    yearly_pivot = yearly[yearly["company"] == data_company].pivot(index="kpi", columns="year", values="value")
    st.dataframe(yearly_pivot.style.format("{:,.0f}"), use_container_width=True)

    st.markdown("**5-year scenarios**")
    scenario_pivot = scenario[scenario["company"] == data_company].pivot(index="kpi", columns="scenario", values="value")
    scenario_pivot = scenario_pivot[SCENARIOS]
    st.dataframe(scenario_pivot.style.format("{:,.0f}"), use_container_width=True)
