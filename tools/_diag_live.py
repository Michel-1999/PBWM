"""Diagnose why live Gemini calls may fall back to mock."""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app import fixtures, gemini  # noqa: E402

fam = fixtures.seed_family()
p = fam["portfolios"]["principal"]
m = fam["members"]["principal"]

print("is_live:", gemini.is_live(), "| model:", gemini.MODEL_NAME)

# 1) Raw call — surface the real exception if any
ctx = gemini.context_block(p, m)
sysinst = gemini._chat_system_instruction("principal", ctx)
print("\n[Raw _generate test]")
try:
    txt = gemini._generate(sysinst, [], "What is my total portfolio value?", gemini.MODEL_NAME)
    print("RAW OK:", txt[:120])
except Exception as exc:  # noqa: BLE001
    print("RAW EXCEPTION:", type(exc).__name__, str(exc)[:400])

# 2) Rapid repeated chat calls — detect rate limiting
print("\n[Rapid portfolio_chat x6]")
for i in range(6):
    r = gemini.portfolio_chat("principal", p, m, [], "Summarise my asset allocation briefly.")
    print(f"  {i+1}: mode={r['mode']:9s} note={r.get('note','')[:80]}")
    time.sleep(0.5)

# 3) Briefing call
print("\n[Briefing]")
sc = __import__("app.score", fromlist=["compute_score"]).compute_score(fam)
rb = gemini.briefing(p, m, sc)
print("  mode:", rb["mode"], "note:", rb.get("note", ""))
