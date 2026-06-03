"""View — Prototype Instructions (landing / hub)."""

from __future__ import annotations

import streamlit as st

from app import ui

ui.header_bar("Prototype Instructions", "",
              right_html='<span class="tb-wordmark">THE BANK</span>', logo="bank")

st.markdown(
    "This interactive prototype brings the paper's three AI use cases to life for **The Bank**, a "
    "family-owned Swiss private bank. Everything runs on one platform, **Meridian** (the same platform "
    "for the relationship manager and for clients), and its built-in AI layer appears throughout as "
    "**Meridian AI (LLM)**, though it does a different job in each use case. The prototype follows one "
    "family, the **Müllers**, across two workspaces: **Advisor Wealth Intelligence** (the relationship "
    "manager's view) and **My Wealth Intelligence** (each client's view). Both workspaces share one live "
    "state, so an action in one (a deposit, a confirmed meeting, a market move) updates the other in "
    "real time."
)
st.markdown(
    '<div style="background:var(--tb-tint);border-left:4px solid var(--tb-green);border-radius:8px;'
    'padding:10px 14px;font-size:.9rem;color:#1A1A1A"><b>Two things to keep apart while you explore.</b> '
    'A workspace is a place you open; there are two: Advisor Wealth Intelligence and My Wealth '
    'Intelligence. A use case is an AI capability; there are three, and they appear inside the '
    'workspaces. So: two workspaces, three use cases.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    "The three use cases are implemented in the same web app and complement each other. They could also "
    "be implemented wherever a platform such as Meridian and an AI layer such as Meridian AI exist. Use "
    "case 1 is the conversational AI layer, the assistant through which the advisor and the client work. "
    "Use cases 2 and 3 are the two rule-based engines that feed it data: use case 2 produces the "
    "**engagement score** and the **inheritance score**, while use case 3 produces the **strategy "
    "flags**. These data points can also answer the advisor's questions in the chat. The Meridian AI "
    "layer then analyses and interprets all of these rule-based scores and flags and turns them into "
    "next actions, surfaced as recommendations to the advisor."
)

# --- The three use cases ----------------------------------------------------
ui.pediment("The three AI use cases")


def _use_case(chip: str, title: str, body: str, where: str) -> str:
    return (
        '<div class="tb-card accent" style="height:100%">'
        f'<span class="tb-chip solid">{chip}</span>'
        f'<div class="tb-metric-value" style="font-size:1.16rem;margin-top:8px">{title}</div>'
        f'<p style="font-size:.88rem;color:#1A1A1A;margin-top:6px;line-height:1.5">{body}</p>'
        '<div style="font-size:.78rem;color:var(--tb-muted);border-top:1px solid var(--tb-hairline);'
        f'padding-top:8px;margin-top:8px"><b>Where:</b> {where}</div></div>'
    )


c1, c2, c3 = st.columns(3, gap="large")
c1.markdown(
    _use_case(
        "Use case 1", "Conversational AI Layer",
        "The Meridian AI assistant that both sides talk to. In Advisor Wealth Intelligence it is a full "
        "co-pilot with access to the whole family's data: a family-wide chat, ready-to-review message "
        "drafts, and the next-best-actions that consolidate the signals from use cases 2 and 3. In My "
        "Wealth Intelligence it is a slimmed-down version scoped to a single client, answering only "
        "questions about that client's own portfolio, returns and strategy in plain language. Use case 1 "
        "does not produce the engagement score or the strategy flags itself; it surfaces them and turns "
        "them into action. It empowers the advisor; it does not replace them.",
        "full co-pilot in Advisor Wealth Intelligence, a single-client assistant in My Wealth Intelligence.",
    ),
    unsafe_allow_html=True,
)
c2.markdown(
    _use_case(
        "Use case 2", "Engagement Engine",
        "A transparent, rule-based engine (not Meridian AI) that produces two linked scores. The "
        "engagement score is per family member, from platform behaviour (logins, goals, deposits and "
        "meetings). The inheritance score is per family: it builds on the engagement scores and adds "
        "age and wealth at stake to flag at-risk AUM. Meridian AI then interprets both into discreet, "
        "personalised client nudges and concrete next-best-actions for the advisor.",
        "both scores shown to the advisor in Advisor Wealth Intelligence; felt as personalised nudges in "
        "My Wealth Intelligence.",
    ),
    unsafe_allow_html=True,
)
c3.markdown(
    _use_case(
        "Use case 3", "Client Strategy Monitor",
        "An always-on check of each client's agreed strategy: allocation bands, concentration, cash, "
        "digital-asset risk, cross-border rules and life-goal funding. A transparent rule engine "
        "produces the strategy flags (including from the market simulation); Meridian AI then interprets "
        "each flag, explaining it and proposing a conversation, never a trade. In Advisor Wealth "
        "Intelligence the advisor sees a strategy-fulfilment score, traffic-light flags and AI "
        "recommendations; in My Wealth Intelligence the client sees a plain-language My strategy view.",
        "full view in Advisor Wealth Intelligence, a My strategy view in My Wealth Intelligence.",
    ),
    unsafe_allow_html=True,
)

# --- How it all connects ----------------------------------------------------
ui.pediment("How it all connects")
st.markdown(
    '<div class="tb-card"><ol style="margin:0 0 0 1.1rem;font-size:.93rem;line-height:1.75">'
    "<li>Open the Advisor Wealth Intelligence (Reto Wyss). Meet the family, chat with Meridian AI "
    "(use case 1), open AI recommendations for proposed next actions, and open the Client Strategy "
    "Monitor (use case 3) to see how well each client follows their strategy.</li>"
    "<li>Open Lukas (Son) in My Wealth Intelligence and, in the goal tracker, set a savings goal or "
    "make a deposit. His behaviour feeds the Engagement Engine (use case 2): his engagement score "
    "rises and the family inheritance score falls, live.</li>"
    "<li>Back in the Advisor Wealth Intelligence, open AI recommendations, send a meeting request, "
    "then open Lukas again and confirm it. Both workspaces update together.</li>"
    "<li>In the Client Strategy Monitor, run the simulation (for example a market drop). A strategy "
    "flag appears with an AI recommendation; send a rebalancing meeting, the client confirms, and the "
    "flag clears. On Lukas's page, the same strategy is shown as a plain-language My strategy view.</li>"
    "</ol></div>",
    unsafe_allow_html=True,
)

# --- Enter the prototype (distinct call-to-action) --------------------------
st.markdown(
    '<div style="background:var(--tb-green);border-radius:12px;padding:18px 24px;'
    'border-bottom:5px solid var(--tb-gold);margin:24px 0 14px;box-shadow:0 4px 14px rgba(22,58,42,.18)">'
    '<div style="color:#fff;font-family:var(--tb-serif);font-size:1.5rem;font-weight:400">'
    '▶  Enter the prototype</div>'
    '<div style="color:#EAF2EC;font-size:.92rem;margin-top:3px">Pick a workspace to begin. The bold '
    'OVERVIEW button at the top-left of every page brings you back here.</div></div>',
    unsafe_allow_html=True,
)

def _entry_card(avatar_file: str, initials: str, role: str, name: str, colour: str) -> str:
    av = ui.avatar_html(avatar_file, initials, 66, ring=colour)
    return (
        f'<div class="tb-card" style="border-top:3px solid {colour};text-align:center">'
        f'<div style="margin-bottom:8px">{av}</div>'
        f'<div class="tb-metric-label" style="color:{colour}">{role}</div>'
        f'<b style="color:{colour}">{name}</b></div>'
    )


st.markdown('<div style="font-weight:600;color:var(--tb-green);font-size:.95rem;margin-bottom:6px">'
            'Advisor Wealth Intelligence (advisor workspace)</div>', unsafe_allow_html=True)
ac = st.columns([0.34, 0.32, 0.34])
with ac[1]:
    st.markdown(_entry_card("RM.png", "RW", "Relationship Manager", "Reto Wyss", "#1F4F39"),
                unsafe_allow_html=True)
    if st.button("Open  →", key="go_rm", type="primary", width="stretch"):
        st.switch_page("views/rm.py")

st.markdown('<div style="font-weight:600;color:var(--tb-green);font-size:.95rem;margin:16px 0 6px">'
            'My Wealth Intelligence (client workspaces)</div>', unsafe_allow_html=True)
nav_items = [
    ("Hans Müller", "Principal", "views/principal.py", "vater.png", "#34577C"),
    ("Margrit Müller", "Spouse", "views/spouse.py", "Spouse.png", "#7C3340"),
    ("Lukas Müller", "Son", "views/heir.py", "sohn.png", "#176B63"),
]
cols = st.columns(3, gap="medium")
for col, (name, role, path, avatar_file, colour) in zip(cols, nav_items):
    with col:
        initials = "".join(w[0] for w in name.split()[:2]).upper()
        st.markdown(_entry_card(avatar_file, initials, role, name, colour), unsafe_allow_html=True)
        if st.button("Open  →", key=f"go_{role}", type="primary", width="stretch"):
            st.switch_page(path)

ui.disclaimer_note()
ui.footer()
