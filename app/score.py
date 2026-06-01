"""Inheritance Engagement Score — rule-based, transparent, explainable (paper §4).

This is the analytical heart of use case 4.2 and is deliberately NOT the LLM.

Semantics (read this carefully)
-------------------------------
The score is a 0-100 **priority / urgency** indicator for acting on the
generational wealth transfer of one family. **Higher = more at-risk AUM that
needs proactive engagement.** It is a weighted blend of four risk components:

    wealth_at_stake      ~30%   larger principal AUM            -> higher score
    transfer_proximity   ~25%   principal closer to transfer    -> higher score
    heir_disengagement   ~30%   the inverse of heir activity     -> higher score
    relationship_thinness~15%   thin / no RM relationship        -> higher score

Because heir_disengagement is the *inverse* of activity, when the heir engages
(logs in, sets a goal, deposits, agrees a savings plan) the score **falls** —
i.e. at-risk AUM is being secured. That decline is the demo's payoff: the RM
watches the family move from "High priority" toward "Medium/Low" live.

(Note on the spec: §1 loosely says a heir action "raises" the score; §4 — the
detailed analytical section implemented here — defines it as a risk score that
engagement lowers. We follow §4 and surface the direction explicitly in the UI.)
"""

from __future__ import annotations

# Component weights (sum to 1.0). Tunable in one place.
WEIGHTS = {
    "wealth_at_stake": 0.30,
    "transfer_proximity": 0.25,
    "heir_disengagement": 0.30,
    "relationship_thinness": 0.15,
}

# Sub-weights inside the heir-engagement blend (sum to 1.0).
ENGAGEMENT_WEIGHTS = {
    "logins": 0.20,
    "deposits": 0.25,
    "goals": 0.20,
    "savings_plan": 0.20,
    "own_mandate": 0.15,
}

# Calibration constants.
AUM_CAP_CHF = 25_000_000      # AUM at/above which "wealth at stake" maxes out
AGE_LOW, AGE_HIGH = 55, 80    # transfer-proximity ramp
LOGIN_TARGET = 8              # logins / 30d considered "fully engaged"
DEPOSIT_TARGET = 2            # deposits / 90d considered "fully engaged"
GOAL_TARGET = 2              # goals considered "fully engaged"
CONTACT_HORIZON_DAYS = 180    # days-since-contact at which recency maxes out
GOVERNANCE_PROXIMITY_RELIEF = 0.6  # succession planning underway dampens proximity risk

# Band thresholds.
BAND_MEDIUM_MIN = 40
BAND_HIGH_MIN = 67


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def band_for(score: float) -> str:
    if score >= BAND_HIGH_MIN:
        return "high"
    if score >= BAND_MEDIUM_MIN:
        return "medium"
    return "low"


BAND_LABELS = {
    "high": "High priority",
    "medium": "Medium priority",
    "low": "Low priority",
}
BAND_COLORS = {  # brand-aligned: red-ish alert -> gold -> brand green (secured)
    "high": "#9C3B2E",
    "medium": "#C9A24B",
    "low": "#1F4F39",
}


def compute_score(family: dict) -> dict:
    """Return the full, explainable score object for the given family state."""
    eng = family["engagement"]
    principal = family["portfolios"]["principal"]
    age = family["members"]["principal"]["age"]
    aum = float(principal["total_value_chf"])

    # 1) Wealth at stake -----------------------------------------------------
    wealth_sub = _clamp(aum / AUM_CAP_CHF) * 100.0

    # 2) Transfer proximity (relieved if succession planning has started) ----
    proximity_raw = _clamp((age - AGE_LOW) / (AGE_HIGH - AGE_LOW)) * 100.0
    if eng.get("principal_governance_intro_done"):
        proximity_sub = proximity_raw * GOVERNANCE_PROXIMITY_RELIEF
    else:
        proximity_sub = proximity_raw

    # 3) Heir disengagement (the live lever) ---------------------------------
    login_e = _clamp(eng["heir_logins_30d"] / LOGIN_TARGET)
    deposit_e = _clamp(eng["heir_deposits_90d"] / DEPOSIT_TARGET)
    goals_e = _clamp(len(eng["heir_goals"]) / GOAL_TARGET)
    plan_e = 1.0 if eng.get("heir_has_savings_plan") else 0.0
    mandate_e = 1.0 if eng.get("heir_has_own_mandate") else 0.0
    engagement = (
        ENGAGEMENT_WEIGHTS["logins"] * login_e
        + ENGAGEMENT_WEIGHTS["deposits"] * deposit_e
        + ENGAGEMENT_WEIGHTS["goals"] * goals_e
        + ENGAGEMENT_WEIGHTS["savings_plan"] * plan_e
        + ENGAGEMENT_WEIGHTS["own_mandate"] * mandate_e
    )
    disengagement_sub = (1.0 - engagement) * 100.0

    # 4) Relationship thinness ----------------------------------------------
    recency = _clamp(eng["last_rm_contact_days"] / CONTACT_HORIZON_DAYS) * 100.0
    heir_rel = 30.0 if eng.get("heir_has_rm_relationship") else 100.0
    thinness_sub = 0.4 * recency + 0.6 * heir_rel

    components = {
        "wealth_at_stake": round(wealth_sub, 1),
        "transfer_proximity": round(proximity_sub, 1),
        "heir_disengagement": round(disengagement_sub, 1),
        "relationship_thinness": round(thinness_sub, 1),
    }
    raw = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    score = int(round(max(0.0, min(100.0, raw))))
    band = band_for(score)

    drivers = _drivers(components, eng, age, aum)

    return {
        "score": score,
        "band": band,
        "band_label": BAND_LABELS[band],
        "color": BAND_COLORS[band],
        "components": components,
        "weights": WEIGHTS,
        "weighted_contributions": {
            k: round(components[k] * WEIGHTS[k], 1) for k in WEIGHTS
        },
        "engagement_index": round(engagement * 100, 1),  # secondary "good" indicator
        "drivers": drivers,
    }


def _drivers(components: dict, eng: dict, age: int, aum: float) -> list[str]:
    """Plain-language reasons, ordered by weighted impact (what the RM reads)."""
    out: list[str] = []
    if components["wealth_at_stake"] >= 60:
        out.append(
            f"CHF {aum/1e6:.1f}m of principal AUM is exposed at the wealth transfer."
        )
    if components["transfer_proximity"] >= 30:
        note = " (eased — succession planning has started)" if eng.get(
            "principal_governance_intro_done") else ""
        out.append(f"Principal is {age} and approaching the transfer horizon{note}.")
    if components["heir_disengagement"] >= 50:
        bits = []
        if eng["heir_logins_30d"] < LOGIN_TARGET:
            bits.append(f"{eng['heir_logins_30d']} logins/30d")
        if eng["heir_deposits_90d"] == 0:
            bits.append("no deposits in 90d")
        if not eng["heir_goals"]:
            bits.append("no savings goal")
        if not eng.get("heir_has_savings_plan"):
            bits.append("no savings plan")
        if not eng.get("heir_has_own_mandate"):
            bits.append("no own mandate")
        out.append("Heir is disengaged: " + ", ".join(bits) + ".")
    elif components["heir_disengagement"] >= 25:
        out.append("Heir engagement is improving but not yet self-sustaining.")
    if not eng.get("heir_has_rm_relationship"):
        out.append("Heir has no direct relationship-manager relationship yet.")
    elif components["relationship_thinness"] >= 40:
        out.append(f"Last family contact was {eng['last_rm_contact_days']} days ago.")
    return out


# ---------------------------------------------------------------------------
# Next-Best-Actions — derived from the same rules; these are what the RM clicks.
# ---------------------------------------------------------------------------
def generate_nbas(family: dict) -> list[dict]:
    """Generate prioritised NBAs from the score signals and current state.

    NBAs are suppressed once their precondition is met (e.g. governance intro
    done, or a savings meeting already requested), so the list reflects reality.
    """
    eng = family["engagement"]
    members = family["members"]
    meetings = family.get("meetings", [])
    nbas: list[dict] = []

    def has_meeting(target: str, contains: str) -> bool:
        return any(
            m["with"] == target
            and contains.lower() in m.get("topic", "").lower()
            and m["status"] in ("requested", "confirmed")
            for m in meetings
        )

    # 1) Heir savings-plan conversation (the hero-flow NBA) ------------------
    heir_disengaged = (
        eng["heir_deposits_90d"] == 0
        or not eng.get("heir_has_savings_plan")
        or eng["heir_logins_30d"] < LOGIN_TARGET
    )
    if heir_disengaged and not has_meeting("heir", "savings"):
        has_goal = bool(eng["heir_goals"])
        if has_goal:
            title = "Propose Lukas a savings plan to fund his goal"
            rationale = (
                "Lukas has set a savings goal but has no savings plan or mandate. "
                "Convert intent into a funded monthly plan now."
            )
        else:
            title = "Offer Lukas a monthly savings-plan conversation"
            rationale = (
                "Lukas is the at-risk next-generation asset: thin activity, no "
                "deposits, no plan. A savings-plan conversation starts the direct "
                "relationship 10-15 years before the inheritance event."
            )
        nbas.append({
            "id": "nba-heir-savings",
            "title": title,
            "rationale": rationale,
            "target": "heir",
            "action": "request_meeting",
            "topic": "Savings plan & first investment review",
            "message": (
                "Gruezi Lukas, hier ist Reto Wyss von The Bank. Ihr Vater erwaehnte "
                "Ihr Interesse am Anlegen und Sparen. Gerne richte ich Ihnen einen "
                "einfachen monatlichen Sparplan ein - haetten Sie 30 Minuten fuer ein "
                "kurzes Gespraech?"
            ),
            "priority": 1,
        })

    # 2) Principal family-governance / succession intro ---------------------
    if members["principal"]["age"] >= 65 and not eng.get("principal_governance_intro_done"):
        nbas.append({
            "id": "nba-governance",
            "title": "Introduce Hans to family-governance & succession planning",
            "rationale": (
                "Principal is 65 and approaching retirement. A discreet family-"
                "governance conversation protects the Trusted-Advisor relationship "
                "and creates the natural bridge to engage the next generation."
            ),
            "target": "principal",
            "action": "request_meeting",
            "topic": "Family governance & succession planning",
            "message": (
                "Sehr geehrter Herr Mueller, im Hinblick auf Ihre Pensionierung "
                "moechte ich Ihnen unsere Begleitung bei Familien-Governance und "
                "Nachfolgeplanung anbieten - unverbindlich und vertraulich. Wann "
                "wuerde Ihnen ein Gespraech passen?"
            ),
            "priority": 2,
        })

    # 3) Alternative investments follow-up (based on the last review) --------
    if not has_meeting("principal", "alternative"):
        nbas.append({
            "id": "nba-alt-investments",
            "title": "Propose alternative investment classes to Hans",
            "rationale": (
                "Based on the last review (Q4-2025), Hans is open to diversification. Propose "
                "private-market / alternative investments to complement the core portfolio."
            ),
            "target": "principal",
            "action": "send_message",
            "topic": "Alternative investments proposal",
            "message": (
                "Sehr geehrter Herr Mueller, anknuepfend an unser letztes Gespraech moechte ich "
                "Ihnen gerne ergaenzende Anlageklassen (u.a. Private Markets) vorstellen. Wann "
                "wuerde Ihnen ein kurzer Termin passen?"
            ),
            "priority": 2,
        })

    # 4) Heir KYC refresh (cross-border) ------------------------------------
    if members["heir"].get("kyc_status") == "review":
        nbas.append({
            "id": "nba-heir-kyc",
            "title": "Arrange Lukas's KYC refresh (cross-border DE)",
            "rationale": (
                "Heir KYC is in review (source-of-wealth & ID re-verification). "
                "Required before any deposit uplift or advisory mandate; digital "
                "re-verification runs via IDnow."
            ),
            "target": "heir",
            "action": "send_message",
            "topic": "KYC refresh",
            "message": (
                "Gruezi Lukas, fuer die Aktualisierung Ihres Kontos benoetigen wir "
                "eine kurze digitale Identitaetspruefung (ca. 5 Minuten via IDnow). "
                "Ich sende Ihnen gerne den Link."
            ),
            "priority": 3,
        })

    nbas.sort(key=lambda n: n["priority"])
    return nbas
