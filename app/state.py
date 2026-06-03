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
from app.score import compute_member_engagement, compute_score, generate_nbas
from app.strategy import (generate_strategy_alerts, is_bond_holding, is_digital_holding,
                          is_equity_holding, is_fx_holding, portfolio_health)

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
    # A fresh seed carries no market shock, but clear the keys defensively so a
    # demo reset is always clean.
    for k in ("_shock_active", "_shock_snapshot", "_shock_params"):
        st.session_state["family"].pop(k, None)
    # Restore all recommendations (clear dismissals + their timestamps).
    st.session_state["dismissed_recs"] = []
    st.session_state["rec_seen"] = {}
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


def _log_family(fam: dict, text: str) -> None:
    fam["activity_log"].insert(0, {"ts": _now(), "text": text})


def _log(text: str) -> None:
    _log_family(get_family(), text)


def _recompute_family(fam: dict, reason: str = "") -> dict:
    """Pure recompute on a family dict (no session access — usable headless).

    Recomputes the engagement score + NBAs (score.py) AND the Client Strategy
    Monitor flags + per-member strategy-fit (strategy.py), then appends to history.
    """
    sc = compute_score(fam)
    fam["current_score"] = sc
    fam["engagement_scores"] = compute_member_engagement(fam)
    fam["nbas"] = generate_nbas(fam)
    fam["alerts"] = generate_strategy_alerts(fam)
    fam["health"] = {
        m: portfolio_health(fam["portfolios"][m], fam["members"][m], fam["engagement"])
        for m in fam["portfolios"]
    }
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


def recompute(reason: str = "") -> dict:
    """Recompute score + NBAs + Strategy Monitor, cache them, and append to history."""
    return _recompute_family(st.session_state["family"], reason)


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


def _confirm_meeting_family(fam: dict, meeting_id: str) -> bool:
    """Pure confirm logic (no session access). Returns True if a meeting matched."""
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
            _log_family(fam, f"Meeting confirmed with {m['with']}: {m.get('topic')}")
            # A rebalancing / portfolio-review meeting clears the strategy-monitor
            # drift breach by bringing the portfolio back to its target — mirrors
            # how a "savings" meeting sets heir_has_savings_plan above.
            if "rebalanc" in topic or "portfolio review" in topic:
                _rebalance_family(fam, m["with"])
            _recompute_family(fam, f"Meeting confirmed with {m['with']}")
            return True
    return False


def confirm_meeting(meeting_id: str) -> None:
    _confirm_meeting_family(get_family(), meeting_id)


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


# ---------------------------------------------------------------------------
# Client Strategy Monitor levers (paper §4.3) — a market simulator + rebalance.
#
# These are SAFE to call only from a button handler, never from the render path
# (they mutate shared state). The pure ``_*_family`` helpers operate on a plain
# family dict so they can be unit-tested headlessly (tools/_check_sentinel.py);
# the public mutators wrap them with logging + recompute on the session family.
# ---------------------------------------------------------------------------
def _shock_family(fam: dict, equity_pct: float, fx_pct: float = 0.0,
                  crypto_pct: float = 0.0, bond_pct: float = 0.0) -> set:
    """Apply a single active market shock to a family dict; snapshot first.

    Captures the CURRENT holding values (so deposits made before the shock are
    preserved on reset), then scales equity / FX-marked / digital-asset / bond
    holdings by their respective moves. Re-applying replaces the prior shock.
    """
    if fam.get("_shock_active"):
        _unshock_family(fam)  # single active shock; reset before re-applying
    fam["_shock_snapshot"] = {
        mk: [h["value_chf"] for h in p["holdings"]] for mk, p in fam["portfolios"].items()
    }
    fam["_shock_active"] = True
    fam["_shock_params"] = {"equity_pct": equity_pct, "fx_pct": fx_pct,
                            "crypto_pct": crypto_pct, "bond_pct": bond_pct}
    affected: set = set()
    for mk, p in fam["portfolios"].items():
        changed = False
        for h in p["holdings"]:
            factor = 1.0
            if equity_pct and is_equity_holding(h):
                factor *= (1.0 + equity_pct / 100.0)
            if crypto_pct and is_digital_holding(h):
                factor *= (1.0 + crypto_pct / 100.0)
            if bond_pct and is_bond_holding(h):
                factor *= (1.0 + bond_pct / 100.0)
            if fx_pct and is_fx_holding(h):
                factor *= (1.0 + fx_pct / 100.0)
            if factor != 1.0:
                h["value_chf"] *= factor
                changed = True
        if changed:
            fixtures.recompute_portfolio_derived(p)
            affected.add(mk)
    return affected


def _unshock_family(fam: dict) -> bool:
    """Restore the pre-shock holding values from the snapshot (exact reversal)."""
    snap = fam.get("_shock_snapshot")
    active = fam.get("_shock_active")
    fam.pop("_shock_active", None)
    fam.pop("_shock_snapshot", None)
    fam.pop("_shock_params", None)
    if not snap or not active:
        return False
    for mk, vals in snap.items():
        p = fam["portfolios"].get(mk)
        if not p:
            continue
        for h, v in zip(p["holdings"], vals):
            h["value_chf"] = v
        fixtures.recompute_portfolio_derived(p)
    return True


def _rebalance_family(fam: dict, member: str) -> bool:
    """Move a member's holdings to policy.target_allocation, preserving TOTAL value."""
    p = fam["portfolios"].get(member)
    if not p:
        return False
    target = p.get("policy", {}).get("target_allocation")
    if not target:
        return False
    total = float(sum(h["value_chf"] for h in p["holdings"]))
    groups: dict = {}
    for h in p["holdings"]:
        groups.setdefault(h["asset_class"], []).append(h)
    for cls, hs in groups.items():
        tw = target.get(cls)
        if tw is None:
            continue  # class not in target — leave it untouched
        target_val = total * tw / 100.0
        current = sum(h["value_chf"] for h in hs)
        if current > 0:
            for h in hs:
                h["value_chf"] = h["value_chf"] / current * target_val
        else:
            share = target_val / len(hs)
            for h in hs:
                h["value_chf"] = share
    fixtures.recompute_portfolio_derived(p)
    return True


def apply_market_shock(equity_pct: float, fx_pct: float = 0.0,
                       crypto_pct: float = 0.0, bond_pct: float = 0.0) -> None:
    fam = get_family()
    _shock_family(fam, float(equity_pct), float(fx_pct), float(crypto_pct), float(bond_pct))
    _log(f"Simulation applied: equity {equity_pct:+.0f}%, FX {fx_pct:+.0f}%, "
         f"crypto {crypto_pct:+.0f}%, bonds {bond_pct:+.0f}%")
    recompute("Market simulation applied")


def reset_market_shock() -> None:
    fam = get_family()
    if _unshock_family(fam):
        _log("Market shock reset to pre-shock state")
        recompute("Market shock reset")


def rebalance_to_target(member: str) -> None:
    fam = get_family()
    if _rebalance_family(fam, member):
        _log(f"Rebalanced {member} to the policy target")
        recompute(f"Rebalanced {member} to target")


def shock_active() -> bool:
    return bool(get_family().get("_shock_active"))
