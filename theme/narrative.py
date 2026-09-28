"""
Small data-to-prose helpers: turn an aggregated series into one plain-English
sentence instead of a table. Shared across pages so every "year-over-year"
tab reads the same way instead of each page inventing its own phrasing.
"""

from __future__ import annotations

import calendar
from typing import Callable

import pandas as pd


def yoy_story(
    prev: pd.Series,
    curr: pd.Series,
    prev_year: int,
    curr_year: int,
    fmt: Callable[[float], str],
) -> str:
    """Reads two years of the same monthly series (indexed by month number,
    1-12) into one sentence: overall change plus the strongest month.

    `fmt` formats a single value for display (e.g. currency or plain count).

    `curr` is expected pre-filled to all 12 months (zero where there's no
    data yet, e.g. an in-progress year) — trailing zero months are dropped
    before comparing, so a partial current year is measured against the
    same months of the prior year rather than against a full 12 vs. a
    handful, which would understate it.
    """
    curr = curr.reindex(sorted(curr.index))
    nonzero = curr[curr > 0]
    last_month = int(nonzero.index.max()) if len(nonzero) else int(curr.index.max())
    curr = curr.loc[:last_month]

    idx = sorted(curr.index)
    prev = prev.reindex(idx, fill_value=0)
    total_prev, total_curr = float(prev.sum()), float(curr.sum())
    total_growth = (total_curr / total_prev - 1) * 100 if total_prev else 0.0
    direction = "ahead of" if total_growth >= 0 else "behind"

    month_diff_pct = pd.Series(
        [(c / p - 1) * 100 if p else 0.0 for p, c in zip(prev, curr)], index=idx
    )
    best_month = month_diff_pct.idxmax()

    sentence = (
        f"**{curr_year}** closes **{abs(total_growth):.0f}% {direction} {prev_year}** overall "
        f"({fmt(total_curr)} vs {fmt(total_prev)}), led by **{calendar.month_name[int(best_month)]}** "
        f"({month_diff_pct[best_month]:+.0f}% year-over-year)."
    )
    return escape_dollar(sentence)


def escape_dollar(text: str) -> str:
    """Escapes a literal '$' (e.g. from an "R$ 1,234" currency string) so
    st.markdown() doesn't read a pair of them as inline LaTeX and swallow
    everything between into math mode instead of rendering it as prose."""
    return text.replace("$", r"\$")
