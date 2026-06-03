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
def config_popover(persona_key: str) -> None:
    """Compact dashboard settings, shown as a small top-right control."""
    flags = st.session_state.setdefault(f"widgets_{persona_key}", {w: True for w in WIDGETS})
    with st.popover("⚙  Configure dashboard"):
        st.markdown("**Modules to show**")
        for w in WIDGETS:
            flags[w] = st.checkbox(w, value=flags.get(w, True), key=f"cfg_{persona_key}_{w}")
        st.markdown("**Appearance**")
        ui.accent_picker(persona_key)
        st.caption("Your accent colour re-themes your whole Meridian interface.")
        default_ct = "Line" if persona_key == "heir" else "Bar"
        st.selectbox("Performance chart style", ["Bar", "Line"],
                     index=(1 if default_ct == "Line" else 0), key=f"cfg_ct_{persona_key}")
        st.checkbox("Show benchmark", value=True, key=f"cfg_bm_{persona_key}")
        st.checkbox("Compact view", value=False, key=f"cfg_compact_{persona_key}")
        st.caption("More modules coming soon: " + ", ".join(COMING_SOON))


def render(persona_key: str, portfolio: dict, member: dict) -> None:
    flags = st.session_state.setdefault(f"widgets_{persona_key}", {w: True for w in WIDGETS})
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
            "- **Booking centre** Switzerland: assets held & reported from Zurich.\n"
            "- **Domicile** Germany: income & gains taxable in your country of residence.\n"
            "- **Swiss withholding** 35% on Swiss-source income, reclaimable under the CH/DE treaty.\n"
            "- **Reporting** annual DE-compatible tax statement provided by The Bank."
        )
        st.caption("General information only. Not tax advice.")


# Kept in sync with the fixtures policy.goals (so the Strategy Monitor's goal-gap
# check and the client-facing tracker show the same funding levels).
STATIC_GOALS = {
    "principal": [
        {"name": "Legacy fund for grandchildren", "target": 500_000, "saved": 380_000},
        {"name": "Ticino property upkeep reserve", "target": 200_000, "saved": 165_000},
    ],
    "spouse": [
        {"name": "Family foundation endowment", "target": 400_000, "saved": 300_000},
        {"name": "Travel & arts fund", "target": 120_000, "saved": 96_000},
    ],
}


def _life_goals(persona_key: str, accent: str) -> None:
    if persona_key in STATIC_GOALS:
        for g in STATIC_GOALS[persona_key]:
            st.markdown(f"**{g['name']}**: {ui.money(g['saved'])} of {ui.money(g['target'])}")
            ui.hbar("Progress", g["saved"] / g["target"] * 100, color=accent, suffix="%")
        return

    # Heir: goals are live and editable — these actions move the family score.
    eng = state.get_family()["engagement"]
    if not eng["heir_goals"]:
        st.info("No goals yet. Create your first one below.")
    for g in eng["heir_goals"]:
        prog = (g["saved_chf"] / g["target_chf"] * 100) if g["target_chf"] else 0
        st.markdown(f"**{g['name']}**: {ui.money(g['saved_chf'])} of {ui.money(g['target_chf'])} ({g['horizon_years']}y)")
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
# My strategy (paper §4.3, client side) — a plain summary of the strategy the
# client agreed with their advisor. Clients see WHAT was agreed, not a fulfilment
# score or AI recommendations (those live in the advisor's Client Strategy Monitor).
# ---------------------------------------------------------------------------
def strategy_summary_card(persona_key: str, portfolio: dict, member: dict) -> None:
    policy = portfolio.get("policy", {})
    target = policy.get("target_allocation", {})
    limits = policy.get("limits", {})
    risk = policy.get("risk_profile") or portfolio.get("risk_profile", "")

    top = sorted(target.items(), key=lambda kv: kv[1], reverse=True)[:4]
    mix = ", ".join(f"{c} {w:.0f}%" for c, w in top) or "balanced across asset classes"

    guards = []
    if limits.get("concentration_limit_pct"):
        guards.append(f"no single holding above {limits['concentration_limit_pct']}%")
    if limits.get("cash_floor_pct") is not None and limits.get("cash_ceiling_pct") is not None:
        guards.append(f"cash kept around {limits['cash_floor_pct']}–{limits['cash_ceiling_pct']}%")
    if limits.get("da_vol_budget_pct"):
        guards.append(f"digital assets up to {limits['da_vol_budget_pct']}%")
    guards_txt = "; ".join(guards) if guards else "diversification and risk discipline"

    if member["role"] == "heir":
        goals = [g["name"] for g in state.get_family()["engagement"].get("heir_goals", [])]
        goals_txt = ", ".join(goals) if goals else "your first goal (set one in the goal tracker below)"
    else:
        goals = [g["name"] for g in policy.get("goals", [])]
        goals_txt = ", ".join(goals) if goals else "none on file"

    ui.pediment("My strategy")
    st.markdown(
        '<div class="tb-card accent">'
        '<div class="tb-metric-label">Agreed with Reto Wyss at the annual review</div>'
        f'<div style="font-weight:400;color:var(--tb-green);font-size:1.08rem;margin:3px 0 9px">'
        f'{ui._esc(risk)} mandate</div>'
        '<div style="font-size:.92rem;line-height:1.75">'
        f'<b>Target mix:</b> {ui._esc(mix)}<br>'
        f'<b>Guardrails:</b> {ui._esc(guards_txt)}<br>'
        f'<b>Goals we track together:</b> {ui._esc(goals_txt)}</div></div>',
        unsafe_allow_html=True,
    )
    if st.button("I'd like to adjust something: schedule a meeting with Reto Wyss",
                 key=f"strategy_meet_{persona_key}", type="primary"):
        state.add_message(
            persona_key, "rm",
            "Hallo Reto, ich würde gerne meine Strategie anschauen und ggf. anpassen. "
            "Können wir einen Termin vereinbaren?")
        st.toast("Sent to Reto Wyss. He will reach out to schedule a meeting.", icon="✅")


# ---------------------------------------------------------------------------
# Advisor touchpoints (shared)
# ---------------------------------------------------------------------------
def advisor_touchpoints(persona_key: str) -> None:
    ui.pediment("Your advisor, Mr. Reto Wyss")
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
