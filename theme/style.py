"""
Shared visual system for PixFlow Analytics: global CSS + reusable KPI card
components (plain HTML, injected via st.markdown).
"""

from __future__ import annotations

import streamlit as st

ACCENT_FROM = "#3987e5"
ACCENT_TO = "#9085e9"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}

        .stApp {{
            background:
                radial-gradient(1200px 600px at 10% -10%, rgba(57,135,229,0.10), transparent),
                radial-gradient(1000px 500px at 100% 0%, rgba(144,133,233,0.08), transparent),
                #0d0d0d;
        }}

        h1 {{
            font-size: 2.1rem !important;
            font-weight: 800 !important;
            background: linear-gradient(90deg, {ACCENT_FROM}, {ACCENT_TO});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding-bottom: 0.2rem;
            letter-spacing: -0.02em;
        }}

        h2, h3 {{
            color: #ffffff !important;
            font-weight: 650 !important;
            border-bottom: 1px solid #2c2c2a;
            padding-bottom: 0.4rem;
            margin-top: 1.4rem !important;
        }}

        [data-testid="stSidebar"] {{
            background: #111114 !important;
            border-right: 1px solid #2c2c2a;
        }}
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {{
            color: #c3c2b7 !important;
            font-size: 0.85rem !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            background: #17181d;
            border-radius: 10px;
            padding: 4px;
            gap: 4px;
            border: 1px solid #2c2c2a;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            color: #898781 !important;
            font-weight: 500;
            padding: 0.45rem 1.1rem;
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {ACCENT_FROM}, {ACCENT_TO}) !important;
            color: #fff !important;
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #2c2c2a !important;
        }}
        [data-testid="stExpander"] {{
            background: #17181d;
            border: 1px solid #2c2c2a !important;
            border-radius: 12px;
        }}
        [data-testid="stAlert"] {{ border-radius: 10px; border-left-width: 4px; }}
        hr {{ border-color: #2c2c2a !important; margin: 1.4rem 0; }}

        .pf-badge {{
            display: inline-block;
            background: #17181d;
            border: 1px solid {ACCENT_FROM};
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 0.82rem;
            color: #9ec5f4;
            margin-bottom: 1rem;
        }}

        .pf-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 14px;
            margin: 0.6rem 0 1.4rem;
        }}
        .pf-kpi-card {{
            position: relative;
            background: linear-gradient(160deg, #191a20, #131318);
            border: 1px solid #2c2c2a;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 4px 18px rgba(0,0,0,0.35);
            transition: transform 0.15s ease, border-color 0.15s ease;
            overflow: hidden;
        }}
        .pf-kpi-card::before {{
            content: "";
            position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, {ACCENT_FROM}, {ACCENT_TO});
            opacity: 0.85;
        }}
        .pf-kpi-card:hover {{ transform: translateY(-2px); border-color: rgba(57,135,229,0.4); }}
        .pf-kpi-icon {{ font-size: 1.15rem; opacity: 0.9; }}
        .pf-kpi-label {{
            color: #898781; font-size: 0.72rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.35rem;
        }}
        .pf-kpi-value {{ color: #ffffff; font-size: 1.55rem; font-weight: 750; margin-top: 0.15rem; }}
        .pf-kpi-delta {{ font-size: 0.78rem; font-weight: 600; margin-top: 0.3rem; }}
        .pf-kpi-delta.up {{ color: #0ca30c; }}
        .pf-kpi-delta.down {{ color: #e66767; }}

        .pf-section-header {{
            display: flex; align-items: center; gap: 10px;
            margin: 1.4rem 0 0.7rem; border-bottom: 1px solid #2c2c2a; padding-bottom: 0.5rem;
        }}
        .pf-section-header .icon {{ font-size: 1.25rem; }}
        .pf-section-header .title {{ color: #ffffff; font-size: 1.02rem; font-weight: 650; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(icon: str, title: str) -> None:
    st.markdown(
        f"""<div class="pf-section-header"><span class="icon">{icon}</span>
        <span class="title">{title}</span></div>""",
        unsafe_allow_html=True,
    )


def kpi_grid(cards: list[dict]) -> None:
    """Renders a grid of modern KPI cards.

    cards: [{"icon": "👥", "label": "...", "value": "...", "delta": "+12.3%", "positive": True}, ...]
    """
    # Note: no indentation/blank lines in the generated HTML — Streamlit's
    # markdown parser treats lines indented with 4+ spaces as a code block,
    # which would break the cards. Everything on a single line per card.
    items = []
    for c in cards:
        delta_html = ""
        if c.get("delta") is not None:
            cls = "up" if c.get("positive", True) else "down"
            arrow = "▲" if cls == "up" else "▼"
            delta_html = f'<div class="pf-kpi-delta {cls}">{arrow} {c["delta"]}</div>'
        card_html = (
            '<div class="pf-kpi-card">'
            f'<div class="pf-kpi-icon">{c.get("icon", "")}</div>'
            f'<div class="pf-kpi-label">{c["label"]}</div>'
            f'<div class="pf-kpi-value">{c["value"]}</div>'
            f"{delta_html}"
            "</div>"
        )
        items.append(card_html)
    st.markdown(f'<div class="pf-kpi-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def period_badge(text: str) -> None:
    st.markdown(f'<div class="pf-badge">📅 {text}</div>', unsafe_allow_html=True)
