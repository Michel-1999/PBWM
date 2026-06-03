"""View — Advisor Wealth Intelligence (Mr. Reto Wyss).

Order: the family overview (total wealth + per-member cockpit), the always-on
Meridian AI chat, the AI recommendations, the Client Strategy Monitor, the
Engagement & Inheritance Engine, and the relationship tools (messaging + calendar).
"""

from __future__ import annotations

import datetime as _dt

import pandas as pd
import streamlit as st

from app import gemini, state, strategy, ui

state.init_state()

fam = state.get_family()
sc = state.get_score()
NAME = {"rm": "Mr. Reto Wyss", "principal": "Hans Müller", "spouse": "Margrit Müller", "heir": "Lukas Müller"}
MEMBERS = ["principal", "spouse", "heir"]

# Each client's chosen accent (their My Wealth Intelligence colour) frames their card.
DEFAULT_ACCENT = {"principal": ui.ACCENTS["Slate blue"], "spouse": ui.ACCENTS["Burgundy"],
                  "heir": ui.ACCENTS["Teal"]}

# Traffic lights: green = on track, orange = risky, red = act now.
TL = {"ok": ("#1F4F39", "On track"), "info": ("#3C5A4B", "Monitored"),
      "watch": ("#C8791E", "Risky"), "breach": ("#9C3B2E", "Act now")}
_CHECK_ORDER = ("drift", "concentration", "cash", "vol_budget", "goal_gap", "cross_border")

# Where a recommendation comes from (which sensing engine / use case).
SRC_ENGAGEMENT = "Engagement Engine"
SRC_STRATEGY = "Client Strategy Monitor"
SRC_COLOR = {SRC_ENGAGEMENT: "#34577C", SRC_STRATEGY: "#176B63"}


def _src_chip(src: str) -> str:
    col = SRC_COLOR.get(src, "#3C5A4B")
    return f'<span class="tb-chip" style="background:{col};color:#fff;border-color:{col}">{src}</span>'


def _initials(name: str) -> str:
    return "".join(w[0] for w in name.split()[:2]).upper()


def _accent(key: str) -> str:
    return st.session_state.get(f"accent_{key}", DEFAULT_ACCENT.get(key, ui.PALETTE["green"]))


def _stat(label: str, value: str, color: str = "var(--tb-ink)") -> str:
    return (f'<div style="display:flex;justify-content:space-between;font-size:.87rem;padding:3px 0;'
            f'border-top:1px solid var(--tb-hairline)"><span style="color:var(--tb-muted)">{label}</span>'
            f'<b style="color:{color}">{value}</b></div>')


def _fit_color(fit: int) -> str:
    if fit >= 85:
        return "#1F4F39"
    return "#C8791E" if fit >= 60 else "#9C3B2E"


def _member_cockpit_html(key: str) -> str:
    m = fam["members"][key]
    p = fam["portfolios"][key]
    nr = p["net_return"]
    ds = p["digital_asset_sleeve"]["weight_pct"]
    kyc = m["kyc_status"]
    accent = _accent(key)
    kyc_col = ui.PALETTE["alert"] if kyc == "review" else accent
    av = ui.avatar_html(m.get("avatar"), _initials(m["name"]), 52, ring=accent)
    return (
        f'<div class="tb-card" style="border-top:3px solid {accent}">'
        f'<div style="display:flex;gap:11px;align-items:center;margin-bottom:6px">{av}'
        f'<div><div style="font-weight:600;font-size:1.02rem">{m["name"]}</div>'
        f'<div style="font-size:.76rem;color:var(--tb-muted)">{m["title"]}, age {m["age"]}</div>'
        f'</div></div>'
        + _stat("Portfolio value", ui.money(p["total_value_chf"]))
        + _stat("Net return", f"{nr['annualised_return_irr_pct']:+.1f}% p.a.")
        + _stat("Digital assets", f"{ds}%")
        + _stat("KYC", kyc.upper(), kyc_col)
        + "</div>"
    )


def _fulfilment_card_html(key: str) -> str:
    m = fam["members"][key]
    h = fam.get("health", {}).get(key, {})
    fit = h.get("policy_fit", 100)
    checks = h.get("checks", {})
    accent = _accent(key)
    av = ui.avatar_html(m.get("avatar"), _initials(m["name"]), 40, ring=accent)
    rows = ""
    for cat in _CHECK_ORDER:
        status = checks.get(cat, {}).get("status", "ok")
        color, word = TL.get(status, TL["info"])
        label = strategy.CATEGORY_LABEL.get(cat, cat)
        rows += (
            '<div style="display:flex;justify-content:space-between;align-items:center;'
            'font-size:.78rem;padding:2px 0">'
            f'<span style="color:var(--tb-muted)"><span style="display:inline-block;width:9px;'
            f'height:9px;border-radius:50%;background:{color};margin-right:7px"></span>{label}</span>'
            f'<span style="color:{color};font-weight:600">{word}</span></div>'
        )
    fc = _fit_color(fit)
    return (
        f'<div class="tb-card" style="border-top:3px solid {accent}">'
        f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:6px">{av}'
        f'<div><div style="font-weight:600">{m["name"]}</div>'
        '<div style="font-size:.72rem;color:var(--tb-muted)">Strategy fulfilment</div></div></div>'
        f'<div class="tb-metric-value" style="color:{fc};font-size:1.9rem">{fit}'
        '<span style="font-size:.8rem;color:var(--tb-muted)"> / 100</span></div>'
        f'<div style="margin-top:6px;border-top:1px solid var(--tb-hairline);padding-top:6px">{rows}</div>'
        '</div>'
    )


def _eng_color(score: int) -> str:
    if score >= 66:
        return "#1F4F39"
    return "#C8791E" if score >= 40 else "#9C3B2E"


def _engagement_card_html(key: str) -> str:
    m = fam["members"][key]
    e = fam.get("engagement_scores", {}).get(key, {})
    score = e.get("score", 0)
    comps = e.get("components", {})
    accent = _accent(key)
    av = ui.avatar_html(m.get("avatar"), _initials(m["name"]), 40, ring=accent)
    rows = ""
    for label, val in comps.items():
        rows += (
            '<div style="display:flex;align-items:center;gap:7px;font-size:.72rem;margin:2px 0">'
            f'<span style="width:108px;color:var(--tb-muted)">{label}</span>'
            '<span style="flex:1;height:6px;background:var(--tb-tint);border-radius:3px;overflow:hidden">'
            f'<span style="display:block;height:100%;width:{val:.0f}%;background:{accent}"></span></span></div>'
        )
    ec = _eng_color(score)
    return (
        f'<div class="tb-card" style="border-top:3px solid {accent}">'
        f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:6px">{av}'
        f'<div><div style="font-weight:600">{m["name"]}</div>'
        '<div style="font-size:.72rem;color:var(--tb-muted)">Engagement Score</div></div></div>'
        f'<div class="tb-metric-value" style="color:{ec};font-size:1.9rem">{score}'
        '<span style="font-size:.8rem;color:var(--tb-muted)"> / 100</span></div>'
        f'<div style="margin-top:6px;border-top:1px solid var(--tb-hairline);padding-top:6px">{rows}</div>'
        '</div>'
    )


# --- Top bar: overview link + logged-in identity + family picker -----------
ui.back_to_overview()
tl, tr = st.columns([0.55, 0.45], gap="large")
with tl:
    ui.logged_in_strip("Mr. Reto Wyss", "Relationship Manager, Junior", "RM.png", "RW")
with tr:
    ui.family_picker()

ui.header_bar("Advisor Wealth Intelligence")

# ===========================================================================
# 1) Müller family total wealth (always visible) + per-member cockpit
# ===========================================================================
ui.pediment("Müller family total wealth")
total = sum(p["total_value_chf"] for p in fam["portfolios"].values())
chip_members = ui.chip(f"{len(MEMBERS)} family members")
chip_score = ui.chip(f"Inheritance score {sc['score']}/100, {sc['band_label']}", "gold")
st.markdown(
    f'<div class="tb-card accent" style="border-top-width:4px">'
    f'<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:14px;align-items:center">'
    f'<div><div class="tb-metric-label">Total relationship AUM</div>'
    f'<div class="tb-metric-value" style="font-size:2rem">{ui.money_full(total)}</div></div>'
    f'<div style="text-align:right">{chip_members}{chip_score}</div>'
    f'</div></div>',
    unsafe_allow_html=True,
)
st.markdown(" ")
mcols = st.columns(3, gap="medium")
for col, key in zip(mcols, MEMBERS):
    col.markdown(_member_cockpit_html(key), unsafe_allow_html=True)
st.markdown(" ")

# ===========================================================================
# 2) Chat with Meridian AI — always on, directly under the overview
# ===========================================================================
ui.advisor_chat_panel(
    "rm_advisor",
    suggestions=[
        ("Wealth-transfer risk", "What is the wealth-transfer risk for this family and why?"),
        ("Next best actions", "What are the next best actions for the Müller family right now?"),
        ("Tell me about Margrit", "Tell me about Margrit's portfolio and how it fits the family plan."),
    ],
)

# ===========================================================================
# 3) AI recommendations — consolidates both engines (with dismiss + timestamps)
# ===========================================================================
with st.expander("AI recommendations", expanded=False):
    st.caption("Meridian consolidates the signals from both engines into actions you review and send; "
               "nothing is sent automatically. Filter by type, then act on or dismiss each one.")
    st.markdown(
        'Source of each action: ' + _src_chip(SRC_ENGAGEMENT) + ' (use case 2) &nbsp; '
        + _src_chip(SRC_STRATEGY) + ' (use case 3).',
        unsafe_allow_html=True,
    )

    dismissed = st.session_state.setdefault("dismissed_recs", [])
    rec_seen = st.session_state.setdefault("rec_seen", {})
    CATS = ["Meeting request", "Secure message", "Alert"]
    chosen = st.multiselect("Filter by type", CATS, default=CATS, key="rec_filter")

    # Build one combined list from both engines. A strategy flag can be all three
    # types (meeting + message + alert); an engagement action is one type.
    recs = []
    for nba in fam["nbas"]:
        meet = nba["action"] == "request_meeting"
        recs.append({"id": nba["id"], "source": nba.get("source", SRC_ENGAGEMENT), "title": nba["title"],
                     "detail": nba["rationale"], "target": nba["target"], "topic": nba["topic"],
                     "message": nba["message"], "obj": nba, "kind": "nba", "severity": None,
                     "cats": ["Meeting request"] if meet else ["Secure message"],
                     "can_meeting": meet, "can_message": not meet})
    for a in fam.get("alerts", []):
        if a["audience"] in ("rm", "both") and a["suggested_action"] != "none":
            recs.append({"id": a["id"], "source": SRC_STRATEGY, "title": a["title"],
                         "detail": a.get("detail") or a["template_text"], "target": a["member"],
                         "topic": a["topic"], "message": a.get("message", ""), "obj": a, "kind": "alert",
                         "severity": a["severity"], "cats": ["Meeting request", "Secure message", "Alert"],
                         "can_meeting": True, "can_message": True})
    recs = [r for r in recs if r["id"] not in dismissed]

    # Varied, stable "received" timestamps so the feed reads like a real inbox.
    _OFFSET_H = {"alert-spouse-cash": 1, "alert-spouse-drift": 4, "nba-heir-savings": 7,
                 "nba-heir-kyc": 22, "nba-governance": 49, "nba-alt-investments": 98}
    _now_dt = _dt.datetime.now()
    for r in recs:
        if r["id"] not in rec_seen:
            rec_seen[r["id"]] = (_now_dt - _dt.timedelta(hours=_OFFSET_H.get(r["id"], 0))).strftime("%Y-%m-%d %H:%M")
    recs.sort(key=lambda r: rec_seen.get(r["id"], ""), reverse=True)  # newest first
    if chosen:
        recs = [r for r in recs if any(c in chosen for c in r["cats"])]


    def _send(r: dict, action: str) -> None:
        text = r["message"]
        if r["kind"] == "alert":
            with st.spinner("Meridian is drafting…"):
                text = gemini.draft_alert_message(r["obj"], fam)["text"] or r["message"]
        if action == "request_meeting":
            state.request_meeting(with_=r["target"], topic=r["topic"], by="rm")
        state.add_message("rm", r["target"], text)
        if r["id"] not in dismissed:
            dismissed.append(r["id"])

    if not recs:
        st.success("No open recommendations. The family is on track. ✦")
    for r in recs:
        with st.container(border=True):
            left, right = st.columns([0.7, 0.3])
            with left:
                st.markdown(f"**{r['title']}**")
                st.caption(r["detail"])
                chips = _src_chip(r["source"]) + ui.chip(f"For {NAME.get(r['target'], r['target'])}")
                if r["severity"]:
                    col, word = TL.get(r["severity"], TL["info"])
                    chips += (f'<span class="tb-chip" style="background:{col};color:#fff;'
                              f'border-color:{col}">{word}</span>')
                for c in r["cats"]:
                    if c != "Alert":
                        chips += ui.chip(c)
                st.markdown(chips, unsafe_allow_html=True)
                st.caption(f"Received {rec_seen.get(r['id'], '')}")
            with right:
                nm = NAME.get(r["target"], r["target"])
                if r["can_meeting"] and st.button("Send meeting request", key=f"recmtg_{r['id']}",
                                                  type="primary", width="stretch"):
                    _send(r, "request_meeting")
                    st.toast(f"Meeting request sent to {nm}.", icon="✅")
                    st.rerun()
                if r["can_message"] and st.button("Send message", key=f"recmsg_{r['id']}",
                                                  type=("secondary" if r["can_meeting"] else "primary"),
                                                  width="stretch"):
                    _send(r, "send_message")
                    st.toast(f"Message sent to {nm}.", icon="✅")
                    st.rerun()
                if st.button("Dismiss", key=f"recdis_{r['id']}", width="stretch"):
                    if r["id"] not in dismissed:
                        dismissed.append(r["id"])
                    st.rerun()

# ===========================================================================
# 4) Client Strategy Monitor — fulfilment + simulation (actions live above)
# ===========================================================================
with st.container(key="exp_strategy"):
    with st.expander("Client Strategy Monitor", expanded=False):
        st.caption("Each client agreed a personal strategy with Reto Wyss at their annual review. "
                   "Meridian checks the live portfolios against it across six dimensions and scores how "
                   "well each strategy is met. Actionable flags flow into AI recommendations above.")

        sim = bool(fam.get("_shock_active"))
        state_badge = ui.chip("Simulated", "alert") if sim else ui.chip("Live", "gold")
        st.markdown('<div style="font-weight:600;font-size:1rem;margin-top:4px">Strategy fulfilment by '
                    f'client &nbsp;{state_badge}</div>', unsafe_allow_html=True)
        fcols = st.columns(3, gap="medium")
        for col, key in zip(fcols, MEMBERS):
            col.markdown(_fulfilment_card_html(key), unsafe_allow_html=True)

        st.divider()

        st.markdown("**Simulation (stress test)** &nbsp;"
                    + ui.chip("traffic lights above update live", "gold"), unsafe_allow_html=True)
        st.caption("Move the markets and the traffic lights above update (then marked Simulated). "
                   "For example a market drop, a crypto sell-off or a rates move. New flags appear in "
                   "AI recommendations above.")
        g1, g2, g3, g4 = st.columns(4)
        eq_move = g1.slider("Equity move %", -30, 30, -15, key="sim_equity")
        fx_move = g2.slider("FX move % (EUR)", -20, 20, 0, key="sim_fx")
        cr_move = g3.slider("Crypto move %", -50, 50, 0, key="sim_crypto")
        bd_move = g4.slider("Bond move %", -15, 15, 0, key="sim_bond")
        b1, b2, _ = st.columns([0.22, 0.22, 0.56])
        if b1.button("Apply simulation", key="sim_apply", type="primary", width="stretch"):
            state.apply_market_shock(eq_move, fx_move, cr_move, bd_move)
            st.rerun()
        if b2.button("Reset", key="sim_reset", width="stretch"):
            state.reset_market_shock()
            st.rerun()
        if sim:
            prm = fam.get("_shock_params", {})
            st.markdown(ui.chip(f"Simulation active: equity {prm.get('equity_pct', 0):+.0f}%, "
                                f"FX {prm.get('fx_pct', 0):+.0f}%, crypto {prm.get('crypto_pct', 0):+.0f}%, "
                                f"bonds {prm.get('bond_pct', 0):+.0f}%", "alert"), unsafe_allow_html=True)

# ===========================================================================
# 5) Engagement Engine — two rule-based scores (engagement + inheritance)
# ===========================================================================
with st.container(key="exp_engagement"):
    with st.expander("Engagement Engine", expanded=False):
        st.caption("A transparent, rule-based engine (not Meridian AI). It produces a per-member "
                   "Engagement Score from platform behaviour, and a family Inheritance Score that adds "
                   "age and wealth at stake to flag at-risk AUM. Meridian AI only interprets these into "
                   "the AI recommendations above.")

        st.markdown("**Engagement Score by member** (higher = more engaged)")
        ecols = st.columns(3, gap="medium")
        for col, key in zip(ecols, MEMBERS):
            col.markdown(_engagement_card_html(key), unsafe_allow_html=True)

        st.divider()
        st.markdown("**Inheritance Score (family)** (higher = more at-risk AUM)")
        last_delta = fam["score_history"][-1]["delta"] if fam["score_history"] else 0
        left, right = st.columns([0.36, 0.64], gap="large")
        with left:
            good = last_delta < 0
            arrow = "▼" if last_delta < 0 else ("▲" if last_delta > 0 else "—")
            dcolor = ui.PALETTE["green"] if good else (ui.PALETTE["alert"] if last_delta > 0 else ui.PALETTE["muted"])
            delta_line = (f'<div class="tb-metric-sub" style="color:{dcolor}">{arrow} {abs(last_delta)} pts'
                          f'{", AUM secured" if good else ""}</div>') if last_delta else ""
            st.markdown(
                f'<div class="tb-card accent"><div class="tb-metric-label">Priority (higher = more at-risk AUM)</div>'
                f'<div class="tb-metric-value" style="color:{sc["color"]};font-size:2.6rem">{sc["score"]}'
                f'<span style="font-size:1rem;color:{ui.PALETTE["muted"]}"> / 100</span></div>'
                f'<div style="color:{sc["color"]};font-weight:700">{sc["band_label"]}</div>{delta_line}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(" ")
            ui.gauge(sc["score"], sc["color"])
        with right:
            labels = {"wealth_at_stake": "Wealth at stake", "transfer_proximity": "Transfer proximity",
                      "heir_disengagement": "Heir disengagement", "relationship_thinness": "Relationship thinness"}
            for k, label in labels.items():
                ui.hbar(label, sc["components"][k], color=sc["color"])
            st.markdown('<div style="margin-top:6px">' + "".join(f"• {d}<br>" for d in sc["drivers"][:3]) + "</div>",
                        unsafe_allow_html=True)

        hist = fam["score_history"]
        if len(hist) > 1:
            dfh = pd.DataFrame({"Month": [h["ts"][:7] for h in hist],
                                "Priority score": [h["score"] for h in hist]})
            dfh = dfh.groupby("Month", as_index=True).last()
            st.caption("How the priority score developed over time (monthly)")
            st.line_chart(dfh, y="Priority score", height=180, color=ui.PALETTE["green"])

# ===========================================================================
# 6) Relationship — secure messaging + calendar
# ===========================================================================
with st.expander("Secure messages to the family", expanded=False):
    rec_labels = {"Hans Müller (Principal)": "principal", "Margrit Müller (Spouse)": "spouse",
                  "Lukas Müller (Son)": "heir"}
    sel = st.selectbox("Write to", list(rec_labels), key="rm_msg_to")
    rkey = rec_labels[sel]
    thread = [m for m in fam["messages"]
              if (m["from"] == rkey and m["to"] == "rm") or (m["from"] == "rm" and m["to"] == rkey)]
    for m in thread:
        if m["to"] == "rm" and not m["read"]:
            state.mark_read(m["id"])
        ui.chat_bubble(f"{NAME.get(m['from'], m['from'])}, {m['ts'][:16].replace('T', ' ')}", m["text"], "human")
    if not thread:
        st.caption("No messages yet with this family member.")
    with st.form(key=f"rm_send_{rkey}", clear_on_submit=True):
        ic, sc2 = st.columns([0.82, 0.18])
        txt = ic.text_input("Message", key=f"rm_send_inp_{rkey}", label_visibility="collapsed",
                            placeholder=f"Write a secure message to {NAME[rkey]}…")
        if sc2.form_submit_button("Send", type="primary", width="stretch") and txt.strip():
            state.add_message("rm", rkey, txt.strip())
            st.rerun()

with st.expander("Calendar & meetings", expanded=False):
    st.markdown("**Upcoming & requested meetings**")
    meetings = fam["meetings"]
    if not meetings:
        st.caption("No meetings yet. Plan one below.")
    else:
        rows = [{"With": NAME.get(m["with"], m["with"]), "Topic": m["topic"],
                 "When": m["proposed_ts"], "Status": m["status"].capitalize()} for m in meetings]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown("**Past meetings**")
    ui.past_meetings()
    st.markdown("**Plan next meeting**")
    with st.form("rm_plan_meeting", clear_on_submit=True):
        cc = st.columns([0.30, 0.40, 0.30])
        who_label = cc[0].selectbox("With", ["Hans Müller", "Margrit Müller", "Lukas Müller"])
        topic = cc[1].text_input("Topic", value="Portfolio review")
        when = cc[2].date_input("Proposed date", value=_dt.date.today() + _dt.timedelta(days=7))
        if st.form_submit_button("Plan meeting", type="primary"):
            wkey = {"Hans Müller": "principal", "Margrit Müller": "spouse", "Lukas Müller": "heir"}[who_label]
            state.request_meeting(with_=wkey, topic=topic or "Meeting", proposed_ts=str(when), by="rm")
            st.success(f"Meeting requested with {who_label} for {when}.")
            st.rerun()

ui.disclaimer_note()
ui.footer()
