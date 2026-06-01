"""Fixed, documented facts about "The Bank".

Single source of truth for the institutional facts from the examination paper
(course 8,182 "Private Banking and Wealth Management", University of St.Gallen).
These constants are referenced across the prototype so the narrative never
drifts. Do NOT contradict these values elsewhere in the app.

The Bank is a *fictional* family-owned Swiss private bank. All figures here are
the paper's stated facts; all client data (see fixtures.py) is synthetic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Institutional facts (paper §0)
# ---------------------------------------------------------------------------
BANK_PROFILE: dict = {
    "name": "The Bank",
    "legal_form": "Family-owned Swiss private bank",
    "headquarters": "Zurich, Switzerland",
    "fte": 100,
    "aum_chf_bn": 12.0,
    "cost_income_ratio_pct": 70,
    "profit_chf_m": 15,
    "tier1_ratio_pct": 30,
    # Positioning ------------------------------------------------------------
    "model": "Trusted Advisor",
    "model_pillars": [
        "Personal, relationship-led service",
        "Individual, bespoke solutions",
        "Open product architecture (no proprietary products)",
        "Large parts of the value chain outsourced (brokerage, operations, IT)",
    ],
    "differentiator": (
        "Digital-asset / crypto services (trading, custody, advisory) offered via "
        "Swiss partners — a differentiator versus crypto-native banks."
    ),
    # Clients ----------------------------------------------------------------
    "client_segment": "European high-net-worth individuals (HNWIs)",
    "client_avg_age": 65,
    "client_markets": {
        "Switzerland": "served onshore",
        "Germany": "served actively cross-border",
    },
    "booking_centre": "All client assets booked in Switzerland.",
    # Strategic challenge the paper solves -----------------------------------
    "strategic_challenge": "The generational wealth transfer (the 'great wealth transfer').",
    "challenge_detail": (
        "Heirs (aged ~25-45) typically form their primary banking relationship in "
        "their thirties. If The Bank does not engage them 10-15 years before the "
        "inheritance event, it loses the assets at transfer (industry retention "
        "< 20%). Capturing even ~30% of at-risk AUM preserves CHF 1.5-3 bn."
    ),
    "heir_retention_industry_pct": 20,
    "heir_retention_target_pct": 30,
    "aum_at_risk_chf_bn": (1.5, 3.0),
    # Regulatory / sovereignty constraint ------------------------------------
    "data_constraint": (
        "Swiss banking secrecy and data-protection rules require Swiss-hosted AI "
        "and infrastructure partners. Client data may not leave the Swiss "
        "jurisdiction."
    ),
    "cross_border_regime": (
        "Cross-border servicing of German-domiciled clients must respect Swiss "
        "FIDLEG/FINIG conduct rules and German/EU cross-border marketing "
        "restrictions (suitability, documentation, no unsolicited advice into the EU)."
    ),
}

# ---------------------------------------------------------------------------
# Technology partners named in the paper (paper §0).
# In production the AI layer runs on Unique (Swiss-hosted); in THIS prototype
# that layer is simulated with Google Gemini for demonstration only.
# ---------------------------------------------------------------------------
TECH_PARTNERS: list[dict] = [
    {
        "name": "Unique",
        "role": "Swiss-hosted generative AI for wealth managers",
        "note": "Production AI layer. Simulated here with Gemini for the demo only.",
    },
    {
        "name": "Additiv",
        "role": "Modular wealth-tech front end / orchestration",
        "note": "Powers the configurable client 'Wealth OS' dashboards.",
    },
    {"name": "Apiax", "role": "RegTech — encoded cross-border rules", "note": ""},
    {"name": "IDnow", "role": "Digital KYC / identity verification", "note": ""},
]

# AI provider used in THIS prototype (clearly flagged as a simulation).
AI_SIMULATION_NOTE = (
    "In production The Bank's AI runs on the Swiss-hosted **Unique** platform so "
    "client data never leaves Switzerland. This prototype simulates that layer "
    "with Google Gemini purely to demonstrate the concept; no real client data "
    "is used."
)

# Convenience one-liners for headers/footers.
BANK_TAGLINE = "Private Banking & Wealth Management — Zurich"
DISCLAIMER_SHORT = (
    "Prototype with synthetic data. Illustrative AI output, not investment advice."
)


def headline_facts() -> list[tuple[str, str]]:
    """Return (label, value) pairs for a compact 'fact strip' on the landing page."""
    p = BANK_PROFILE
    return [
        ("Headquarters", "Zurich"),
        ("Employees", f"{p['fte']} FTE"),
        ("Assets under management", f"CHF {p['aum_chf_bn']:.0f} bn"),
        ("Cost / income", f"{p['cost_income_ratio_pct']}%"),
        ("Tier 1 ratio", f"{p['tier1_ratio_pct']}%"),
        ("Avg. client age", f"{p['client_avg_age']} years"),
    ]
