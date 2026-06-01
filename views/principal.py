"""View — Hans Müller (Principal) · My Wealth Intelligence (use case 4.2)."""

from __future__ import annotations

import streamlit as st

from app import dashboard, state, ui

state.init_state()
state.mark_all_read("principal")
st.session_state.setdefault("accent_name_principal", "Slate blue")
st.session_state.setdefault("accent_principal", ui.ACCENTS["Slate blue"])
ui.apply_accent("principal")

fam = state.get_family()
portfolio = fam["portfolios"]["principal"]
member = fam["members"]["principal"]

portrait = (
    ui.avatar_html("vater.png", "HM", 112, ring="#fff")
    + '<div style="text-align:right"><div style="color:#fff;font-weight:400;font-size:1.05rem">Hans Müller</div>'
    + '<div style="color:#EAF2EC;font-size:.82rem">Principal, age 65, Munich</div></div>'
)
ui.header_bar("My Wealth Intelligence", "powered by Meridian", right_html=portrait)

# --- Identical KPI boxes ---------------------------------------------------
dashboard.kpi_row(portfolio)

# --- Clio — your personal AI-Assistant (collapsible) -----------------------
st.markdown(" ")
with st.expander("Clio, your personal AI-Assistant", expanded=True):
    ui.ai_chat_panel(
        "principal", portfolio, member, state_key="principal_chat",
        title="Clio", scope="Your personal AI-Assistant",
        suggestions=[
            ("My net return", "What has been my net return, including all trades, since I started investing?"),
            ("My fees", "What fees am I paying?"),
            ("Off-topic test", "Should I buy more Nvidia stock right now?"),
        ],
        placeholder="e.g. What is my net return, including all trades, since I started?",
    )

# --- Personalised nudges (discreet) ----------------------------------------
ui.pediment("For you")
o1, o2 = st.columns(2, gap="large")
with o1:
    if member["age"] >= 65 and not fam["engagement"]["principal_governance_intro_done"]:
        if ui.offer_card(
            "principal_gov", tag="A discreet recommendation",
            title="Family governance & succession",
            body="As retirement approaches, many families value a calm, confidential conversation "
                 "about succession and involving the next generation — entirely at your pace.",
            cta_label="Let Mr. Reto Wyss know I'm interested"):
            state.add_message("principal", "rm",
                              "Ich würde gerne unverbindlich über Familien-Governance und "
                              "Nachfolgeplanung sprechen.")
            st.success("Thank you — Mr. Reto Wyss will be in touch.")
            st.rerun()
    else:
        ui.offer_card("principal_planning", tag="Planning ahead", title="Annual wealth review",
                      body="Your next portfolio review is a good moment to revisit goals, risk and "
                           "the estate plan together.", dismissible=True)
with o2:
    if ui.offer_card(
        "principal_realestate", tag="Planning ahead", title="Real estate in your estate plan",
        body="Holiday homes and property can complicate succession. Ask Mr. Reto Wyss about structuring "
             "real estate (including the Ticino home) for a smooth transfer.",
        cta_label="Request information"):
        state.add_message("principal", "rm",
                          "Können wir bei Gelegenheit über die Nachfolgeplanung für unsere "
                          "Immobilien (u.a. Tessin) sprechen?")
        st.success("Sent to Mr. Reto Wyss.")
        st.rerun()

if st.button("📚  Open the Finance Learning hub", key="finlearn_principal"):
    st.toast("Finance Learning is coming soon.")
st.caption("A financial-education hub for clients (demo placeholder).")

# --- Configurable dashboard + advisor touchpoints --------------------------
dashboard.render("principal", portfolio, member)
dashboard.advisor_touchpoints("principal")
st.checkbox("Also receive paper statements by post (2-year digital-transition option)",
            value=True, key="principal_paper",
            help="Reflects the paper's transition period for the boomer cohort — digital adoption "
                 "at the client's own pace.")

ui.disclaimer_note()
ui.footer()
