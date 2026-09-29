import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_gen.fiat_real import FIAT_MONTHLY, METHOD_MIX_2025, SEP_2025, USERS_MONTHLY
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

# ===========================================================================
# Real data (masked) — independent of the sidebar filters.
# ===========================================================================
section_header(ICON["lock"], "Real data — masked")
st.markdown(
    "Aggregated from the real records of the group's crypto-payments company. Counts and dollar "
    "amounts are masked (see Home); **growth rates, shares and take rates are the real ones**. Values "
    "in US\\$. The sidebar filters don't apply to this block."
)
st.markdown(
    "**How to read it.** Every crypto purchase or sale starts or ends in BRL, and the BRL leg runs on "
    "one of three **fiat rails**: **PIX** (Brazil's instant payment system, 24/7), **boleto** (a "
    "bank slip that settles in a day or two) and **ATM** cash. The platform charges a fee on that leg, "
    "so its fiat revenue is simply *volume × take rate* on each rail. The block looks at how volume "
    "grew, where it runs, what each rail earns, and when in the week the money moves."
)

rf = pd.DataFrame(FIAT_MONTHLY)
rf["ticket"] = rf["volume_usd"] / rf["transactions"]
mix = pd.DataFrame(METHOD_MIX_2025).T
mix["revenue_weight"] = mix["share_of_volume_pct"] * mix["take_rate_pct"]
blended_take = mix["revenue_weight"].sum() / mix["share_of_volume_pct"].sum()
mix["share_of_revenue_pct"] = mix["revenue_weight"] / mix["revenue_weight"].sum() * 100
by_month = rf.set_index("month")
last_m = rf["month"].iloc[-1]
prev_year_m = f"{int(last_m[:4]) - 1}{last_m[4:]}"
vol_yoy = (by_month.loc[last_m, "volume_usd"] / by_month.loc[prev_year_m, "volume_usd"] - 1) * 100

kpi_grid([
    {"icon": ICON["growth"], "label": f"Fiat volume, YoY ({last_m})", "value": f"{vol_yoy:+.0f}%",
     "positive": vol_yoy >= 0},
    {"icon": ICON["pix_page"], "label": "PIX share of volume (Jan–Jul 2025)",
     "value": f"{METHOD_MIX_2025['PIX']['share_of_volume_pct']:.1f}%"},
    {"icon": ICON["fees"], "label": "Blended take rate (Jan–Jul 2025)", "value": f"{blended_take:.2f}%"},
    {"icon": ICON["status"], "label": "Refund rate (Sep 2025)", "value": f"{SEP_2025['refund_rate_pct']:.1f}%"},
])

# ---- Volume and transactions
section_header(ICON["overview"], "Fiat volume and transactions by month")
fig_rv = go.Figure()
fig_rv.add_trace(go.Bar(
    x=rf["month"], y=rf["transactions"], name="Transactions", yaxis="y2",
    marker_color=COLOR_PIX_OUT + "55", hovertemplate="%{x}<br>Transactions: %{y:,.0f}<extra></extra>",
))
fig_rv.add_trace(go.Scatter(
    x=rf["month"], y=rf["volume_usd"], name="Volume (US$)", mode="lines+markers",
    line=dict(color=COLOR_PIX_IN, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
    hovertemplate="%{x}<br>Volume: US$ %{y:,.0f}<extra></extra>",
))
apply_default_layout(fig_rv, height=360)
fig_rv.update_layout(
    hovermode="x unified", legend=dict(orientation="h", y=1.12),
    yaxis=dict(title="Volume (US$, masked)"),
    yaxis2=dict(title="Transactions (masked)", overlaying="y", side="right", showgrid=False),
)
st.plotly_chart(fig_rv, use_container_width=True)

step = by_month.loc["2024-08", "volume_usd"] / by_month.loc["2024-07", "volume_usd"]
y25 = rf[rf["month"].str.startswith("2025")]
vol_25 = (y25["volume_usd"].iloc[-1] / y25["volume_usd"].iloc[0] - 1) * 100
tx_25 = (y25["transactions"].iloc[-1] / y25["transactions"].iloc[0] - 1) * 100
ticket_25 = (y25["ticket"].iloc[-1] / y25["ticket"].iloc[0] - 1) * 100
# Users and transactions carry the same count masking, so this ratio is real.
au = pd.DataFrame(USERS_MONTHLY).set_index("month")["active_users"]
users_25 = (au[y25["month"].iloc[-1]] / au[y25["month"].iloc[0]] - 1) * 100
tx_per_user = (by_month["transactions"] / au).dropna()
freq_25 = tx_per_user[y25["month"].iloc[-1]] / tx_per_user[y25["month"].iloc[0]]
st.markdown(escape_dollar(
    f"Two different growth modes show up. **2024 grows by size**: volume jumps **{step:.1f}×** from "
    f"July to August 2024 — the same month the withdrawal ticket steps up (see Users & Ticket) — "
    f"while transaction counts rise steadily. **2025 grows by frequency**: from January to December "
    f"transactions move **{tx_25:+.0f}%** and volume **{vol_25:+.0f}%**, so the average ticket changes "
    f"by **{ticket_25:+.0f}%** — and with active users only **{users_25:+.0f}%**, the extra transactions "
    f"come from the same people transacting more often: **{freq_25:.1f}×** as many transactions per "
    f"active user by year-end. Users splitting their flows into more, smaller operations is a sign of "
    f"habit — the platform becoming part of routine money movement — but it's harder on unit "
    f"economics, since each transaction carries roughly the same processing and support cost however "
    f"small it is."
))

# ---- Rails
section_header(ICON["fees"], "Rails — where volume runs and what each earns (Jan–Jul 2025)")
col_mix, col_rate = st.columns(2)
rails = mix.index.tolist()
with col_mix:
    fig_mx = go.Figure()
    for col, label, color in (("share_of_volume_pct", "Share of volume", COLOR_PIX_IN),
                              ("share_of_revenue_pct", "Share of revenue", STATUS["CONFIRMED"])):
        fig_mx.add_trace(go.Bar(
            y=rails, x=mix[col], name=label, orientation="h", marker_color=color,
            text=[f"{v:.1f}%" for v in mix[col]], textposition="outside",
            hovertemplate="%{y}: %{x:.1f}%<extra>" + label + "</extra>",
        ))
    apply_default_layout(fig_mx, title="Share of volume vs. share of revenue", height=300)
    fig_mx.update_layout(barmode="group", xaxis=dict(range=[0, 115], ticksuffix="%"),
                         yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_mx, use_container_width=True)
with col_rate:
    fig_tr = go.Figure(go.Bar(
        x=rails, y=mix["take_rate_pct"], marker_color=[COLOR_PIX_IN, COLOR_PIX_OUT, STATUS["PENDING"]],
        text=[f"{v:.2f}%" for v in mix["take_rate_pct"]], textposition="outside",
        hovertemplate="%{x}: %{y:.2f}% of volume<extra></extra>",
    ))
    apply_default_layout(fig_tr, title="Take rate by rail", height=300)
    fig_tr.update_layout(yaxis=dict(range=[0, mix["take_rate_pct"].max() * 1.3], ticksuffix="%"))
    st.plotly_chart(fig_tr, use_container_width=True)

pix = mix.loc["PIX"]
st.markdown(
    f"PIX carries **{pix['share_of_volume_pct']:.1f}%** of the volume and, even at the lowest take rate "
    f"({pix['take_rate_pct']:.2f}%), **{pix['share_of_revenue_pct']:.0f}%** of the fiat revenue. The "
    f"ordering matches what each rail typically costs to operate in Brazil: boleto "
    f"({mix.loc['Boleto', 'take_rate_pct']:.2f}%) involves bank-slip fees and slower settlement, ATM "
    f"({mix.loc['ATM', 'take_rate_pct']:.2f}%) cash handling. Those rails earn more per dollar but move too little to matter to the total — "
    f"so the blended take rate (**{blended_take:.2f}%**) is effectively the PIX rate, and any pressure "
    f"on PIX pricing hits nearly all fiat revenue at once."
)

# ---- Weekday
section_header(ICON["calendar"], "When the money moves — share of value by weekday (Sep 2025)")
wd = pd.Series(SEP_2025["weekday_share_of_value_pct"])
fig_wd = go.Figure(go.Bar(
    x=wd.index, y=wd.values,
    marker_color=[COLOR_PIX_OUT if d == wd.idxmax() else COLOR_PIX_IN for d in wd.index],
    text=[f"{v:.1f}%" for v in wd.values], textposition="outside",
    hovertemplate="%{x}: %{y:.1f}% of the week's value<extra></extra>",
))
apply_default_layout(fig_wd, height=300)
fig_wd.update_layout(yaxis=dict(range=[0, wd.max() * 1.3], ticksuffix="%"))
st.plotly_chart(fig_wd, use_container_width=True)

weekdays_share = wd[["Mon", "Tue", "Wed", "Thu", "Fri"]].sum()
inbound = SEP_2025["inbound_share_of_value_pct"]
st.markdown(
    f"PIX runs 24/7, yet **{weekdays_share:.0f}%** of the value moves Monday to Friday and "
    f"**{wd.idxmax()}** alone carries **{wd.max():.0f}%** — {wd.max() / (100 / 7):.1f}× an even share. "
    f"Money here follows business routines, not the rail's availability. Operationally, the peak day "
    f"sets the BRL liquidity and the support staffing the platform needs; a weekly average would "
    f"understate both. Over the same four weeks, **{inbound:.0f}%** of the value came in and "
    f"{100 - inbound:.0f}% went out — close to balanced, with inflows and outflows largely offsetting "
    f"each other over the month."
)

section_header(ICON["warning"], "What this data can't tell")
st.markdown(
    "- **The rail mix over time.** Rail shares and take rates cover Jan–Jul 2025 only.\n"
    "- **A typical week.** The weekday pattern is four weeks of one month; a single large client can "
    "move it.\n"
    "- **Why the ticket fell.** The 2025 ticket decline is read from monthly totals, without "
    "user-level data.\n"
    "- **Absolute scale.** Counts and US\\$ amounts are masked — compare them over time, not against "
    "other sources."
)

# ===========================================================================
# Modeled activity (synthetic)
# ===========================================================================
st.divider()
section_header(ICON["dataset"], "Modeled activity — synthetic")
st.markdown(
    "A transaction-level PIX history generated algorithmically (Jan 2024 – Mar 2026), used for the "
    "direction, status and correlation views below. It runs in R\\$, the currency PIX itself settles "
    "in. The sidebar filters apply from here down."
)
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
