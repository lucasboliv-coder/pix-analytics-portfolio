import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_gen.generator import END_DATE, START_DATE, load_data
from theme.charts import COLOR_PIX_IN, COLOR_PIX_OUT, STATUS, apply_default_layout
from theme.icons import ICON, mi
from theme.narrative import drop_partial_trailing_month, escape_dollar, monthly_series_story, yoy_story
from theme.style import kpi_grid, period_badge, section_header

st.title(f"{mi(ICON['pix_page'])} PIX Traded")

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
    section_header(ICON["overview"], "Volume traded by month")
    st.markdown(
        "Total PIX volume moved each month, by direction — the base trend the "
        "KPIs above roll up from."
    )

    fig = go.Figure()
    if direction_sel == "Combined":
        monthly_in = df_all[df_all["direction"] == "In"].groupby("month")["amount_brl"].sum().reset_index()
        monthly_out = df_all[df_all["direction"] == "Out"].groupby("month")["amount_brl"].sum().reset_index()
        monthly_in["month"] = monthly_in["month"].astype(str)
        monthly_out["month"] = monthly_out["month"].astype(str)
        for label, monthly, color in (("In", monthly_in, COLOR_PIX_IN), ("Out", monthly_out, COLOR_PIX_OUT)):
            fig.add_trace(go.Scatter(
                x=monthly["month"], y=monthly["amount_brl"], name=label, mode="lines+markers",
                line=dict(color=color, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
                fill="tozeroy", fillcolor=color + "14",
                hovertemplate="%{x}<br>Volume: R$ %{y:,.0f}<extra>" + label + "</extra>",
            ))
    else:
        monthly = df.groupby("month")["amount_brl"].sum().reset_index()
        monthly["month"] = monthly["month"].astype(str)
        color = COLOR_PIX_IN if direction_sel == "In" else COLOR_PIX_OUT
        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["amount_brl"], name=direction_sel, mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
            fill="tozeroy", fillcolor=color + "14",
            hovertemplate="%{x}<br>Volume: R$ %{y:,.0f}<extra>" + direction_sel + "</extra>",
        ))
    apply_default_layout(fig, height=380)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    if direction_sel == "Combined":
        story_in, growth_in = monthly_series_story(
            monthly_in["month"].tolist(), monthly_in["amount_brl"].tolist(), END_DATE, end, lambda v: f"R$ {v:,.0f}"
        )
        story_out, growth_out = monthly_series_story(
            monthly_out["month"].tolist(), monthly_out["amount_brl"].tolist(), END_DATE, end, lambda v: f"R$ {v:,.0f}"
        )
        kpi_grid(
            [
                {"icon": ICON["pix_in"], "label": "PIX In — total change", "value": f"{growth_in:,.0f}%", "positive": growth_in >= 0},
                {"icon": ICON["pix_out"], "label": "PIX Out — total change", "value": f"{growth_out:,.0f}%", "positive": growth_out >= 0},
            ]
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**PIX In** {story_in}")
        with col_b:
            st.markdown(f"**PIX Out** {story_out}")
    else:
        story, growth = monthly_series_story(
            monthly["month"].tolist(), monthly["amount_brl"].tolist(), END_DATE, end, lambda v: f"R$ {v:,.0f}"
        )
        st.markdown(f"**PIX {direction_sel}** {story}")

    section_header(ICON["net_flow"], "Net flow by month")
    st.markdown(
        "Incoming volume minus outgoing, per month — positive means the "
        "operation is a net recipient of funds that month, negative means "
        "more moved out than in."
    )
    net = df_all.groupby(["month", "direction"])["amount_brl"].sum().unstack(fill_value=0)
    net["Net"] = net.get("In", 0) - net.get("Out", 0)
    net = net.reset_index()
    net["month"] = net["month"].astype(str)

    bar_colors = [STATUS["CONFIRMED"] if v >= 0 else STATUS["FAILED"] for v in net["Net"]]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=net["month"], y=net["Net"], marker_color=bar_colors,
        hovertemplate="%{x}<br>Net flow: R$ %{y:,.0f}<extra></extra>",
    ))
    fig3.add_hline(y=0, line_color="rgba(255,255,255,0.18)")
    apply_default_layout(fig3, height=340)
    st.plotly_chart(fig3, use_container_width=True)

    months, values = drop_partial_trailing_month(net["month"].tolist(), net["Net"].tolist(), END_DATE, end)
    total_net = sum(values)
    best_i = max(range(len(values)), key=lambda i: values[i])
    worst_i = min(range(len(values)), key=lambda i: values[i])
    role = "net recipient" if total_net >= 0 else "net payer"
    st.markdown(escape_dollar(
        f"Over the period, the operation is a **{role} of R$ {abs(total_net):,.0f}** overall. "
        f"Strongest net inflow: **{months[best_i]}** (R$ {values[best_i]:+,.0f}); "
        f"weakest: **{months[worst_i]}** (R$ {values[worst_i]:+,.0f})."
    ))

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
