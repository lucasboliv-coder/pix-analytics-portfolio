import streamlit as st

from theme.charts import register_template
from theme.icons import ICON, mi
from theme.style import inject_css

st.set_page_config(
    page_title="PixFlow Analytics",
    layout="wide",
    page_icon=mi(ICON["brand"]),
    initial_sidebar_state="expanded",
)
inject_css()
register_template()

home = st.Page("pages/home.py", title="Home", icon=mi(ICON["home"]), default=True)
users = st.Page("pages/users_and_ticket.py", title="Users & Ticket", icon=mi(ICON["users_page"]))
pix = st.Page("pages/pix_in_out.py", title="PIX Traded", icon=mi(ICON["pix_page"]))
chain = st.Page("pages/blockchain.py", title="Blockchain", icon=mi(ICON["chain_page"]))
financials = st.Page("pages/financial_projections.py", title="Financial Projections", icon=mi(ICON["financials_page"]))

pg = st.navigation([home, users, pix, chain, financials])
pg.run()
