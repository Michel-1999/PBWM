"""Verify the Client Strategy Monitor (paper §4.3): detection, shock, rebalance, reset.

No API key needed — the deterministic detection layer always works and the AI
narration falls back to templates. Mirrors tools/_check_family.py.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app import fixtures, gemini, score, state, strategy  # noqa: E402

# Force the OFFLINE deterministic path regardless of any local secrets.toml key,
# so (a)/(b) genuinely test the no-key behaviour.
gemini._api_key = lambda: None  # type: ignore[assignment]
assert gemini.is_live() is False


def fresh():
    fam = fixtures.seed_family()
    state._recompute_family(fam, "seed")
    return fam


def fits(fam):
    return {m: fam["health"][m]["policy_fit"] for m in fam["portfolios"]}


def holdings(fam, m):
    return [h["value_chf"] for h in fam["portfolios"][m]["holdings"]]


print("(a) deterministic detection runs with no key…")
fam = fresh()
assert isinstance(fam["alerts"], list) and isinstance(fam["health"], dict)
for m in fam["portfolios"]:
    h = strategy.portfolio_health(fam["portfolios"][m], fam["members"][m], fam["engagement"])
    assert 0 <= h["policy_fit"] <= 100
seed_breaches = [a for a in fam["alerts"] if a["severity"] == "breach"]
assert not seed_breaches, f"seed should have no breaches, got {seed_breaches}"
heir_drift = [a for a in fam["alerts"] if a["member"] == "heir" and a["category"] == "drift"]
assert heir_drift and heir_drift[0]["severity"] == "watch", "expected the heir's seed drift watch"
assert fits(fam)["principal"] == 100 and fits(fam)["spouse"] == 84 and fits(fam)["heir"] == 84
# Two light advisor-facing strategy recommendations at seed: one meeting, one message.
rm_flags = [a for a in fam["alerts"] if a["audience"] in ("rm", "both") and a["suggested_action"] != "none"]
assert any(a["member"] == "spouse" and a["category"] == "drift" and a["suggested_action"] == "request_meeting"
           for a in rm_flags), "expected a spouse drift meeting flag at seed"
assert any(a["member"] == "spouse" and a["category"] == "cash" and a["suggested_action"] == "send_message"
           for a in rm_flags), "expected a spouse cash message flag at seed"
print("    seed flags:", [(a["member"], a["category"], a["severity"]) for a in fam["alerts"]])

print("(b) narrate_alert + draft_alert_message return source='mock' with no key…")
a0 = fam["alerts"][0]
for aud in ("rm", "client"):
    r = gemini.narrate_alert(a0, aud, fam)
    assert r["source"] == "mock" and r["text"], f"narrate_alert({aud}) failed: {r}"
d = gemini.draft_alert_message(a0, fam)
assert d["source"] == "mock" and d["text"], f"draft_alert_message failed: {d}"
print("    narration ok (mock):", gemini.narrate_alert(a0, 'client', fam)["text"][:90], "…")

print("(c) +15% equity stress creates a drift breach and lowers strategy-fit…")
fam = fresh()
base = fits(fam)
state._shock_family(fam, 15)
state._recompute_family(fam)
drift_breaches = [a for a in fam["alerts"] if a["category"] == "drift" and a["severity"] == "breach"]
assert drift_breaches, "no drift breach after +15% shock"
target = drift_breaches[0]["member"]
assert fam["health"][target]["policy_fit"] < base[target], "strategy-fit did not fall"
print(f"    {target}: strategy-fit {base[target]} -> {fam['health'][target]['policy_fit']} "
      f"(drift {fam['health'][target]['checks']['drift']['metric']['total_drift_pp']}pp)")

print("(d) confirming a rebalancing meeting clears the breach, total unchanged…")
total_before = fam["portfolios"][target]["total_value_chf"]
mid = "mtg-test-rebal"
fam["meetings"].append({"id": mid, "with": target, "topic": "Portfolio rebalancing review",
                        "status": "requested", "proposed_ts": "", "note": "",
                        "requested_by": "rm", "created_ts": ""})
state._confirm_meeting_family(fam, mid)
assert fam["health"][target]["checks"]["drift"]["status"] == "ok", "drift not cleared by rebalance"
assert not [a for a in fam["alerts"] if a["category"] == "drift" and a["member"] == target], "drift flag remains"
total_after = fam["portfolios"][target]["total_value_chf"]
assert abs(total_after - total_before) < 1, f"rebalance changed total: {total_before} -> {total_after}"
assert fam["health"][target]["policy_fit"] >= base[target], "strategy-fit did not recover"
print(f"    {target}: drift cleared · strategy-fit back to {fam['health'][target]['policy_fit']} · "
      f"total {total_after:,.0f} (unchanged)")

print("(e) reset restores the exact pre-shock holdings…")
fam = fresh()
pre = {m: holdings(fam, m) for m in fam["portfolios"]}
state._shock_family(fam, 15, 5)
state._unshock_family(fam)
for m in fam["portfolios"]:
    post = holdings(fam, m)
    assert all(abs(x - y) < 1e-6 for x, y in zip(pre[m], post)), f"{m} not restored exactly"
print("    all holdings restored exactly")

print("(f) a heir deposit made BEFORE a shock survives a reset…")
fam = fresh()
heir = fam["portfolios"]["heir"]
for h in heir["holdings"]:
    if h["asset_class"] == "Cash":
        h["value_chf"] += 10_000
        break
fixtures.recompute_portfolio_derived(heir)
pre_heir = holdings(fam, "heir")
state._shock_family(fam, 20)
state._unshock_family(fam)
post_heir = holdings(fam, "heir")
assert all(abs(x - y) < 1e-6 for x, y in zip(pre_heir, post_heir)), "deposit was undone by reset"
print("    deposit preserved through shock + reset")

print("(g) heir life-goal flag is client-only and suppressed while the savings flow is open…")
fam = fresh()
fam["engagement"]["heir_goals"].append(
    {"id": "g1", "name": "First apartment", "target_chf": 100_000, "saved_chf": 10_000, "horizon_years": 6})
state._recompute_family(fam)
assert any(n["id"] == "nba-heir-savings" for n in fam["nbas"]), "savings NBA expected at seed"
assert not [a for a in fam["alerts"] if a["member"] == "heir" and a["category"] == "goal_gap"], \
    "heir goal_gap must be suppressed while the savings NBA is open"
eng = fam["engagement"]
eng["heir_deposits_90d"], eng["heir_has_savings_plan"], eng["heir_logins_30d"] = 2, True, 8
state._recompute_family(fam)
assert not any(n["id"] == "nba-heir-savings" for n in fam["nbas"]), "savings NBA should be gone"
gg = [a for a in fam["alerts"] if a["member"] == "heir" and a["category"] == "goal_gap"]
assert gg, "heir goal_gap should appear once the savings flow is resolved"
assert all(a["audience"] == "client" and a["suggested_action"] == "none" for a in gg), \
    "heir goal_gap must be client-only with no RM action"
assert not [a for a in gg if a["audience"] in ("rm", "both")], "no advisor-facing duplicate allowed"
print("    goal flag suppressed → then client-only, no advisor duplicate")

print("(h) the engagement hero flow still lowers the score…")
fam = fixtures.seed_family()
s0 = score.compute_score(fam)["score"]
eng = fam["engagement"]
eng["heir_goals"].append({"id": "g", "name": "Apartment", "target_chf": 100_000, "saved_chf": 20_000, "horizon_years": 6})
eng["heir_deposits_90d"], eng["heir_has_savings_plan"], eng["heir_logins_30d"] = 2, True, 8
s1 = score.compute_score(fam)["score"]
assert s1 < s0, f"engagement should lower the score: {s0} -> {s1}"
print(f"    engagement score {s0} -> {s1} (hero flow intact)")

print("\nALL CLIENT STRATEGY MONITOR CHECKS PASSED")
