import calendar
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_gen.fiat_real import FIAT_MONTHLY, FUNNEL_2025, USERS_MONTHLY
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

# ===========================================================================
# Real data (masked) — independent of the sidebar filters.
# ===========================================================================
section_header(ICON["lock"], "Real data — masked")
st.markdown(
    "Aggregated from the real records of the group's crypto-payments company. Counts and dollar "
    "amounts are masked (see Home); **growth rates, conversion rates and ratios are the real ones**. "
    "Values in US\\$. The sidebar filters don't apply to this block."
)
st.markdown(
    "**How to read it.** A user moves through three stages: **sign-up** (acquisition), **KYC** — "
    "identity verification, required before moving money (activation) — and **transacting** in a "
    "given month (an *active user*, the engagement metric). Growth that only shows up in sign-ups is "
    "marketing; growth that reaches active users is product. The block follows users down that path, "
    "then looks at how much each of them moves."
)

real_users = pd.DataFrame(USERS_MONTHLY)
real_users["yoy_pct"] = real_users["active_users"].pct_change(12) * 100
real_fiat = pd.DataFrame(FIAT_MONTHLY)
funnel = pd.DataFrame(FUNNEL_2025)

last, first = real_users.iloc[-1], real_users.iloc[0]
dec_prev = real_users[real_users["month"] == f"{int(last['month'][:4]) - 1}-{last['month'][5:]}"].iloc[0]
yoy_last = (last["active_users"] / dec_prev["active_users"] - 1) * 100
yoy_first_2025 = real_users[real_users["month"] == "2025-01"]["yoy_pct"].iloc[0]
kyc_weighted = funnel["kyc_completed"].sum() / funnel["new_users"].sum() * 100
out_in_ratio = (real_fiat["ticket_out_usd"] / real_fiat["ticket_in_usd"]).iloc[-1]

kpi_grid([
    {"icon": ICON["growth"], "label": f"Active users, YoY ({last['month']})", "value": f"{yoy_last:+.0f}%",
     "positive": yoy_last >= 0},
    {"icon": ICON["unique_users"], "label": f"Active users, {first['month'][:4]} → {last['month'][:4]}",
     "value": f"{last['active_users'] / first['active_users']:.1f}×"},
    {"icon": ICON["lock"], "label": "KYC completed ÷ sign-ups (Jan–Jul 2025)", "value": f"{kyc_weighted:.1f}%"},
    {"icon": ICON["avg_ticket"], "label": f"Out ÷ in ticket ({real_fiat['month'].iloc[-1]})",
     "value": f"{out_in_ratio:.1f}×"},
])

# ---- Active users
section_header(ICON["growth"], "Active users by month")
fig_au = go.Figure()
fig_au.add_trace(go.Scatter(
    x=real_users["month"], y=real_users["active_users"], name="Active users", mode="lines+markers",
    line=dict(color=COLOR_PIX_IN, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
    fill="tozeroy", fillcolor=COLOR_PIX_IN + "14", customdata=real_users["yoy_pct"],
    hovertemplate="%{x}<br>Active users: %{y:,.0f}<br>YoY: %{customdata:+.0f}%<extra></extra>",
))
apply_default_layout(fig_au, height=340)
st.plotly_chart(fig_au, use_container_width=True)

y2024 = real_users[real_users["month"].str.startswith("2024")]
y2025 = real_users[real_users["month"].str.startswith("2025")]
peak_2025 = y2025.loc[y2025["active_users"].idxmax()]
st.markdown(
    f"2024 is a build-up year: active users grow **{y2024['active_users'].iloc[-1] / y2024['active_users'].iloc[0]:.1f}×** "
    f"from January to December. 2025 opens with a step up and then **flattens** — it peaks in "
    f"**{peak_2025['month']}** and ends the year {((last['active_users'] / peak_2025['active_users']) - 1) * 100:+.0f}% "
    f"off that peak. The year-over-year rate tells the same story from another angle: "
    f"**{yoy_first_2025:+.0f}%** in Jan 2025, **{yoy_last:+.0f}%** by {last['month']}. The base is still "
    f"growing, but decelerating — the typical S-curve of a product that has captured its early, "
    f"easy-to-reach users and now needs a new channel or segment to keep compounding."
)

# ---- Funnel
section_header(ICON["unique_users"], "Sign-up → KYC — Jan to Jul 2025")
fig_fn = go.Figure()
fig_fn.add_trace(go.Bar(x=funnel["month"], y=funnel["new_users"], name="New sign-ups",
                        marker_color=CATEGORICAL["blue"] + "80",
                        hovertemplate="%{x}<br>Sign-ups: %{y:,.0f}<extra></extra>"))
fig_fn.add_trace(go.Bar(x=funnel["month"], y=funnel["kyc_completed"], name="KYC completed",
                        marker_color=CATEGORICAL["blue"],
                        hovertemplate="%{x}<br>KYC completed: %{y:,.0f}<extra></extra>"))
fig_fn.add_trace(go.Scatter(x=funnel["month"], y=funnel["kyc_rate_pct"], name="KYC ÷ sign-ups (%)",
                            yaxis="y2", mode="lines+markers",
                            line=dict(color=CATEGORICAL["yellow"], width=2, dash="dot"), marker=dict(size=8),
                            hovertemplate="%{x}<br>KYC ÷ sign-ups: %{y:.1f}%<extra></extra>"))
apply_default_layout(fig_fn, height=360)
fig_fn.update_layout(
    barmode="overlay", hovermode="x unified", legend=dict(orientation="h", y=1.12),
    yaxis2=dict(overlaying="y", side="right", showgrid=False, range=[0, 30], ticksuffix="%", dtick=5),
)
st.plotly_chart(fig_fn, use_container_width=True)

spike = funnel.iloc[:2]
rest = funnel.iloc[2:]
spike_rate = spike["kyc_completed"].sum() / spike["new_users"].sum() * 100
rest_rate = rest["kyc_completed"].sum() / rest["new_users"].sum() * 100
spike_multiple = spike["new_users"].mean() / rest["new_users"].mean()
st.markdown(
    f"January and February bring **{spike_multiple:.1f}×** the sign-ups of the months that follow — but "
    f"only **{spike_rate:.0f}%** of them complete KYC, against **{rest_rate:.0f}%** from March on. That's "
    f"the classic signature of a volume push: the extra sign-ups are lower-intent, so the funnel widens "
    f"at the top and leaks more below: {spike_multiple:.1f}× the sign-ups at {spike_rate:.0f}% instead of "
    f"{rest_rate:.0f}% yields about **{spike_multiple * spike_rate / rest_rate:.1f}×** the verified users, "
    f"not {spike_multiple:.1f}×. The lesson for any acquisition budget is to judge a channel by "
    f"**cost per verified user**, not cost per sign-up. After the spike, conversion settles in a stable "
    f"~{rest['kyc_rate_pct'].min():.0f}–{rest['kyc_rate_pct'].max():.0f}% band."
)

# ---- Ticket
section_header(ICON["avg_ticket"], "Average ticket — money in vs. money out")
fig_tk = go.Figure()
for col, label, color in (("ticket_in_usd", "In (BRL deposits)", COLOR_PIX_IN),
                          ("ticket_out_usd", "Out (BRL withdrawals)", COLOR_PIX_OUT)):
    fig_tk.add_trace(go.Scatter(
        x=real_fiat["month"], y=real_fiat[col], name=label, mode="lines+markers",
        line=dict(color=color, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
        hovertemplate="%{x}<br>Avg ticket: US$ %{y:,.0f}<extra>" + label + "</extra>",
    ))
apply_default_layout(fig_tk, height=340)
fig_tk.update_layout(hovermode="x unified", yaxis=dict(title="US$ (masked)"))
st.plotly_chart(fig_tk, use_container_width=True)

ratio = real_fiat["ticket_out_usd"] / real_fiat["ticket_in_usd"]
before, after = ratio[real_fiat["month"] < "2024-08"], ratio[real_fiat["month"] >= "2024-08"]
jump = real_fiat.set_index("month")["ticket_out_usd"]
st.markdown(
    f"Until mid-2024 the two tickets sit close together (out ÷ in averages **{before.mean():.1f}×**). In "
    f"**August 2024** the withdrawal ticket steps up **{jump['2024-08'] / jump['2024-07']:.1f}×** in a single "
    f"month and never comes back down: from then on a withdrawal averages **{after.mean():.1f}×** a deposit. "
    f"Deposits stay small and frequent; withdrawals turn large and lumpy. A step change this sharp usually "
    f"means a **new kind of user** rather than existing users changing habits — for example "
    f"higher-balance clients who sell crypto in large blocks. That's a hypothesis the monthly totals "
    f"can't confirm, but the implication holds either way: larger, lumpier withdrawals now set how "
    f"much BRL the platform must keep on hand, so liquidity planning has to cover the size of the "
    f"biggest days, not just the monthly average."
)

section_header(ICON["warning"], "What this data can't tell")
st.markdown(
    "- **Cohorts.** KYC completed in a month isn't only that month's sign-ups — users verify later — "
    "so the KYC rate is a period ratio, not a true cohort conversion.\n"
    "- **Retention.** Monthly active counts can't separate new users from returning ones.\n"
    "- **Who the large tickets are.** The out-ticket break is read from averages; there's no "
    "user-level data behind it here.\n"
    "- **Absolute scale.** Counts and US\\$ amounts are masked — compare them over time, not against "
    "other sources."
)

# ===========================================================================
# Modeled activity (synthetic)
# ===========================================================================
st.divider()
section_header(ICON["dataset"], "Modeled activity — synthetic")
st.markdown(
    "A transaction-level history generated algorithmically (Jan 2024 – Mar 2026), used for the "
    "cohort-style views below that monthly real totals can't support. The sidebar filters apply from "
    "here down."
)
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

    # ---- Trajectory read-out: same "chart + plain-language take" pattern as
    # the Financial Projections trend tab, applied to monthly active users.
    section_header(ICON["overview"], "What the trend shows")

    def _drop_partial_trailing_month(df: pd.DataFrame) -> pd.DataFrame:
        """The last "month" bucket is a partial month whenever the filtered
        period doesn't run through that month's last calendar day — e.g. the
        dataset ending March 17 makes March look like a mid-month crash
        against full-month Jan/Feb, when it's really just not over yet.
        Drops it from the narrative's own read (the chart still plots it)."""
        if len(df) < 2:
            return df
        last_year, last_month = (int(p) for p in df["month"].iloc[-1].split("-"))
        cutoff = min(end, END_DATE)
        is_partial = (cutoff.year, cutoff.month) == (last_year, last_month) and (
            cutoff.day < calendar.monthrange(last_year, last_month)[1]
        )
        return df.iloc[:-1] if is_partial else df

    def _series_story(df: pd.DataFrame) -> tuple[str, float]:
        df = _drop_partial_trailing_month(df)
        first, last = df["Active Users"].iloc[0], df["Active Users"].iloc[-1]
        total_growth = (last / first - 1) * 100 if first else 0.0
        peak_i = int(df["Active Users"].idxmax())
        peak_month, peak_value = df["month"].iloc[peak_i], df["Active Users"].iloc[peak_i]
        if peak_i == len(df) - 1:
            pace = "still climbing" if total_growth >= 0 else "still declining"
            sentence = (
                f"grows from {int(first):,} active users in {df['month'].iloc[0]} to {int(last):,} by "
                f"{df['month'].iloc[-1]} — a {total_growth:,.0f}% increase, {pace} as of the latest month."
            )
        else:
            change_from_peak = (last / peak_value - 1) * 100 if peak_value else 0.0
            sentence = (
                f"peaks at {int(peak_value):,} active users in {peak_month}, then settles to {int(last):,} "
                f"by {df['month'].iloc[-1]} ({change_from_peak:+.0f}% off the peak)."
            )
        return sentence, total_growth

    story_in, growth_in_total = _series_story(m_in)
    story_out, growth_out_total = _series_story(m_out)

    kpi_grid(
        [
            {"icon": ICON["pix_in"], "label": "PIX In — total growth", "value": f"{growth_in_total:,.0f}%", "positive": growth_in_total >= 0},
            {"icon": ICON["pix_out"], "label": "PIX Out — total growth", "value": f"{growth_out_total:,.0f}%", "positive": growth_out_total >= 0},
        ]
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**PIX In** {story_in}")
    with col_b:
        st.markdown(f"**PIX Out** {story_out}")

    faster, slower = ("In", "Out") if growth_in_total >= growth_out_total else ("Out", "In")
    faster_pct = growth_in_total if faster == "In" else growth_out_total
    slower_pct = growth_out_total if faster == "In" else growth_in_total
    st.markdown(
        f"**Takeaway:** both directions move the same way over the period, but **PIX {faster}** grows "
        f"faster ({faster_pct:,.0f}% vs. {slower_pct:,.0f}% for PIX {slower})."
    )

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
