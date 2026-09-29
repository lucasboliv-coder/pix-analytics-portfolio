"""
Single icon family for the whole app: Google Material Symbols (Outlined),
replacing the old emoji set.

Why: emoji glyphs render differently per OS/browser (Apple vs. Segoe UI vs.
Noto), which breaks visual consistency in a portfolio piece viewed on
whatever machine a recruiter happens to have. Material Symbols is a single
vector font, so every icon has identical weight, size and color everywhere.

Two call shapes cover every use site:
- `mi(name)`   -> ":material/name:" shorthand, for native Streamlit
                  parameters that already understand it (st.Page(icon=...),
                  st.page_link(icon=...), st.info(icon=...), and inline in
                  any text-rendering element: st.title, st.markdown, st.tabs
                  labels, ...).
- `icon_html`  -> a raw <span> for the app's own hand-built HTML components
                  (KPI cards, section headers) where text goes through
                  st.markdown(unsafe_allow_html=True) instead of a native
                  Streamlit widget.
"""

from __future__ import annotations


def mi(name: str) -> str:
    """":material/<name>:" shorthand for native Streamlit icon parameters."""
    return f":material/{name}:"


def icon_html(name: str, size: int = 18, color: str | None = None) -> str:
    """Inline <span> rendering one Material Symbol, for custom HTML blocks."""
    style = f"font-size:{size}px;"
    if color:
        style += f"color:{color};"
    return f'<span class="material-symbols-outlined" style="{style}">{name}</span>'


# Central names, keyed by role — one word to update if an icon ever needs to
# change, and one place to see the whole vocabulary at a glance.
ICON = {
    # Brand / navigation
    "brand": "bolt",
    "home": "home",
    "users_page": "group",
    "pix_page": "sync_alt",
    "chain_page": "hub",
    "financials_page": "trending_up",
    # Generic sections
    "overview": "bar_chart",
    "dashboards": "explore",
    "about": "waving_hand",
    "dataset": "dataset",
    "data": "table_rows",
    "filters": "tune",
    "calendar": "calendar_month",
    "yoy": "cached",
    "search": "manage_search",
    "correlation": "scatter_plot",
    "status": "science",
    "symbol": "monetization_on",
    "growth": "trending_up",
    "net_flow": "swap_vert",
    # KPI concepts
    "revenue": "payments",
    "ebitda": "trending_up",
    "clients": "group",
    "scenario": "track_changes",
    "fees": "receipt_long",
    "transactions": "swap_horiz",
    "pix_in": "call_received",
    "pix_out": "call_made",
    "unique_users": "diversity_3",
    "avg_ticket": "point_of_sale",
    "wallet": "account_balance_wallet",
    "value": "diamond",
    "average": "calculate",
    "gas_fee": "local_gas_station",
    "bridge": "link",
    "plan_actual": "fact_check",
    "costs": "receipt_long",
    # Alerts / links
    "lock": "lock",
    "warning": "warning",
    "linkedin": "work",
    "github": "code",
    "email": "mail",
    "resume": "description",
    "link_out": "open_in_new",
}
