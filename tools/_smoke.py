"""Dev smoke test (no Streamlit): validate fixtures, score, NBAs, mutations."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import fixtures, score  # noqa: E402


def line(s=""):
    print(s)


fam = fixtures.seed_family()
p = fam["portfolios"]["principal"]
h = fam["portfolios"]["heir"]

line("== PRINCIPAL ==")
line(f"total={p['total_value_chf']:,.0f}  sum_holdings={sum(x['value_chf'] for x in p['holdings']):,.0f}")
line(f"alloc_sum_pct={sum(a['weight_pct'] for a in p['asset_allocation']):.2f}  "
     f"holding_weights_sum={sum(x['weight_pct'] for x in p['holdings']):.2f}")
line(f"digital_sleeve={p['digital_asset_sleeve']['weight_pct']}%  "
     f"value={p['digital_asset_sleeve']['value_chf']:,.0f}")
nr = p["net_return"]
line(f"net: contrib={nr['net_contributions_chf']:,.0f} value={nr['current_value_chf']:,.0f} "
     f"gain={nr['cumulative_net_gain_chf']:,.0f} simple={nr['simple_net_return_pct']}% "
     f"irr={nr['annualised_return_irr_pct']}%")

line()
line("== HEIR ==")
line(f"total={h['total_value_chf']:,.0f}  sum_holdings={sum(x['value_chf'] for x in h['holdings']):,.0f}")
line(f"alloc_sum_pct={sum(a['weight_pct'] for a in h['asset_allocation']):.2f}")
line(f"cost_sum={sum(x['cost_basis_chf'] for x in h['holdings']):,.0f}  "
     f"value_sum={sum(x['value_chf'] for x in h['holdings']):,.0f}")
nrh = h["net_return"]
line(f"net: contrib={nrh['net_contributions_chf']:,.0f} value={nrh['current_value_chf']:,.0f} "
     f"gain={nrh['cumulative_net_gain_chf']:,.0f} simple={nrh['simple_net_return_pct']}% "
     f"irr={nrh['annualised_return_irr_pct']}%")

line()
line("== SCORE (initial) ==")
sc = score.compute_score(fam)
line(f"score={sc['score']}  band={sc['band_label']}  engagement_index={sc['engagement_index']}")
line(f"components={sc['components']}")
line(f"weighted={sc['weighted_contributions']}")
for d in sc["drivers"]:
    line(f"  - {d}")
line("NBAs: " + ", ".join(f"{n['priority']}:{n['id']}->{n['target']}" for n in score.generate_nbas(fam)))

line()
line("== SIMULATE HERO FLOW (manual mutation) ==")
fam["engagement"]["heir_goals"].append({"name": "First apartment", "target_chf": 150000, "saved_chf": 0})
fam["engagement"]["heir_logins_30d"] = 5
fam["engagement"]["heir_deposits_90d"] = 1
fam["engagement"]["heir_has_savings_plan"] = True
fam["engagement"]["heir_has_rm_relationship"] = True
fam["engagement"]["last_rm_contact_days"] = 0
fam["engagement"]["principal_governance_intro_done"] = True
sc2 = score.compute_score(fam)
line(f"score_after={sc2['score']}  band={sc2['band_label']}  (delta={sc2['score']-sc['score']})")
line(f"components_after={sc2['components']}")
line("NBAs_after: " + ", ".join(f"{n['id']}" for n in score.generate_nbas(fam)))

print("\nALL CHECKS RAN OK")
