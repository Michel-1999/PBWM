"""View — Margrit Müller (Spouse) · My Wealth Intelligence (use case 4.2).

The same configurable Meridian platform, with Margrit's own design (Burgundy
accent) and offers around philanthropy and estate/art succession.
"""

from __future__ import annotations

import streamlit as st

from app import dashboard, state, ui

state.init_state()
state.mark_all_read("spouse")
st.session_state.setdefault("accent_name_spouse", "Burgundy")
st.session_state.setdefault("accent_spouse", ui.ACCENTS["Burgundy"])
ui.apply_accent("spouse")

fam = state.get_family()
portfolio = fam["portfolios"]["spouse"]
member = fam["members"]["spouse"]

_tl, _tm, _tr = st.columns([0.3, 0.4, 0.3])
with _tl:
    ui.back_to_overview()
with _tr:
    dashboard.config_popover("spouse")

portrait = (
    ui.avatar_html("Spouse.png", "MM", 112, ring="#fff")
    + '<div style="text-align:right"><div style="color:#fff;font-weight:400;font-size:1.05rem">Margrit Müller</div>'
    + '<div style="color:#EAF2EC;font-size:.82rem">Spouse, age 62, Munich</div></div>'
)
ui.header_bar("My Wealth Intelligence", "powered by Meridian", right_html=portrait)

# --- 1) Identical KPI boxes ------------------------------------------------
dashboard.kpi_row(portfolio)

# --- 2) My strategy (agreed with the advisor) ------------------------------
dashboard.strategy_summary_card("spouse", portfolio, member)

# --- 3) Chat with Meridian AI --------------------------------------------
st.markdown(" ")
with st.expander("Chat with Meridian AI", expanded=True):
    ui.ai_chat_panel(
        "spouse", portfolio, member, state_key="spouse_chat",
        suggestions=[
            ("My net return", "What has been my net return, including all trades, since I started investing?"),
            ("My allocation", "Summarise my asset allocation and risk profile."),
            ("Off-topic test", "What is the S&P 500 going to do next quarter?"),
        ],
        placeholder="e.g. What is my portfolio worth and how is it allocated?",
    )

# --- 4) Personalised offers ------------------------------------------------
ui.pediment("For you")
o1, o2 = st.columns(2, gap="large")
with o1:
    if ui.offer_card(
        "spouse_foundation", tag="Planning ahead", title="Family foundation & philanthropy",
        body="Structuring your giving through the family foundation can be both meaningful and "
             "tax-efficient. Mr. Reto Wyss can walk you through the options.",
        cta_label="Request information"):
        state.add_message("spouse", "rm",
                          "Ich würde gerne über die Strukturierung unserer Stiftung und "
                          "philanthropische Themen sprechen.")
        st.toast("Sent to Reto Wyss.", icon="✅")
with o2:
    ui.offer_card(
        "spouse_art", tag="Planning ahead", title="Estate & art succession",
        body="Art and collectibles deserve their own succession plan, covering valuation, insurance "
             "and a smooth transfer to the next generation.", dismissible=True)

if st.button("📚  Open the Finance Learning hub", key="finlearn_spouse"):
    st.toast("Finance Learning is coming soon.")

# --- 5) Configurable dashboard + 6) advisor touchpoints --------------------
dashboard.render("spouse", portfolio, member)
dashboard.advisor_touchpoints("spouse")

ui.disclaimer_note()
ui.footer()
