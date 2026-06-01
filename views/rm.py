"""View — Wealth Intelligence Advisor (Mr. Reto Wyss) · use case 4.1.

Top: the whole Müller family's total wealth + per-member overview. Then: Chat
with Clio (whole-family), the Inheritance Engagement Score, Clio-proposed
Next-Best-Actions, secure messaging, and a calendar with past & planned meetings.
"""

from __future__ import annotations

import datetime as _dt

import pandas as pd
import streamlit as st

from app import state, ui

state.init_state()

fam = state.get_family()
sc = state.get_score()
NAME = {"rm": "Mr. Reto Wyss", "principal": "Hans Müller", "spouse": "Margrit Müller", "heir": "Lukas Müller"}
MEMBERS = ["principal", "spouse", "heir"]


def _initials(name: str) -> str:
    return "".join(w[0] for w in name.split()[:2]).upper()


# --- Top strip: logged-in identity + family picker -------------------------
tl, tr = st.columns([0.55, 0.45], gap="large")
with tl:
    ui.logged_in_strip("Mr. Reto Wyss", "Relationship Manager, Junior", "RM.png", "RW")
with tr:
    ui.family_picker()

ui.header_bar("Wealth Intelligence Advisor", "powered by Meridian")

# ===========================================================================
# Müller Family — Total Wealth (always on top)
# ===========================================================================
ui.pediment("Müller Family Total Wealth")
total = sum(p["total_value_chf"] for p in fam["portfolios"].values())
chip_members = ui.chip(f"{len(MEMBERS)} family members")
chip_score = ui.chip(f"Engagement score {sc['score']}/100, {sc['band_label']}", "gold")
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


def _stat(label: str, value: str, color: str = "var(--tb-ink)") -> str:
    return (f'<div style="display:flex;justify-content:space-between;font-size:.87rem;padding:3px 0;'
            f'border-top:1px solid var(--tb-hairline)"><span style="color:var(--tb-muted)">{label}</span>'
            f'<b style="color:{color}">{value}</b></div>')


# Compact 3-column advisor cockpit (distinct from the client dashboards)
mcols = st.columns(3, gap="medium")
for col, key in zip(mcols, MEMBERS):
    m = fam["members"][key]
    p = fam["portfolios"][key]
    nr = p["net_return"]
    ds = p["digital_asset_sleeve"]["weight_pct"]
    kyc = m["kyc_status"]
    kyc_col = ui.PALETTE["alert"] if kyc == "review" else "var(--tb-green)"
    av = ui.avatar_html(m.get("avatar"), _initials(m["name"]), 52)
    with col:
        st.markdown(
            f'<div class="tb-card accent">'
            f'<div style="display:flex;gap:11px;align-items:center;margin-bottom:6px">{av}'
            f'<div><div style="font-weight:600;font-size:1.02rem">{m["name"]}</div>'
            f'<div style="font-size:.76rem;color:var(--tb-muted)">{m["title"]}, age {m["age"]}</div>'
            f'</div></div>'
            + _stat("Portfolio value", ui.money(p["total_value_chf"]))
            + _stat("Net return", f"{nr['annualised_return_irr_pct']:+.1f}% p.a.")
            + _stat("Digital assets", f"{ds}%")
            + _stat("KYC", kyc.upper(), kyc_col)
            + "</div>",
            unsafe_allow_html=True,
        )
st.markdown(" ")

# ===========================================================================
# Chat with Clio — ONE co-pilot over the whole family (right below total wealth)
# ===========================================================================
with st.expander("Chat with Clio", expanded=True):
    ui.advisor_chat_panel(
        "rm_advisor",
        suggestions=[
            ("Wealth-transfer risk", "What is the wealth-transfer risk for this family and why?"),
            ("Next best actions", "What are the next best actions for the Müller family right now?"),
            ("Tell me about Margrit", "Tell me about Margrit's portfolio and how it fits the family plan."),
        ],
    )

# ===========================================================================
# Inheritance Engagement Score (collapsible)
# ===========================================================================
with st.expander("Inheritance Engagement Score", expanded=True):
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
        if len(fam["score_history"]) > 1:
            st.line_chart(pd.DataFrame({"score": [h["score"] for h in fam["score_history"]]}),
                          height=120, color=ui.PALETTE["green"])

# ===========================================================================
# Next-Best-Actions — proposed by Clio (collapsible)
# ===========================================================================
with st.expander("Next-Best-Actions (proposed by Clio)", expanded=True):
    if not fam["nbas"]:
        st.success("No open actions. The family is well engaged. ✦")
    for nba in fam["nbas"]:
        with st.container(border=True):
            c1, c2 = st.columns([0.74, 0.26])
            with c1:
                st.markdown(f"**{nba['title']}**")
                st.caption(nba["rationale"])
                st.markdown(ui.chip(f"For {NAME[nba['target']]}")
                            + ui.chip("Meeting" if nba["action"] == "request_meeting" else "Message", "gold"),
                            unsafe_allow_html=True)
            with c2:
                label = "Send meeting request" if nba["action"] == "request_meeting" else "Send message"
                if st.button(label, key=f"nba_{nba['id']}", type="primary", width="stretch"):
                    if nba["action"] == "request_meeting":
                        state.request_meeting(with_=nba["target"], topic=nba["topic"], by="rm")
                    state.add_message("rm", nba["target"], nba["message"])
                    st.success(f"Sent to {NAME[nba['target']]}.")
                    st.rerun()

# ===========================================================================
# Messages — write to the family (both directions persist) (collapsible)
# ===========================================================================
with st.expander("Messages to the family", expanded=False):
    rec_labels = {"Hans Müller (Principal)": "principal", "Margrit Müller (Spouse)": "spouse",
                  "Lukas Müller (Son)": "heir"}
    sel = st.selectbox("Write to", list(rec_labels), key="rm_msg_to")
    rkey = rec_labels[sel]
    thread = [m for m in fam["messages"]
              if (m["from"] == rkey and m["to"] == "rm") or (m["from"] == "rm" and m["to"] == rkey)]
    for m in thread:
        if m["to"] == "rm" and not m["read"]:
            state.mark_read(m["id"])
        ui.chat_bubble(f"{NAME.get(m['from'], m['from'])} — {m['ts'][:16].replace('T', ' ')}", m["text"], "human")
    if not thread:
        st.caption("No messages yet with this family member.")
    with st.form(key=f"rm_send_{rkey}", clear_on_submit=True):
        ic, sc2 = st.columns([0.82, 0.18])
        txt = ic.text_input("Message", key=f"rm_send_inp_{rkey}", label_visibility="collapsed",
                            placeholder=f"Write a secure message to {NAME[rkey]}…")
        if sc2.form_submit_button("Send", type="primary", width="stretch") and txt.strip():
            state.add_message("rm", rkey, txt.strip())
            st.rerun()

# ===========================================================================
# Calendar & meetings (collapsible)
# ===========================================================================
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
