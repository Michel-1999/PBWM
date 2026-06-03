"""Client Strategy Monitor — continuous strategy adherence (paper §4.3).

Each client agrees a personal strategy with their advisor at the annual review and
follow-up meetings: target asset-allocation bands, a single-name concentration
limit, a cash range, a digital-asset volatility budget, cross-border suitability,
and the funding of their life goals. This module continuously checks the live
portfolios against that agreed strategy and produces an overall *strategy-fit*
score plus per-dimension flags.

Detection is a transparent, deterministic rule engine (NOT the language model):
threshold comparisons decide whether something is off strategy, exactly like
score.py. The Meridian AI layer (gemini.py) only explains each flag in plain
language and proposes a conversation; it never decides a breach, recommends a
specific trade, gives tax advice, or makes a market forecast.

This module imports nothing from the rest of the app (no state, no dashboard);
data is shared only via the family/portfolio dicts.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Single source of truth for the strategy thresholds. Per-portfolio limits
# (concentration / cash band / da_vol_budget) may be overridden in the fixtures
# "policy.limits" block; THRESHOLDS holds the canonical defaults and the rules
# (drift band, cash-drag horizon, goal-funding floor) that are global.
# ---------------------------------------------------------------------------
THRESHOLDS = {
    "drift_band_pp": 5,            # total allocation distance from target before a rebalance
    "concentration_limit_pct": 15,  # max weight of a single direct (single-name) holding
    "cash_floor_pct": 2,           # minimum cash (liquidity)
    "cash_ceiling_pct": 8,         # cash above this is potential drag
    "cash_drag_days": 90,          # how long idle cash may sit before it is flagged as drag
    "goal_funding_floor_pct": 70,  # funding level below which a goal is "behind plan"
    # da_vol_budget_pct is intentionally NOT here — it is per-portfolio and lives
    # in each fixtures "policy.limits" block (risk budgets differ by member).
}

# Severity model -> traffic lights: ok/info = green, watch = orange, breach = red.
SEVERITY_RANK = {"breach": 0, "watch": 1, "info": 2, "ok": 3}
# strategy-fit deduction per active check status (documented formula, see below).
DEDUCTION = {"breach": 20, "watch": 8, "info": 0, "ok": 0}

CATEGORIES = ("drift", "concentration", "cash", "cross_border", "vol_budget", "goal_gap")
CATEGORY_LABEL = {
    "drift": "Allocation drift", "concentration": "Concentration", "cash": "Cash level",
    "cross_border": "Cross-border", "vol_budget": "Digital-asset risk", "goal_gap": "Life-goal funding",
}
PRIORITY = {"drift": 1, "concentration": 1, "vol_budget": 2, "cash": 2,
            "goal_gap": 3, "cross_border": 5}
TOPIC = {"drift": "Portfolio rebalancing review", "concentration": "Concentration review",
         "cash": "Cash deployment review", "vol_budget": "Digital-asset risk review",
         "goal_gap": "Savings plan & goal review", "cross_border": "Cross-border compliance"}

_SALUTATION = {"principal": "Sehr geehrter Herr Mueller", "spouse": "Sehr geehrte Frau Mueller",
               "heir": "Gruezi Lukas"}


# ---------------------------------------------------------------------------
# Small classification helpers (used by the market simulator in state.py too).
# ---------------------------------------------------------------------------
_EQUITY_RE = re.compile(r"equit|stock|shares", re.IGNORECASE)


def is_equity_holding(holding: dict) -> bool:
    """Equity for the market shock: matched on the asset_class field."""
    return bool(_EQUITY_RE.search(str(holding.get("asset_class", ""))))


def is_fx_holding(holding: dict) -> bool:
    """FX-exposed for the shock: a EUR-marked holding (ticker/name). No marker -> no-op."""
    blob = (str(holding.get("ticker", "")) + " " + str(holding.get("name", ""))).lower()
    return "eur" in blob


def is_digital_holding(holding: dict) -> bool:
    """Digital-asset / crypto holding (for the crypto move in the simulation)."""
    return "digital" in str(holding.get("asset_class", "")).lower()


def is_bond_holding(holding: dict) -> bool:
    """Bond holding (for the rates / bond move in the simulation)."""
    return "bond" in str(holding.get("asset_class", "")).lower()


def _limit(portfolio: dict, key: str):
    """Per-portfolio override from policy.limits, else the global THRESHOLDS default."""
    lim = portfolio.get("policy", {}).get("limits", {})
    if key in lim:
        return lim[key]
    return THRESHOLDS.get(key)


def _cash_weight(portfolio: dict) -> float:
    return float(sum(a["weight_pct"] for a in portfolio["asset_allocation"]
                     if a["asset_class"].lower() == "cash"))


# ---------------------------------------------------------------------------
# The six deterministic checks. Each returns (status, detail, metric).
# ---------------------------------------------------------------------------
def _check_drift(portfolio: dict) -> tuple[str, str, dict]:
    target = portfolio.get("policy", {}).get("target_allocation")
    band = THRESHOLDS["drift_band_pp"]
    if not target:
        return "ok", "No target allocation on file.", {"total_drift_pp": 0.0, "band_pp": band}
    current = {a["asset_class"]: a["weight_pct"] for a in portfolio["asset_allocation"]}
    classes = set(target) | set(current)
    devs = {c: round(current.get(c, 0.0) - target.get(c, 0.0), 2) for c in classes}
    total = round(sum(abs(d) for d in devs.values()), 1)
    worst_c = max(devs, key=lambda c: abs(devs[c]))
    worst = devs[worst_c]
    metric = {"total_drift_pp": total, "band_pp": band, "worst_class": worst_c,
              "worst_pp": worst, "deviations": devs}
    if total > band:
        status = "breach"
    elif total > 0.6 * band:
        status = "watch"
    else:
        status = "ok"
    detail = (f"Allocation is {total:.1f}pp from the agreed target mix (rebalancing band "
              f"{band}pp); largest gap: {worst_c} {worst:+.1f}pp.")
    return status, detail, metric


def _check_concentration(portfolio: dict) -> tuple[str, str, dict]:
    limit = _limit(portfolio, "concentration_limit_pct")
    singles = [h for h in portfolio["holdings"] if "direct" in h["asset_class"].lower()]
    if not singles:
        return "ok", f"No single-name position above the {limit}% limit.", {"max_pct": 0.0, "limit_pct": limit}
    top = max(singles, key=lambda h: h["weight_pct"])
    metric = {"name": top["name"], "max_pct": top["weight_pct"], "limit_pct": limit}
    if top["weight_pct"] > limit:
        status = "breach"
    elif top["weight_pct"] > 0.8 * limit:
        status = "watch"
    else:
        status = "ok"
    detail = f"Largest single-name holding {top['name']} is {top['weight_pct']:.1f}% (limit {limit}%)."
    return status, detail, metric


def _check_cash(portfolio: dict) -> tuple[str, str, dict]:
    floor = _limit(portfolio, "cash_floor_pct")
    ceiling = _limit(portfolio, "cash_ceiling_pct")
    cash = round(_cash_weight(portfolio), 1)
    metric = {"cash_pct": cash, "floor_pct": floor, "ceiling_pct": ceiling,
              "drag_days": THRESHOLDS["cash_drag_days"]}
    if cash < floor:
        status = "watch"
        detail = f"Cash is {cash:.1f}%, below the {floor}% liquidity floor."
    elif cash > ceiling:
        over = cash - ceiling
        status = "breach" if over > 5 else "watch"
        detail = (f"Cash is {cash:.1f}%, above the {ceiling}% upper band — potential cash drag if "
                  f"it persists beyond {THRESHOLDS['cash_drag_days']} days.")
    else:
        status = "ok"
        detail = f"Cash is {cash:.1f}%, within the {floor}-{ceiling}% band."
    return status, detail, metric


def _check_cross_border(member: dict) -> tuple[str, str, dict]:
    if not member.get("cross_border"):
        return "ok", "Domestic client.", {}
    metric = {"domicile": member.get("domicile"), "kyc": member.get("kyc_status")}
    detail = (f"Cross-border {member.get('domicile')} client — Swiss FIDLEG suitability, German "
              "cross-border rules and withholding-tax handling apply (encoded in Apiax rules).")
    return "info", detail, metric


def _check_vol_budget(portfolio: dict) -> tuple[str, str, dict]:
    budget = _limit(portfolio, "da_vol_budget_pct")
    da = float(portfolio["digital_asset_sleeve"]["weight_pct"])
    metric = {"da_pct": da, "budget_pct": budget}
    if not budget:  # 0 or None -> no digital-asset budget for this member
        return "ok", "No digital-asset risk budget set.", metric
    if da > budget:
        status = "breach" if da > budget + 3 else "watch"
        detail = f"Digital-asset sleeve is {da:.1f}%, above the {budget}% volatility budget."
    elif da > 0.9 * budget:
        status = "watch"
        detail = f"Digital-asset sleeve is {da:.1f}%, near the {budget}% volatility budget."
    else:
        status = "ok"
        detail = f"Digital-asset sleeve is {da:.1f}%, within the {budget}% volatility budget."
    return status, detail, metric


def _check_goal_gap(portfolio: dict, member: dict, engagement: dict) -> tuple[str, str, dict]:
    floor = THRESHOLDS["goal_funding_floor_pct"]
    if member["role"] == "heir":
        goals = engagement.get("heir_goals", [])
        target = sum(g.get("target_chf", 0) for g in goals)
        saved = sum(g.get("saved_chf", 0) for g in goals)
    else:
        goals = portfolio.get("policy", {}).get("goals", [])
        target = sum(g.get("target_chf", 0) for g in goals)
        saved = sum(g.get("saved_chf", 0) for g in goals)
    if not goals or target <= 0:
        return "ok", "No funding goals tracked.", {"funding_pct": None, "floor_pct": floor}
    funding = round(saved / target * 100.0, 1)
    metric = {"funding_pct": funding, "floor_pct": floor, "saved_chf": saved, "target_chf": target}
    if funding < floor:
        status = "watch"
        detail = f"Goal funding is {funding:.0f}%, below the {floor}% checkpoint."
    else:
        status = "ok"
        detail = f"Goal funding is {funding:.0f}%, at or above the {floor}% checkpoint."
    return status, detail, metric


def portfolio_health(portfolio: dict, member: dict, engagement: dict) -> dict:
    """Run the six checks and a transparent strategy-fit score.

    strategy_fit formula (auditable): start at 100, then subtract a fixed amount
    for each active check — breach -20, watch -8, info/ok 0 — and clamp to [0, 100].
    """
    s_drift, d_drift, m_drift = _check_drift(portfolio)
    s_con, d_con, m_con = _check_concentration(portfolio)
    s_cash, d_cash, m_cash = _check_cash(portfolio)
    s_xb, d_xb, m_xb = _check_cross_border(member)
    s_vol, d_vol, m_vol = _check_vol_budget(portfolio)
    s_goal, d_goal, m_goal = _check_goal_gap(portfolio, member, engagement)

    checks = {
        "drift": {"status": s_drift, "detail": d_drift, "metric": m_drift},
        "concentration": {"status": s_con, "detail": d_con, "metric": m_con},
        "cash": {"status": s_cash, "detail": d_cash, "metric": m_cash},
        "cross_border": {"status": s_xb, "detail": d_xb, "metric": m_xb},
        "vol_budget": {"status": s_vol, "detail": d_vol, "metric": m_vol},
        "goal_gap": {"status": s_goal, "detail": d_goal, "metric": m_goal},
    }
    deduction = sum(DEDUCTION.get(c["status"], 0) for c in checks.values())
    policy_fit = max(0, min(100, 100 - deduction))
    return {"policy_fit": policy_fit, "checks": checks}


# ---------------------------------------------------------------------------
# Routing — who a flag is for, and what action it offers. The life-goal rule
# keeps the heir's nudge client-only and away from score.py.
# ---------------------------------------------------------------------------
def _route(member_key: str, category: str) -> tuple[str, str]:
    """Return (audience, suggested_action) for a (member, category) pair."""
    if member_key == "heir":
        # The next generation is engaged self-serve; the RM action for the heir
        # (the savings conversation) is owned by score.py's nba-heir-savings.
        return "client", "none"
    action = {"drift": "request_meeting", "goal_gap": "request_meeting"}.get(category, "send_message")
    return "both", action


# ---------------------------------------------------------------------------
# Deterministic template narration + outgoing-message drafts (offline fallback
# for the AI layer). The live AI grounds on the same fields.
# ---------------------------------------------------------------------------
def _template_text(member_key: str, name: str, category: str, status: str, metric: dict) -> str:
    not_advice = " This is a monitoring signal, not investment advice."
    if category == "drift":
        base = (f"{name}'s portfolio has drifted {metric['total_drift_pp']:.1f}pp from the agreed "
                f"target mix (largest gap in {metric['worst_class']}). A short rebalancing review "
                f"would bring it back inside the {metric['band_pp']}pp band.")
    elif category == "concentration":
        base = (f"A single position ({metric['name']}) is {metric['max_pct']:.1f}% of {name}'s "
                f"portfolio, above the {metric['limit_pct']}% concentration guideline. Worth a "
                "conversation about trimming it.")
    elif category == "cash":
        if member_key == "heir":
            base = (f"You are currently holding {metric['cash_pct']:.0f}% in cash, a little above "
                    "your plan. Putting some of it to work toward your goal could help it grow.")
        else:
            base = (f"{name} is holding {metric['cash_pct']:.0f}% in cash (guideline up to "
                    f"{metric['ceiling_pct']}%). A short review could decide whether to deploy some of it.")
    elif category == "vol_budget":
        base = (f"{name}'s digital-asset sleeve is {metric['da_pct']:.1f}%, above the "
                f"{metric['budget_pct']}% volatility budget. A review of position sizing may be warranted.")
    elif category == "goal_gap":
        if member_key == "heir":
            base = (f"Your goal is about {metric['funding_pct']:.0f}% funded — a little behind plan for "
                    "the timeline. A small regular top-up would close the gap.")
        else:
            base = (f"{name}'s funding goals are about {metric['funding_pct']:.0f}% funded, below the "
                    f"{metric['floor_pct']}% checkpoint. Worth reviewing the contribution plan.")
    elif category == "cross_border":
        base = ("Reminder: the Mueller family is served cross-border (Germany). Confirm FIDLEG "
                "suitability documentation and withholding-tax handling are current and that no "
                "unsolicited EU solicitation occurs. Compliance reminder — no client action required.")
        return base
    else:
        base = f"{name}: {category} signal ({status})."
    return base + not_advice


def _draft_message(member_key: str, category: str, metric: dict) -> str:
    """A short DRAFT (advisor -> client) for the suggested action. Never auto-sent."""
    sal = _SALUTATION.get(member_key, "Gruezi")
    if category == "drift":
        body = ("einige Positionen haben sich vom vereinbarten Zielband entfernt. Ich schlage einen "
                "kurzen Rebalancing-Termin vor, um das Portfolio wieder ins Gleichgewicht zu bringen.")
    elif category == "concentration":
        body = ("eine Einzelposition ist relativ gross geworden. Gerne bespreche ich mit Ihnen, ob "
                "wir sie etwas reduzieren moechten.")
    elif category == "cash":
        body = ("aktuell liegt vergleichsweise viel Liquiditaet auf dem Konto. Gerne zeige ich Ihnen "
                "unverbindlich Moeglichkeiten, einen Teil davon anzulegen.")
    elif category == "vol_budget":
        body = ("der Anteil digitaler Vermoegenswerte liegt ueber dem vereinbarten Risikobudget. "
                "Gerne ueberpruefen wir gemeinsam die Positionsgroesse.")
    elif category == "goal_gap":
        body = ("Ihr Sparziel liegt aktuell etwas hinter dem Plan. Gerne richte ich mit Ihnen einen "
                "passenden Sparplan ein, um die Luecke zu schliessen.")
    else:
        body = "gerne bespreche ich die aktuellen Punkte unverbindlich mit Ihnen."
    return (f"{sal}, {body} Wann wuerde Ihnen ein kurzes Gespraech passen?\n\n"
            "Mit freundlichen Gruessen\nReto Wyss, The Bank")


def _mk_alert(member_key: str, name: str, category: str, status: str, metric: dict) -> dict:
    audience, action = _route(member_key, category)
    if category == "cross_border":
        audience, action = "rm", "none"
    return {
        "id": f"alert-{member_key}-{category}",
        "member": member_key,
        "member_name": name,
        "severity": status,
        "category": category,
        "category_label": CATEGORY_LABEL.get(category, category),
        "title": f"{TOPIC[category]} — {name}",
        "detail": "",
        "template_text": _template_text(member_key, name, category, status, metric),
        "suggested_action": action,
        "topic": TOPIC[category],
        "message": _draft_message(member_key, category, metric),
        "policy_ref": category,
        "metric": metric,
        "audience": audience,
        "priority": PRIORITY[category],
    }


# ---------------------------------------------------------------------------
# Flag generation — what the advisor surface renders. Suppressed once resolved,
# exactly like score.generate_nbas suppresses NBAs.
# ---------------------------------------------------------------------------
def generate_strategy_alerts(family: dict) -> list[dict]:
    eng = family["engagement"]
    meetings = family.get("meetings", [])
    nbas = family.get("nbas", [])

    def has_meeting(target: str, *subs: str) -> bool:
        return any(
            m["with"] == target
            and any(s in m.get("topic", "").lower() for s in subs)
            and m["status"] in ("requested", "confirmed")
            for m in meetings
        )

    savings_nba_open = any(n["id"] == "nba-heir-savings" for n in nbas)
    alerts: list[dict] = []

    for member_key in ("principal", "spouse", "heir"):
        portfolio = family["portfolios"][member_key]
        member = family["members"][member_key]
        name = member["name"]
        checks = portfolio_health(portfolio, member, eng)["checks"]

        for category in ("drift", "concentration", "cash", "vol_budget"):
            chk = checks[category]
            if chk["status"] not in ("watch", "breach"):
                continue
            # Suppress drift once a rebalancing / portfolio-review meeting is in flight.
            if category == "drift" and has_meeting(member_key, "rebalanc", "portfolio review"):
                continue
            alert = _mk_alert(member_key, name, category, chk["status"], chk["metric"])
            alert["detail"] = chk["detail"]
            alerts.append(alert)

        # Life-goal funding — special ownership rule.
        gg = checks["goal_gap"]
        if gg["status"] in ("watch", "breach"):
            if member_key == "heir":
                # Client-only, and suppressed while the savings hero flow is active,
                # so it never duplicates score.py's nba-heir-savings.
                if not savings_nba_open and not has_meeting("heir", "savings"):
                    alert = _mk_alert("heir", name, "goal_gap", gg["status"], gg["metric"])
                    alert["detail"] = gg["detail"]
                    alerts.append(alert)
            elif not has_meeting(member_key, "savings", "goal", "portfolio review"):
                alert = _mk_alert(member_key, name, "goal_gap", gg["status"], gg["metric"])
                alert["detail"] = gg["detail"]
                alerts.append(alert)

        # Cross-border — a single standing compliance reminder (advisor, informational).
        if member_key == "principal":
            cb = checks["cross_border"]
            if cb["status"] != "ok":
                alert = _mk_alert("principal", name, "cross_border", cb["status"], cb["metric"])
                alert["detail"] = cb["detail"]
                alerts.append(alert)

    alerts.sort(key=lambda a: (SEVERITY_RANK.get(a["severity"], 9), a["priority"]))
    return alerts
