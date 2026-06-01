"""Grounded, guardrailed Gemini layer (paper §5).

Two personas + generative helpers, none fine-tuned: all are *grounded* by
injecting the relevant person's simulated portfolio/CRM into the system
instruction, and *guardrailed* to stay strictly inside "The Bank universe".

Robustness (paper §5c):
  * No API key  -> MOCK_MODE: believable canned answers computed from the real
    fixture data, so the whole app still demos offline.
  * Live call fails / 429 / quota -> retry once on the lighter fallback model,
    then fall back to mock with a friendly notice. A live demo never dies.

Model is set in ONE place (MODEL_NAME) so it can be swapped in a line.
"""

from __future__ import annotations

import re

import streamlit as st

from app import fixtures

# --- One-line model config (paper §2) --------------------------------------
# flash-lite is the default because it has the most generous FREE-tier quota,
# which keeps a live demo from being throttled; flash is the higher-quality
# fallback. Swap these two lines to prefer flash.
MODEL_NAME = "gemini-2.5-flash-lite"
FALLBACK_MODEL = "gemini-2.5-flash"

_PLACEHOLDER_KEYS = {"", "PASTE_YOUR_FREE_AISTUDIO_KEY_HERE", "YOUR_KEY_HERE", "CHANGEME"}


# ---------------------------------------------------------------------------
# Key / client management
# ---------------------------------------------------------------------------
def _api_key() -> str | None:
    """Resolve the Gemini key: a user-supplied session key first, then secrets.

    The session key lets anyone using a public/deployed build enable live AI with
    their own free key, without the maintainer's key ever being committed.
    """
    key = ""
    try:
        key = str(st.session_state.get("user_gemini_key", "") or "").strip()
    except Exception:
        key = ""
    if not key:
        try:
            key = str(st.secrets.get("GEMINI_API_KEY", "") or "").strip()
        except Exception:
            key = ""
    return None if key in _PLACEHOLDER_KEYS else key


def is_live() -> bool:
    return _api_key() is not None


def mode_label() -> str:
    return "Live (Gemini)" if is_live() else "Offline mock mode"


@st.cache_resource(show_spinner=False)
def _client(key: str):
    from google import genai  # imported lazily so the app loads without the SDK
    return genai.Client(api_key=key)


def _is_rate_limit(exc: Exception) -> bool:
    s = str(exc).lower()
    return any(t in s for t in ("429", "quota", "rate limit", "resource_exhausted", "exhausted"))


# ---------------------------------------------------------------------------
# Grounding: serialise a person's simulated data into a context block
# ---------------------------------------------------------------------------
def _fmt_chf(x: float) -> str:
    return f"CHF {float(x):,.0f}"


def context_block(portfolio: dict, member: dict) -> str:
    p = portfolio
    nr = p["net_return"]
    alloc = "; ".join(f"{a['asset_class']} {a['weight_pct']}% ({_fmt_chf(a['value_chf'])})"
                      for a in p["asset_allocation"])
    holdings = "; ".join(f"{h['name']} {h['weight_pct']}% ({_fmt_chf(h['value_chf'])})"
                         for h in p["holdings"])
    perf = "; ".join(f"{r['year']} {r['portfolio_pct']:+.1f}/{r['benchmark_pct']:+.1f}"
                     for r in p["performance_annual"])
    trades = "; ".join(
        f"{t['date']} {t['side']} {t['instrument']} {_fmt_chf(t['amount_chf'])}"
        + (f" ({t['note']})" if t.get("note") else "")
        for t in p["trades"])
    ds = p["digital_asset_sleeve"]
    fees = p["fees"]
    crm = p["crm"]
    return f"""CLIENT: {p['owner']} ({member['role']}), age {member['age']}, domicile {crm['domicile']}, KYC {member['kyc_status']}.
MANDATE: {p['mandate_type']}. Risk profile: {p['risk_profile']}. Relationship since {p['relationship_since']}. Benchmark: {p['benchmark']}.
TOTAL PORTFOLIO VALUE (as of {p['as_of']}): {_fmt_chf(p['total_value_chf'])}.
ASSET ALLOCATION: {alloc}.
HOLDINGS: {holdings}.
DIGITAL-ASSET SLEEVE: {ds['weight_pct']}% ({_fmt_chf(ds['value_chf'])}) — {', '.join(ds['instruments'])}; custody: {ds['custodian']}.
ANNUAL PERFORMANCE (portfolio%/benchmark%): {perf}.
NET RETURN since {nr['inception_date']}: net contributions {_fmt_chf(nr['net_contributions_chf'])}, current value {_fmt_chf(nr['current_value_chf'])}, cumulative net gain {_fmt_chf(nr['cumulative_net_gain_chf'])}, simple net return {nr['simple_net_return_pct']:+.1f}%, annualised (money-weighted, net of fees) {nr['annualised_return_irr_pct']:+.1f}% p.a. Basis: {nr['basis']}.
ALL TRADES: {trades}.
FEES: advisory {fees['advisory_fee_pct_pa']}% p.a., custody {fees['custody_fee_pct_pa']}% p.a., crypto custody {fees['crypto_custody_fee_pct_pa']}% p.a.; {fees['transaction_fees']}; retrocessions: {fees['retrocessions']}; last 12m fees {_fmt_chf(fees['last_12m_fees_chf'])}.
CRM: occupation {crm['occupation']}; interests {', '.join(crm['interests'])}; favourite drink {crm.get('favourite_drink', 'n/a')}; personality {crm.get('personality', 'n/a')}; household {crm['household']}; life events {crm['life_events']}; last review {crm['last_review']}; open tasks {crm['open_tasks']}.
FAMILY STRATEGY (context): {fixtures.FAMILY_STRATEGY['summary']} Investment approach: {fixtures.FAMILY_STRATEGY['investment_approach']}"""


# ---------------------------------------------------------------------------
# Personas (paper §5a)
# ---------------------------------------------------------------------------
PERSONA = {
    "principal": {
        "salutation": "Mr. Mueller",
        "tone": "Concise, formal and precise. Address the reader respectfully. Short paragraphs.",
    },
    "heir": {
        "salutation": "Lukas",
        "tone": ("Explanatory and educational, friendly but professional. Briefly explain "
                 "any jargon (e.g. what an ETF or a money-weighted return is). Encouraging."),
    },
    "spouse": {
        "salutation": "Mrs. Mueller",
        "tone": "Concise, warm and formal. Address the reader respectfully. Short paragraphs.",
    },
}


def _chat_system_instruction(person_key: str, context: str) -> str:
    persona = PERSONA[person_key]
    return f"""You are Clio, The Bank's AI assistant on the Meridian platform, speaking with {persona['salutation']}.

STRICT SCOPE — answer ONLY using the CONTEXT below, which is {persona['salutation']}'s own portfolio with The Bank. You operate entirely inside "The Bank universe".

You MUST politely refuse and redirect for ANYTHING outside this person's own data, including: other clients' data; general market/stock tips or "what should I buy/sell"; macro or economic forecasts; tax or legal advice; and any general-knowledge question. Standard refusal: "I can only answer questions about your own portfolio with The Bank." Then offer to connect them with their relationship manager, Mr. Reto Wyss. Stay in persona while refusing.

NEVER invent or estimate figures that are not in the CONTEXT. If a detail is missing, say you do not have it on file and offer to ask Mr. Reto Wyss.

STYLE: {persona['tone']} Use plain language. When you state returns or figures, add a short one-line reminder that this is information about existing holdings, not investment advice.

CONTEXT (the only knowledge you have):
{context}
"""


# ---------------------------------------------------------------------------
# Deterministic guardrail pre-filter (works in both live and mock paths)
# ---------------------------------------------------------------------------
_OFF_TOPIC_PATTERNS = [
    r"\bshould i (buy|sell|invest|hold)\b",
    r"\bwhat should i (buy|sell|invest|do)\b",
    r"\b(recommend|recommendation|hot stock|stock tip|which stock|best stock|price target)\b",
    r"\b(market (outlook|forecast|crash|timing)|will .*(go up|go down|rise|fall|crash|moon))\b",
    r"\b(s&p ?500|nasdaq|dow jones|interest rate|rate cut|inflation (forecast|outlook)|recession)\b",
    r"\b(tax (advice|return|optimi|implication|loophole)|avoid (tax|taxes)|inheritance tax|legal advice)\b",
    r"\b(capital of|weather|who is|what is the meaning|recipe|translate|president|football|world cup|movie|song|joke)\b",
    r"\bbitcoin price (today|now|prediction)\b",
]
_OFF_TOPIC_RE = re.compile("|".join(_OFF_TOPIC_PATTERNS), re.IGNORECASE)


def _decline_text(person_key: str) -> str:
    if person_key == "principal":
        return ("I'm sorry, Mr. Mueller — I can only answer questions about your own "
                "portfolio with The Bank. For market views, tax or legal matters, your "
                "relationship manager Mr. Reto Wyss would be glad to assist.")
    return ("I can only help with your own portfolio here at The Bank — not general market "
            "tips, forecasts or tax advice. For those, Mr. Reto Wyss (your family's relationship "
            "manager) is the right contact. I'm happy to explain anything about your own "
            "holdings, returns or goals, though!")


def _looks_off_topic(msg: str) -> bool:
    return bool(_OFF_TOPIC_RE.search(msg or ""))


# Narrower guardrail for the Advisor Co-Pilot: the RM legitimately asks "what
# should I do next / what do you recommend for the family", so only block clearly
# external requests (market forecasts, general knowledge).
_ADVISOR_OFF_TOPIC_PATTERNS = [
    r"\b(market (outlook|forecast|crash|timing)|will .*(go up|go down|rise|fall|crash|moon))\b",
    r"\b(s&p ?500|nasdaq|dow jones|interest rate|rate cut|inflation (forecast|outlook)|recession)\b",
    r"\b(capital of|the weather|who is|what is the meaning|recipe|translate|president|world cup|movie|a joke)\b",
    r"\bbitcoin price (today|now|prediction)\b",
]
_ADVISOR_OFF_TOPIC_RE = re.compile("|".join(_ADVISOR_OFF_TOPIC_PATTERNS), re.IGNORECASE)


def _looks_off_topic_advisor(msg: str) -> bool:
    return bool(_ADVISOR_OFF_TOPIC_RE.search(msg or ""))


# ---------------------------------------------------------------------------
# Public: portfolio chat (5a)
# ---------------------------------------------------------------------------
def portfolio_chat(person_key: str, portfolio: dict, member: dict,
                   history: list[tuple[str, str]], user_msg: str) -> dict:
    """Answer a portfolio question for one person. Returns {text, mode, note}."""
    # Deterministic guardrail first — guarantees refusal & saves quota.
    if _looks_off_topic(user_msg):
        return {"text": _decline_text(person_key), "mode": "guardrail", "note": "Off-topic — declined by guardrail."}

    if not is_live():
        return {"text": _mock_chat(person_key, portfolio, user_msg), "mode": "mock", "note": ""}

    sys_inst = _chat_system_instruction(person_key, context_block(portfolio, member))
    try:
        text, mode, note = _run_generate(sys_inst, history, user_msg)
        return {"text": text, "mode": mode, "note": note}
    except Exception as exc:  # noqa: BLE001
        return {"text": _mock_chat(person_key, portfolio, user_msg), "mode": "mock",
                "note": _offline_note(exc)}


def _generate(system_instruction: str, history: list[tuple[str, str]],
              user_msg: str, model: str) -> str:
    from google.genai import types
    client = _client(_api_key())
    contents = []
    for role, text in history[-8:]:  # keep recent turns; roles: 'user' | 'model'
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_msg)]))
    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            max_output_tokens=700,
        ),
    )
    return (resp.text or "").strip() or "(No response — please try rephrasing.)"


def _run_generate(system_instruction: str, history: list[tuple[str, str]], user_msg: str):
    """Try the primary model, then the fallback. Returns (text, mode, note)."""
    last: Exception | None = None
    for i, model in enumerate((MODEL_NAME, FALLBACK_MODEL)):
        try:
            text = _generate(system_instruction, history, user_msg, model)
            note = "" if i == 0 else "Primary model was busy — used the backup model."
            return text, ("live" if i == 0 else "fallback"), note
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise last if last else RuntimeError("generation failed")


def _offline_note(exc: Exception) -> str:
    if _is_rate_limit(exc):
        return ("Gemini is briefly rate-limited on the free tier — showing a grounded offline "
                "answer. Try again in a moment.")
    return "Live AI is temporarily unavailable — showing a grounded offline answer."


# ---------------------------------------------------------------------------
# Public: Advisor Co-Pilot helpers (5b) — drafts for the human RM
# ---------------------------------------------------------------------------
def _copilot(system_instruction: str, user_prompt: str, mock_fn) -> dict:
    if not is_live():
        return {"text": mock_fn(), "mode": "mock", "note": ""}
    try:
        text, mode, note = _run_generate(system_instruction, [], user_prompt)
        return {"text": text, "mode": mode, "note": note}
    except Exception as exc:  # noqa: BLE001
        return {"text": mock_fn(), "mode": "mock", "note": _offline_note(exc)}


_COPILOT_SYS = (
    "You are Clio, the Advisor Co-Pilot for Mr. Reto Wyss, a relationship manager at The Bank "
    "(a Swiss private bank). You support — never replace — the human advisor: every "
    "output is a DRAFT for his review, never auto-sent. Be precise, concise and "
    "practical. The clients are German-domiciled and served cross-border from "
    "Switzerland, so always respect Swiss FIDLEG/FINIG conduct rules and German/EU "
    "cross-border restrictions. Ground everything ONLY in the supplied context; do "
    "not invent figures."
)


# ---------------------------------------------------------------------------
# Advisor Co-Pilot — ONE assistant over the WHOLE family database (RM only)
# ---------------------------------------------------------------------------
_ADVISOR_SYS = (
    "You are Clio, the Advisor Co-Pilot for Mr. Reto Wyss, a relationship manager at The Bank (a Swiss "
    "private bank). You have access to The Bank's COMPLETE internal database for the MUELLER "
    "FAMILY ONLY — every member (Hans the principal, Margrit his spouse, Lukas the heir, and "
    "Sophie, a not-yet-client prospect), all portfolios, CRM, life events, the Inheritance "
    "Engagement Score and the open next-best-actions. Answer using ONLY this family's data. You "
    "may discuss any member, cross-member totals, wealth-transfer strategy and concrete next "
    "actions. The family is German-domiciled and served cross-border from Switzerland — respect "
    "Swiss FIDLEG/FINIG and German cross-border rules. Politely decline anything outside this "
    "family's data: other client families, live market tips or forecasts, and general-knowledge "
    "questions. Be concise and practical; ground every figure in the data and never invent numbers."
)


def _member_summary(family: dict, key: str) -> str:
    m = family["members"].get(key)
    p = family["portfolios"].get(key)
    if not m:
        return ""
    if not p:
        return (f"- {m['name']} ({m['role']}, age {m['age']}, KYC {m.get('kyc_status', 'n/a')}): "
                f"not yet a client — prospect, no portfolio on file.")
    nr = p["net_return"]
    top = sorted(p["asset_allocation"], key=lambda a: a["value_chf"], reverse=True)[:3]
    alloc = ", ".join(f"{a['asset_class']} {a['weight_pct']}%" for a in top)
    crm = p["crm"]
    return (f"- {m['name']} ({m['role']}, age {m['age']}, domicile {crm['domicile']}, "
            f"KYC {m['kyc_status']}): value {_fmt_chf(p['total_value_chf'])}, net return "
            f"{nr['annualised_return_irr_pct']:+.1f}% p.a., top allocation {alloc}, digital assets "
            f"{p['digital_asset_sleeve']['weight_pct']}%, risk {p['risk_profile']}, last review "
            f"{crm['last_review']}. Interests: {', '.join(crm.get('interests', []))}; "
            f"favourite drink: {crm.get('favourite_drink', 'n/a')}; "
            f"personality: {crm.get('personality', 'n/a')}.")


def family_context_block(family: dict, score: dict) -> str:
    order = ["principal", "spouse", "heir"]
    total = sum(p["total_value_chf"] for p in family["portfolios"].values())
    members = "\n".join(s for s in (_member_summary(family, k) for k in order) if s)
    pcrm = family["portfolios"]["principal"]["crm"]
    household = pcrm.get("household", {})
    events = "; ".join(f"{e['date']}: {e['event']}"
                       for k in order if family["portfolios"].get(k)
                       for e in family["portfolios"][k]["crm"].get("life_events", []))
    nbas = "; ".join(f"{n['title']} (for {n['target']})" for n in family.get("nbas", [])) or "none open"
    msgs = "; ".join(f"{m['from']}->{m['to']}: {m['text'][:80]}" for m in family.get("messages", [])[-4:]) or "none"
    strategy_txt = " ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in fixtures.FAMILY_STRATEGY.items())
    names = {k: v.get("name", k) for k, v in family["members"].items()}
    history = "; ".join(
        f"{mm['date']} '{mm['topic']}' ({mm['mode']}, RM {mm['rm']}, present: "
        f"{', '.join(names.get(a, a) for a in mm['attendees'])}) — {mm['summary']}"
        for mm in family.get("meeting_history", [])) or "none on file"
    return f"""MUELLER FAMILY — total relationship AUM with The Bank: {_fmt_chf(total)}.
MEMBERS:
{members}
HOUSEHOLD: {household}. (Sophie, 29, is a prospect — not yet a client.)
FAMILY STRATEGY (pursued so far): {strategy_txt}
INHERITANCE ENGAGEMENT SCORE: {score['score']}/100 ({score['band_label']}). Components: {score['components']}.
Drivers: {'; '.join(score['drivers'])}.
OPEN NEXT-BEST-ACTIONS: {nbas}.
PAST MEETINGS (what was discussed; most recent first): {history}.
LIFE EVENTS: {events}.
RECENT SECURE MESSAGES: {msgs}."""


def _advisor_decline() -> str:
    return ("I'm Clio, the Müller family's Advisor Co-Pilot — I can help with anything in this family's "
            "data (any member, totals, the engagement score, next-best-actions), but not market "
            "calls, forecasts, tax/legal advice or general questions.")


def advisor_chat(family: dict, history: list[tuple[str, str]], user_msg: str) -> dict:
    """Family-wide co-pilot for the RM. Returns {text, mode, note}."""
    if _looks_off_topic_advisor(user_msg):
        return {"text": _advisor_decline(), "mode": "guardrail", "note": "Off-topic — declined by guardrail."}
    score = family.get("current_score")
    if not score:
        from app.score import compute_score
        score = compute_score(family)
    if not is_live():
        return {"text": _mock_advisor(family, score, user_msg), "mode": "mock", "note": ""}
    sys_inst = _ADVISOR_SYS + "\n\nFAMILY DATABASE (the only knowledge you have):\n" + family_context_block(family, score)
    try:
        text, mode, note = _run_generate(sys_inst, history, user_msg)
        return {"text": text, "mode": mode, "note": note}
    except Exception as exc:  # noqa: BLE001
        return {"text": _mock_advisor(family, score, user_msg), "mode": "mock", "note": _offline_note(exc)}


def _mock_advisor(family: dict, score: dict, msg: str) -> str:
    m = (msg or "").lower()
    total = sum(p["total_value_chf"] for p in family["portfolios"].values())
    if any(k in m for k in ("score", "risk", "engagement", "priority")):
        return (f"The Müller family's Inheritance Engagement Score is {score['score']}/100 "
                f"({score['band_label']}). Key drivers: {'; '.join(score['drivers'][:3])}.")
    if any(k in m for k in ("next", "action", "do", "recommend", "propose")):
        nbas = family.get("nbas", [])
        if not nbas:
            return "No open next-best-actions — the family is well engaged."
        return "Open next-best-actions:\n" + "\n".join(f"• {n['title']} (for {n['target']})" for n in nbas)
    if any(k in m for k in ("wife", "spouse", "margrit", "mother", "mutter")):
        sp = family["portfolios"].get("spouse")
        if sp:
            return (f"Margrit Müller (spouse, 62): portfolio {_fmt_chf(sp['total_value_chf'])}, "
                    f"risk {sp['risk_profile']}, net return {sp['net_return']['annualised_return_irr_pct']:+.1f}% p.a. "
                    f"Conservative profile; no digital-asset sleeve.")
    if any(k in m for k in ("sophie", "daughter", "tochter")):
        return "Sophie Müller (29) is the daughter — a prospect, not yet a client. A natural next-gen target alongside Lukas."
    if any(k in m for k in ("total", "family", "wealth", "aum", "overview")):
        return (f"Total Müller relationship AUM is {_fmt_chf(total)} across "
                f"{len([p for p in family['portfolios']])} members (Hans, Margrit, Lukas). "
                f"Engagement score {score['score']}/100 ({score['band_label']}).")
    return (f"Müller family overview: total AUM {_fmt_chf(total)}; engagement score {score['score']}/100 "
            f"({score['band_label']}). Ask me about any member, the score, or next-best-actions.")


def briefing(portfolio: dict, member: dict, score_obj: dict) -> dict:
    ctx = context_block(portfolio, member)
    score_txt = (f"Inheritance Engagement Score: {score_obj['score']}/100 "
                 f"({score_obj['band_label']}). Drivers: {'; '.join(score_obj['drivers'])}.")
    prompt = (
        f"{ctx}\n\n{score_txt}\n\n"
        "Write a concise pre-meeting briefing for Mr. Reto Wyss with these sections:\n"
        "1) Snapshot (value, allocation, risk profile)\n"
        "2) Performance & attribution (use the annual series and net return)\n"
        "3) Recent touchpoints & CRM life events\n"
        "4) CROSS-BORDER COMPLIANCE ALERT (FIDLEG / German cross-border — be specific)\n"
        "5) Pending tasks\n"
        "6) Three talking points for the conversation\n"
        "Keep it under ~250 words, use short bullet points."
    )
    return _copilot(_COPILOT_SYS, prompt, lambda: _mock_briefing(portfolio, member, score_obj))


def draft_email(portfolio: dict, member: dict, purpose: str) -> dict:
    ctx = context_block(portfolio, member)
    prompt = (f"{ctx}\n\nDraft a short, warm but professional follow-up email from Mr. Reto Wyss "
              f"to {portfolio['owner']} about: {purpose}. German salutation is fine. Keep it "
              "to ~120 words. End with a clear next step. Remember it is a draft for review.")
    return _copilot(_COPILOT_SYS, prompt, lambda: _mock_email(portfolio, member, purpose))


def draft_agenda(portfolio: dict, member: dict, topic: str) -> dict:
    ctx = context_block(portfolio, member)
    prompt = (f"{ctx}\n\nDraft a focused meeting agenda (5-6 items, with a one-line note each) "
              f"for a conversation with {portfolio['owner']} on: {topic}. Include a cross-border "
              "compliance checkpoint.")
    return _copilot(_COPILOT_SYS, prompt, lambda: _mock_agenda(portfolio, member, topic))


def summarise_conversation(portfolio: dict, member: dict, messages: list[dict]) -> dict:
    convo = "\n".join(f"[{m['from']}->{m['to']}] {m['text']}" for m in messages) or "(no messages on file)"
    ctx = context_block(portfolio, member)
    prompt = (f"{ctx}\n\nRecent secure messages:\n{convo}\n\n"
              "Summarise the last conversation in 4-5 bullets and list any follow-ups for Mr. Reto Wyss.")
    return _copilot(_COPILOT_SYS, prompt, lambda: _mock_summary(portfolio, messages))


# ---------------------------------------------------------------------------
# Mock implementations (grounded in the real fixture data, so they're credible)
# ---------------------------------------------------------------------------
def _mock_chat(person_key: str, p: dict, msg: str) -> str:
    m = (msg or "").lower()
    owner = p["owner"]
    nr = p["net_return"]
    nd = "  \n_This is information about your existing holdings, not investment advice._"

    if any(k in m for k in ("net return", "return since", "since i started", "made money",
                            "performance", "how have i done", "total return", "incl", "trades")):
        return (f"Since {nr['inception_date']} you have contributed {_fmt_chf(nr['net_contributions_chf'])} "
                f"net of withdrawals. Your portfolio is worth {_fmt_chf(nr['current_value_chf'])} today, "
                f"a cumulative net gain of {_fmt_chf(nr['cumulative_net_gain_chf'])} "
                f"({nr['simple_net_return_pct']:+.1f}%). Including every trade and the timing of your "
                f"contributions, that is a money-weighted return of about {nr['annualised_return_irr_pct']:+.1f}% "
                f"per year, net of all fees." + nd)
    if any(k in m for k in ("allocation", "asset", "split", "diversif", "breakdown", "mix")):
        rows = ", ".join(f"{a['asset_class']} {a['weight_pct']}%" for a in p["asset_allocation"])
        return f"Your portfolio of {_fmt_chf(p['total_value_chf'])} is allocated as: {rows}." + nd
    if any(k in m for k in ("crypto", "digital", "bitcoin", "btc", "ethereum", "eth")):
        ds = p["digital_asset_sleeve"]
        return (f"Your digital-asset sleeve is {ds['weight_pct']}% of the portfolio "
                f"({_fmt_chf(ds['value_chf'])}), held in {', '.join(ds['instruments'])} via "
                f"{ds['custodian']}" + nd)
    if any(k in m for k in ("fee", "cost", "charge", "retrocession")):
        f = p["fees"]
        return (f"Your fees are: advisory {f['advisory_fee_pct_pa']}% p.a., custody "
                f"{f['custody_fee_pct_pa']}% p.a., and {f['crypto_custody_fee_pct_pa']}% p.a. on the "
                f"crypto sleeve. {f['retrocessions']}. Over the last 12 months that was "
                f"{_fmt_chf(f['last_12m_fees_chf'])}." + nd)
    if any(k in m for k in ("trade", "bought", "sold", "buy", "history", "transaction")):
        last = p["trades"][-3:]
        rows = "; ".join(f"{t['date']} {t['side']} {t['instrument']} {_fmt_chf(t['amount_chf'])}" for t in last)
        return (f"You have made {len(p['trades'])} trades since inception. Most recent: {rows}." + nd)
    if any(k in m for k in ("hold", "own", "position", "what do i", "stocks", "biggest")):
        top = sorted(p["holdings"], key=lambda h: h["value_chf"], reverse=True)[:5]
        rows = ", ".join(f"{h['name']} ({h['weight_pct']}%)" for h in top)
        return f"Your largest positions are: {rows}." + nd
    # Generic grounded overview
    return (f"Here is a quick overview, {PERSONA[person_key]['salutation']}: your portfolio is worth "
            f"{_fmt_chf(p['total_value_chf'])} as of {p['as_of']}, with a net gain of "
            f"{_fmt_chf(nr['cumulative_net_gain_chf'])} since {nr['inception_date']}. Ask me about your "
            f"allocation, performance, fees, trade history or the digital-asset sleeve." + nd)


def _mock_briefing(p: dict, member: dict, sc: dict) -> str:
    nr = p["net_return"]
    last = p["performance_annual"][-1]
    alloc = ", ".join(f"{a['asset_class']} {a['weight_pct']}%" for a in p["asset_allocation"][:4])
    events = "; ".join(e["event"] for e in p["crm"]["life_events"][:2])
    xborder = ("Client is German-domiciled, served cross-border from Switzerland. Confirm FIDLEG "
               "suitability documentation is current and that any advice is delivered within the "
               "Swiss cross-border ruleset for Germany (no unsolicited EU solicitation).")
    return f"""**Pre-meeting briefing — {p['owner']}**  _(draft for Mr. Reto Wyss · offline)_

**1 · Snapshot** — {_fmt_chf(p['total_value_chf'])}; {alloc}. Risk: {p['risk_profile']}.

**2 · Performance & attribution** — {last['year']} {last['portfolio_pct']:+.1f}% vs benchmark
{last['benchmark_pct']:+.1f}%. Since {nr['inception_date']}: net gain {_fmt_chf(nr['cumulative_net_gain_chf'])}
({nr['annualised_return_irr_pct']:+.1f}% p.a., money-weighted, net of fees). Digital sleeve at
{p['digital_asset_sleeve']['weight_pct']}% has contributed to recent performance.

**3 · Touchpoints & life events** — Last review {p['crm']['last_review']}. {events}.

**4 · ⚠ Cross-border compliance alert** — {xborder}

**5 · Pending tasks** — {', '.join(p['crm']['open_tasks'])}.

**6 · Talking points** — (a) Inheritance Engagement Score is {sc['score']}/100 ({sc['band_label']}); next
generation engagement is the priority. (b) Succession & family-governance introduction. (c) Review the
digital-asset sleeve and rebalancing into year-end."""


def _mock_email(p: dict, member: dict, purpose: str) -> str:
    sal = "Sehr geehrter Herr Mueller" if member["role"] == "principal" else "Gruezi Lukas"
    return (f"{sal},\n\nvielen Dank fuer Ihr Vertrauen. {purpose} — gerne moechte ich dies mit Ihnen "
            f"persoenlich vertiefen.\n\nIhr Portfolio entwickelt sich im Rahmen unserer Erwartungen "
            f"(Stand {p['as_of']}: {_fmt_chf(p['total_value_chf'])}). Ich schlage ein kurzes Gespraech "
            f"in den naechsten zwei Wochen vor und sende Ihnen gerne Terminvorschlaege.\n\n"
            f"Mit freundlichen Gruessen\nReto Wyss\nThe Bank — Private Banking, Zuerich\n\n"
            f"_(Draft — review before sending.)_")


def _mock_agenda(p: dict, member: dict, topic: str) -> str:
    return (f"**Meeting agenda — {p['owner']}**  _(draft)_\n\n"
            f"1. Welcome & objectives — focus: {topic}.\n"
            f"2. Portfolio review — {_fmt_chf(p['total_value_chf'])}, allocation vs. target.\n"
            f"3. Performance & fees — net return since inception, cost transparency.\n"
            f"4. {topic} — options and next steps.\n"
            f"5. ⚠ Cross-border checkpoint — FIDLEG suitability & German cross-border documentation.\n"
            f"6. Actions & follow-up — owner, deadline, next contact.")


def _mock_summary(p: dict, messages: list[dict]) -> str:
    if not messages:
        return "_No secure messages on file yet for this client._"
    bullets = "\n".join(f"- [{m['from']} → {m['to']}] {m['text'][:120]}" for m in messages[-5:])
    return (f"**Conversation summary — {p['owner']}**  _(draft)_\n\n{bullets}\n\n"
            f"**Follow-ups:** respond to open items above; confirm next meeting; log in CRM.")
