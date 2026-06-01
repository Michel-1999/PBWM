"""Meridian — AI prototype · entry point / router.

Run locally:  streamlit run streamlit_app.py
On Streamlit Community Cloud, set the main file path to: streamlit_app.py

Brands:
  * Clio     — the AI assistant behind everything (chat + recommendations)
  * Meridian — the platform by The Bank
  * Dashboards: clients see "My Wealth Intelligence", the RM the
    "Wealth Intelligence Advisor", both powered by Meridian.

Access control: if APP_PASSWORD is set in secrets (e.g. on Streamlit Cloud), the
app shows a password screen first. With no APP_PASSWORD configured it is open.
"""

from __future__ import annotations

import streamlit as st

from app import state, ui

st.set_page_config(page_title="Meridian", page_icon="🏛️",
                   layout="wide", initial_sidebar_state="expanded")
ui.inject_brand()

if not ui.password_gate():
    st.stop()

ui.sidebar_brand()
state.init_state()

pages = [
    st.Page("views/instructions.py", title="Prototype Instructions", default=True),
    st.Page("views/rm.py", title="Reto Wyss (Advisor)"),
    st.Page("views/principal.py", title="Hans Müller (Principal)"),
    st.Page("views/spouse.py", title="Margrit Müller (Spouse)"),
    st.Page("views/heir.py", title="Lukas Müller (Son)"),
]
nav = st.navigation(pages, position="sidebar")
ui.sidebar_controls()
nav.run()
