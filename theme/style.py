"""
Shared visual system for PixFlow Analytics: global CSS (dark glassmorphism)
+ reusable KPI card components (plain HTML, injected via st.markdown).

Icons throughout are Material Symbols (see theme.icons), not emoji — see
theme/icons.py for why.
"""

from __future__ import annotations

import streamlit as st

from theme.icons import icon_html

ACCENT_FROM = "#3987e5"
ACCENT_TO = "#9085e9"


def inject_css() -> None:
    # st.html(), not st.markdown(unsafe_allow_html=True): a CSS block this
    # size, fed through the markdown-to-HTML pipeline, gets its raw-HTML
    # block cut short at the first blank line inside it (CommonMark's
    # blank-line-terminated HTML block rule), leaking the rest of the CSS
    # as literal page text. st.html() renders the string directly, no
    # markdown parsing involved.
    #
    # No separate font import: Streamlit already ships Material Symbols
    # Rounded for its own native :material/name: icons (nav, st.title,
    # st.button, ...), confirmed loaded via document.fonts once any of
    # those render. Reusing that exact font for our own HTML-based icons
    # (KPI cards, section headers) both sidesteps an unreliable external
    # Google Fonts fetch and keeps every icon in the app pixel-identical.
    st.html(
        f"""
        <style>
        html, body, [class*="css"] {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}

        .material-symbols-outlined {{
            font-family: 'Material Symbols Rounded';
            font-weight: normal;
            font-style: normal;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-smoothing: antialiased;
            vertical-align: middle;
            font-variation-settings: 'FILL' 0, 'wght' 380, 'GRAD' 0, 'opsz' 24;
        }}

        /* ------------------------------------------------------------ */
        /* Backdrop: dark plane + soft color glow, the "light" the glass */
        /* panels below pick up via backdrop-filter.                     */
        /* ------------------------------------------------------------ */
        .stApp {{
            background:
                radial-gradient(1200px 640px at 8% -12%, rgba(57,135,229,0.16), transparent 60%),
                radial-gradient(1000px 560px at 102% 6%, rgba(144,133,233,0.13), transparent 60%),
                radial-gradient(900px 500px at 40% 108%, rgba(57,135,229,0.07), transparent 60%),
                #0a0a0b;
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
        h1 .material-symbols-outlined {{
            -webkit-text-fill-color: {ACCENT_FROM};
            font-size: 1.6rem;
            margin-right: 0.15rem;
        }}

        h2, h3 {{
            color: #ffffff !important;
            font-weight: 650 !important;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 0.4rem;
            margin-top: 1.4rem !important;
        }}

        /* ------------------------------------------------------------ */
        /* Sidebar: frosted glass panel                                  */
        /* ------------------------------------------------------------ */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(23,24,29,0.80), rgba(10,10,11,0.92)) !important;
            backdrop-filter: blur(22px) saturate(160%);
            -webkit-backdrop-filter: blur(22px) saturate(160%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }}
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {{
            color: #c3c2b7 !important;
            font-size: 0.85rem !important;
        }}
        [data-testid="stSidebar"] nav a {{
            border-radius: 10px !important;
            margin: 1px 0;
            transition: background 0.15s ease, color 0.15s ease;
        }}
        [data-testid="stSidebar"] nav a:hover {{
            background: rgba(255,255,255,0.06) !important;
        }}
        [data-testid="stSidebar"] nav a[aria-current="page"] {{
            background: linear-gradient(90deg, rgba(57,135,229,0.22), rgba(144,133,233,0.12)) !important;
            box-shadow: inset 2px 0 0 {ACCENT_FROM};
        }}

        /* ------------------------------------------------------------ */
        /* Tabs                                                          */
        /* ------------------------------------------------------------ */
        .stTabs [data-baseweb="tab-list"] {{
            background: rgba(255,255,255,0.035);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-radius: 12px;
            padding: 4px;
            gap: 4px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 9px;
            color: #898781 !important;
            font-weight: 500;
            padding: 0.45rem 1.1rem;
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {ACCENT_FROM}, {ACCENT_TO}) !important;
            color: #fff !important;
            box-shadow: 0 4px 16px rgba(57,135,229,0.35);
        }}

        /* ------------------------------------------------------------ */
        /* Panels: dataframe, expander, alert — same glass surface        */
        /* ------------------------------------------------------------ */
        [data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.10) !important;
            box-shadow: 0 8px 28px rgba(0,0,0,0.35);
        }}
        [data-testid="stExpander"] {{
            background: rgba(255,255,255,0.035);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: 14px;
        }}
        [data-testid="stAlert"] {{
            border-radius: 12px;
            border-left-width: 3px;
            background: rgba(255,255,255,0.035) !important;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }}
        hr {{ border-color: rgba(255,255,255,0.08) !important; margin: 1.4rem 0; }}

        /* ------------------------------------------------------------ */
        /* Inputs: selects, date range, slider, radio                    */
        /* ------------------------------------------------------------ */
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
            background: rgba(255,255,255,0.045) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 10px !important;
        }}
        [data-testid="stSlider"] [role="slider"] {{
            box-shadow: 0 0 0 4px rgba(57,135,229,0.20);
        }}

        /* ------------------------------------------------------------ */
        /* Buttons / link buttons — glass pill, glow on hover             */
        /* ------------------------------------------------------------ */
        .stButton button, .stLinkButton a, .stDownloadButton button {{
            background: rgba(255,255,255,0.045) !important;
            border: 1px solid rgba(255,255,255,0.14) !important;
            border-radius: 10px !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
        }}
        .stButton button:hover, .stLinkButton a:hover, .stDownloadButton button:hover {{
            border-color: rgba(57,135,229,0.55) !important;
            box-shadow: 0 0 0 1px rgba(57,135,229,0.30), 0 6px 20px rgba(57,135,229,0.22);
            transform: translateY(-1px);
        }}

        /* ------------------------------------------------------------ */
        /* Custom components                                             */
        /* ------------------------------------------------------------ */
        .pf-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255,255,255,0.045);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(57,135,229,0.35);
            border-radius: 20px;
            padding: 5px 14px;
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
            background: linear-gradient(160deg, rgba(255,255,255,0.07), rgba(255,255,255,0.015));
            backdrop-filter: blur(20px) saturate(160%);
            -webkit-backdrop-filter: blur(20px) saturate(160%);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.40), inset 0 1px 0 rgba(255,255,255,0.07);
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
            overflow: hidden;
        }}
        .pf-kpi-card::before {{
            content: "";
            position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, {ACCENT_FROM}, {ACCENT_TO});
            opacity: 0.9;
        }}
        .pf-kpi-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(57,135,229,0.45);
            box-shadow: 0 14px 34px rgba(0,0,0,0.45), 0 0 0 1px rgba(57,135,229,0.20), inset 0 1px 0 rgba(255,255,255,0.08);
        }}
        .pf-kpi-icon-chip {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px; height: 34px;
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(57,135,229,0.22), rgba(144,133,233,0.16));
            border: 1px solid rgba(255,255,255,0.10);
        }}
        .pf-kpi-icon-chip .material-symbols-outlined {{ color: #9ec5f4; font-size: 18px; }}
        .pf-kpi-label {{
            color: #9a988f; font-size: 0.72rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.5rem;
        }}
        .pf-kpi-value {{ color: #ffffff; font-size: 1.55rem; font-weight: 750; margin-top: 0.15rem; }}
        .pf-kpi-delta {{ font-size: 0.78rem; font-weight: 600; margin-top: 0.3rem; }}
        .pf-kpi-delta.up {{ color: #34c759; }}
        .pf-kpi-delta.down {{ color: #e66767; }}

        .pf-section-header {{
            display: flex; align-items: center; gap: 10px;
            margin: 1.4rem 0 0.7rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.5rem;
        }}
        .pf-section-header .pf-kpi-icon-chip {{ width: 28px; height: 28px; border-radius: 8px; }}
        .pf-section-header .pf-kpi-icon-chip .material-symbols-outlined {{ font-size: 15px; }}
        .pf-section-header .title {{ color: #ffffff; font-size: 1.02rem; font-weight: 650; }}
        </style>
        """
    )


def section_header(icon: str, title: str) -> None:
    """`icon` is a Material Symbols name (see theme.icons.ICON), not an emoji."""
    chip = f'<span class="pf-kpi-icon-chip">{icon_html(icon)}</span>'
    st.markdown(
        f'<div class="pf-section-header">{chip}<span class="title">{title}</span></div>',
        unsafe_allow_html=True,
    )


def kpi_grid(cards: list[dict]) -> None:
    """Renders a grid of glass KPI cards.

    cards: [{"icon": "<material symbol name>", "label": "...", "value": "...",
             "delta": "+12.3%", "positive": True}, ...]
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
        icon_chip = f'<span class="pf-kpi-icon-chip">{icon_html(c.get("icon", "circle"))}</span>'
        card_html = (
            '<div class="pf-kpi-card">'
            f"{icon_chip}"
            f'<div class="pf-kpi-label">{c["label"]}</div>'
            f'<div class="pf-kpi-value">{c["value"]}</div>'
            f"{delta_html}"
            "</div>"
        )
        items.append(card_html)
    st.markdown(f'<div class="pf-kpi-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def period_badge(text: str) -> None:
    st.markdown(f'<div class="pf-badge">{icon_html("calendar_month", size=15)} {text}</div>', unsafe_allow_html=True)
