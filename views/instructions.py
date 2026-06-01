"""View — Prototype Instructions (landing)."""

from __future__ import annotations

import streamlit as st

from app import ui

ui.header_bar("Prototype Instructions", "",
              right_html='<span class="tb-wordmark">THE BANK</span>', logo="bank")

st.markdown(
    "This interactive prototype demonstrates the two AI use cases from the paper for **The Bank**, a "
    "family-owned Swiss private bank. **Clio** is the AI assistant working behind everything. "
    "**Meridian** is the platform by The Bank: clients use **My Wealth Intelligence** (powered by "
    "Meridian) and the relationship manager uses the **Wealth Intelligence Advisor** (powered by "
    "Meridian). The prototype follows one client family, the **Müller family**, across four "
    "connected workspaces that share one live state."
)

# --- The two use cases ------------------------------------------------------
ui.pediment("The two use cases")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown(
        '<div class="tb-card accent">'
        '<span class="tb-chip solid">Use case 4.1</span>'
        '<div class="tb-metric-value" style="font-size:1.25rem;margin-top:8px">Wealth Intelligence Advisor</div>'
        "<p style=\"font-size:.9rem;color:#1A1A1A;margin-top:6px\">"
        "The relationship manager's workspace, powered by <b>Clio</b>. It brings together a "
        "whole-family briefing, the engagement score, secure messaging, a meeting calendar and "
        "data-driven <i>next-best-actions</i>. It empowers the advisor; it does not replace them.</p>"
        '<span class="tb-chip">Advisor Co-Pilot (Clio)</span></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        '<div class="tb-card accent">'
        '<span class="tb-chip solid">Use case 4.2</span>'
        '<div class="tb-metric-value" style="font-size:1.25rem;margin-top:8px">My Wealth Intelligence</div>'
        "<p style=\"font-size:.9rem;color:#1A1A1A;margin-top:6px\">"
        "Each client's own configurable dashboard on Meridian (portfolio, goals, scenarios and "
        "taxes), with <b>Clio</b> answering in plain language and discreet, personalised nudges "
        "that engage heirs years before the wealth transfer.</p>"
        '<span class="tb-chip">Client dashboard (Meridian)</span></div>',
        unsafe_allow_html=True,
    )

# --- How to explore ---------------------------------------------------------
ui.pediment("How to explore the prototype")
st.markdown(
    "**Click through all four profiles** (in the sidebar, or via the cards below) to see one "
    "shared, reactive platform from every angle. To watch the live loop in action, follow these steps:"
)
st.markdown(
    '<div class="tb-card"><ol style="margin:0 0 0 1.1rem;font-size:.94rem;line-height:1.7">'
    '<li>Open the <b>Wealth Intelligence Advisor</b> (Reto Wyss). Meet the family and chat with <b>Clio</b>.</li>'
    '<li>Open <b>Lukas (Son)</b> and set a savings goal or make a deposit. Your engagement updates the family plan.</li>'
    '<li>Back in the <b>Advisor</b> workspace, act on a <i>next-best-action</i> and send a meeting request.</li>'
    '<li>Open <b>Lukas</b> again and confirm it. The engagement score and every dashboard update together.</li>'
    '</ol></div>',
    unsafe_allow_html=True,
)

# --- Enter a workspace (prominent, clickable, coloured per profile) ---------
ui.pediment("Enter a workspace")
nav_items = [
    ("Reto Wyss", "Advisor", "views/rm.py", "Score, Clio and next-best-actions.", "#1F4F39"),
    ("Hans Müller", "Principal", "views/principal.py", "Dashboard, Clio and governance.", "#34577C"),
    ("Margrit Müller", "Spouse", "views/spouse.py", "Her own design and offers.", "#7C3340"),
    ("Lukas Müller", "Son", "views/heir.py", "Goals, deposits and Clio.", "#176B63"),
]
cols = st.columns(4, gap="medium")
for col, (name, role, path, desc, colour) in zip(cols, nav_items):
    with col:
        st.markdown(
            f'<div class="tb-card" style="border-top:3px solid {colour}">'
            f'<div class="tb-metric-label" style="color:{colour}">{role}</div>'
            f'<b style="color:{colour}">{name}</b><br>'
            f'<span style="color:#3C5A4B;font-size:.84rem">{desc}</span></div>',
            unsafe_allow_html=True,
        )
        if st.button("Open  →", key=f"go_{role}", type="primary", width="stretch"):
            st.switch_page(path)

ui.disclaimer_note()
ui.footer()
