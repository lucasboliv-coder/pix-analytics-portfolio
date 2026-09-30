import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_gen.chain_real import BLOCKCHAIN_MONTHLY, BRIDGE_MONTHLY, SNAPSHOT, SNAPSHOT_PERIOD
from data_gen.generator import END_DATE, START_DATE, load_data
from theme.charts import (COLOR_BLOCKCHAIN, COLOR_BRIDGE, COLOR_PIX_IN, COLOR_PIX_OUT, SYMBOL_COLORS, STATUS,
                          apply_default_layout)
from theme.icons import ICON, mi
from theme.narrative import escape_dollar, monthly_series_story, yoy_story
from theme.style import kpi_grid, period_badge, section_header

st.title(f"{mi(ICON['chain_page'])} Blockchain & Bridge")

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

TYPE_LABEL = {"BLOCKCHAIN": "Blockchain", "BRIDGE": "Bridge"}
TYPE_COLOR = {"BLOCKCHAIN": COLOR_BLOCKCHAIN, "BRIDGE": COLOR_BRIDGE}


def fmt_value(v: float) -> str:
    return f"US$ {v:,.0f}"


# Whether the filtered period stops mid-month (the dataset itself ends on
# END_DATE, or the viewer's date filter does) — the narratives below read that
# last month as "not over yet" instead of as a sudden drop.
cutoff = min(end, END_DATE)
cutoff_is_partial = cutoff.day < calendar.monthrange(cutoff.year, cutoff.month)[1]

# ===========================================================================
# Real data (masked) — independent of the sidebar filters, which only drive
# the modeled section below.
# ===========================================================================
section_header(ICON["lock"], "Real data — masked")
st.markdown(
    "Aggregated from the real transaction records of the group's crypto-payments company. "
    "Volumes and counts are masked (see Home); **percentages are the real ones**. Values in "
    "US\\$ (USDT). The sidebar filters don't apply to this block."
)
st.markdown(
    "**How the flow works.** A user funds the account in BRL (via PIX), buys crypto, and then either "
    "keeps it on the platform or sends it out. Sending out takes one of two routes: a **direct "
    "blockchain transfer** on the asset's own network, or a **bridge**, which moves the asset to a "
    "different network first — one extra hop, and the platform charges for it. Money also runs the "
    "other way: users send crypto *in* to sell it for BRL. In industry terms the platform is both an "
    "**on-ramp** (fiat → crypto) and an **off-ramp** (crypto → fiat); the on-chain data below shows "
    "which side dominates, what the bridge earns per dollar moved, and how reliably both routes settle."
)

bridge_real = pd.DataFrame(BRIDGE_MONTHLY)
all_months = pd.period_range(bridge_real["month"].min(), bridge_real["month"].max(), freq="M").astype(str)
bridge_full = bridge_real.set_index("month").reindex(all_months)
gap = bridge_full[bridge_full["volume_usd"].isna()].index.tolist()
weighted_take = (
    (bridge_real["take_rate_pct"] * bridge_real["volume_usd"]).sum() / bridge_real["volume_usd"].sum()
)

kpi_grid([
    {"icon": ICON["fees"], "label": "Bridge take rate (volume-weighted)", "value": f"{weighted_take:.2f}%"},
    {"icon": ICON["bridge"], "label": "Bridge share of on-chain US$",
     "value": f"{SNAPSHOT['bridge_share_of_usd_pct']:.1f}%"},
    {"icon": ICON["chain_page"], "label": "Success rate — blockchain",
     "value": f"{SNAPSHOT['success_rate_pct']['BLOCKCHAIN']:.1f}%"},
    {"icon": ICON["bridge"], "label": "Success rate — bridge",
     "value": f"{SNAPSHOT['success_rate_pct']['BRIDGE']:.1f}%"},
])

section_header(ICON["bridge"], "Bridge — monthly volume and take rate")
fig_real = go.Figure()
fig_real.add_trace(go.Scatter(
    x=bridge_full.index, y=bridge_full["volume_usd"], name="Volume (US$, masked)", mode="lines+markers",
    line=dict(color=COLOR_BRIDGE, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=7),
    connectgaps=False,  # no area fill: it would bridge the Aug-Nov gap
    hovertemplate="%{x}<br>Volume: US$ %{y:,.0f}<extra></extra>",
))
fig_real.add_trace(go.Scatter(
    x=bridge_full.index, y=bridge_full["take_rate_pct"], name="Take rate (%, real)", yaxis="y2",
    mode="markers+lines", line=dict(color=SYMBOL_COLORS["BTC"], width=1.5, dash="dot"),
    marker=dict(size=8, symbol="diamond"), connectgaps=False,
    hovertemplate="%{x}<br>Take rate: %{y:.2f}%<extra></extra>",
))
if gap:
    fig_real.add_vrect(x0=gap[0], x1=gap[-1], fillcolor="rgba(255,255,255,0.04)", line_width=0,
                       annotation_text="no reliable record", annotation_position="top left")
apply_default_layout(fig_real, height=380)
fig_real.update_layout(
    hovermode="x unified",
    yaxis=dict(title="Volume (US$)"),
    yaxis2=dict(title="Take rate", overlaying="y", side="right", showgrid=False,
                range=[0, 1], ticksuffix="%", tickformat=".1f"),
    legend=dict(orientation="h", y=1.12),
)
st.plotly_chart(fig_real, width="stretch")

h1 = bridge_real[bridge_real["month"] < "2025-08"]
recent = bridge_real[bridge_real["month"] >= "2025-12"]
peak = h1.loc[h1["volume_usd"].idxmax()]
lo, hi = bridge_real.loc[bridge_real["take_rate_pct"].idxmin()], bridge_real.loc[bridge_real["take_rate_pct"].idxmax()]
recent_vs_h1 = (recent["volume_usd"].mean() / h1["volume_usd"].mean() - 1) * 100
st.markdown(escape_dollar(
    f"In Jan–Jul 2025, bridge volume peaks in **{peak['month']}**. By Dec 2025–Jan 2026 the average "
    f"month runs **{recent_vs_h1:+.0f}%** against the Jan–Jul 2025 average. The take rate ranges from "
    f"**{lo['take_rate_pct']:.2f}%** ({lo['month']}) to **{hi['take_rate_pct']:.2f}%** ({hi['month']}) — "
    f"**{weighted_take:.2f}%** weighted by volume. Aug–Nov 2025 is left blank: there's no record for "
    f"those months reliable enough to publish."
))

# ---- Unit economics: revenue = volume × take rate, so a month-over-month
# revenue change splits exactly into a volume effect and a rate (price)
# effect. Both effects are computed from ratios, so the masking cancels out.
section_header(ICON["revenue"], "Unit economics — what moves bridge revenue")
dec, jan = bridge_real.iloc[-2], bridge_real.iloc[-1]
vol_ratio = jan["volume_usd"] / dec["volume_usd"]
rate_ratio = jan["take_rate_pct"] / dec["take_rate_pct"]
volume_effect = (vol_ratio - 1) * 100
rate_effect = vol_ratio * (rate_ratio - 1) * 100
revenue_change = volume_effect + rate_effect
col_wf, col_ue = st.columns([3, 2])
with col_wf:
    fig_wf = go.Figure(go.Waterfall(
        x=[f"{dec['month']} revenue", "Volume effect", "Rate effect", f"{jan['month']} revenue"],
        measure=["absolute", "relative", "relative", "total"],
        y=[100, volume_effect, rate_effect, None],
        text=["100", f"{volume_effect:+.0f}", f"{rate_effect:+.0f}", f"{100 + revenue_change:.0f}"],
        textposition="outside",
        increasing=dict(marker=dict(color=STATUS["CONFIRMED"])),
        decreasing=dict(marker=dict(color=STATUS["FAILED"])),
        totals=dict(marker=dict(color=COLOR_BRIDGE)),
        connector=dict(line=dict(color="rgba(255,255,255,0.25)")),
        hovertemplate="%{x}: %{text}<extra></extra>",
    ))
    apply_default_layout(fig_wf, title=f"Bridge revenue, {dec['month']} = 100", height=340)
    fig_wf.update_layout(showlegend=False, yaxis=dict(rangemode="tozero"))
    st.plotly_chart(fig_wf, width="stretch")
with col_ue:
    kpi_grid([
        {"icon": ICON["fees"], "label": "Revenue per US$ 1,000 bridged",
         "value": f"US$ {weighted_take * 10:.2f}"},
        {"icon": ICON["revenue"], "label": f"Revenue change, {dec['month']} → {jan['month']}",
         "value": f"{revenue_change:+.0f}%", "positive": revenue_change >= 0},
    ])
st.markdown(escape_dollar(
    f"Bridge revenue is volume × take rate — at the weighted rate, **US$ {weighted_take * 10:.2f} for "
    f"every US$ 1,000 bridged**. That identity lets a month-over-month change be split exactly: from "
    f"{dec['month']} to {jan['month']}, lower volume alone would have moved revenue **{volume_effect:+.0f}%**, "
    f"and the higher rate added **{rate_effect:+.0f}** points back, for **{revenue_change:+.0f}%** in total. "
    + ("The rate, not volume, drove most of the change — "
       if abs(rate_effect) > abs(volume_effect) else
       "Volume, not the rate, drove most of the change — ")
    + "though monthly totals can't say whether the rate moved because pricing changed or because the "
    "mix shifted toward routes or sizes that carry higher fees."
))

section_header(ICON["symbol"], f"On-chain snapshot — {SNAPSHOT_PERIOD[0]} to {SNAPSHOT_PERIOD[1]}")
col_mix, col_split = st.columns(2)
with col_mix:
    mix = pd.Series(SNAPSHOT["symbol_share_of_transactions_pct"])
    fig_mix = px.pie(values=mix.values, names=mix.index, hole=0.55, color=mix.index,
                     color_discrete_map=SYMBOL_COLORS)
    fig_mix.update_traces(hovertemplate="%{label}: %{value:.1f}% of transactions<extra></extra>")
    apply_default_layout(fig_mix, title="Transactions by symbol", height=320)
    st.plotly_chart(fig_mix, width="stretch")
with col_split:
    out_share = SNAPSHOT["blockchain_out_share_of_usd_pct"]
    bridge_share = SNAPSHOT["bridge_share_of_usd_pct"]
    splits = pd.DataFrame([
        {"split": "Direction (blockchain)", "part": "In", "pct": 100 - out_share, "color": COLOR_PIX_IN},
        {"split": "Direction (blockchain)", "part": "Out", "pct": out_share, "color": COLOR_PIX_OUT},
        {"split": "Route", "part": "Blockchain", "pct": 100 - bridge_share, "color": COLOR_BLOCKCHAIN},
        {"split": "Route", "part": "Bridge", "pct": bridge_share, "color": COLOR_BRIDGE},
    ])
    fig_split = go.Figure()
    for _, r in splits.iterrows():
        fig_split.add_trace(go.Bar(
            y=[r["split"]], x=[r["pct"]], orientation="h", name=r["part"], marker_color=r["color"],
            # Label only slices wide enough to hold it; the rest read on hover
            # and in the text below.
            text=f"{r['part']} {r['pct']:.0f}%" if r["pct"] >= 15 else "", textposition="inside",
            textangle=0, insidetextanchor="middle", textfont=dict(color="#ffffff"), showlegend=False,
            hovertemplate=f"{r['part']}: {r['pct']:.1f}% of US$ value<extra></extra>",
        ))
    fig_split.update_layout(barmode="stack", xaxis=dict(range=[0, 100], ticksuffix="%"))
    apply_default_layout(fig_split, title="Share of US$ value", height=320)
    st.plotly_chart(fig_split, width="stretch")

direct_months = pd.DataFrame(BLOCKCHAIN_MONTHLY)
tx_growth = (direct_months["transactions"].iloc[-1] / direct_months["transactions"].iloc[0] - 1) * 100
vol_growth = (direct_months["volume_usd"].iloc[-1] / direct_months["volume_usd"].iloc[0] - 1) * 100
# Counts and volumes carry different masks, but each mask cancels out in its
# own month-over-month ratio — so the change in average ticket is real.
ticket_change = ((1 + vol_growth / 100) / (1 + tx_growth / 100) - 1) * 100
top_symbol = mix.idxmax()
hhi = ((mix / 100) ** 2).sum()
fail_per_k = {route: (100 - SNAPSHOT["success_rate_pct"][route]) * 10 for route in ("BLOCKCHAIN", "BRIDGE")}
in_share = 100 - out_share

st.markdown(
    f"**Concentration.** {top_symbol} carries **{mix[top_symbol]:.0f}%** of transfers, the group's own "
    f"token (PFT) {mix.get('PFT', 0):.0f}% and BTC {mix.get('BTC', 0):.0f}%. On the Herfindahl-Hirschman "
    f"index — the sum of squared shares, where 1.0 means a single asset and antitrust practice treats "
    f"anything above 0.25 as highly concentrated — the mix scores **{hhi:.2f}**. This is a stablecoin "
    f"rail: the mix points to users treating the platform as a way to hold dollars more than as a way "
    f"to take crypto exposure. The flip side is dependency — "
    f"liquidity, pricing and regulatory risk on {top_symbol} land on almost the whole business at once."
)
st.markdown(
    f"**Flow and ticket.** Of the value moved directly on-chain, **{out_share:.0f}%** leaves the "
    f"platform and **{in_share:.0f}%** arrives — a net outflow of {out_share - in_share:.0f} points. "
    f"The platform works mainly as an **on-ramp**: BRL comes in through PIX and leaves as crypto; the "
    f"off-ramp side (crypto in, sold for BRL) is real but smaller. From December to January direct "
    f"transfers move **{tx_growth:+.0f}%** in count and **{vol_growth:+.0f}%** in value, so the "
    f"average ticket changes by **{ticket_change:+.0f}%** — "
    + ("more transfers, each smaller. One plausible reading, not tested here: year-end income (the "
       "13th salary, bonuses) inflates December tickets, and January returns to smaller, more "
       "frequent transfers."
       if ticket_change < 0 else
       "fewer transfers, each larger.")
)
st.markdown(
    f"**Reliability.** {SNAPSHOT['success_rate_pct']['BLOCKCHAIN']:.1f}% of direct transfers and "
    f"{SNAPSHOT['success_rate_pct']['BRIDGE']:.1f}% of bridges settle. Put per 1,000 operations, that's "
    f"about **{fail_per_k['BLOCKCHAIN']:.0f}** direct transfers and **{fail_per_k['BRIDGE']:.0f}** bridges "
    f"that don't — a bridge is **{fail_per_k['BRIDGE'] / fail_per_k['BLOCKCHAIN']:.1f}×** as likely to "
    f"need follow-up. That's expected of the extra hop: a bridge depends on two networks confirming and "
    f"on liquidity being available on the destination side, and every unsettled operation turns into "
    f"support time or a refund — a cost the take rate has to cover."
)

section_header(ICON["warning"], "What this data can't tell")
st.markdown(
    "- **Seasonality.** Two full months of on-chain snapshot and nine months of bridge history "
    "aren't enough to separate a trend from a seasonal swing.\n"
    "- **Absolute scale.** Volumes and counts are masked; compare them over time within this block, "
    "not against other sources.\n"
    "- **Causality.** The take-rate and ticket readings above describe what moved together, not why — "
    "there's no pricing experiment or user-level data behind them.\n"
    "- **Aug–Nov 2025.** No reliable record, so it's left blank rather than estimated."
)

# ===========================================================================
# Modeled activity (synthetic, calibrated to the snapshot above)
# ===========================================================================
st.divider()
section_header(ICON["dataset"], "Modeled activity — synthetic")
st.markdown(
    "A longer, transaction-level history generated algorithmically (Jan 2024 – Mar 2026), with its "
    "route split, symbol mix, success rates and bridge take rate calibrated to the real snapshot "
    "above. The sidebar filters apply from here down."
)
period_badge(f"{start:%m/%d/%Y} — {end:%m/%d/%Y}")

kpi_grid(
    [
        {"icon": ICON["value"], "label": "Total value", "value": f"US$ {df['value'].sum():,.0f}"},
        {"icon": ICON["average"], "label": "Average value", "value": f"US$ {df['value'].mean():,.2f}" if len(df) else "US$ 0.00"},
        {"icon": ICON["gas_fee"], "label": "Total fee", "value": f"US$ {df['tx_fee'].sum():,.2f}"},
        {"icon": ICON["transactions"], "label": "Transactions", "value": f"{len(df):,}"},
    ]
)

tab1, tab2, tab3, tab4 = st.tabs([
    f"{mi(ICON['overview'])} Overview",
    f"{mi(ICON['yoy'])} Year-over-Year",
    f"{mi(ICON['status'])} Status & Correlation",
    f"{mi(ICON['data'])} Data",
])

with tab1:
    section_header(ICON["overview"], "Monthly volume — Blockchain vs Bridge")
    st.markdown(
        "On-chain value moved each month, split by route: a direct **blockchain** "
        "transfer, or a **bridge** that moves the asset across networks first."
    )
    monthly = df.groupby(["month", "type"])["value"].sum().reset_index()
    monthly["month"] = monthly["month"].astype(str)
    fig = go.Figure()
    for tx_type in ("BLOCKCHAIN", "BRIDGE"):
        sub = monthly[monthly["type"] == tx_type]
        if sub.empty:
            continue
        color = TYPE_COLOR[tx_type]
        fig.add_trace(go.Scatter(
            x=sub["month"], y=sub["value"], name=TYPE_LABEL[tx_type], mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline", smoothing=0.3), marker=dict(size=6),
            fill="tozeroy", fillcolor=color + "14",
            hovertemplate="%{x}<br>Value: US$ %{y:,.0f}<extra>" + TYPE_LABEL[tx_type] + "</extra>",
        ))
    apply_default_layout(fig, height=380)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, width="stretch")

    types_present = [t for t in ("BLOCKCHAIN", "BRIDGE") if t in monthly["type"].unique()]
    stories = {}
    for tx_type in types_present:
        sub = monthly[monthly["type"] == tx_type]
        if len(sub) >= 2:
            stories[tx_type] = monthly_series_story(
                sub["month"].tolist(), sub["value"].tolist(), END_DATE, end, fmt_value
            )

    if stories:
        kpi_grid([
            {"icon": ICON["chain_page"] if t == "BLOCKCHAIN" else ICON["bridge"],
             "label": f"{TYPE_LABEL[t]} — total change", "value": f"{growth:,.0f}%", "positive": growth >= 0}
            for t, (_, growth) in stories.items()
        ])
        cols = st.columns(len(stories))
        for col, (t, (story, _)) in zip(cols, stories.items()):
            with col:
                st.markdown(f"**{TYPE_LABEL[t]}** {story}")

    if len(types_present) == 2 and df["value"].sum():
        bridge_share = df.loc[df["type"] == "BRIDGE", "value"].sum() / df["value"].sum() * 100
        route_read = (
            "most value settles directly on its native chain, with bridging as the secondary route."
            if bridge_share < 50
            else "bridging is the main route here, ahead of direct on-chain transfers."
        )
        st.markdown(f"Bridges carry **{bridge_share:.0f}%** of the value moved — {route_read}")

    # ---- The link back to PIX: on-chain volume is where the BRL that leaves
    # through PIX Out ends up, so the two monthly series should move together.
    # Only read for settled flow (a FAILED/PENDING-only view isn't that flow),
    # and only over enough months for a correlation to mean something.
    pix_out = data["pix_out"]
    pix_out = pix_out[(pix_out["created_at"].dt.date >= start) & (pix_out["created_at"].dt.date <= end)]
    pix_monthly = pix_out.groupby(pix_out["created_at"].dt.to_period("M"))["amount_brl"].sum()
    chain_monthly = df.groupby("month")["value"].sum()
    paired = chain_monthly.to_frame("chain").join(pix_monthly.rename("pix_out"), how="inner")
    if cutoff_is_partial:
        paired = paired[paired.index != pd.Period(cutoff, freq="M")]
    if status_sel in ("All", "CONFIRMED") and len(paired) >= 6:
        r = paired["chain"].corr(paired["pix_out"])
        strength = "closely" if r >= 0.7 else "loosely" if r >= 0.4 else "barely"
        st.markdown(
            f"**Model link:** modeled on-chain volume tracks **{strength}** with PIX Out withdrawals "
            f"(correlation **{r:.2f}** over {len(paired)} months). That's by design — the model assumes "
            f"BRL leaving through PIX lands on-chain, which the real outbound share above "
            f"({SNAPSHOT['blockchain_out_share_of_usd_pct']:.0f}% of direct-transfer value) is consistent with."
        )

    section_header(ICON["symbol"], "Volume by symbol")
    by_symbol = df.groupby("symbol")["value"].sum().reset_index().sort_values("value", ascending=False)
    fig_s = px.bar(by_symbol, x="symbol", y="value", color="symbol",
                   color_discrete_map=SYMBOL_COLORS, labels={"value": "Value (US$)", "symbol": "Symbol"})
    fig_s.update_layout(showlegend=False)
    apply_default_layout(fig_s, height=320)
    st.plotly_chart(fig_s, width="stretch")

    if len(by_symbol) >= 3 and by_symbol["value"].sum():
        shares = by_symbol.set_index("symbol")["value"] / by_symbol["value"].sum() * 100
        top, second, smallest = shares.index[0], shares.index[1], shares.index[-1]
        st.markdown(
            f"**{top}** leads with **{shares[top]:.0f}%** of the value, and together with **{second}** "
            f"the top two account for **{shares[top] + shares[second]:.0f}%**. **{smallest}** is the "
            f"smallest slice at {shares[smallest]:.0f}%."
        )

with tab2:
    section_header(ICON["yoy"], "Year-over-year comparison — value by type")
    for tx_type in ("BLOCKCHAIN", "BRIDGE"):
        sub = df[df["type"] == tx_type]
        if sub.empty:
            continue
        pivot = sub.groupby(["month_num", "year"])["value"].sum().unstack(fill_value=0)
        pivot = pivot.reindex(range(1, 13), fill_value=0)
        fig2 = go.Figure()
        for year in pivot.columns:
            fig2.add_trace(go.Scatter(x=pivot.index, y=pivot[year], name=str(year), mode="lines+markers"))
        apply_default_layout(fig2, title=f"{TYPE_LABEL[tx_type]} — monthly value by year", height=340)
        fig2.update_layout(xaxis=dict(
            tickmode="array", tickvals=list(range(1, 13)),
            ticktext=[calendar.month_abbr[m] for m in range(1, 13)],
        ))
        st.plotly_chart(fig2, width="stretch")

        years = sorted(pivot.columns)
        if len(years) >= 2:
            y_prev, y_curr = years[-2], years[-1]
            curr = pivot[y_curr].copy()
            # A month that isn't over yet would be compared in full against
            # the prior year's complete month — leave it out of the read.
            partial_note = ""
            if cutoff_is_partial and cutoff.year == y_curr:
                curr[cutoff.month] = 0
                partial_note = f" {calendar.month_name[cutoff.month]} {y_curr} is left out, since it's still partial."
            covered = curr[curr > 0]
            if len(covered) and covered.index.max() < 12:
                first_m, last_m = calendar.month_abbr[covered.index.min()], calendar.month_abbr[covered.index.max()]
                span = first_m if first_m == last_m else f"{first_m}–{last_m}"
                partial_note = f" Same months only: {span} of each year." + partial_note
            # Same months of the prior year must have something to compare against.
            if curr.sum() and pivot[y_prev][curr > 0].sum():
                st.markdown(
                    f"**{TYPE_LABEL[tx_type]}:** "
                    + yoy_story(pivot[y_prev], curr, y_prev, y_curr, fmt_value)
                    + partial_note
                )

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        section_header(ICON["status"], "Status distribution")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig3 = px.pie(status_counts, values="Count", names="Status", hole=0.55,
                      color="Status", color_discrete_map=STATUS)
        apply_default_layout(fig3, height=320)
        st.plotly_chart(fig3, width="stretch")
    with col2:
        section_header(ICON["correlation"], "Value × Fee")
        sample = df.sample(min(len(df), 3000), random_state=42) if len(df) else df
        fig4 = px.scatter(sample, x="value", y="tx_fee", trendline="ols", opacity=0.5,
                          labels={"value": "Value (US$)", "tx_fee": "Fee (US$)"})
        fig4.update_traces(marker=dict(color=COLOR_BLOCKCHAIN))
        apply_default_layout(fig4, height=320)
        st.plotly_chart(fig4, width="stretch")

    section_header(ICON["overview"], "What status and fees show")
    if status_sel != "All":
        st.markdown(
            f"The sidebar is filtering to **{status_sel}** only, so the status split above is a single "
            f"slice — set Status back to *All* to compare success and failure rates."
        )
    elif len(df):
        rates = df["status"].value_counts(normalize=True) * 100
        confirmed, pending, failed = (rates.get(s, 0.0) for s in ("CONFIRMED", "PENDING", "FAILED"))
        line = (
            f"**{confirmed:.1f}%** of transactions confirm; {pending:.1f}% are still pending and "
            f"**{failed:.1f}%** failed."
        )
        fail_by_type = df.groupby("type")["status"].apply(lambda s: (s == "FAILED").mean() * 100)
        if len(fail_by_type) == 2:
            higher, lower = fail_by_type.idxmax(), fail_by_type.idxmin()
            if fail_by_type[higher] - fail_by_type[lower] < 0.5:
                line += (
                    f" Failures run {fail_by_type[higher]:.1f}% on {TYPE_LABEL[higher].lower()} vs. "
                    f"{fail_by_type[lower]:.1f}% on {TYPE_LABEL[lower].lower()} — close enough that "
                    f"the route isn't what drives failures."
                )
            else:
                line += (
                    f" Failures concentrate on **{TYPE_LABEL[higher].lower()}** "
                    f"({fail_by_type[higher]:.1f}% vs. {fail_by_type[lower]:.1f}%)."
                )
        st.markdown(line)

    if len(df) >= 2 and df["value"].sum():
        r = df["value"].corr(df["tx_fee"])
        fee_line = (
            f"In the modeled data, network fees scale with the amount moved (correlation **{r:.2f}**) — "
            f"a percentage of value rather than a flat charge."
        )
        chain_df, bridge_df = df[df["type"] == "BLOCKCHAIN"], df[df["type"] == "BRIDGE"]
        if chain_df["value"].sum() and bridge_df["value"].sum():
            chain_rate = chain_df["tx_fee"].sum() / chain_df["value"].sum() * 100
            bridge_rate = (bridge_df["tx_fee"].sum() + bridge_df["fee_value"].sum()) / bridge_df["value"].sum() * 100
            fee_line += (
                f" A modeled direct transfer costs about **{chain_rate:.2f}%** of value; a bridge adds its "
                f"own fee on top (drawn from the real take-rate range above), bringing the all-in cost to "
                f"**{bridge_rate:.2f}%** — roughly **{bridge_rate / chain_rate:.1f}×** as expensive per unit moved."
            )
        st.markdown(fee_line)

with tab4:
    section_header(ICON["data"], "Raw data (sample)")
    display_df = df.copy()
    display_df["tx_hash"] = display_df["tx_hash"].str[:18] + "..."
    st.dataframe(display_df.head(300), width="stretch")
