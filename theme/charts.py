"""
Palette and Plotly template shared across all PixFlow Analytics pages.

Palette validated (contrast + colorblind separation) via the dataviz skill —
fixed categorical order, never cycled; sequential/diverging/status colors
follow the role they play, not the mood of the moment.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# ---------------------------------------------------------------------------
# Color tokens (dark instance of the reference palette)
# ---------------------------------------------------------------------------
SURFACE = "#1a1a19"
PAGE_PLANE = "#0d0d0d"
CARD_SURFACE = "#17181d"
INK_PRIMARY = "#ffffff"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BASELINE = "#383835"
BORDER = "rgba(255,255,255,0.10)"

# Fixed categorical order — never cycle, never reorder by rank
CATEGORICAL = {
    "blue": "#3987e5",
    "orange": "#d95926",
    "teal": "#199e70",
    "yellow": "#c98500",
    "magenta": "#d55181",
    "green": "#008300",
    "violet": "#9085e9",
    "red": "#e66767",
}
CATEGORICAL_ORDER = list(CATEGORICAL.values())

# Fixed business roles (keeps the same color for the same concept across the app)
COLOR_PIX_IN = CATEGORICAL["blue"]
COLOR_PIX_OUT = CATEGORICAL["orange"]
COLOR_BLOCKCHAIN = CATEGORICAL["blue"]
COLOR_BRIDGE = CATEGORICAL["teal"]
SYMBOL_COLORS = {
    "BTC": CATEGORICAL["blue"],
    "ETH": CATEGORICAL["orange"],
    "USDT": CATEGORICAL["teal"],
    "MATIC": CATEGORICAL["yellow"],
    "SOL": CATEGORICAL["magenta"],
}

# Status — reserved, never repurposed as "series 4"
STATUS = {
    "CONFIRMED": "#0ca30c",
    "PENDING": "#fab219",
    "FAILED": "#d03b3b",
}

# Financial Projections page: one color per company, and the scenario colors
# reuse the status semantics (green=upside, yellow=base, red=downside).
COLOR_COMPANY_A = CATEGORICAL["blue"]
COLOR_COMPANY_B = CATEGORICAL["violet"]
SCENARIO_COLORS = {
    "Optimistic": STATUS["CONFIRMED"],
    "Conservative": STATUS["PENDING"],
    "Pessimistic": STATUS["FAILED"],
}

# Sequential ramp (single hue, light -> dark) for table heatmaps
SEQUENTIAL_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

TEMPLATE_NAME = "pixflow"


def register_template() -> None:
    """Registers (once) the shared Plotly template and sets it as default."""
    if TEMPLATE_NAME in pio.templates:
        pio.templates.default = TEMPLATE_NAME
        return

    layout = go.Layout(
        colorway=CATEGORICAL_ORDER,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, -apple-system, sans-serif", color=INK_SECONDARY, size=13),
        title=dict(font=dict(color=INK_PRIMARY, size=15)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=INK_SECONDARY)),
        xaxis=dict(
            gridcolor=GRIDLINE, zerolinecolor=BASELINE, linecolor=BASELINE,
            tickfont=dict(color=INK_MUTED),
        ),
        yaxis=dict(
            gridcolor=GRIDLINE, zerolinecolor=BASELINE, linecolor=BASELINE,
            tickfont=dict(color=INK_MUTED),
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        hoverlabel=dict(bgcolor=CARD_SURFACE, font=dict(color=INK_PRIMARY), bordercolor=BORDER),
    )
    pio.templates[TEMPLATE_NAME] = go.layout.Template(layout=layout)
    pio.templates.default = TEMPLATE_NAME


def apply_default_layout(fig: go.Figure, title: str | None = None, height: int = 360) -> go.Figure:
    fig.update_layout(height=height)
    if title:
        fig.update_layout(title=title)
    return fig
