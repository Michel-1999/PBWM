"""Verify the configured Gemini key actually produces a live, grounded answer."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app import fixtures, gemini  # noqa: E402

print("is_live():", gemini.is_live(), "| mode:", gemini.mode_label())
fam = fixtures.seed_family()
p = fam["portfolios"]["principal"]
m = fam["members"]["principal"]
r = gemini.portfolio_chat(
    "principal", p, m, [],
    "What is my total portfolio value and my net return since inception?")
print("\n-> mode:", r["mode"])
if r.get("note"):
    print("-> note:", r["note"])
print("-> answer:\n", r["text"])
