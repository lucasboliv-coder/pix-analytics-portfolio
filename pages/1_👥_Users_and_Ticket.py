from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_gen.generator import END_DATE, START_DATE, load_data
from theme.charts import COLOR_PIX_IN, COLOR_PIX_OUT, apply_default_layout, register_template
from theme.style import inject_css, kpi_grid, period_badge, section_header

st.set_page_config(page_title="Users & Avg Ticket · PixFlow", layout="wide", page_icon="👥")
inject_css()
register_template()

st.title("👥 Active Users & Avg Ticket")

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
        {"icon": "📥", "label": "Active — PIX In", "value": f"{active_in:,}"},
        {"icon": "📤", "label": "Active — PIX Out", "value": f"{active_out:,}"},
        {"icon": "🧑‍🤝‍🧑", "label": "Unique users (total)", "value": f"{active_total:,}"},
        {"icon": "💰", "label": "Average ticket", "value": f"R$ {avg_ticket:,.2f}"},
    ]
)

# ---------------------------------------------------------------------------
# Growth chart (in vs out)
# ---------------------------------------------------------------------------
section_header("📈", "Active user growth by month")

series_in = pix_in.groupby("month")["user_id"].nunique().rename("PIX In")
series_out = pix_out.groupby("month")["user_id"].nunique().rename("PIX Out")
series = pd.concat([series_in, series_out], axis=1).fillna(0).sort_index()
series.index = series.index.astype(str)

fig = go.Figure()
fig.add_trace(go.Scatter(x=series.index, y=series["PIX In"], name="PIX In",
                          mode="lines", stackgroup="active", line=dict(color=COLOR_PIX_IN, width=2)))
fig.add_trace(go.Scatter(x=series.index, y=series["PIX Out"], name="PIX Out",
                          mode="lines", stackgroup="active", line=dict(color=COLOR_PIX_OUT, width=2)))
apply_default_layout(fig, height=340)
st.plotly_chart(fig, use_container_width=True)


def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    """Formats a monthly active-users series as clean display strings.

    Plain st.dataframe (not a pandas Styler) so the table renders through
    Streamlit's own grid and picks up the app's dark theme — a Styler's
    background_gradient() paints its own light HTML table that clashes with it.
    """
    growth = df["Active Users"].pct_change().mul(100).fillna(0)
    return pd.DataFrame(
        {
            "Month": df["month"],
            "Active Users": df["Active Users"].map("{:,.0f}".format),
            "Growth %": growth.map("{:+.1f}%".format),
        }
    )


tab1, tab2, tab3, tab4 = st.tabs(["📈 Monthly Matrix", "🔄 Year-over-Year", "💰 Avg Ticket", "📋 Data"])

with tab1:
    section_header("📥", "Active users — PIX In")
    m_in = pix_in.groupby("month")["user_id"].nunique().reset_index(name="Active Users")
    m_in["month"] = m_in["month"].astype(str)
    st.dataframe(monthly_table(m_in), hide_index=True, use_container_width=True)

    section_header("📤", "Active users — PIX Out")
    m_out = pix_out.groupby("month")["user_id"].nunique().reset_index(name="Active Users")
    m_out["month"] = m_out["month"].astype(str)
    st.dataframe(monthly_table(m_out), hide_index=True, use_container_width=True)

with tab2:
    section_header("🔄", "Year-over-year comparison — active users")
    y_in = pix_in.groupby(["month_num", "year"])["user_id"].nunique().unstack(fill_value=0)
    y_out = pix_out.groupby(["month_num", "year"])["user_id"].nunique().unstack(fill_value=0)
    yearly = y_in.add(y_out, fill_value=0).astype(int)
    years = sorted(yearly.columns)
    if len(years) >= 2:
        y_prev, y_curr = years[-2], years[-1]
        difference = yearly[y_curr] - yearly[y_prev]
        difference_pct = (difference / yearly[y_prev].replace(0, pd.NA) * 100).fillna(0)
        comparison = pd.DataFrame(
            {
                "Month": yearly.index,
                str(y_prev): yearly[y_prev].map("{:,.0f}".format),
                str(y_curr): yearly[y_curr].map("{:,.0f}".format),
                "Difference": difference.map("{:+,.0f}".format),
                "Difference %": difference_pct.map("{:+.1f}%".format),
            }
        )
        st.dataframe(comparison, hide_index=True, use_container_width=True)
    else:
        st.info("More than one year in the selected period is needed to compare.")

with tab3:
    section_header("💰", "Average ticket — PIX In")
    t_in = pix_in.groupby("month")["amount_brl"].agg(["mean", "count", "sum"]).reset_index()
    st.dataframe(
        pd.DataFrame(
            {
                "Month": t_in["month"].astype(str),
                "Avg Ticket (R$)": t_in["mean"].map("R$ {:,.2f}".format),
                "Transactions": t_in["count"].map("{:,.0f}".format),
                "Total Volume (R$)": t_in["sum"].map("R$ {:,.0f}".format),
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    section_header("💰", "Average ticket — PIX Out")
    t_out = pix_out.groupby("month")["amount_brl"].agg(["mean", "count", "sum"]).reset_index()
    st.dataframe(
        pd.DataFrame(
            {
                "Month": t_out["month"].astype(str),
                "Avg Ticket (R$)": t_out["mean"].map("R$ {:,.2f}".format),
                "Transactions": t_out["count"].map("{:,.0f}".format),
                "Total Volume (R$)": t_out["sum"].map("R$ {:,.0f}".format),
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

with tab4:
    section_header("📊", "General data")
    kpi_grid(
        [
            {"icon": "🪪", "label": "Unique wallets", "value": f"{users['wallet'].nunique():,}"},
            {"icon": "📅", "label": "Analyzed period", "value": f"{start:%m/%d/%Y} – {end:%m/%d/%Y}"},
        ]
    )
    section_header("📋", "Raw data (sample)")
    with st.expander("Active users — In"):
        st.dataframe(pix_in.head(200))
    with st.expander("Active users — Out"):
        st.dataframe(pix_out.head(200))
