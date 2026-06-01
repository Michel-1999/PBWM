"""Shared state backbone (paper §3).

A single dict in ``st.session_state["family"]`` is read AND written by all three
pages — that shared, reactive state is the whole point of the prototype. Every
mutation goes through a small helper here (never scattered dict edits), and each
helper recomputes the Inheritance Engagement Score so the coupling stays
consistent across pages.

Optional persistence to ``family_state.json`` lets a live demo be reset cleanly.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime

import streamlit as st

from app import fixtures
from app.score import compute_score, generate_nbas

# family_state.json lives next to app.py (project root).
_STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "family_state.json")


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init_state() -> None:
    """Seed shared state once per session (idempotent)."""
    if "family" not in st.session_state:
        st.session_state["family"] = fixtures.seed_family()
        recompute("Initial assessment")
    # Per-session UI flags (chat objects, dismissed nudges) live alongside.
    st.session_state.setdefault("ui_flags", {})


def reset_state() -> None:
    """Reset the whole demo to the seeded Mueller family."""
    st.session_state["family"] = fixtures.seed_family()
    st.session_state["ui_flags"] = {}
    # Drop any cached chat sessions so personas re-ground on fresh data.
    for k in list(st.session_state.keys()):
        if k.endswith("_chat") or k.endswith("_chat_history"):
            del st.session_state[k]
    recompute("Demo reset")


def get_family() -> dict:
    init_state()
    return st.session_state["family"]


def get_score() -> dict:
    fam = get_family()
    if "current_score" not in fam:
        recompute("Recompute")
    return fam["current_score"]


# ---------------------------------------------------------------------------
# Persistence (optional)
# ---------------------------------------------------------------------------
def save() -> bool:
    try:
        with open(_STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump(st.session_state["family"], fh, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load() -> bool:
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r", encoding="utf-8") as fh:
                st.session_state["family"] = json.load(fh)
            recompute("Loaded saved state")
            return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------
def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _nid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _log(text: str) -> None:
    get_family()["activity_log"].insert(0, {"ts": _now(), "text": text})


def recompute(reason: str = "") -> dict:
    """Recompute score + NBAs, cache them, and append to the trend history."""
    fam = st.session_state["family"]
    sc = compute_score(fam)
    fam["current_score"] = sc
    fam["nbas"] = generate_nbas(fam)
    hist = fam["score_history"]
    prev = hist[-1]["score"] if hist else None
    delta = (sc["score"] - prev) if prev is not None else 0
    hist.append({
        "ts": _now(),
        "score": sc["score"],
        "band": sc["band"],
        "reason": reason,
        "delta": delta,
    })
    return sc


# ---------------------------------------------------------------------------
# Human <-> human messaging (NOT the AI chat)
# ---------------------------------------------------------------------------
def add_message(frm: str, to: str, text: str) -> dict:
    fam = get_family()
    msg = {"id": _nid("m"), "from": frm, "to": to, "text": text.strip(),
           "ts": _now(), "read": False}
    fam["messages"].append(msg)
    _log(f"Message: {frm} -> {to}")
    return msg


def mark_read(message_id: str) -> None:
    for m in get_family()["messages"]:
        if m["id"] == message_id:
            m["read"] = True


def mark_all_read(to: str) -> None:
    for m in get_family()["messages"]:
        if m["to"] == to:
            m["read"] = True


def unread_count(to: str) -> int:
    return sum(1 for m in get_family()["messages"] if m["to"] == to and not m["read"])


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------
def request_meeting(with_: str, topic: str, proposed_ts: str = "",
                    note: str = "", by: str = "rm") -> dict:
    fam = get_family()
    meeting = {
        "id": _nid("mtg"), "with": with_, "topic": topic,
        "status": "requested", "proposed_ts": proposed_ts or "to be agreed",
        "note": note, "requested_by": by, "created_ts": _now(),
    }
    fam["meetings"].append(meeting)
    _log(f"Meeting requested with {with_}: {topic}")
    recompute(f"Meeting requested with {with_}")
    return meeting


def confirm_meeting(meeting_id: str) -> None:
    fam = get_family()
    eng = fam["engagement"]
    for m in fam["meetings"]:
        if m["id"] == meeting_id:
            m["status"] = "confirmed"
            topic = m.get("topic", "").lower()
            if m["with"] == "heir":
                eng["heir_has_rm_relationship"] = True
                eng["last_rm_contact_days"] = 0
                if "savings" in topic:
                    eng["heir_has_savings_plan"] = True
            if m["with"] == "principal":
                eng["last_rm_contact_days"] = 0
                if "governance" in topic or "succession" in topic:
                    eng["principal_governance_intro_done"] = True
            _log(f"Meeting confirmed with {m['with']}: {m.get('topic')}")
            recompute(f"Meeting confirmed with {m['with']}")
            return


def decline_meeting(meeting_id: str) -> None:
    fam = get_family()
    for m in fam["meetings"]:
        if m["id"] == meeting_id:
            m["status"] = "declined"
            _log(f"Meeting declined with {m['with']}")
            recompute(f"Meeting declined with {m['with']}")
            return


def meetings_with(target: str) -> list[dict]:
    return [m for m in get_family()["meetings"] if m["with"] == target]


# ---------------------------------------------------------------------------
# Heir engagement levers (the hero-flow triggers)
# ---------------------------------------------------------------------------
def add_goal(name: str, target_chf: float, horizon_years: int = 5) -> dict:
    fam = get_family()
    goal = {"id": _nid("goal"), "name": name.strip(),
            "target_chf": float(target_chf), "saved_chf": 0.0,
            "horizon_years": int(horizon_years), "created_ts": _now()}
    fam["engagement"]["heir_goals"].append(goal)
    _log(f"Heir created goal: {name}")
    recompute("Heir created a savings goal")
    return goal


def record_deposit(amount: float) -> None:
    fam = get_family()
    eng = fam["engagement"]
    eng["heir_deposits_90d"] += 1
    # Credit the heir's cash and (if present) the first active goal.
    heir = fam["portfolios"]["heir"]
    for h in heir["holdings"]:
        if h["asset_class"] == "Cash":
            h["value_chf"] += float(amount)
            break
    if eng["heir_goals"]:
        eng["heir_goals"][0]["saved_chf"] += float(amount)
    fixtures.recompute_portfolio_derived(heir)
    _log(f"Heir deposited CHF {amount:,.0f}")
    recompute("Heir made a deposit")


def simulate_login() -> None:
    fam = get_family()
    fam["engagement"]["heir_logins_30d"] += 1
    _log("Heir logged in")
    recompute("Heir logged in")


def set_governance_intro_done(done: bool = True) -> None:
    get_family()["engagement"]["principal_governance_intro_done"] = bool(done)
    recompute("Governance intro updated")
