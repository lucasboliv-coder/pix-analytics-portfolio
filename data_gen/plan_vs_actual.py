"""
Plan vs. actual — the first out-of-sample check of the PixFlow projection.

The revenue projection was built in Nov 2025, with Jan-Jul 2025 seeded from
realized figures (so those months match by construction and aren't a test).
The months after the seed with a reliable realized figure are Oct 2025 (before
the model was built, but not seeded) and Dec 2025 - Jan 2026 (after it was
built), for Bridge revenue only. Each value below is realized revenue divided
by the Conservative scenario's projection for that month — a ratio, so it is
real, and no absolute figure is published.
"""

PRODUCT = "Bridge"
SCENARIO = "Conservative"
PROJECTION_BUILT = "2025-11"
SEEDED_THROUGH = "2025-07"
ACTUAL_TO_PLAN = [
    {'month': '2025-10', 'actual_to_plan': 2.3, 'after_model_built': False},
    {'month': '2025-12', 'actual_to_plan': 2.83, 'after_model_built': True},
    {'month': '2026-01', 'actual_to_plan': 2.35, 'after_model_built': True},
]
