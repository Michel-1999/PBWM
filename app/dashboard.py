"""Shared client dashboard (paper §4.2).

Principal and heir use the SAME configurable framework — identical KPI boxes, the
same modular widget library, the same colour personalisation — so the prototype
proves "one platform, two generations". The pages differ only in their
persona-specific offer/nudge content and AI-chat persona.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import state, ui

WIDGETS = ["Portfolio statistics", "Holdings detail", "Life-goal tracker",
           "Scenario simulation", "Tax overview"]
COMING_SOON = ["Cash-flow planner", "ESG / sustainability lens", "Currency exposure", "Liquidity ladder"]


# ---------------------------------------------------------------------------
# Identical KPI boxes (same for both personas)
# ---------------------------------------------------------------------------
def kpi_row(portfolio: dict) -> None:
    nr = portfolio["net_return"]
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        ui.metric_card("Portfolio value", ui.money(portfolio["total_value_chf"]), f"as of {portfolio['as_of']}")
    with k2:
        ui.metric_card("Net return", f"{nr['annualised_return_irr_pct']:+.1f}% p.a.", "money-weighted, net of fees")
    with k3:
        ui.metric_card("Total gain", ui.money(nr["cumulative_net_gain_chf"]),
                       f"{nr['simple_net_return_pct']:+.1f}% on contributions")
    with k4:
        ds = portfolio["digital_asset_sleeve"]
        ui.metric_card("Digital assets", f"{ds['weight_pct']}%", ui.money(ds["value_chf"]))


# ---------------------------------------------------------------------------
# Configurable dashboard
# ---------------------------------------------------------------------------
def render(persona_key: str, portfolio: dict, member: dict) -> None:
    flags = st.session_state.setdefault(f"widgets_{persona_key}",
                                        {w: True for w in WIDGETS})
    with st.expander("⚙ Configure your dashboard — your design, your way", expanded=False):
        st.markdown("**Modules** — show or hide what you care about")
        cols = st.columns(len(WIDGETS))
        for col, w in zip(cols, WIDGETS):
            flags[w] = col.checkbox(w, value=flags.get(w, True), key=f"cfg_{persona_key}_{w}")
        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            ui.accent_picker(persona_key)
            st.caption("Your accent colour re-themes your whole Meridian interface.")
        with oc2:
            default_ct = "Line" if persona_key == "heir" else "Bar"
            st.selectbox("Performance chart style", ["Bar", "Line"],
                         index=(1 if default_ct == "Line" else 0), key=f"cfg_ct_{persona_key}")
            show_bm = st.checkbox("Show benchmark", value=True, key=f"cfg_bm_{persona_key}")
        with oc3:
            compact = st.checkbox("Compact view", value=False, key=f"cfg_compact_{persona_key}")
        st.caption("More modules coming soon — " + ", ".join(COMING_SOON))
    accent = ui.accent_for(persona_key)
    show_bm = st.session_state.get(f"cfg_bm_{persona_key}", True)
    chart_type = "line" if st.session_state.get(f"cfg_ct_{persona_key}",
                                                ("Line" if persona_key == "heir" else "Bar")) == "Line" else "bar"
    chart_h = 210 if st.session_state.get(f"cfg_compact_{persona_key}") else 250

    if flags.get("Portfolio statistics"):
        ui.pediment("Portfolio statistics")
        a, b = st.columns(2, gap="large")
        with a:
            st.markdown("**Asset allocation**")
            ui.allocation_chart(portfolio, accent)
        with b:
            st.markdown("**Annual performance**" + (" vs. benchmark" if show_bm else ""))
            ui.performance_chart(portfolio, accent, height=chart_h, show_benchmark=show_bm,
                                 chart_type=chart_type)

    if flags.get("Holdings detail"):
        ui.pediment("Holdings detail")
        hdf = pd.DataFrame([
            {"Holding": h["name"], "Asset class": h["asset_class"],
             "Value (CHF)": h["value_chf"], "Weight %": h["weight_pct"]}
            for h in portfolio["holdings"]
        ])
        st.dataframe(hdf, hide_index=True, width="stretch")

    if flags.get("Life-goal tracker"):
        ui.pediment("Life-goal tracker")
        _life_goals(persona_key, accent)

    if flags.get("Scenario simulation"):
        ui.pediment("Scenario simulation")
        _scenario(persona_key, portfolio, accent)

    if flags.get("Tax overview"):
        ui.pediment("Tax overview · cross-border DE / CH")
        st.markdown(
            "- **Booking centre** Switzerland — assets held & reported from Zurich.\n"
            "- **Domicile** Germany — income & gains taxable in your country of residence.\n"
            "- **Swiss withholding** 35% on Swiss-source income, reclaimable under the CH–DE treaty.\n"
            "- **Reporting** annual DE-compatible tax statement provided by The Bank."
        )
        st.caption("General information only. Not tax advice.")


STATIC_GOALS = {
    "principal": [
        {"name": "Legacy fund for grandchildren", "target": 500_000, "saved": 320_000},
        {"name": "Ticino property upkeep reserve", "target": 200_000, "saved": 165_000},
    ],
    "spouse": [
        {"name": "Family foundation endowment", "target": 400_000, "saved": 250_000},
        {"name": "Travel & arts fund", "target": 120_000, "saved": 78_000},
    ],
}


def _life_goals(persona_key: str, accent: str) -> None:
    if persona_key in STATIC_GOALS:
        for g in STATIC_GOALS[persona_key]:
            st.markdown(f"**{g['name']}** — {ui.money(g['saved'])} of {ui.money(g['target'])}")
            ui.hbar("Progress", g["saved"] / g["target"] * 100, color=accent, suffix="%")
        return

    # Heir: goals are live and editable — these actions move the family score.
    eng = state.get_family()["engagement"]
    if not eng["heir_goals"]:
        st.info("No goals yet. Create your first one below.")
    for g in eng["heir_goals"]:
        prog = (g["saved_chf"] / g["target_chf"] * 100) if g["target_chf"] else 0
        st.markdown(f"**{g['name']}** — {ui.money(g['saved_chf'])} of {ui.money(g['target_chf'])} · {g['horizon_years']}y")
        ui.hbar("Progress", prog, color=accent, suffix="%")

    a, b = st.columns(2, gap="large")
    with a:
        with st.form("heir_goal_form", clear_on_submit=True):
            st.markdown("**Add a goal**")
            gname = st.text_input("Goal", value="First apartment", label_visibility="collapsed")
            gtarget = st.number_input("Target (CHF)", 5_000, 2_000_000, 150_000, 5_000)
            ghoriz = st.slider("Horizon (years)", 1, 20, 6)
            if st.form_submit_button("Create goal", type="primary", width="stretch"):
                state.add_goal(gname, gtarget, ghoriz)
                st.rerun()
    with b:
        with st.form("heir_deposit_form", clear_on_submit=True):
            st.markdown("**Add to your plan**")
            amount = st.number_input("Amount (CHF)", 50, 100_000, 500, 50)
            st.caption("Credited to your cash and your first goal.")
            if st.form_submit_button("Deposit", type="primary", width="stretch"):
                state.record_deposit(amount)
                st.rerun()


def _scenario(persona_key: str, portfolio: dict, accent: str) -> None:
    st.caption("Project how your wealth could grow if you keep investing, with an illustrative "
               "uncertainty band. Not a forecast.")
    c1, c2, c3, c4 = st.columns(4)
    ret = c1.slider("Expected return % p.a.", 0.0, 10.0, 5.0, 0.5, key=f"sc_ret_{persona_key}")
    contrib = c2.slider("Monthly contribution CHF", 0, 10_000,
                        500 if persona_key == "heir" else 0, 250, key=f"sc_con_{persona_key}")
    years = c3.slider("Horizon (years)", 1, 30, 15, key=f"sc_yrs_{persona_key}")
    vol = c4.slider("Volatility (± band) %", 0.0, 15.0, 7.0, 0.5, key=f"sc_vol_{persona_key}")

    end_value = ui.projection_chart(portfolio["total_value_chf"], ret, contrib, years, vol, accent)
    invested = portfolio["total_value_chf"] + contrib * years * 12
    m1, m2, m3 = st.columns(3)
    with m1:
        ui.metric_card("Projected value", ui.money(end_value), f"in {years} years", accent=accent)
    with m2:
        ui.metric_card("Total contributed", ui.money(invested), "today + monthly")
    with m3:
        ui.metric_card("Projected growth", ui.money(end_value - invested), "expected, illustrative", accent=accent)
    st.caption("Illustrative geometric projection · ± band = return ± volatility. More scenarios coming soon.")


# ---------------------------------------------------------------------------
# Advisor touchpoints (shared)
# ---------------------------------------------------------------------------
def advisor_touchpoints(persona_key: str) -> None:
    ui.pediment("Your advisor — Mr. Reto Wyss")
    t1, t2, t3 = st.tabs(["Secure messaging", "Meetings", "Documents"])
    with t1:
        st.markdown(ui.chip("Secure message to your advisor", "gold") + ui.chip("Not the AI chat"),
                    unsafe_allow_html=True)
        ui.secure_messaging_widget(persona_key)
    with t2:
        ui.meetings_widget(persona_key)
        st.markdown("**Past meetings**")
        ui.past_meetings(persona_key)
    with t3:
        st.caption("Document exchange (placeholder).")
        st.markdown("- 📄 Latest portfolio review.pdf\n- 📄 Suitability profile.pdf\n- 📄 Fee schedule.pdf")
        st.file_uploader("Securely upload a document for Mr. Reto Wyss", key=f"upload_{persona_key}")
