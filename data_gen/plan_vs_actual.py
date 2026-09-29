"""
Plan vs. actual — the first out-of-sample check of the PixFlow projection.

The revenue projection was built in Nov 2025, with Jan-Jul 2025 seeded from
realized figures (so those months match by construction and aren't a test).
The first months after it with a reliable realized figure are Dec 2025 and
Jan 2026, for Bridge revenue only. Each value below is realized revenue
divided by the Conservative scenario's projection for that month — a ratio,
so it is real, and no absolute figure is published.
"""

PRODUCT = "Bridge"
SCENARIO = "Conservative"
PROJECTION_BUILT = "2025-11"
ACTUAL_TO_PLAN = [{'month': '2025-12', 'actual_to_plan': 2.83}, {'month': '2026-01', 'actual_to_plan': 2.35}]
