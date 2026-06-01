"""View — Lukas Müller (Son) · My Wealth Intelligence, next-gen (use case 4.2).

The same configurable Meridian platform, with Lukas's own design (Teal accent,
line-chart performance by default). Setting a goal or making a deposit (in the
life-goal tracker) and confirming a meeting move the shared engagement score.
"""

from __future__ import annotations

import streamlit as st

from app import dashboard, state, ui

state.init_state()
state.mark_all_read("heir")
st.session_state.setdefault("accent_name_heir", "Teal")
st.session_state.setdefault("accent_heir", ui.ACCENTS["Teal"])
ui.apply_accent("heir")

fam = state.get_family()
eng = fam["engagement"]
portfolio = fam["portfolios"]["heir"]
member = fam["members"]["heir"]

portrait = (
    ui.avatar_html("sohn.png", "LM", 112, ring="#fff")
    + '<div style="text-align:right"><div style="color:#fff;font-weight:400;font-size:1.05rem">Lukas Müller</div>'
    + '<div style="color:#EAF2EC;font-size:.82rem">Next generation, age 32, Munich</div></div>'
)
ui.header_bar("My Wealth Intelligence", "powered by Meridian", right_html=portrait)

# --- Identical KPI boxes ---------------------------------------------------
dashboard.kpi_row(portfolio)

# --- Clio — your personal AI-Assistant (collapsible) -----------------------
st.markdown(" ")
with st.expander("Clio, your personal AI-Assistant", expanded=True):
    ui.ai_chat_panel(
        "heir", portfolio, member, state_key="heir_chat",
        title="Clio", scope="Your personal AI-Assistant",
        suggestions=[
            ("How am I doing?", "What has been my net return, including all trades, since I started?"),
            ("What's an ETF?", "What ETFs do I hold and what does that mean?"),
            ("Off-topic test", "Which crypto coin should I buy to get rich?"),
        ],
        placeholder="e.g. How much have I made since I started? What do I own?",
    )

# --- Personalised offers ----------------------------------------------------
ui.pediment("For you")
o1, o2 = st.columns(2, gap="large")
with o1:
    if ui.offer_card(
        "heir_savings", tag="Save smarter", icon="◆",
        title="Turn a goal into a monthly savings plan",
        body="A small automatic amount toward a goal (a first apartment, say) is the easiest way "
             "to build momentum. From CHF 100 / month, set up in 30 minutes with Mr. Reto Wyss.",
        cta_label="I'd like a savings-plan chat"):
        state.add_message("heir", "rm",
                          "Hi Reto, ich würde gerne einen einfachen monatlichen Sparplan "
                          "einrichten. Wann hätten Sie Zeit für ein kurzes Gespräch?")
        st.success("Nice! Mr. Reto Wyss will reach out to set it up.")
        st.rerun()
with o2:
    ui.offer_card(
        "heir_academy", tag="Learn", icon="◆", title="First-time investor academy",
        body="Short, plain-language explainers on ETFs, risk and compounding, tailored to where "
             "you are today. New modules coming soon.", dismissible=True)

if st.button("📚  Open the Finance Learning hub", key="finlearn_heir"):
    st.toast("Finance Learning is coming soon.")
st.caption("Short explainers on investing, risk and compounding (demo placeholder).")

# --- Configurable dashboard (life-goal tracker holds the engagement levers) -
dashboard.render("heir", portfolio, member)
dashboard.advisor_touchpoints("heir")

ui.disclaimer_note()
ui.footer()
