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


def drop_partial_trailing_month(
    months: list[str], values: list[float], dataset_end, filter_end
) -> tuple[list[str], list[float]]:
    """Drops the last (month, value) pair when that month isn't actually
    complete — the dataset, or the viewer's own date filter, cuts off
    mid-month — so a monthly narrative doesn't read a partial month as a
    sudden move. `dataset_end`/`filter_end` are `date`s; whichever cuts off
    earlier wins. `months` are labels like "2026-03"."""
    if len(months) < 2:
        return months, values
    last_year, last_month = (int(p) for p in months[-1].split("-"))
    cutoff = min(filter_end, dataset_end)
    is_partial = (cutoff.year, cutoff.month) == (last_year, last_month) and (
        cutoff.day < calendar.monthrange(last_year, last_month)[1]
    )
    return (months[:-1], values[:-1]) if is_partial else (months, values)


def monthly_series_story(
    months: list[str],
    values: list[float],
    dataset_end,
    filter_end,
    fmt: Callable[[float], str],
) -> tuple[str, float]:
    """Reads a chronological monthly series (labels like "2026-03") into one
    sentence — "climbs from X to Y" if the last month is also the peak,
    "peaks then eases" otherwise — plus the total % change used for it.

    See `drop_partial_trailing_month` for why the last month may be dropped.
    """
    months, values = drop_partial_trailing_month(months, values, dataset_end, filter_end)

    first, last = values[0], values[-1]
    total_growth = (last / first - 1) * 100 if first else 0.0
    peak_i = max(range(len(values)), key=lambda i: values[i])

    if peak_i == len(values) - 1:
        pace = "still climbing" if total_growth >= 0 else "still declining"
        sentence = (
            f"goes from {fmt(first)} in {months[0]} to {fmt(last)} by {months[-1]} — "
            f"a {total_growth:,.0f}% change, {pace} as of the latest month."
        )
    else:
        change_from_peak = (last / values[peak_i] - 1) * 100 if values[peak_i] else 0.0
        sentence = (
            f"peaks at {fmt(values[peak_i])} in {months[peak_i]}, then settles to {fmt(last)} "
            f"by {months[-1]} ({change_from_peak:+.0f}% off the peak)."
        )
    return escape_dollar(sentence), total_growth


def escape_dollar(text: str) -> str:
    """Escapes a literal '$' (e.g. from an "R$ 1,234" currency string) so
    st.markdown() doesn't read a pair of them as inline LaTeX and swallow
    everything between into math mode instead of rendering it as prose."""
    return text.replace("$", r"\$")
