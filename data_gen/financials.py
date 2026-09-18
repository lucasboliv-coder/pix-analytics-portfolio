"""
Masked financial KPI dataset for the group's two portfolio companies.

Unlike the rest of this app (100% synthetic transaction data), this one
starts from real multi-year financial models built professionally for two
companies of a payments/fintech group. Two layers of masking are applied
before anything here is published:

1. Company and product names are fully fictionalized.
2. Every figure is scaled by a fixed, per-company multiplier that was
   generated once and discarded — never recorded anywhere, including here.
   The same multiplier is applied to every KPI for a given company, so
   year-over-year growth rates and cross-KPI ratios (e.g. cost as a share
   of revenue) closely track the real model's — small deviations come from
   independently rounding each output value, not from the masking itself.
   The absolute dollar/count values below are not the real ones.

The numbers below are the masked output — there is no way to recover the
original figures from them.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

COMPANIES = ["PixFlow", "NovaPay Finance"]
YEARS = [2025, 2026, 2027, 2028, 2029]
SCENARIOS = ["Conservative", "Pessimistic", "Optimistic"]

# Client-count KPIs are point-in-time levels (end of 2029), not a 5-year sum —
# the UI labels them differently from the flow KPIs (revenue, costs, volume).
STOCK_KPIS = {"Retail Clients (EoP)", "Institutional Clients (EoP)"}

HEADLINE_KPIS = [
    "Gross Revenue",
    "Total Costs",
    "Estimated EBITDA",
    "Volume Processed",
    "Retail Clients (EoP)",
    "Institutional Clients (EoP)",
]

COST_BREAKDOWN_KPIS = {
    "PixFlow": ["Customer Support Expenses"],
    "NovaPay Finance": ["People Expenses", "Sales & Marketing Expenses", "Operations Expenses", "IT Expenses"],
}

_YEARLY = {
    "PixFlow": {
        "Retail Clients (EoP)": [3930, 48200, 55800, 52600, 49900],
        "Institutional Clients (EoP)": [225, 1670, 3610, 5620, 8450],
        "Volume Processed": [62_280_000, 134_320_000, 194_120_000, 262_830_000, 335_360_000],
        "Gross Revenue": [225000, 638000, 1_090_000, 1_470_000, 1_920_000],
        "Total Costs": [517000, 700000, 730000, 762000, 794000],
        "Customer Support Expenses": [55000, 75800, 79100, 82500, 86000],
    },
    "NovaPay Finance": {
        "Retail Clients (EoP)": [176000, 509000, 886000, 1_310_000, 1_740_000],
        "Institutional Clients (EoP)": [148, 1100, 2370, 3700, 5560],
        "Volume Processed": [1_178_400_000, 1_617_250_000, 1_690_390_000, 1_763_530_000, 1_836_680_000],
        "Gross Revenue": [9_220_000, 12_750_000, 13_300_000, 13_860_000, 14_470_000],
        "Total Costs": [4_970_000, 6_670_000, 6_770_000, 6_870_000, 6_970_000],
        "People Expenses": [371000, 811000, 828000, 846000, 864000],
        "Sales & Marketing Expenses": [161000, 73100, 73100, 73100, 73100],
        "Operations Expenses": [1_100_000, 1_410_000, 1_430_000, 1_430_000, 1_430_000],
        "IT Expenses": [140000, 206000, 208000, 208000, 208000],
    },
}

_SCENARIO = {
    "PixFlow": {
        "Retail Clients (EoP)": {"Conservative": 252000, "Pessimistic": 103000, "Optimistic": 658000},
        "Institutional Clients (EoP)": {"Conservative": 19700, "Pessimistic": 8090, "Optimistic": 51500},
        "Volume Processed": {"Conservative": 1_009_910_000, "Pessimistic": 210_680_000, "Optimistic": 1_346_870_000},
        "Gross Revenue": {"Conservative": 5_420_000, "Pessimistic": 2_220_000, "Optimistic": 5_800_000},
        "Total Costs": {"Conservative": 3_670_000, "Pessimistic": 1_510_000, "Optimistic": 3_930_000},
        "Customer Support Expenses": {"Conservative": 397000, "Pessimistic": 163000, "Optimistic": 794000},
    },
    "NovaPay Finance": {
        "Retail Clients (EoP)": {"Conservative": 4_710_000, "Pessimistic": 1_930_000, "Optimistic": 12_300_000},
        "Institutional Clients (EoP)": {"Conservative": 13000, "Pessimistic": 5320, "Optimistic": 33900},
        "Volume Processed": {"Conservative": 1_324_680_000, "Pessimistic": 542_880_000, "Optimistic": 3_453_930_000},
        "Gross Revenue": {"Conservative": 66_710_000, "Pessimistic": 21_840_000, "Optimistic": 139_030_000},
        "Total Costs": {"Conservative": 33_890_000, "Pessimistic": 13_900_000, "Optimistic": 67_790_000},
        "People Expenses": {"Conservative": 3_920_000, "Pessimistic": 1_610_000, "Optimistic": 7_840_000},
        "Sales & Marketing Expenses": {"Conservative": 503000, "Pessimistic": 206000, "Optimistic": 1_010_000},
        "Operations Expenses": {"Conservative": 7_200_000, "Pessimistic": 2_950_000, "Optimistic": 14_410_000},
        "IT Expenses": {"Conservative": 1_020_000, "Pessimistic": 420000, "Optimistic": 2_050_000},
    },
}


def _add_estimated_ebitda() -> None:
    """Derived KPI: Gross Revenue - Total Costs.

    Not an audited P&L line — the source models don't compute EBITDA at this
    summary level — just a simple profitability proxy for the trend and
    scenario views.
    """
    for company in COMPANIES:
        revenue = _YEARLY[company]["Gross Revenue"]
        costs = _YEARLY[company]["Total Costs"]
        _YEARLY[company]["Estimated EBITDA"] = [r - c for r, c in zip(revenue, costs)]

        _SCENARIO[company]["Estimated EBITDA"] = {
            s: _SCENARIO[company]["Gross Revenue"][s] - _SCENARIO[company]["Total Costs"][s]
            for s in SCENARIOS
        }


_add_estimated_ebitda()


@st.cache_data(show_spinner=False)
def load_financials() -> dict[str, pd.DataFrame]:
    """Single entry point: returns the yearly trend and scenario tables in long format."""
    yearly_rows = [
        {"company": company, "kpi": kpi, "year": year, "value": value}
        for company, kpis in _YEARLY.items()
        for kpi, values in kpis.items()
        for year, value in zip(YEARS, values)
    ]

    scenario_rows = [
        {"company": company, "kpi": kpi, "scenario": scenario_name, "value": value}
        for company, kpis in _SCENARIO.items()
        for kpi, values in kpis.items()
        for scenario_name, value in values.items()
    ]

    return {
        "yearly": pd.DataFrame(yearly_rows),
        "scenario": pd.DataFrame(scenario_rows),
    }
