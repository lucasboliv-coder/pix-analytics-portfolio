import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_gen.generator import END_DATE, START_DATE, load_data
from theme.charts import COLOR_PIX_IN, COLOR_PIX_OUT, STATUS, apply_default_layout
from theme.icons import ICON, mi
from theme.narrative import yoy_story
from theme.style import kpi_grid, period_badge, section_header

st.title(f"{mi(ICON['pix_page'])} PIX In / Out")

data = load_data()
pix_in, pix_out = data["pix_in"].copy(), data["pix_out"].copy()
pix_in["direction"], pix_out["direction"] = "In", "Out"
df_all = pd.concat([pix_in, pix_out], ignore_index=True)

st.sidebar.header("Filters")
date_range = st.sidebar.date_input("Date range", value=(START_DATE, END_DATE),
                                    min_value=START_DATE, max_value=END_DATE)
start, end = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (START_DATE, END_DATE)
if start > end:
    start, end = end, start

status_options = ["All"] + sorted(df_all["status"].unique().tolist())
status_sel = st.sidebar.selectbox("Status", status_options)

df_all = df_all[(df_all["created_at"].dt.date >= start) & (df_all["created_at"].dt.date <= end)]
if status_sel != "All":
    df_all = df_all[df_all["status"] == status_sel]

min_v, max_v = float(df_all["amount_brl"].min()), float(df_all["amount_brl"].max())
value_range = st.sidebar.slider("Amount (R$)", min_v, max_v, (min_v, max_v))
df_all = df_all[(df_all["amount_brl"] >= value_range[0]) & (df_all["amount_brl"] <= value_range[1])]

df_all["month"] = df_all["created_at"].dt.to_period("M")
df_all["year"] = df_all["created_at"].dt.year
df_all["month_num"] = df_all["created_at"].dt.month

period_badge(f"{start:%m/%d/%Y} — {end:%m/%d/%Y}")

direction_sel = st.radio("Direction", ["Combined", "In", "Out"], horizontal=True)
df = df_all if direction_sel == "Combined" else df_all[df_all["direction"] == direction_sel]

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
kpi_grid(
    [
        {"icon": ICON["revenue"], "label": "Total volume", "value": f"R$ {df['amount_brl'].sum():,.0f}"},
        {"icon": ICON["fees"], "label": "Total fees", "value": f"R$ {df['fee_brl'].sum():,.0f}"},
        {"icon": ICON["avg_ticket"], "label": "Average ticket", "value": f"R$ {df['amount_brl'].mean():,.2f}" if len(df) else "R$ 0.00"},
        {"icon": ICON["transactions"], "label": "Transactions", "value": f"{len(df):,}"},
    ]
)

tab1, tab2, tab3, tab4 = st.tabs([
    f"{mi(ICON['overview'])} Overview",
    f"{mi(ICON['calendar'])} Time & Yearly",
    f"{mi(ICON['search'])} Transactions",
    f"{mi(ICON['correlation'])} Correlation",
])

with tab1:
    section_header(ICON["overview"], "Volume by month")
    col1, col2 = st.columns(2)
    with col1:
        if direction_sel == "Combined":
            monthly = df_all.groupby(["month", "direction"])["amount_brl"].sum().reset_index()
            monthly["month"] = monthly["month"].astype(str)
            fig = px.bar(monthly, x="month", y="amount_brl", color="direction", barmode="group",
                         color_discrete_map={"In": COLOR_PIX_IN, "Out": COLOR_PIX_OUT},
                         labels={"amount_brl": "Volume (R$)", "month": "Month", "direction": "Direction"})
        else:
            monthly = df.groupby("month")["amount_brl"].sum().reset_index()
            monthly["month"] = monthly["month"].astype(str)
            color = COLOR_PIX_IN if direction_sel == "In" else COLOR_PIX_OUT
            fig = px.bar(monthly, x="month", y="amount_brl", labels={"amount_brl": "Volume (R$)", "month": "Month"})
            fig.update_traces(marker_color=color)
        apply_default_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig2 = px.pie(status_counts, values="Count", names="Status", hole=0.55,
                      color="Status", color_discrete_map=STATUS)
        apply_default_layout(fig2, title="Status distribution")
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    section_header(ICON["yoy"], "Year-over-year comparison")
    years = sorted(df["year"].unique())
    pivot = df.groupby(["month_num", "year"])["amount_brl"].sum().unstack(fill_value=0)
    fig3 = go.Figure()
    for year in pivot.columns:
        fig3.add_trace(go.Scatter(x=pivot.index, y=pivot[year], name=str(year), mode="lines+markers"))
    apply_default_layout(fig3, title="Monthly volume by year", height=380)
    fig3.update_layout(xaxis=dict(
        tickmode="array", tickvals=list(range(1, 13)),
        ticktext=[calendar.month_abbr[m] for m in range(1, 13)],
    ))
    st.plotly_chart(fig3, use_container_width=True)

    if len(years) >= 2:
        y_prev, y_curr = years[-2], years[-1]
        st.markdown(yoy_story(pivot[y_prev], pivot[y_curr], y_prev, y_curr, lambda v: f"R$ {v:,.0f}"))

with tab3:
    section_header(ICON["search"], "High-value transactions")
    high_value = df[df["amount_brl"] > df["amount_brl"].quantile(0.97)]
    st.dataframe(high_value[["user_id", "direction", "amount_brl", "fee_brl", "status", "created_at"]]
                 .sort_values("amount_brl", ascending=False).head(50), use_container_width=True)

with tab4:
    section_header(ICON["correlation"], "Amount × Fee")
    fig4 = px.scatter(df.sample(min(len(df), 3000), random_state=42), x="amount_brl", y="fee_brl",
                      trendline="ols", opacity=0.5,
                      labels={"amount_brl": "Amount (R$)", "fee_brl": "Fee (R$)"})
    fig4.update_traces(marker=dict(color="#3987e5"))
    apply_default_layout(fig4, height=400)
    st.plotly_chart(fig4, use_container_width=True)
    st.caption(f"Correlation (Pearson): {df['amount_brl'].corr(df['fee_brl']):.2f}")
