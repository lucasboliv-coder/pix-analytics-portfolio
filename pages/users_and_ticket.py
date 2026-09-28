import calendar
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_gen.generator import END_DATE, START_DATE, load_data
from theme.charts import CATEGORICAL, COLOR_PIX_IN, COLOR_PIX_OUT, apply_default_layout
from theme.icons import ICON, mi
from theme.narrative import escape_dollar, yoy_story
from theme.style import kpi_grid, period_badge, section_header

st.title(f"{mi(ICON['users_page'])} Active Users & Avg Ticket")

data = load_data()
users = data["users"]
pix_in, pix_out = data["pix_in"].copy(), data["pix_out"].copy()

st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Period (created_at)",
    value=(START_DATE, END_DATE),
    min_value=START_DATE,
    max_value=END_DATE,
)
start, end = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (START_DATE, END_DATE)
if start > end:
    start, end = end, start

mask_in = (pix_in["created_at"].dt.date >= start) & (pix_in["created_at"].dt.date <= end)
mask_out = (pix_out["created_at"].dt.date >= start) & (pix_out["created_at"].dt.date <= end)
pix_in, pix_out = pix_in[mask_in], pix_out[mask_out]

for df in (pix_in, pix_out):
    df["month"] = df["created_at"].dt.to_period("M")
    df["year"] = df["created_at"].dt.year
    df["month_num"] = df["created_at"].dt.month

period_badge(f"{start:%m/%d/%Y} — {end:%m/%d/%Y}")

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
active_in = pix_in["user_id"].nunique()
active_out = pix_out["user_id"].nunique()
active_total = pd.concat([pix_in["user_id"], pix_out["user_id"]]).nunique()
total_volume = pix_in["amount_brl"].sum() + pix_out["amount_brl"].sum()
n_transactions = len(pix_in) + len(pix_out)
avg_ticket = total_volume / n_transactions if n_transactions else 0

kpi_grid(
    [
        {"icon": ICON["pix_in"], "label": "Active — PIX In", "value": f"{active_in:,}"},
        {"icon": ICON["pix_out"], "label": "Active — PIX Out", "value": f"{active_out:,}"},
        {"icon": ICON["unique_users"], "label": "Unique users (total)", "value": f"{active_total:,}"},
        {"icon": ICON["avg_ticket"], "label": "Average ticket", "value": f"R$ {avg_ticket:,.2f}"},
    ]
)

tab1, tab2, tab3, tab4 = st.tabs([
    f"{mi(ICON['growth'])} Monthly Trend",
    f"{mi(ICON['yoy'])} Year-over-Year",
    f"{mi(ICON['avg_ticket'])} Avg Ticket",
    f"{mi(ICON['data'])} Data",
])

with tab1:
    section_header(ICON["growth"], "Active users by month — PIX In vs PIX Out")
    m_in = pix_in.groupby("month")["user_id"].nunique().reset_index(name="Active Users")
    m_out = pix_out.groupby("month")["user_id"].nunique().reset_index(name="Active Users")
    m_in["month"] = m_in["month"].astype(str)
    m_out["month"] = m_out["month"].astype(str)
    # Growth % rides along as hover detail instead of a separate table column
    # — one chart carries the same information a two-table-plus-column layout
    # used to, with In/Out directly comparable on one axis.
    growth_in = m_in["Active Users"].pct_change().mul(100).fillna(0)
    growth_out = m_out["Active Users"].pct_change().mul(100).fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=m_in["month"], y=m_in["Active Users"], name="PIX In", mode="lines+markers",
        line=dict(color=COLOR_PIX_IN, width=2.5, shape="spline", smoothing=0.3),
        marker=dict(size=6),
        customdata=growth_in,
        hovertemplate="%{x}<br>Active users: %{y:,.0f}<br>MoM growth: %{customdata:+.1f}%<extra>PIX In</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=m_out["month"], y=m_out["Active Users"], name="PIX Out", mode="lines+markers",
        line=dict(color=COLOR_PIX_OUT, width=2.5, shape="spline", smoothing=0.3),
        marker=dict(size=6),
        customdata=growth_out,
        hovertemplate="%{x}<br>Active users: %{y:,.0f}<br>MoM growth: %{customdata:+.1f}%<extra>PIX Out</extra>",
    ))
    apply_default_layout(fig, height=380)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    section_header(ICON["yoy"], "Year-over-year comparison — active users")
    y_in = pix_in.groupby(["month_num", "year"])["user_id"].nunique().unstack(fill_value=0)
    y_out = pix_out.groupby(["month_num", "year"])["user_id"].nunique().unstack(fill_value=0)
    yearly = y_in.add(y_out, fill_value=0).astype(int)
    years = sorted(yearly.columns)
    if len(years) >= 2:
        y_prev, y_curr = years[-2], years[-1]
        month_labels = [calendar.month_abbr[m] for m in yearly.index]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=month_labels, y=yearly[y_prev], name=str(y_prev), marker_color=CATEGORICAL["violet"]))
        fig.add_trace(go.Bar(x=month_labels, y=yearly[y_curr], name=str(y_curr), marker_color=CATEGORICAL["blue"]))
        fig.update_layout(barmode="group")
        apply_default_layout(fig, height=360)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(yoy_story(yearly[y_prev], yearly[y_curr], y_prev, y_curr, lambda v: f"{v:,.0f}"))
    else:
        st.info("More than one year in the selected period is needed to compare.")

with tab3:
    section_header(ICON["avg_ticket"], "Average ticket by month — PIX In vs PIX Out")
    t_in = pix_in.groupby("month")["amount_brl"].agg(["mean", "count", "sum"]).reset_index()
    t_out = pix_out.groupby("month")["amount_brl"].agg(["mean", "count", "sum"]).reset_index()
    t_in["month"] = t_in["month"].astype(str)
    t_out["month"] = t_out["month"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t_in["month"], y=t_in["mean"], name="PIX In", mode="lines+markers",
        line=dict(color=COLOR_PIX_IN, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
        customdata=np.column_stack([t_in["count"], t_in["sum"]]),
        hovertemplate="%{x}<br>Avg ticket: R$ %{y:,.2f}<br>Transactions: %{customdata[0]:,.0f}"
                       "<br>Volume: R$ %{customdata[1]:,.0f}<extra>PIX In</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=t_out["month"], y=t_out["mean"], name="PIX Out", mode="lines+markers",
        line=dict(color=COLOR_PIX_OUT, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
        customdata=np.column_stack([t_out["count"], t_out["sum"]]),
        hovertemplate="%{x}<br>Avg ticket: R$ %{y:,.2f}<br>Transactions: %{customdata[0]:,.0f}"
                       "<br>Volume: R$ %{customdata[1]:,.0f}<extra>PIX Out</extra>",
    ))
    apply_default_layout(fig, height=380)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    avg_in, avg_out = t_in["mean"].mean(), t_out["mean"].mean()
    higher, lower = ("In", "Out") if avg_in >= avg_out else ("Out", "In")
    diff_pct = abs(avg_in - avg_out) / min(avg_in, avg_out) * 100 if min(avg_in, avg_out) else 0
    st.markdown(escape_dollar(
        f"Across the period, the average PIX **{higher}** ticket (R$ {max(avg_in, avg_out):,.2f}) runs "
        f"**{diff_pct:.0f}% higher** than PIX **{lower}** (R$ {min(avg_in, avg_out):,.2f})."
    ))

with tab4:
    section_header(ICON["overview"], "General data")
    kpi_grid(
        [
            {"icon": ICON["wallet"], "label": "Unique wallets", "value": f"{users['wallet'].nunique():,}"},
            {"icon": ICON["calendar"], "label": "Analyzed period", "value": f"{start:%m/%d/%Y} – {end:%m/%d/%Y}"},
        ]
    )
    section_header(ICON["data"], "Raw data (sample)")
    with st.expander("Active users — In"):
        st.dataframe(pix_in.head(200))
    with st.expander("Active users — Out"):
        st.dataframe(pix_out.head(200))
