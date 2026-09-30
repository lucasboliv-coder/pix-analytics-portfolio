import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_gen.financials import (
    COMPANIES,
    COST_BREAKDOWN_KPIS,
    HEADLINE_KPIS,
    SCENARIOS,
    YEARS,
    load_financials,
)
from data_gen.chain_real import BRIDGE_MONTHLY
from data_gen.plan_vs_actual import ACTUAL_TO_PLAN, PRODUCT, PROJECTION_BUILT, SCENARIO, SEEDED_THROUGH
from theme.charts import (CATEGORICAL_ORDER, COLOR_COMPANY_A, COLOR_COMPANY_B, INK_MUTED, SCENARIO_COLORS,
                          SCENARIO_SYMBOLS, apply_default_layout)
from theme.icons import ICON, mi
from theme.narrative import escape_dollar, estimate_gaps
from theme.style import kpi_grid, section_header

st.title(f"{mi(ICON['financials_page'])} Financial Projections")

st.info(
    "**Unlike the rest of this app, this page is not synthetic — it's real "
    "data, mathematically masked.** It's derived from real multi-year "
    "financial models I built professionally for the two companies of a "
    "payments/fintech group. Company names and product lines are "
    "fictionalized, and every figure has additionally been run through a "
    "random, per-company mathematical operation — generated once and never "
    "recorded — before publishing, so growth rates and cost/revenue ratios "
    "closely track the real model (aside from rounding), but the absolute "
    "dollar and client-count values can't be reverse-engineered from what's "
    "published.",
    icon=mi(ICON["warning"]),
)

data = load_financials()
yearly, scenario = data["yearly"], data["scenario"]

COMPANY_COLOR = {COMPANIES[0]: COLOR_COMPANY_A, COMPANIES[1]: COLOR_COMPANY_B}
PVA_COMPANY = COMPANIES[0]  # the plan-vs-actual check covers PixFlow only


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
        # Less than a point between the first and last year's growth reads as
        # steady, not accelerating — otherwise a flat ~4%/yr path gets called "building".
        "accelerating": len(yoy) >= 2 and yoy.iloc[-1] - yoy.iloc[0] >= 1.0,
        "decelerating": len(yoy) >= 2 and yoy.iloc[0] - yoy.iloc[-1] >= 3.0,
        "yoy_first": yoy.iloc[0] if len(yoy) else 0.0, "yoy_last": yoy.iloc[-1] if len(yoy) else 0.0,
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
        if stats["accelerating"]:
            pace = "and the pace is still building — the strongest year-over-year gain lands at the end of the window"
        elif stats["decelerating"]:
            pace = (f"with growth easing from {stats['yoy_first']:+.0f}% in the first year to "
                    f"{stats['yoy_last']:+.0f}% in the last as the base gets larger")
        else:
            pace = "at a steady pace across the window"
        return (
            f"climbs from {fmt(stats['first'])} in {stats['first_year']} to {fmt(stats['last'])} in "
            f"{stats['last_year']} — a {stats['total_growth']:,.0f}% increase, compounding at roughly "
            f"{stats['cagr']:.1f}% a year, {pace}."
        )
    change_from_peak = (stats["last"] / stats["peak_value"] - 1) * 100 if stats["peak_value"] else 0.0
    return (
        f"builds to a peak of {fmt(stats['peak_value'])} in {stats['peak_year']}, then settles to "
        f"{fmt(stats['last'])} by {stats['last_year']} ({change_from_peak:+.0f}% off the peak) — the curve "
        f"flattens out instead of compounding to the end of the window."
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

# Display order: Scenario Comparison first, then 5-Year Trend (tab2 / tab1 keep
# their content — only the order they're shown in changes).
tab2, tab1, tab3, tab4, tab_pva, tab5 = st.tabs([
    f"{mi(ICON['scenario'])} Scenario Comparison",
    f"{mi(ICON['growth'])} 5-Year Trend",
    f"{mi(ICON['costs'])} Cost Breakdown",
    f"{mi(ICON['clients'])} Clients & Volume",
    f"{mi(ICON['plan_actual'])} Plan vs. Actual",
    f"{mi(ICON['data'])} Data",
])

# ---------------------------------------------------------------------------
with tab1:
    section_header(ICON["growth"], "Base forecast — how each company's trajectory is shaped")
    st.markdown(
        "The base forecast is the model's central path — the same figures the Conservative scenario adds up "
        "to. **Each company is masked with its own factor**, so their *levels* can't be compared with each "
        "other; their *trajectories* can. Everything here is therefore indexed (first year = 100) or expressed "
        "as a rate, which the masking doesn't touch."
    )
    kpi_sel = st.selectbox("KPI", HEADLINE_KPIS, key="trend_kpi")
    is_margin = kpi_sel == "Estimated EBITDA"      # starts negative for one company: read it as a margin
    is_client = kpi_sel in {"Retail Clients (EoP)", "Institutional Clients (EoP)"}
    # 2025 client counts are the actual balance when the model was built; later years are year-end
    # projections — client growth is measured from 2026 so it compares year-end to year-end.
    base_year = YEARS[1] if is_client else YEARS[0]

    def company_series(c: str, kpi: str) -> pd.Series:
        return yearly[(yearly["company"] == c) & (yearly["kpi"] == kpi)].set_index("year")["value"].sort_index()

    stats_by_company = {c: trend_stats(yearly[(yearly["company"] == c) & (yearly["kpi"] == kpi_sel)
                                              & (yearly["year"] >= base_year)]) for c in COMPANIES}
    if is_margin:
        shown = {c: (company_series(c, "Gross Revenue") - company_series(c, "Total Costs"))
                 / company_series(c, "Gross Revenue") * 100 for c in COMPANIES}
    else:
        shown = {c: company_series(c, kpi_sel).loc[base_year:] for c in COMPANIES}
        shown = {c: s / s.iloc[0] * 100 for c, s in shown.items()}
    raw = {c: company_series(c, kpi_sel).loc[base_year:] for c in COMPANIES}
    span = YEARS[-1] - base_year
    cagr = {c: ((raw[c].iloc[-1] / raw[c].iloc[0]) ** (1 / span) - 1) * 100
            if raw[c].iloc[0] > 0 and raw[c].iloc[-1] > 0 else None for c in COMPANIES}
    yoy = {c: raw[c].pct_change().dropna() * 100 for c in COMPANIES}

    cards = []
    for c in COMPANIES:
        if is_margin:
            m = shown[c]
            cards.append({"icon": ICON["ebitda"], "label": f"{c} — EBITDA margin, {YEARS[0]} → {YEARS[-1]}",
                          "value": f"{m.iloc[0]:.0f}% → {m.iloc[-1]:.0f}%"})
        else:
            cards.append({"icon": ICON["growth"], "label": f"{c} — CAGR {base_year}–{YEARS[-1]}",
                          "value": f"{cagr[c]:.1f}%/yr" if cagr[c] is not None else "n/a"})
    for c in COMPANIES:
        if is_margin:
            m = shown[c]
            cards.append({"icon": ICON["overview"], "label": f"{c} — margin change",
                          "value": f"{m.iloc[-1] - m.iloc[0]:+.0f} pts"})
        else:
            y = yoy[c]
            cards.append({"icon": ICON["overview"], "label": f"{c} — growth, first year → last year",
                          "value": f"{y.iloc[0]:+.0f}% → {y.iloc[-1]:+.0f}%"})
    kpi_grid(cards)

    # ---- Indexed trajectory (or margin), both companies, one axis
    fig = go.Figure()
    for c in COMPANIES:
        s = shown[c]
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name=c, mode="lines+markers+text",
            line=dict(color=COMPANY_COLOR[c], width=3), marker=dict(size=8),
            text=[""] * (len(s) - 1) + [f"{s.iloc[-1]:.0f}{'%' if is_margin else ''}"], textposition="middle right",
            hovertemplate="%{x}<br>" + c + (": %{y:.1f}% margin" if is_margin else f": %{{y:.0f}} ({base_year} = 100)")
                          + "<extra></extra>",
        ))
    if is_margin:
        fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"),
                      annotation_text="break-even", annotation_position="bottom right")
    else:
        fig.add_hline(y=100, line=dict(color="rgba(255,255,255,0.25)", width=1, dash="dot"))
    title = ("Estimated EBITDA margin (EBITDA ÷ revenue)" if is_margin
             else f"{kpi_sel}, indexed ({base_year} = 100)")
    apply_default_layout(fig, title=title, height=380)
    fig.update_layout(legend=dict(orientation="h", y=-0.15), margin=dict(r=50),
                      xaxis=dict(tickmode="array", tickvals=list(shown[COMPANIES[0]].index)),
                      yaxis=dict(ticksuffix="%" if is_margin else ""))
    st.plotly_chart(fig, width="stretch")
    if is_margin:
        st.caption("Estimated EBITDA = Gross Revenue − Total Costs; not an audited P&L line.")

    # ---- Year-over-year growth: is the pace holding, accelerating or fading?
    section_header(ICON["overview"], f"Year-over-year change — {kpi_sel.lower()}")
    fig_y = go.Figure()
    for c in COMPANIES:
        if is_margin:
            ys = shown[c].diff().dropna()
            fmt_bar, suffix = "{:+.0f} pts", " pts"
        else:
            ys = yoy[c]
            fmt_bar, suffix = "{:+.0f}%", "%"
        fig_y.add_trace(go.Bar(
            x=[f"{y - 1}→{str(y)[2:]}" for y in ys.index], y=ys.values, name=c, marker_color=COMPANY_COLOR[c],
            marker_line=dict(color="#1a1a19", width=2), text=[fmt_bar.format(v) for v in ys.values],
            textposition="outside",
            hovertemplate="%{x}<br>" + c + ": %{y:+.1f}" + suffix + "<extra></extra>",
        ))
    apply_default_layout(fig_y, height=320)
    all_vals = pd.concat([shown[c].diff().dropna() if is_margin else yoy[c] for c in COMPANIES])
    pad = (all_vals.max() - min(0, all_vals.min())) * 0.18
    fig_y.update_layout(barmode="group", legend=dict(orientation="h", y=1.12),
                        yaxis=dict(ticksuffix=suffix.strip() if not is_margin else "",
                                   range=[min(0, all_vals.min()) - pad, all_vals.max() + pad]))
    st.plotly_chart(fig_y, width="stretch")

    # ---- Reading
    section_header(ICON["plan_actual"], f"What the {kpi_sel.lower()} trajectory shows")
    col_a, col_b = st.columns(2)
    for col, c in zip((col_a, col_b), COMPANIES):
        with col:
            st.markdown(f"**{c}** {trend_story(stats_by_company[c], kpi_sel)}")

    if is_margin:
        m = {c: shown[c] for c in COMPANIES}
        widen = max(COMPANIES, key=lambda c: m[c].iloc[-1] - m[c].iloc[0])
        other = [c for c in COMPANIES if c != widen][0]
        st.markdown(
            f"**Comparing the two.** Margins are a real, like-for-like measure. **{widen}** gains the most — "
            f"**{m[widen].iloc[-1] - m[widen].iloc[0]:+.0f} points** — as revenue outgrows its cost base, while "
            f"**{other}** moves {m[other].iloc[-1] - m[other].iloc[0]:+.0f} points from an already-high "
            f"{m[other].iloc[0]:.0f}%. By {YEARS[-1]} they sit at {m[widen].iloc[-1]:.0f}% and "
            f"{m[other].iloc[-1]:.0f}%."
        )
    elif all(v is not None for v in cagr.values()):
        fast = max(COMPANIES, key=lambda c: cagr[c])
        slow = [c for c in COMPANIES if c != fast][0]
        # Same classification as each company's own sentence above (trend_stats flags).
        fade = {c: yoy[c].iloc[0] - yoy[c].iloc[-1] for c in COMPANIES}
        pace = {c: ("picks up" if stats_by_company[c]["accelerating"] else
                    ("slows sharply" if fade[c] > 20 else "eases") if stats_by_company[c]["decelerating"] else
                    "holds steady") for c in COMPANIES}
        if abs(cagr[fast] - cagr[slow]) < 1 and pace[fast] == pace[slow]:
            st.markdown(
                f"**Comparing the two.** On {kpi_sel}, the two companies move almost identically — "
                f"**{cagr[fast]:.1f}%/yr** and **{cagr[slow]:.1f}%/yr**, with the same year-over-year shape "
                f"({yoy[fast].iloc[0]:+.0f}% → {yoy[fast].iloc[-1]:+.0f}%). Matching paths like this usually mean "
                f"both lines were built from the same growth assumption rather than company-specific drivers."
            )
        else:
            st.markdown(
                f"**Comparing the two.** On {kpi_sel}, **{fast}** compounds at **{cagr[fast]:.1f}%/yr** against "
                f"**{cagr[slow]:.1f}%/yr** for {slow}. The year-over-year bars show the shape behind those "
                f"averages: {fast}'s growth {pace[fast]} ({yoy[fast].iloc[0]:+.0f}% in the first year, "
                f"{yoy[fast].iloc[-1]:+.0f}% in the last), {slow}'s {pace[slow]} ({yoy[slow].iloc[0]:+.0f}% → "
                f"{yoy[slow].iloc[-1]:+.0f}%). The average growth rate alone would hide that shape — a steep "
                f"early climb and a steady path can average out to similar numbers and mean very different things."
            )
    if is_client:
        st.caption(f"The {YEARS[0]} client count is the actual balance when the model was built; {base_year}–{YEARS[-1]} "
                   f"are year-end projections. Growth is measured from {base_year} so every year compares year-end "
                   f"to year-end.")

    section_header(ICON["warning"], "What to take from this")
    st.markdown(
        "- **Read shapes, not sizes.** The two companies are masked separately, so a taller line on a raw chart "
        "would say nothing about which business is bigger — only growth rates, indices and margins compare.\n"
        "- **Early growth fades by design.** High first-year rates come off small bases; the later, slower years "
        "are the better guide to the run-rate the model expects.\n"
        "- **All of it is organic.** Neither company runs paid acquisition in this model — the base forecast is "
        "what the existing channels deliver, not a ceiling (see Scenario Comparison for the spread around it)."
    )

# ---------------------------------------------------------------------------
with tab2:
    # Everything below is read from the scenario and base tables; the masking is
    # one constant per company, so every ratio, index and margin here is real.
    scen = {c: scenario[scenario["company"] == c].pivot(index="kpi", columns="scenario", values="value")[SCENARIOS]
            for c in COMPANIES}
    for c in COMPANIES:
        s = scen[c]
        s.loc["Revenue per client"] = s.loc["Gross Revenue"] / s.loc["Retail Clients (EoP)"]
    index = {c: scen[c].div(scen[c]["Conservative"], axis=0) * 100 for c in COMPANIES}
    margin = {c: (scen[c].loc["Gross Revenue"] - scen[c].loc["Total Costs"]) / scen[c].loc["Gross Revenue"] * 100
              for c in COMPANIES}
    base_vs_cons = {c: yearly[(yearly["company"] == c) & (yearly["kpi"] == "Gross Revenue")]["value"].sum()
                    / scen[c].loc["Gross Revenue", "Conservative"] for c in COMPANIES}
    client_flex = {s: index[COMPANIES[0]].loc["Retail Clients (EoP)", s] / 100 for s in ("Pessimistic", "Optimistic")}
    ORDINAL = ["Pessimistic", "Conservative", "Optimistic"]  # worst -> base -> best, for legends and bars

    section_header(ICON["scenario"], "Three scenarios around one base case — 2025-2029")
    base_note = (
        "**Conservative is the base case**: its 5-year totals match the base forecast on the 5-Year "
        "Trend tab (within 0.1%)."
        if all(abs(v - 1) < 0.01 for v in base_vs_cons.values())
        else "**Conservative** is the reference case the other two are measured against."
    )
    st.markdown(
        f"{base_note} The other two flex the one input the model is built on — the **client base**: "
        f"Pessimistic lands at **{client_flex['Pessimistic']:.2f}×** Conservative's end-2029 clients, "
        f"Optimistic at **{client_flex['Optimistic']:.2f}×**. Volume, revenue and costs then follow from the "
        f"model's per-client assumptions. That's what makes the comparison useful: when a scenario's revenue "
        f"doesn't move with its clients, the model is saying something about how each client is monetized."
    )

    kpi_grid([
        {"icon": ICON["revenue"], "label": f"{c} — 5-yr revenue, downside → upside (base = 100)",
         "value": f"{index[c].loc['Gross Revenue', 'Pessimistic']:.0f} → "
                  f"{index[c].loc['Gross Revenue', 'Optimistic']:.0f}"}
        for c in COMPANIES
    ] + [
        {"icon": ICON["ebitda"], "label": f"{c} — 5-yr EBITDA margin, lowest–highest case",
         "value": f"{margin[c].min():.0f}–{margin[c].max():.0f}%"}
        for c in COMPANIES
    ])

    # ---- Range of outcomes: one dot plot per company, one shared index axis
    section_header(ICON["overview"], "Range of outcomes — Conservative = 100")
    ROWS = ["Retail Clients (EoP)", "Volume Processed", "Gross Revenue", "Revenue per client",
            "Total Costs", "Estimated EBITDA"]
    ROW_LABELS = {"Retail Clients (EoP)": "Clients (end-2029)", "Volume Processed": "Volume",
                  "Gross Revenue": "Revenue", "Revenue per client": "Revenue per client",
                  "Total Costs": "Total costs", "Estimated EBITDA": "EBITDA"}
    x_max = max(index[c].loc[ROWS].max().max() for c in COMPANIES) * 1.12
    cols = st.columns(len(COMPANIES))
    for i, (col, c) in enumerate(zip(cols, COMPANIES)):
        with col:
            ix = index[c].loc[ROWS]
            labels = [ROW_LABELS[r] for r in ROWS]
            fig = go.Figure()
            for r, lab in zip(ROWS, labels):  # the spread each KPI covers, drawn first so markers sit on top
                fig.add_trace(go.Scatter(
                    x=[ix.loc[r].min(), ix.loc[r].max()], y=[lab, lab], mode="lines",
                    line=dict(color="rgba(255,255,255,0.18)", width=2), hoverinfo="skip", showlegend=False,
                ))
            for s in ORDINAL:
                fig.add_trace(go.Scatter(
                    x=ix[s], y=labels, mode="markers", name=s,
                    marker=dict(color=SCENARIO_COLORS[s], symbol=SCENARIO_SYMBOLS[s], size=12,
                                line=dict(color="#1a1a19", width=2)),
                    showlegend=True,
                    hovertemplate="%{y}<br>" + s + ": %{x:.0f} (Conservative = 100)<extra></extra>",
                ))
            fig.add_vline(x=100, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"))
            apply_default_layout(fig, title=c, height=360)
            fig.update_layout(
                xaxis=dict(range=[0, x_max], title="Index, Conservative = 100"),
                yaxis=dict(autorange="reversed"),
                legend=dict(orientation="h", y=-0.22), margin=dict(l=10, r=10, t=50, b=60),
            )
            st.plotly_chart(fig, width="stretch")

    def _read(c: str) -> str:
        ix = index[c]
        cl, rev, rpc, ebitda, cost = (ix.loc[k] for k in ("Retail Clients (EoP)", "Gross Revenue",
                                                          "Revenue per client", "Estimated EBITDA", "Total Costs"))
        if rev["Optimistic"] < 0.5 * cl["Optimistic"]:
            return (
                f"**{c}** — growth without monetization. The Optimistic case brings **{cl['Optimistic'] / 100:.1f}×** "
                f"the clients but only **{rev['Optimistic'] / 100:.2f}×** the revenue, so revenue per client falls "
                f"to **{rpc['Optimistic']:.0f}%** of Conservative's, and with costs still rising, EBITDA lands at "
                f"**{ebitda['Optimistic']:.0f}** — below the base case. In this model, more clients are a cost before "
                f"they're a revenue line: the Optimistic case is missing a monetization assumption (revenue per "
                f"client that holds as the base grows), which is the first thing to revisit before treating it as "
                f"upside."
            )
        return (
            f"**{c}** — the scenarios scale coherently. Clients **{cl['Pessimistic'] / 100:.2f}×** / "
            f"**{cl['Optimistic'] / 100:.2f}×** carry revenue to **{rev['Pessimistic'] / 100:.2f}×** / "
            f"**{rev['Optimistic'] / 100:.2f}×** and EBITDA to **{ebitda['Pessimistic'] / 100:.2f}×** / "
            f"**{ebitda['Optimistic'] / 100:.2f}×**. EBITDA swings further than revenue because costs and "
            f"revenue don't move together: in the downside costs fall to **{cost['Pessimistic'] / 100:.2f}×** while "
            f"revenue falls to {rev['Pessimistic'] / 100:.2f}×, squeezing the margin; in the upside costs rise only "
            f"**{cost['Optimistic'] / 100:.2f}×** against revenue's {rev['Optimistic'] / 100:.2f}×, widening it. "
            f"Revenue per client slips in both flexed cases ({rpc['Pessimistic']:.0f} and "
            f"{rpc['Optimistic']:.0f}), so neither scenario is a pure multiple of the base."
        )

    for c in COMPANIES:
        st.markdown(escape_dollar(_read(c)))

    # ---- Profitability: one bar per scenario, grouped by company, one % axis
    section_header(ICON["ebitda"], "Profitability by scenario — 5-year EBITDA margin")
    fig_m = go.Figure()
    for s in ORDINAL:
        fig_m.add_trace(go.Bar(
            x=COMPANIES, y=[margin[c][s] for c in COMPANIES], name=s, marker_color=SCENARIO_COLORS[s],
            marker_line=dict(color="#1a1a19", width=2),
            text=[f"{margin[c][s]:.0f}%" for c in COMPANIES], textposition="outside",
            hovertemplate="%{x}<br>" + s + ": %{y:.1f}% EBITDA margin<extra></extra>",
        ))
    apply_default_layout(fig_m, height=340)
    fig_m.update_layout(barmode="group", bargap=0.35, bargroupgap=0.08,
                        yaxis=dict(range=[0, max(m.max() for m in margin.values()) * 1.25], ticksuffix="%"),
                        legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig_m, width="stretch")

    margin_lines = []
    for c in COMPANIES:
        m = margin[c]
        spread = m.max() - m.min()
        margin_lines.append(
            f"**{c}** keeps a **{m.min():.0f}–{m.max():.0f}%** margin across all three cases "
            f"({spread:.0f} points of spread) and is most profitable in the **{m.idxmax()}** case."
        )
    all_profitable = all(margin[c].min() > 0 for c in COMPANIES)
    st.markdown(
        " ".join(margin_lines)
        + (" Every scenario stays profitable over the five years for both companies — the downside is a "
           "smaller business, not a loss-making one. That's the useful property of a scenario set: it bounds the "
           "size of the outcome while showing that the unit economics survive the bad case."
           if all_profitable else
           " At least one case runs at a loss over the five years — the downside changes the business's "
           "economics, not just its size.")
    )

    section_header(ICON["plan_actual"], "What to take from this")
    st.markdown(
        f"- **The downside is the better-defined case.** In the Pessimistic case revenue falls to "
        f"{min(index[c].loc['Gross Revenue', 'Pessimistic'] for c in COMPANIES) / 100:.2f}–"
        f"{max(index[c].loc['Gross Revenue', 'Pessimistic'] for c in COMPANIES) / 100:.2f}× the base across the "
        f"two companies, with clients, volume and costs all moving down together.\n"
        f"- **{COMPANIES[0]}'s upside is under-modeled, not absent.** Its Optimistic case adds clients and "
        "volume without revenue per client to match. The Plan vs. Actual tab points the same way: realized "
        "bridge revenue already runs well above plan. Both are signals to revisit monetization assumptions, "
        "not to discount growth.\n"
        "- **Paid acquisition isn't in any case.** All three scenarios are organic — the spread is what the "
        "model says the existing growth engine can do, not a ceiling."
    )
    st.caption(
        "Scenario totals are cumulative 2025-2029; client counts are end-2029 levels; revenue per client is "
        "5-year revenue over end-2029 clients. Scenarios are the model's alternatives, not weighted by "
        "probability. Full scenario figures are on the Data tab."
    )

# ---------------------------------------------------------------------------
with tab3:
    # All ratios here (cost/revenue, margins, shares, growth rates) are real:
    # the masking is one constant per company, and it cancels inside each ratio.
    section_header(ICON["costs"], "Costs — when the model turns profitable")
    cost_company = st.radio("Company", COMPANIES, horizontal=True, key="cost_company")
    yc = yearly[yearly["company"] == cost_company].pivot(index="kpi", columns="year", values="value")
    rev_c, cost_c = yc.loc["Gross Revenue"], yc.loc["Total Costs"]
    y0, y1 = YEARS[0], YEARS[-1]
    span = y1 - y0
    ratio_c = cost_c / rev_c * 100
    margin_c = (rev_c - cost_c) / rev_c * 100
    cost_cagr = ((cost_c[y1] / cost_c[y0]) ** (1 / span) - 1) * 100
    revenue_cagr = ((rev_c[y1] / rev_c[y0]) ** (1 / span) - 1) * 100
    profitable = [y for y in YEARS if rev_c[y] > cost_c[y]]
    if not profitable:
        breakeven_label = f"after {y1}"
    elif profitable[0] == y0:
        breakeven_label = f"already in {y0}"
    else:
        breakeven_label = str(profitable[0])

    kpi_grid([
        {"icon": ICON["costs"], "label": f"Costs as % of revenue, {y0} → {y1}",
         "value": f"{ratio_c[y0]:.0f}% → {ratio_c[y1]:.0f}%"},
        {"icon": ICON["ebitda"], "label": "First profitable year", "value": breakeven_label},
        {"icon": ICON["growth"], "label": "Revenue vs. cost growth", "value": f"{revenue_cagr:.0f}% vs {cost_cagr:.0f}%/yr"},
        {"icon": ICON["ebitda"], "label": f"EBITDA margin, {y1}", "value": f"{margin_c[y1]:.0f}%"},
    ])

    fig_rc = go.Figure()
    fig_rc.add_trace(go.Scatter(
        x=YEARS, y=rev_c.values, name="Gross revenue", mode="lines+markers",
        line=dict(color=COMPANY_COLOR[cost_company], width=2.5), marker=dict(size=8),
        hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig_rc.add_trace(go.Scatter(
        x=YEARS, y=cost_c.values, name="Total costs", mode="lines+markers",
        line=dict(color=INK_MUTED, width=2.5, dash="dash"), marker=dict(size=8),
        hovertemplate="%{x}<br>Costs: $%{y:,.0f}<extra></extra>",
    ))
    if profitable and profitable[0] != y0:
        fig_rc.add_vline(x=profitable[0], line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"),
                         annotation_text="first profitable year", annotation_position="top left")
    apply_default_layout(fig_rc, title=f"{cost_company} — revenue vs. costs", height=360)
    fig_rc.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.15),
                         xaxis=dict(tickmode="array", tickvals=YEARS), yaxis=dict(tickprefix="$", rangemode="tozero"))
    st.plotly_chart(fig_rc, width="stretch")

    if profitable and profitable[0] != y0:
        path = (f"costs run at **{ratio_c[y0]:.0f}%** of revenue in {y0} — a margin of {margin_c[y0]:.0f}% — "
                f"and the lines cross in **{profitable[0]}**, after which the margin widens to "
                f"**{margin_c[y1]:.0f}%** by {y1}")
    else:
        path = (f"the business is profitable across the whole window, with costs going from "
                f"**{ratio_c[y0]:.0f}%** to **{ratio_c[y1]:.0f}%** of revenue and the margin from "
                f"{margin_c[y0]:.0f}% to **{margin_c[y1]:.0f}%**")
    st.markdown(escape_dollar(
        f"For **{cost_company}**, {path}. The mechanism is the gap between the two growth rates: revenue "
        f"compounds at **{revenue_cagr:.0f}%/yr** while costs grow **{cost_cagr:.0f}%/yr**. When most of the "
        f"cost base doesn't scale with activity, every extra dollar of revenue falls mostly to profit — "
        f"*operating leverage*. It cuts both ways: the same structure that widens the margin on the way up "
        f"would compress it just as fast if revenue fell short."
    ))

    # ---- Cost-to-revenue ratio, both companies, one % axis
    section_header(ICON["overview"], "Cost-to-revenue ratio — both companies")
    fig_ratio = go.Figure()
    for c in COMPANIES:
        yc_all = yearly[yearly["company"] == c].pivot(index="kpi", columns="year", values="value")
        r = yc_all.loc["Total Costs"] / yc_all.loc["Gross Revenue"] * 100
        fig_ratio.add_trace(go.Scatter(
            x=YEARS, y=r.values, name=c, mode="lines+markers+text",
            line=dict(color=COMPANY_COLOR[c], width=2.5), marker=dict(size=8),
            text=[f"{v:.0f}%" if y in (y0, y1) else "" for y, v in zip(YEARS, r.values)],
            textposition="bottom center" if c == COMPANIES[0] else "top center", hovertemplate="%{x}<br>" + c + ": costs = %{y:.0f}% of revenue<extra></extra>",
        ))
    fig_ratio.add_hline(y=100, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"),
                        annotation_text="costs = revenue (break-even)", annotation_position="top right")
    apply_default_layout(fig_ratio, height=340)
    fig_ratio.update_layout(legend=dict(orientation="h", y=1.12), xaxis=dict(tickmode="array", tickvals=YEARS),
                            yaxis=dict(ticksuffix="%", rangemode="tozero"))
    st.plotly_chart(fig_ratio, width="stretch")

    ratios_all = {c: (yearly[(yearly["company"] == c) & (yearly["kpi"] == "Total Costs")].set_index("year")["value"]
                      / yearly[(yearly["company"] == c) & (yearly["kpi"] == "Gross Revenue")].set_index("year")["value"]
                      * 100) for c in COMPANIES}
    drop = {c: ratios_all[c][y0] - ratios_all[c][y1] for c in COMPANIES}
    steep, flat = max(drop, key=drop.get), min(drop, key=drop.get)
    st.markdown(
        f"The two companies sit at different points of the same curve. **{steep}** is early: its ratio falls "
        f"**{drop[steep]:.0f} points** over the window as revenue catches up with a cost base built ahead of it. "
        f"**{flat}** is already mature — its ratio moves only **{drop[flat]:.0f} points**, from "
        f"{ratios_all[flat][y0]:.0f}% to {ratios_all[flat][y1]:.0f}%, because revenue and costs now grow at "
        f"similar speeds. A young company's case rests on the slope; a mature one's on the level."
    )

    # ---- Where the money goes: 100% stacked composition for the selected company
    section_header(ICON["costs"], f"Where {cost_company}'s costs go")
    lines = COST_BREAKDOWN_KPIS[cost_company]
    comp = yc.loc[lines].copy()
    comp.loc["Not itemized in the model"] = cost_c - comp.sum()
    share = comp.div(cost_c, axis=1) * 100
    if len(lines) >= 2:  # one itemized line would be a near-solid gray block — text says it better
        fig_comp = go.Figure()
        for i, line in enumerate(share.index):
            color = INK_MUTED if line == "Not itemized in the model" else CATEGORICAL_ORDER[i]
            fig_comp.add_trace(go.Bar(
                x=YEARS, y=share.loc[line].values, name=line, marker_color=color,
                marker_line=dict(color="#1a1a19", width=2),
                hovertemplate="%{x}<br>" + line + ": %{y:.1f}% of costs<extra></extra>",
            ))
        apply_default_layout(fig_comp, height=340)
        fig_comp.update_layout(barmode="stack", legend=dict(orientation="h", y=-0.15),
                               xaxis=dict(tickmode="array", tickvals=YEARS), yaxis=dict(ticksuffix="%", range=[0, 100]))
        st.plotly_chart(fig_comp, width="stretch")

    itemized = share.drop("Not itemized in the model")
    biggest = itemized[y1].idxmax()
    growth_26_29 = {l: ((comp.loc[l, y1] / comp.loc[l, YEARS[1]]) ** (1 / (y1 - YEARS[1])) - 1) * 100 for l in lines}
    fastest = max(growth_26_29, key=growth_26_29.get)
    comp_text = (
        (f"The model itemizes a single line for {cost_company}: **{biggest}**, a steady "
         f"**{itemized.loc[biggest, y1]:.0f}%** of costs every year" if len(lines) == 1 else
         f"The largest itemized line is **{biggest}** at **{itemized.loc[biggest, y1]:.0f}%** of {y1} costs")
        + (f"; the fastest-growing from {YEARS[1]} is **{fastest}** at {growth_26_29[fastest]:.1f}%/yr."
           if len(lines) > 1 else ".")
    )
    if "Sales & Marketing Expenses" in lines:
        sm = share.loc["Sales & Marketing Expenses"]
        comp_text += (f" Sales & marketing shrinks from **{sm[y0]:.1f}%** to **{sm[y1]:.1f}%** of costs — the model "
                      f"assumes growth without paid acquisition, which is why its client curve is an organic floor.")
    comp_text += (f" **{share.loc['Not itemized in the model', y1]:.0f}%** of {cost_company}'s costs aren't broken out "
                  f"at this summary level" + (" (the gray block)" if len(lines) >= 2 else "")
                  + ", so this covers only part of the base.")
    st.markdown(comp_text)

    section_header(ICON["plan_actual"], "What to take from this")
    st.markdown(
        f"- **Profitability here is a question of scale, not of pricing.** Both companies' margins improve "
        f"because revenue outgrows a slow-moving cost base, not because costs are cut.\n"
        f"- **{steep}'s case depends on the growth actually arriving** — the break-even year moves if revenue "
        f"lands below plan, since the costs are committed either way. The Plan vs. Actual tab is the first "
        f"check on that.\n"
        f"- **The itemized lines are a partial view** — read the composition as a guide to the named lines, "
        f"not the full cost structure."
    )

# ---------------------------------------------------------------------------
with tab4:
    section_header(ICON["clients"], "Clients & volume — where the growth comes from")
    y_start = YEARS[1]  # 2025 = actual balance when the model was built; measure year-end to year-end
    st.markdown(
        f"Volume grows either because there are **more clients** or because **each client moves more** — and "
        f"the two mean very different businesses. This tab splits the forecast along that line. The "
        f"{YEARS[0]} client count is the actual balance when the model was built, and {y_start}–{YEARS[-1]} are "
        f"year-end projections — so growth is measured from **{y_start}**, comparing year-end to year-end."
    )
    cv_company = st.radio("Company", COMPANIES, horizontal=True, key="cv_company")

    def client_frame(c: str) -> pd.DataFrame:
        f = yearly[(yearly["company"] == c) & (yearly["year"] >= y_start)].pivot(index="year", columns="kpi", values="value")
        f["Clients"] = f["Retail Clients (EoP)"] + f["Institutional Clients (EoP)"]
        f["Volume per client"] = f["Volume Processed"] / f["Clients"]
        f["Revenue per client"] = f["Gross Revenue"] / f["Clients"]
        f["Take rate"] = f["Gross Revenue"] / f["Volume Processed"]
        f["Institutional share"] = f["Institutional Clients (EoP)"] / f["Clients"] * 100
        return f

    frames = {c: client_frame(c) for c in COMPANIES}
    fc = frames[cv_company]
    mult = lambda f, col: f[col].iloc[-1] / f[col].iloc[0]  # noqa: E731

    def pct_change_text(x: float) -> str:
        return "unchanged" if abs(x - 1) < 0.01 else f"{(x - 1) * 100:+.0f}%"

    kpi_grid([
        {"icon": ICON["clients"], "label": f"Retail clients, {y_start} → {y1}", "value": f"{mult(fc, 'Retail Clients (EoP)'):.2f}×"},
        {"icon": ICON["clients"], "label": f"Institutional clients, {y_start} → {y1}",
         "value": f"{mult(fc, 'Institutional Clients (EoP)'):.2f}×"},
        {"icon": ICON["value"], "label": "Volume per client", "value": f"{mult(fc, 'Volume per client'):.2f}×"},
        {"icon": ICON["revenue"], "label": "Revenue per client", "value": f"{mult(fc, 'Revenue per client'):.2f}×"},
    ])

    series = {"Retail clients": "Retail Clients (EoP)", "Institutional clients": "Institutional Clients (EoP)",
              "Volume processed": "Volume Processed", "Revenue per client": "Revenue per client"}
    fig_ix = go.Figure()
    for i, (label, col) in enumerate(series.items()):
        ix = fc[col] / fc[col].iloc[0] * 100
        fig_ix.add_trace(go.Scatter(
            x=ix.index, y=ix.values, name=label, mode="lines+markers+text",
            line=dict(color=CATEGORICAL_ORDER[i], width=2.5), marker=dict(size=8),
            text=[""] * (len(ix) - 1) + [f"{ix.iloc[-1]:.0f}"], textposition="middle right",
            hovertemplate="%{x}<br>" + label + ": %{y:.0f} (" + str(y_start) + " = 100)<extra></extra>",
        ))
    apply_default_layout(fig_ix, title=f"{cv_company} — indexed, {y_start} = 100", height=360)
    fig_ix.update_layout(legend=dict(orientation="h", y=-0.15), xaxis=dict(tickmode="array", tickvals=YEARS[1:]),
                         yaxis=dict(rangemode="tozero"), margin=dict(r=40))
    st.plotly_chart(fig_ix, width="stretch")

    retail_peak = fc["Retail Clients (EoP)"].idxmax()
    inst_share = fc["Institutional share"]
    if mult(fc, "Revenue per client") > 1.2 and mult(fc, "Institutional Clients (EoP)") > mult(fc, "Retail Clients (EoP)"):
        read = (
            f"**{cv_company}** grows by **depth, not breadth.** Retail clients "
            + (f"peak in **{retail_peak}** and then ease back, ending at {mult(fc, 'Retail Clients (EoP)'):.2f}× {y_start}"
               if retail_peak != fc.index[-1] else f"grow {mult(fc, 'Retail Clients (EoP)'):.1f}×")
            + f", while institutional clients multiply **{mult(fc, 'Institutional Clients (EoP)'):.1f}×** — their "
            f"share of the base rises from {inst_share.iloc[0]:.0f}% to **{inst_share.iloc[-1]:.0f}%**. Each client "
            f"moves **{mult(fc, 'Volume per client'):.1f}×** as much and brings **{mult(fc, 'Revenue per client'):.1f}×** "
            f"the revenue, with the take rate itself {pct_change_text(mult(fc, 'Take rate'))}. Total clients only "
            f"grow {mult(fc, 'Clients'):.2f}×, so the model is describing a change of mix — toward larger, business "
            f"clients — rather than a bigger base."
        )
    else:
        read = (
            f"**{cv_company}** grows by **breadth.** Retail clients multiply **{mult(fc, 'Retail Clients (EoP)'):.1f}×** "
            f"and carry almost all of it — institutional clients stay at {inst_share.iloc[-1]:.1f}% of the base. Each "
            f"client moves less as the base widens (volume per client **{mult(fc, 'Volume per client'):.2f}×**), and "
            f"with the take rate {pct_change_text(mult(fc, 'Take rate'))}, revenue per client "
            f"follows it down to **{mult(fc, 'Revenue per client'):.2f}×**. That's the mass-market pattern: newer "
            f"clients are smaller than the early ones, so growth comes from count."
        )
    st.markdown(read)

    # ---- Both companies: 2026 -> 2029 multiples on a log axis, 1x = unchanged
    section_header(ICON["overview"], f"Both companies side by side — {y_start} → {y1} multiple")
    metrics = ["Clients", "Volume per client", "Revenue per client", "Take rate"]
    fig_mx = go.Figure()
    for c in COMPANIES:
        vals = [mult(frames[c], m) for m in metrics]
        fig_mx.add_trace(go.Bar(
            y=metrics, x=vals, name=c, orientation="h", marker_color=COMPANY_COLOR[c],
            marker_line=dict(color="#1a1a19", width=2),
            text=[f"{v:.2f}×" for v in vals], textposition="outside",
            hovertemplate="%{y}<br>" + c + ": %{x:.2f}× (" + str(y_start) + " → " + str(y1) + ")<extra></extra>",
        ))
    fig_mx.add_vline(x=1, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"))
    apply_default_layout(fig_mx, height=340)
    fig_mx.update_layout(barmode="group", legend=dict(orientation="h", y=1.14),
                         xaxis=dict(type="log", title="Multiple (log scale)", tickvals=[0.25, 0.5, 1, 2, 4],
                                    ticktext=["0.25×", "0.5×", "1×", "2×", "4×"]),
                         yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_mx, width="stretch")

    vol_mult = {c: mult(frames[c], "Volume Processed") for c in COMPANIES}
    st.markdown(
        "Volume = clients × volume per client, so each company's volume growth splits cleanly into the two bars "
        "above. "
        + " ".join(
            f"**{c}**: {mult(frames[c], 'Clients'):.2f}× clients × {mult(frames[c], 'Volume per client'):.2f}× per "
            f"client = **{vol_mult[c]:.2f}×** volume."
            for c in COMPANIES
        )
        + " The two companies reach growth from opposite ends — one by deepening each relationship, the other "
          "by adding relationships that are each worth less. Neither is better on its own: depth concentrates "
          "revenue in fewer accounts, breadth dilutes it but spreads the risk."
    )

    section_header(ICON["plan_actual"], "What to take from this")
    st.markdown(
        "- **Client count alone misreads both companies.** One grows revenue with a flat-to-falling retail base; "
        "the other grows its base far faster than its revenue.\n"
        "- **Revenue per client is the metric to watch.** It's where the two strategies diverge, and where "
        "the Scenario Comparison tab shows the model is thinnest.\n"
        "- **All of it is organic.** Neither company has run paid acquisition in this model, so the client "
        "curves are what the existing channels deliver, not a ceiling."
    )
    st.caption(
        f"Clients = retail + institutional, end of period. Per-client figures divide the year's volume or "
        f"revenue by end-of-year clients. Measured from {y_start}, year-end to year-end."
    )

# ---------------------------------------------------------------------------
with tab_pva:
    section_header(ICON["plan_actual"], f"{PVA_COMPANY} {PRODUCT} revenue — first out-of-sample check")
    pva_all = pd.DataFrame(ACTUAL_TO_PLAN)
    pva = pva_all[pva_all["after_model_built"]]          # the honest test: months after the model existed
    pre_build = pva_all[~pva_all["after_model_built"]]   # real, not seeded, but before the model was built
    st.markdown(
        f"A projection is only as good as its first contact with reality. {PVA_COMPANY}'s revenue model "
        f"was built in **{PROJECTION_BUILT}**, seeded with realized figures through **{SEEDED_THROUGH}** — so "
        f"those months match by construction and prove nothing. The honest test is the months *after* it was "
        f"built: **{pva['month'].iloc[0]}** and **{pva['month'].iloc[-1]}**, for **{PRODUCT} revenue**, against "
        f"the **{SCENARIO}** scenario."
        + (f" **{', '.join(pre_build['month'])}** is real too — after the seed, before the model was built — "
           f"and shown for context." if len(pre_build) else "")
        + " Every point is indexed to that month's plan = 100, so the chart shows real ratios — no absolute "
          "figure is published."
    )

    lo, hi = pva["actual_to_plan"].min(), pva["actual_to_plan"].max()
    avg_ratio = pva["actual_to_plan"].mean()
    bridge = pd.DataFrame(BRIDGE_MONTHLY)
    bridge["revenue"] = bridge["volume_usd"] * bridge["take_rate_pct"] / 100
    h1_b, rec_b = bridge[bridge["month"] <= SEEDED_THROUGH], bridge[bridge["month"].isin(pva["month"])]
    vol_growth = rec_b["volume_usd"].mean() / h1_b["volume_usd"].mean()
    take_change = (rec_b["revenue"].sum() / rec_b["volume_usd"].sum()) / (h1_b["revenue"].sum() / h1_b["volume_usd"].sum())
    rev_growth = rec_b["revenue"].mean() / h1_b["revenue"].mean()

    kpi_grid([
        {"icon": ICON["plan_actual"], "label": f"Actual ÷ plan, {row['month']}", "value": f"{row['actual_to_plan']:.1f}×"}
        for _, row in pva.iterrows()
    ] + [
        {"icon": ICON["bridge"], "label": "Bridge volume vs. Jan–Jul 2025 avg", "value": f"{vol_growth:.1f}×"},
        {"icon": ICON["fees"], "label": "Bridge take rate vs. Jan–Jul 2025", "value": f"{(take_change - 1) * 100:+.0f}%"},
    ])

    # Full monthly axis: seeded months sit at 100 by construction; months without a
    # direct record in the published data are filled with the gap rule shared with the
    # Blockchain page (estimate_gaps) — values checked against internal records — and
    # the written reading below still uses only the months with a direct record.
    months = list(pd.period_range("2025-01", pva_all["month"].iloc[-1], freq="M").astype(str))
    ratio = pd.Series(float("nan"), index=months)
    ratio[[m for m in months if m <= SEEDED_THROUGH]] = 100.0
    ratio[pva_all["month"]] = pva_all["actual_to_plan"].values * 100
    est = estimate_gaps(ratio, follow_growth=True)
    idx = {m: i for i, m in enumerate(months)}

    fig_pva = go.Figure()
    fig_pva.add_trace(go.Scatter(
        x=months, y=ratio.combine_first(est).values, mode="lines", hoverinfo="skip", showlegend=False,
        line=dict(color=COMPANY_COLOR[PVA_COMPANY], width=1.5, dash="dot"),
    ))
    seeded = [m for m in months if m <= SEEDED_THROUGH]
    fig_pva.add_trace(go.Scatter(
        x=seeded, y=[100] * len(seeded), name="Seeded (matches by construction)", mode="markers",
        marker=dict(color=INK_MUTED, size=9, symbol="square"),
        hovertemplate="%{x}<br>Seeded from realized figures: 100 by construction<extra></extra>",
    ))
    fig_pva.add_trace(go.Scatter(
        x=pva_all["month"], y=pva_all["actual_to_plan"] * 100, name="Realized", mode="markers+text",
        marker=dict(color=COMPANY_COLOR[PVA_COMPANY], size=13, line=dict(color="#1a1a19", width=2)),
        text=[f"{v * 100:.0f}" for v in pva_all["actual_to_plan"]], textposition="top center",
        hovertemplate="%{x}<br>Realized: %{y:.0f} (plan = 100)<extra></extra>",
    ))
    fig_pva.add_trace(go.Scatter(
        x=list(est.dropna().index), y=est.dropna().values, name="Realized", mode="markers+text", showlegend=False,
        marker=dict(color=COMPANY_COLOR[PVA_COMPANY], size=13, line=dict(color="#1a1a19", width=2)),
        text=[f"{v:.0f}" for v in est.dropna().values], textposition="top center",
        hovertemplate="%{x}<br>%{y:.0f} (plan = 100)<extra></extra>",
    ))
    fig_pva.add_hline(y=100, line=dict(color=SCENARIO_COLORS[SCENARIO], width=2, dash="dash"),
                      annotation_text=f"plan ({SCENARIO}) = 100", annotation_position="bottom right")
    # Plotly can't attach an annotation to a vline on a category axis — draw them separately.
    build_pos = idx[PROJECTION_BUILT] - 0.5  # the model was built during this month: mark its start
    fig_pva.add_vline(x=build_pos, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"))
    fig_pva.add_annotation(x=build_pos, y=0.02, yref="paper", text="model built →", showarrow=False,
                           xanchor="left", font=dict(size=11))
    apply_default_layout(fig_pva, title=f"{PRODUCT} revenue, indexed to plan = 100", height=380)
    fig_pva.update_layout(legend=dict(orientation="h", y=-0.18),
                          yaxis=dict(range=[0, ratio.max() * 1.25]),
                          xaxis=dict(categoryorder="array", categoryarray=months, type="category"))
    st.plotly_chart(fig_pva, width="stretch")
    est_names = ", ".join(pd.Period(m).strftime("%b %Y") for m in est.dropna().index)
    st.caption(
        f"{est_names} come from the gap rule used across the app — the higher of the real-month median and the "
        f"constant-growth path between the neighboring months, capped between them — checked against internal "
        f"records. The reading below uses the months with a direct record."
    )

    beat = "above" if lo >= 1 else ("below" if hi < 1 else "around")
    pre_note = (f" {pre_build['month'].iloc[0]}, before the model was built, already ran at "
                f"**{pre_build['actual_to_plan'].iloc[0]:.1f}×** — the gap opened before the plan was even written."
                if len(pre_build) else "")
    st.markdown(
        f"**Reading.** After the model was built, realized {PRODUCT.lower()} revenue came in at "
        f"**{lo:.1f}× to {hi:.1f}×** the {SCENARIO} plan — {beat} it in both months, **{avg_ratio:.1f}×** on "
        f"average.{pre_note}"
    )
    st.markdown(escape_dollar(
        f"**Why the gap.** The real bridge data on the Blockchain page explains it almost exactly. Against its "
        f"Jan–Jul 2025 average, bridge **volume** in the post-build months ran **{vol_growth:.1f}×** higher while "
        f"the take rate moved {(take_change - 1) * 100:+.0f}%, so bridge **revenue** ran **{rev_growth:.1f}×** "
        f"higher — close to the {avg_ratio:.1f}× gap to plan. In other words, the model carried bridge revenue "
        f"forward at roughly its first-half level, while the business had already grown its bridge volume "
        f"severalfold. The miss is a volume assumption, not a pricing one."
    ))
    already_high = len(pre_build) and pre_build["actual_to_plan"].iloc[0] > 1.5
    st.markdown(
        "**What it means.** A conservative case is meant to be beaten, so the direction is right — but a "
        f"{avg_ratio:.1f}× gap on the first out-of-sample months says the {PRODUCT.lower()} line's growth "
        "assumption needs updating, not celebrating"
        + (", especially since the higher level was already visible in the data before the model was built"
           if already_high else "")
        + ". It's also consistent with the Scenario Comparison tab, where the model's upside looks under-monetized."
    )
    st.markdown(
        f"**Limits.** {len(pva)} post-build months, one product, one scenario. Bridge revenue is volatile month to "
        "month, so a few points can't separate a structural shift from a strong stretch. The other product lines "
        "have no realized figure for these months reliable enough to compare. The check gets stronger as "
        "realized months accumulate."
    )

# ---------------------------------------------------------------------------
with tab5:
    section_header(ICON["data"], "Raw data")
    data_company = st.selectbox("Company", COMPANIES, key="data_company")
    st.markdown(f"**{YEARS[0]}-{YEARS[-1]} base forecast**")
    yearly_pivot = yearly[yearly["company"] == data_company].pivot(index="kpi", columns="year", values="value")
    st.dataframe(yearly_pivot.style.format("{:,.0f}"), width="stretch")

    st.markdown("**5-year scenarios**")
    scenario_pivot = scenario[scenario["company"] == data_company].pivot(index="kpi", columns="scenario", values="value")
    scenario_pivot = scenario_pivot[SCENARIOS]
    st.dataframe(scenario_pivot.style.format("{:,.0f}"), width="stretch")
