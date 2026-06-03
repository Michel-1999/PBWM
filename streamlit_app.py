"""Meridian — AI prototype · entry point / router.

Run locally:  streamlit run streamlit_app.py
On Streamlit Community Cloud, set the main file path to: streamlit_app.py

Brands:
  * Meridian — the platform by The Bank; its built-in AI is surfaced as
    "Meridian AI" (chat + recommendations).
  * Dashboards: clients see "My Wealth Intelligence", the RM the
    "Advisor Wealth Intelligence", both powered by Meridian.

Navigation: the sidebar page menu is hidden. The app opens on the Prototype
Instructions hub; from there the user enters a workspace, and each workspace has
a top-left "Overview" link back to the hub.

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
# The sidebar page menu is hidden: the Instructions hub is the entry point and
# routes to the workspaces (each has a top-left "Overview" link back).
nav = st.navigation(pages, position="hidden")
ui.sidebar_controls()
nav.run()
