import streamlit as st

from data_gen.generator import END_DATE, START_DATE, load_data
from theme.icons import ICON, mi
from theme.style import kpi_grid, section_header

section_header(ICON["about"], "About the Author")

col_bio, col_links = st.columns([2.2, 1])
with col_bio:
    st.markdown(
        "**Lucas Bastos** — Data Analyst focused on ETL, data modeling and revenue analytics. "
        "Currently the first data hire at a crypto-payments fintech, building pipelines and "
        "dashboards for PIX, crypto and banking transactions from the ground up; previously in "
        "EdTech planning/forecasting and manufacturing BI. This app is a portfolio piece built to "
        "showcase that kind of work end-to-end — data generation, modeling, and dashboard design. "
        "The product dashboards (Users, PIX, Blockchain) run on synthetic data, generated algorithmically "
        "with scale and growth curves checked against real usage numbers I have access to professionally; "
        "Financial Projections runs on real financial data, mathematically masked before publishing (see "
        "the disclaimer below)."
    )
with col_links:
    st.link_button(
        "Resume",
        "https://raw.githubusercontent.com/lucasboliv-coder/pix-analytics-portfolio/master/docs/Lucas_Bastos_Resume.pdf",
        icon=mi(ICON["resume"]), use_container_width=True,
    )
    st.link_button("LinkedIn", "https://www.linkedin.com/in/lucas-bastos-56756084/", icon=mi(ICON["linkedin"]), use_container_width=True)
    st.link_button("GitHub", "https://github.com/lucasboliv-coder", icon=mi(ICON["github"]), use_container_width=True)
    st.link_button("Email", "mailto:lucasboliv@gmail.com", icon=mi(ICON["email"]), use_container_width=True)

st.markdown("---")

st.title(f"{mi(ICON['brand'])} PixFlow Analytics — PixFlow & NovaPay Finance")
st.markdown(
    "Data Analyst portfolio project — product and financial dashboards for two fictional "
    "companies of a payments/crypto fintech group, **PixFlow** and **NovaPay Finance**."
)

st.info(
    "**Two different kinds of \"not real\" on this page — worth telling apart.** "
    "Users, PIX and Blockchain are synthetic: generated algorithmically "
    "(`data_gen/generator.py`, fixed seed) — the growth curves, weekly "
    "seasonality and overall scale were checked against real usage numbers "
    "I have access to professionally. PixFlow itself is a fictional brand "
    "created for this portfolio. "
    "**Financial Projections** is different: it's real data. Company names "
    "are fictionalized, and every figure has been run through a random, "
    "per-company mathematical operation — generated once and never recorded, "
    "including by me — before publishing. Growth rates and cost/revenue "
    "ratios closely track the real model (aside from rounding); the absolute "
    "numbers can't be reverse-engineered from what's published. See that "
    "page for details.",
    icon=mi(ICON["lock"]),
)

data = load_data()
users = data["users"]
pix_in, pix_out = data["pix_in"], data["pix_out"]
chain = data["chain"]

section_header(ICON["dataset"], "Synthetic dataset overview")

pix_volume = pix_in["amount_brl"].sum() + pix_out["amount_brl"].sum()
chain_volume = chain["value"].sum()
total_transactions = len(pix_in) + len(pix_out) + len(chain)

kpi_grid(
    [
        {"icon": ICON["users_page"], "label": "Registered users", "value": f"{len(users):,}"},
        {"icon": "payments", "label": "PIX volume (in + out)", "value": f"R$ {pix_volume:,.0f}"},
        {"icon": ICON["chain_page"], "label": "On-chain volume", "value": f"{chain_volume:,.0f}"},
        {"icon": ICON["transactions"], "label": "Total transactions", "value": f"{total_transactions:,}"},
    ]
)

st.markdown(f"**Simulated period:** {START_DATE:%m/%d/%Y} — {END_DATE:%m/%d/%Y}")

section_header(ICON["dashboards"], "Dashboards")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"#### {mi(ICON['users_page'])} Users & Avg Ticket")
    st.markdown(
        "Active user growth, monthly/yearly matrix and average ticket "
        "trend by direction (in/out)."
    )
    st.page_link("pages/users_and_ticket.py", label="Open dashboard", icon=mi(ICON["users_page"]))
with col2:
    st.markdown(f"#### {mi(ICON['pix_page'])} PIX Traded")
    st.markdown(
        "Volume, fees, status and value×fee correlation for incoming and "
        "outgoing PIX transactions."
    )
    st.page_link("pages/pix_in_out.py", label="Open dashboard", icon=mi(ICON["pix_page"]))
with col3:
    st.markdown(f"#### {mi(ICON['chain_page'])} Blockchain")
    st.markdown(
        "On-chain and bridge activity, by symbol, with year-over-year "
        "comparison and status analysis."
    )
    st.page_link("pages/blockchain.py", label="Open dashboard", icon=mi(ICON["chain_page"]))
with col4:
    st.markdown(f"#### {mi(ICON['financials_page'])} Financial Projections")
    st.markdown(
        "Revenue, costs and client growth for the group's two companies, "
        "projected through 2029 across 3 scenarios. *(real data, mathematically masked)*"
    )
    st.page_link("pages/financial_projections.py", label="Open dashboard", icon=mi(ICON["financials_page"]))

st.markdown("---")
st.caption(
    "Stack: Streamlit + Plotly + pandas/numpy. "
    "[Source code on GitHub](https://github.com/lucasboliv-coder/pix-analytics-portfolio)."
)
