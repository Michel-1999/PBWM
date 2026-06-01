"""Check family data totals reconcile and scenario projection math is sane."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app import fixtures  # noqa: E402

fam = fixtures.seed_family()
grand = 0.0
for k, p in fam["portfolios"].items():
    hsum = sum(h["value_chf"] for h in p["holdings"])
    alloc = sum(a["weight_pct"] for a in p["asset_allocation"])
    nr = p["net_return"]
    assert abs(hsum - p["total_value_chf"]) < 1, f"{k}: holdings != total"
    assert abs(alloc - 100.0) < 0.2, f"{k}: alloc {alloc}"
    assert abs(nr["current_value_chf"] - p["total_value_chf"]) < 1, f"{k}: net_return value mismatch"
    print(f"  {k:9s} total={p['total_value_chf']:>12,.0f}  alloc%={alloc:6.2f}  "
          f"irr={nr['annualised_return_irr_pct']:+.1f}%  digital={p['digital_asset_sleeve']['weight_pct']}%")
    grand += p["total_value_chf"]
print(f"  FAMILY TOTAL = CHF {grand:,.0f}")


def proj(start, ann_pct, contrib, years):
    r = (1 + ann_pct / 100.0) ** (1 / 12) - 1
    v = start
    for _ in range(years * 12):
        v = v * (1 + r) + contrib
    return v


print("\nScenario projection sanity (start 280k, 5%/yr, 500/mo, 15y):")
end = proj(280_000, 5.0, 500.0, 15)
invested = 280_000 + 500 * 12 * 15
print(f"  end={end:,.0f}  invested={invested:,.0f}  growth={end-invested:,.0f}")
# zero-return sanity: end should equal invested when return = 0
z = proj(280_000, 0.0, 500.0, 15)
assert abs(z - invested) < 1, f"zero-return projection should equal invested, got {z}"
print(f"  zero-return check OK (end={z:,.0f} == invested={invested:,.0f})")
print("\nFAMILY DATA + SCENARIO OK")
