"""The Mueller family seed data (paper §6).

Everything an examiner might cross-check reconciles *by construction*:

* Holding weights and the asset-allocation summary are DERIVED from the holding
  values, so they always sum to 100% and to the portfolio total.
* The annualised return (IRR / money-weighted) is COMPUTED from the actual
  dated cash flows and the terminal value via a small bisection solver, so the
  "net return including all trades" figure is genuinely defensible.

All persons and figures are FICTIONAL and consistent with the bank profile
(German family, active cross-border, principal 65, heir 32). No real data.
"""

from __future__ import annotations

import copy
from datetime import date

# As-of date for all portfolio snapshots (kept in sync with the demo "today").
AS_OF = date(2026, 5, 31)
AS_OF_STR = AS_OF.isoformat()

BENCHMARK_PRINCIPAL = "Custom 45/25/30 reference (MSCI World / Global Agg Bond / Diversified Alt.)"
BENCHMARK_HEIR = "80/20 reference (MSCI World / CHF cash)"

# The family's overarching wealth strategy (shared context for the AI).
FAMILY_STRATEGY = {
    "summary": "Preserve and grow the family's wealth across generations with a balanced, "
               "open-architecture approach, while preparing an orderly transfer to the next "
               "generation (Lukas).",
    "investment_approach": "Core balanced portfolios (equities + bonds) complemented by selective "
                           "alternatives and a small digital-asset sleeve as The Bank's "
                           "differentiator. Conservative tilt for Margrit, balanced for Hans, "
                           "growth tilt for Lukas.",
    "wealth_transfer": "Engage the next generation 10-15 years before the inheritance event: "
                       "introduce Hans to family governance, build Lukas's direct relationship via "
                       "a monthly savings plan, and retain at least 30% of at-risk AUM at transfer.",
    "liquidity": "Keep 6-12 months of liquidity per household member; CHF 1.5m was withdrawn in 2023 "
                 "for the Ticino property.",
    "philanthropy_esg": "A moderate ESG tilt; Margrit's family foundation channels the family's giving.",
    "near_term": "Hans retires at end-2026; finalise the succession and estate structure with the "
                 "external notary and formalise a family-governance charter.",
}


# ---------------------------------------------------------------------------
# Small finance helpers — keep the data honest.
# ---------------------------------------------------------------------------
def xirr(cashflows: list[tuple[date, float]]) -> float:
    """Money-weighted annual return (XIRR) from dated cash flows.

    Convention: amounts the client pays IN are negative, amounts returned to the
    client (incl. the terminal portfolio value) are positive. Solved by
    bisection on ACT/365 day-count — robust and dependency-free.
    """
    t0 = min(d for d, _ in cashflows)

    def npv(rate: float) -> float:
        return sum(
            amt / ((1.0 + rate) ** ((d - t0).days / 365.0)) for d, amt in cashflows
        )

    lo, hi = -0.95, 3.0
    f_lo = npv(lo)
    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = npv(mid)
        if abs(f_mid) < 1e-4:
            return mid
        if (f_lo < 0) == (f_mid < 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _finalize_holdings(holdings: list[dict]) -> tuple[list[dict], float]:
    """Add weight_pct to every holding (derived) and return (holdings, total)."""
    total = float(sum(h["value_chf"] for h in holdings))
    for h in holdings:
        h["weight_pct"] = round(h["value_chf"] / total * 100.0, 2)
    return holdings, total


def _allocation_from_holdings(holdings: list[dict], total: float) -> list[dict]:
    """Group holdings by asset_class into an allocation summary (sums to 100%)."""
    order: list[str] = []
    buckets: dict[str, float] = {}
    for h in holdings:
        ac = h["asset_class"]
        if ac not in buckets:
            buckets[ac] = 0.0
            order.append(ac)
        buckets[ac] += h["value_chf"]
    return [
        {
            "asset_class": ac,
            "value_chf": round(buckets[ac], 2),
            "weight_pct": round(buckets[ac] / total * 100.0, 2),
        }
        for ac in order
    ]


def _digital_sleeve(holdings: list[dict], total: float) -> dict:
    dav = sum(h["value_chf"] for h in holdings if h["asset_class"] == "Digital Assets")
    names = [h["name"] for h in holdings if h["asset_class"] == "Digital Assets"]
    return {
        "value_chf": round(dav, 2),
        "weight_pct": round(dav / total * 100.0, 2),
        "instruments": names,
        "custodian": "The Bank's regulated Swiss digital-asset partner (segregated cold storage).",
    }


def recompute_portfolio_derived(portfolio: dict) -> None:
    """Recompute total, weights, allocation and the digital sleeve in place.

    Called after a mutation (e.g. a heir deposit) so the portfolio stays
    internally consistent — weights sum to 100% and to the new total.
    """
    holdings, total = _finalize_holdings(portfolio["holdings"])
    portfolio["total_value_chf"] = total
    portfolio["asset_allocation"] = _allocation_from_holdings(holdings, total)
    portfolio["digital_asset_sleeve"] = _digital_sleeve(holdings, total)


# ---------------------------------------------------------------------------
# Principal — Hans Mueller, 65.
# ---------------------------------------------------------------------------
def _build_principal() -> dict:
    holdings = [
        # Direct equities ----------------------------------------------------
        {"name": "Nestle SA", "ticker": "NESN.SW", "asset_class": "Equities (direct)", "value_chf": 1_400_000},
        {"name": "Roche Holding AG", "ticker": "ROG.SW", "asset_class": "Equities (direct)", "value_chf": 1_150_000},
        {"name": "Novartis AG", "ticker": "NOVN.SW", "asset_class": "Equities (direct)", "value_chf": 1_050_000},
        {"name": "ASML Holding NV", "ticker": "ASML.AS", "asset_class": "Equities (direct)", "value_chf": 920_000},
        {"name": "LVMH Moet Hennessy", "ticker": "MC.PA", "asset_class": "Equities (direct)", "value_chf": 880_000},
        {"name": "Apple Inc.", "ticker": "AAPL", "asset_class": "Equities (direct)", "value_chf": 872_000},
        # Third-party funds (open architecture) ------------------------------
        {"name": "iShares Core MSCI World ETF", "ticker": "IWDA", "asset_class": "Equity funds", "value_chf": 1_600_000},
        {"name": "Vanguard FTSE All-World ETF", "ticker": "VWRL", "asset_class": "Equity funds", "value_chf": 1_232_000},
        {"name": "Pictet Global Megatrend Selection", "ticker": "PF-GMS", "asset_class": "Equity funds", "value_chf": 1_200_000},
        # Bonds --------------------------------------------------------------
        {"name": "Swiss Confederation 1.25% 2031", "ticker": "CH-GOVT", "asset_class": "Bonds", "value_chf": 1_800_000},
        {"name": "German Bund 2.30% 2033", "ticker": "DE-BUND", "asset_class": "Bonds", "value_chf": 1_600_000},
        {"name": "iShares Global Corp Bond ETF", "ticker": "CRPS", "asset_class": "Bonds", "value_chf": 1_300_000},
        {"name": "Nestle Finance 0.875% 2029", "ticker": "NESN-29", "asset_class": "Bonds", "value_chf": 900_000},
        # Alternatives -------------------------------------------------------
        {"name": "Partners Group Global Value (PE)", "ticker": "PGGV", "asset_class": "Alternatives", "value_chf": 1_400_000},
        {"name": "Man AHL Trend Alternative", "ticker": "AHL", "asset_class": "Alternatives", "value_chf": 1_288_000},
        # Real estate --------------------------------------------------------
        {"name": "UBS (CH) Property Fund - Swiss Mixed", "ticker": "UBS-SM", "asset_class": "Real estate", "value_chf": 868_000},
        {"name": "Swiss Prime Site AG", "ticker": "SPSN.SW", "asset_class": "Real estate", "value_chf": 700_000},
        # Digital assets (the differentiator) --------------------------------
        {"name": "Bitcoin (BTC)", "ticker": "BTC", "asset_class": "Digital Assets", "value_chf": 560_000},
        {"name": "Ethereum (ETH)", "ticker": "ETH", "asset_class": "Digital Assets", "value_chf": 250_000},
        {"name": "Ethereum - staked (custody)", "ticker": "ETH-STK", "asset_class": "Digital Assets", "value_chf": 86_000},
        # Cash ---------------------------------------------------------------
        {"name": "CHF current account", "ticker": "CASH-CHF", "asset_class": "Cash", "value_chf": 844_000},
        {"name": "EUR current account", "ticker": "CASH-EUR", "asset_class": "Cash", "value_chf": 500_000},
    ]
    holdings, total = _finalize_holdings(holdings)  # total == 22,400,000

    # External cash flows (client's perspective): pay-in negative, terminal +.
    cashflows = [
        (date(2019, 1, 15), -12_000_000.0),   # opened mandate
        (date(2021, 9, 20), -6_000_000.0),    # invested company-stake proceeds
        (date(2023, 4, 10), +1_500_000.0),    # withdrawal (Ticino property)
        (AS_OF, +total),                       # terminal portfolio value
    ]
    net_contributions = 12_000_000 + 6_000_000 - 1_500_000  # = 16,500,000
    net_gain = total - net_contributions
    irr = xirr(cashflows)

    return {
        "owner": "Hans Mueller",
        "as_of": AS_OF_STR,
        "currency": "CHF",
        "risk_profile": "Balanced (moderate)",
        "mandate_type": "Advisory mandate (open architecture, no proprietary products)",
        "benchmark": BENCHMARK_PRINCIPAL,
        "relationship_since": 2019,
        "total_value_chf": total,
        "holdings": holdings,
        "asset_allocation": _allocation_from_holdings(holdings, total),
        "digital_asset_sleeve": _digital_sleeve(holdings, total),
        # Suitability policy block — used by the Client Strategy Monitor (§4.3). The
        # target_allocation keys mirror the asset_class labels above and sum to
        # 100; at seed the holdings sit on target, so the principal is IN policy.
        # limits override sentinel.THRESHOLDS defaults where the member differs;
        # da_vol_budget_pct is genuinely per-portfolio (risk budget for crypto).
        "policy": {
            "risk_profile": "Balanced (moderate)",
            "target_allocation": {
                "Equities (direct)": 28, "Equity funds": 18, "Bonds": 25,
                "Alternatives": 12, "Real estate": 7, "Digital Assets": 4, "Cash": 6,
            },
            "limits": {"concentration_limit_pct": 15, "cash_floor_pct": 2,
                       "cash_ceiling_pct": 8, "da_vol_budget_pct": 8},
            "goals": [
                {"name": "Legacy fund for grandchildren", "target_chf": 500_000, "saved_chf": 380_000},
                {"name": "Ticino property upkeep reserve", "target_chf": 200_000, "saved_chf": 165_000},
            ],
        },
        "performance_annual": [
            {"year": "2019", "portfolio_pct": 16.8, "benchmark_pct": 18.2},
            {"year": "2020", "portfolio_pct": 6.2, "benchmark_pct": 6.5},
            {"year": "2021", "portfolio_pct": 14.1, "benchmark_pct": 15.0},
            {"year": "2022", "portfolio_pct": -9.8, "benchmark_pct": -12.4},
            {"year": "2023", "portfolio_pct": 11.3, "benchmark_pct": 12.1},
            {"year": "2024", "portfolio_pct": 9.7, "benchmark_pct": 10.4},
            {"year": "2025", "portfolio_pct": 13.5, "benchmark_pct": 14.2},
            {"year": "2026 YTD", "portfolio_pct": 4.2, "benchmark_pct": 4.6},
        ],
        "net_return": {
            "inception_date": "2019-01-15",
            "net_contributions_chf": net_contributions,
            "current_value_chf": total,
            "cumulative_net_gain_chf": net_gain,
            "simple_net_return_pct": round(net_gain / net_contributions * 100.0, 1),
            "annualised_return_irr_pct": round(irr * 100.0, 1),
            "total_fees_paid_since_inception_chf": 520_000,
            "basis": "Net of all fees; money-weighted (XIRR) across all contributions, "
                     "the 2023 withdrawal and every trade since 2019-01-15.",
        },
        "trades": [
            {"date": "2019-01-20", "side": "BUY", "instrument": "Nestle SA", "amount_chf": 1_000_000},
            {"date": "2019-02-05", "side": "BUY", "instrument": "iShares Core MSCI World ETF", "amount_chf": 1_200_000},
            {"date": "2019-03-12", "side": "BUY", "instrument": "Swiss Confederation 1.25% 2031", "amount_chf": 1_800_000},
            {"date": "2020-03-23", "side": "BUY", "instrument": "ASML Holding NV", "amount_chf": 500_000, "note": "Added in the COVID drawdown"},
            {"date": "2021-09-25", "side": "BUY", "instrument": "Partners Group Global Value (PE)", "amount_chf": 1_400_000, "note": "Deployed company-stake proceeds"},
            {"date": "2021-10-02", "side": "BUY", "instrument": "Bitcoin (BTC)", "amount_chf": 300_000, "note": "Initial digital-asset allocation"},
            {"date": "2022-06-15", "side": "SELL", "instrument": "Apple Inc.", "amount_chf": 250_000, "note": "Trimmed after strong run"},
            {"date": "2023-04-10", "side": "SELL", "instrument": "iShares Global Corp Bond ETF", "amount_chf": 1_500_000, "note": "Funded CHF 1.5m withdrawal"},
            {"date": "2024-02-12", "side": "BUY", "instrument": "Ethereum (ETH)", "amount_chf": 150_000},
            {"date": "2025-03-05", "side": "BUY", "instrument": "Pictet Global Megatrend Selection", "amount_chf": 400_000},
        ],
        "fees": {
            "advisory_fee_pct_pa": 0.35,
            "custody_fee_pct_pa": 0.15,
            "crypto_custody_fee_pct_pa": 0.50,
            "transaction_fees": "Brokerage at cost + 0.10% (outsourced execution)",
            "retrocessions": "None retained — open product architecture",
            "last_12m_fees_chf": 112_000,
        },
        "crm": {
            "occupation": "Retired entrepreneur (manufacturing)",
            "domicile": "Munich, Germany (served cross-border; assets booked in CH)",
            "preferred_contact": "In person & phone; paper statements by post",
            "risk_tolerance": "Moderate — capital preservation with measured growth",
            "interests": ["Classical music (Tonhalle patron)", "Vintage cars", "Golf", "Holiday home in Ticino"],
            "favourite_drink": "Barolo red wine; a strong espresso after lunch",
            "personality": "Detail-oriented and discreet; values long-term relationships, punctuality "
                           "and being addressed formally.",
            "household": {
                "spouse": "Margrit Mueller (62)",
                "children": ["Lukas Mueller (32) - client"],
            },
            "life_events": [
                {"date": "2021-09", "event": "Sold a minority stake in the family manufacturing business; CHF 6.0m proceeds invested with The Bank."},
                {"date": "2024-11", "event": "Began estate-planning conversations with an external notary."},
                {"date": "2026-04", "event": "Approaching full retirement (end-2026); reviewing succession and family governance."},
            ],
            "last_review": "2026-02-04 (Q4-2025 portfolio review, in person, Zurich)",
            "open_tasks": ["Annual suitability re-assessment due Q3-2026"],
        },
    }


# ---------------------------------------------------------------------------
# Heir — Lukas Mueller, 32. Deliberately disengaged so the hero flow can move it.
# ---------------------------------------------------------------------------
def _build_heir() -> dict:
    holdings = [
        {"name": "iShares Core MSCI World ETF", "ticker": "IWDA", "asset_class": "Equity ETFs",
         "value_chf": 173_600, "cost_basis_chf": 130_000},
        {"name": "iShares Automation & Robotics ETF", "ticker": "RBOT", "asset_class": "Equity ETFs",
         "value_chf": 42_000, "cost_basis_chf": 36_000},
        {"name": "Bitcoin (BTC)", "ticker": "BTC", "asset_class": "Digital Assets",
         "value_chf": 22_000, "cost_basis_chf": 14_000},
        {"name": "Ethereum (ETH)", "ticker": "ETH", "asset_class": "Digital Assets",
         "value_chf": 11_600, "cost_basis_chf": 12_000},
        {"name": "CHF cash (incl. accrued dividends)", "ticker": "CASH-CHF", "asset_class": "Cash",
         "value_chf": 30_800, "cost_basis_chf": 30_000},
    ]
    holdings, total = _finalize_holdings(holdings)  # total == 280,000

    cashflows = [
        (date(2021, 11, 15), -200_000.0),  # family gift, invested
        (date(2022, 8, 20), -40_000.0),    # own salary savings
        (AS_OF, +total),                    # terminal value
    ]
    net_contributions = 240_000
    net_gain = total - net_contributions  # 40,000
    irr = xirr(cashflows)

    return {
        "owner": "Lukas Mueller",
        "as_of": AS_OF_STR,
        "currency": "CHF",
        "risk_profile": "Growth (high risk capacity, long horizon)",
        "mandate_type": "Execution-only sub-account (no advisory mandate yet)",
        "benchmark": BENCHMARK_HEIR,
        "relationship_since": 2021,
        "total_value_chf": total,
        "holdings": holdings,
        "asset_allocation": _allocation_from_holdings(holdings, total),
        "digital_asset_sleeve": _digital_sleeve(holdings, total),
        # Suitability policy block (paper §4.3). The heir is deliberately a little
        # OFF target at seed (cash has drifted up ~2pp), so one gentle client-side
        # plan-check alert exists from the start without any market shock.
        "policy": {
            "risk_profile": "Growth (high risk capacity, long horizon)",
            # Growth mandate: high equity, a small digital-asset sleeve, and only a
            # modest cash buffer for his near-term apartment goal. He has drifted a
            # touch above the tight cash ceiling, so the monitor shows one gentle cash
            # flag plus a small allocation-drift flag.
            "target_allocation": {"Equity ETFs": 79, "Digital Assets": 12, "Cash": 9},
            "limits": {"concentration_limit_pct": 15, "cash_floor_pct": 2,
                       "cash_ceiling_pct": 10, "da_vol_budget_pct": 15},
            # The heir's funding goals are LIVE (engagement.heir_goals) — set in the
            # life-goal tracker — so none are hard-coded here.
        },
        "performance_annual": [
            {"year": "2022", "portfolio_pct": -14.2, "benchmark_pct": -12.4},
            {"year": "2023", "portfolio_pct": 22.5, "benchmark_pct": 18.6},
            {"year": "2024", "portfolio_pct": 18.1, "benchmark_pct": 15.2},
            {"year": "2025", "portfolio_pct": 16.8, "benchmark_pct": 14.2},
            {"year": "2026 YTD", "portfolio_pct": 6.4, "benchmark_pct": 4.6},
        ],
        "net_return": {
            "inception_date": "2021-11-15",
            "net_contributions_chf": net_contributions,
            "current_value_chf": total,
            "cumulative_net_gain_chf": net_gain,
            "simple_net_return_pct": round(net_gain / net_contributions * 100.0, 1),
            "annualised_return_irr_pct": round(irr * 100.0, 1),
            "total_fees_paid_since_inception_chf": 3_200,
            "basis": "Net of fees; money-weighted (XIRR) across both contributions and "
                     "every trade since 2021-11-15. Annual figures are time-weighted "
                     "full-year returns (the Nov-Dec 2021 stub is excluded).",
        },
        "trades": [
            {"date": "2021-11-15", "side": "BUY", "instrument": "iShares Core MSCI World ETF", "amount_chf": 100_000, "note": "Initial — from family gift"},
            {"date": "2021-11-15", "side": "BUY", "instrument": "Bitcoin (BTC)", "amount_chf": 14_000, "note": "First crypto position"},
            {"date": "2022-01-10", "side": "BUY", "instrument": "iShares Automation & Robotics ETF", "amount_chf": 36_000},
            {"date": "2022-08-20", "side": "BUY", "instrument": "iShares Core MSCI World ETF", "amount_chf": 30_000, "note": "Own salary savings"},
            {"date": "2024-05-02", "side": "BUY", "instrument": "Ethereum (ETH)", "amount_chf": 12_000},
        ],
        "fees": {
            "advisory_fee_pct_pa": 0.35,
            "custody_fee_pct_pa": 0.15,
            "crypto_custody_fee_pct_pa": 0.50,
            "transaction_fees": "Brokerage at cost + 0.10% (outsourced execution)",
            "retrocessions": "None retained — open product architecture",
            "last_12m_fees_chf": 1_050,
        },
        "crm": {
            "occupation": "Product manager at a Munich technology company",
            "domicile": "Munich, Germany (served cross-border; assets booked in CH)",
            "preferred_contact": "Mobile app & secure chat",
            "risk_tolerance": "High — long horizon, comfortable with volatility",
            "interests": ["Passive / ETF investing", "Crypto (curious)", "Saving for a first apartment", "Tech & startups"],
            "hobbies": ["Mountain biking", "Climbing", "Travel", "Following tech startups"],
            "favourite_drink": "Craft beer; an oat-milk flat white",
            "personality": "Curious, time-poor and digital-first; learns by doing and prefers short, "
                           "plain-language explanations.",
            "household": {"parents": ["Hans Mueller (65)", "Margrit Mueller (62)"]},
            "life_events": [
                {"date": "2021-11", "event": "Received CHF 200k family gift; opened a sub-account with The Bank."},
                {"date": "2025-09", "event": "Mentioned (via father) an interest in saving for a first apartment."},
            ],
            "last_review": "None — no direct advisory relationship yet",
            "open_tasks": ["KYC refresh due (source-of-wealth & ID re-verification via IDnow)"],
            "engagement_note": "Disengaged: 2 logins in 30 days, no deposits in 90 days, no savings "
                               "goal, no advisory mandate, and no direct RM relationship. This is the "
                               "at-risk next-generation asset.",
        },
    }


# ---------------------------------------------------------------------------
# Spouse — Margrit Mueller, 62 (conservative; gives the Advisor Co-Pilot the
# complete family database, incl. data "about the wife").
# ---------------------------------------------------------------------------
def _build_spouse() -> dict:
    holdings = [
        {"name": "iShares Global Govt Bond ETF", "ticker": "IGLO", "asset_class": "Bonds", "value_chf": 1_360_000},
        {"name": "Vanguard FTSE All-World ETF", "ticker": "VWRL", "asset_class": "Equity funds", "value_chf": 1_020_000},
        {"name": "UBS (CH) Property Fund - Swiss Mixed", "ticker": "UBS-SM", "asset_class": "Real estate", "value_chf": 408_000},
        {"name": "CHF current account", "ticker": "CASH-CHF", "asset_class": "Cash", "value_chf": 612_000},
    ]
    holdings, total = _finalize_holdings(holdings)  # 3,400,000
    cashflows = [(date(2019, 3, 1), -3_000_000.0), (AS_OF, +total)]
    net_contributions = 3_000_000
    net_gain = total - net_contributions
    irr = xirr(cashflows)
    return {
        "owner": "Margrit Mueller",
        "as_of": AS_OF_STR,
        "currency": "CHF",
        "risk_profile": "Conservative",
        "mandate_type": "Advisory mandate (conservative)",
        "benchmark": "Custom 60/30/10 (Bonds / Equities / Real estate)",
        "relationship_since": 2019,
        "total_value_chf": total,
        "holdings": holdings,
        "asset_allocation": _allocation_from_holdings(holdings, total),
        "digital_asset_sleeve": _digital_sleeve(holdings, total),
        # Suitability policy block (paper §4.3). Conservative profile keeps a
        # larger liquidity buffer, so her cash ceiling is wider; at seed the
        # holdings sit on target, so the spouse is IN policy.
        "policy": {
            "risk_profile": "Conservative",
            # Slightly off target at seed: she holds 18% cash vs a 16% target/ceiling,
            # which produces one light drift flag and one light cash flag for the advisor.
            "target_allocation": {"Bonds": 41, "Equity funds": 31, "Real estate": 12, "Cash": 16},
            "limits": {"concentration_limit_pct": 15, "cash_floor_pct": 5,
                       "cash_ceiling_pct": 16, "da_vol_budget_pct": 0},
            "goals": [
                {"name": "Family foundation endowment", "target_chf": 400_000, "saved_chf": 300_000},
                {"name": "Travel & arts fund", "target_chf": 120_000, "saved_chf": 96_000},
            ],
        },
        "performance_annual": [
            {"year": "2019", "portfolio_pct": 8.2, "benchmark_pct": 9.0},
            {"year": "2020", "portfolio_pct": 4.1, "benchmark_pct": 4.5},
            {"year": "2021", "portfolio_pct": 6.0, "benchmark_pct": 7.0},
            {"year": "2022", "portfolio_pct": -6.5, "benchmark_pct": -8.0},
            {"year": "2023", "portfolio_pct": 6.8, "benchmark_pct": 7.5},
            {"year": "2024", "portfolio_pct": 5.2, "benchmark_pct": 6.0},
            {"year": "2025", "portfolio_pct": 6.4, "benchmark_pct": 7.0},
            {"year": "2026 YTD", "portfolio_pct": 2.1, "benchmark_pct": 2.4},
        ],
        "net_return": {
            "inception_date": "2019-03-01",
            "net_contributions_chf": net_contributions,
            "current_value_chf": total,
            "cumulative_net_gain_chf": net_gain,
            "simple_net_return_pct": round(net_gain / net_contributions * 100.0, 1),
            "annualised_return_irr_pct": round(irr * 100.0, 1),
            "total_fees_paid_since_inception_chf": 74_000,
            "basis": "Net of fees; money-weighted (XIRR) since 2019-03-01.",
        },
        "trades": [
            {"date": "2019-03-05", "side": "BUY", "instrument": "iShares Global Govt Bond ETF", "amount_chf": 1_300_000},
            {"date": "2019-03-05", "side": "BUY", "instrument": "Vanguard FTSE All-World ETF", "amount_chf": 900_000},
            {"date": "2022-11-10", "side": "BUY", "instrument": "UBS (CH) Property Fund - Swiss Mixed", "amount_chf": 400_000},
        ],
        "fees": {
            "advisory_fee_pct_pa": 0.30,
            "custody_fee_pct_pa": 0.15,
            "crypto_custody_fee_pct_pa": 0.0,
            "transaction_fees": "Brokerage at cost + 0.10%",
            "retrocessions": "None retained — open product architecture",
            "last_12m_fees_chf": 15_300,
        },
        "crm": {
            "occupation": "Patron of the family foundation; arts & culture",
            "domicile": "Munich, Germany (served cross-border; assets booked in CH)",
            "preferred_contact": "Phone & in person",
            "risk_tolerance": "Low — capital preservation",
            "interests": ["Arts patronage", "Opera", "Family foundation", "Travel"],
            "hobbies": ["Collecting modern art", "Opera & classical concerts", "Charity galas"],
            "favourite_drink": "Champagne on occasion; chamomile tea",
            "personality": "Warm, culturally engaged and philanthropic; cares about family legacy.",
            "household": {"spouse": "Hans Mueller (65)", "children": ["Lukas (32)"]},
            "life_events": [
                {"date": "2024-11", "event": "Co-leads early estate-planning discussions with Hans."},
            ],
            "last_review": "2026-02-04 (joint review with Hans, Zurich)",
            "open_tasks": [],
        },
    }


# ---------------------------------------------------------------------------
# Full family seed.
# ---------------------------------------------------------------------------
def _seed_score_history() -> list:
    """A rising monthly priority-score history (the risk has grown as Hans nears
    retirement while Lukas stayed disengaged). The live demo then bends it down."""
    months = [(2025, 6), (2025, 7), (2025, 8), (2025, 9), (2025, 10), (2025, 11),
              (2025, 12), (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5)]
    scores = [62, 63, 65, 66, 68, 69, 70, 72, 73, 74, 75, 75]
    out, prev = [], None
    for (y, mo), s in zip(months, scores):
        band = "high" if s >= 67 else ("medium" if s >= 40 else "low")
        out.append({"ts": f"{y}-{mo:02d}-28", "score": s, "band": band,
                    "reason": "Monthly assessment", "delta": (s - prev) if prev is not None else 0})
        prev = s
    return out


def seed_family() -> dict:
    """Return a fresh, deep-copied seed of the whole shared family state."""
    family = {
        "family_id": "mueller",
        "family_name": "Mueller",
        "members": {
            "principal": {
                "name": "Hans Mueller", "role": "principal", "age": 65,
                "domicile": "DE", "cross_border": True, "kyc_status": "ok",
                "avatar": "vater.png", "title": "Principal",
            },
            "spouse": {
                "name": "Margrit Mueller", "role": "spouse", "age": 62,
                "domicile": "DE", "cross_border": True, "kyc_status": "ok",
                "avatar": "Spouse.png", "title": "Spouse",
            },
            "heir": {
                "name": "Lukas Mueller", "role": "heir", "age": 32,
                "domicile": "DE", "cross_border": True, "kyc_status": "review",
                "avatar": "sohn.png", "title": "Heir",
            },
        },
        "rm": {"name": "Reto Wyss", "role": "Relationship Manager", "desk": "Cross-border DE / HNWI"},
        "portfolios": {
            "principal": _build_principal(),
            "spouse": _build_spouse(),
            "heir": _build_heir(),
        },
        "engagement": {
            "heir_logins_30d": 2,
            "heir_deposits_90d": 0,
            "heir_goals": [],
            "heir_has_rm_relationship": False,
            "heir_has_own_mandate": False,
            "heir_has_savings_plan": False,
            "principal_governance_intro_done": False,
            "last_rm_contact_days": 24,
            "principal_last_review_days": 115,
            # Per-member behaviour for the Engagement Score (the heir's is derived
            # live from the fields above). Hans is active, Margrit moderate.
            "members": {
                "principal": {"logins_30d": 7, "deposits_12m": 2, "goals": 2, "meetings_12m": 3, "depth": 0.8},
                "spouse": {"logins_30d": 4, "deposits_12m": 1, "goals": 2, "meetings_12m": 2, "depth": 0.6},
            },
        },
        "messages": [
            {
                "id": "m-seed-1", "from": "rm", "to": "principal",
                "text": "Sehr geehrter Herr Mueller, anbei die Q1-2026 Portfoliouebersicht. "
                        "Die Allokation liegt weiter im Zielband; gerne bespreche ich Details "
                        "bei unserem naechsten Termin.",
                "ts": "2026-05-08T10:15:00", "read": True,
            },
            {
                "id": "m-seed-2", "from": "principal", "to": "rm",
                "text": "Besten Dank, Reto. Mein Sohn Lukas beginnt sich fuer das Anlegen zu "
                        "interessieren - koennten Sie sich direkt bei ihm melden?",
                "ts": "2026-05-20T18:42:00", "read": False,
            },
        ],
        "meetings": [],
        "meeting_history": [
            {"date": "2026-02-04", "topic": "Q4-2025 portfolio review", "mode": "In person (Zurich)",
             "rm": "Reto Wyss", "attendees": ["principal", "spouse"],
             "summary": "Reviewed 2025 performance (+13.5%), rebalanced into the digital-asset sleeve, "
                        "and discussed retirement timing for end-2026."},
            {"date": "2025-09-18", "topic": "Mid-year review & cross-border check", "mode": "Video call",
             "rm": "Reto Wyss", "attendees": ["principal"],
             "summary": "Confirmed FIDLEG suitability documentation; Hans mentioned Lukas's growing "
                        "interest in investing."},
            {"date": "2024-11-12", "topic": "Estate-planning introduction", "mode": "In person (Zurich)",
             "rm": "Reto Wyss", "attendees": ["principal", "spouse"],
             "summary": "First succession & family-governance conversation; agreed to involve an "
                        "external notary."},
            {"date": "2021-11-20", "topic": "Sub-account opening (family gift)", "mode": "In person (Zurich)",
             "rm": "Reto Wyss", "attendees": ["heir", "principal"],
             "summary": "Opened Lukas's sub-account funded by a CHF 200k family gift; set up the "
                        "Meridian app and first ETF & crypto positions."},
        ],
        "nbas": [],            # generated by score.py
        "score_history": _seed_score_history(),  # seeded trend + appended on every recompute
        "activity_log": [],    # human-readable trail for the demo
    }
    return copy.deepcopy(family)


# Convenience: the at-risk AUM headline used in nudges/score drivers.
def principal_aum_chf() -> float:
    return float(seed_family()["portfolios"]["principal"]["total_value_chf"])
