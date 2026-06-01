"""Verify the family-wide Advisor Co-Pilot (whole-family DB) + guardrail."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app import fixtures, gemini, score  # noqa: E402

fam = fixtures.seed_family()
fam["current_score"] = score.compute_score(fam)
fam["nbas"] = score.generate_nbas(fam)

print("is_live:", gemini.is_live())
for q in [
    "What did we discuss in the last meeting and what is the family's strategy so far?",
    "What are Hans's hobbies and what does he like to drink?",
    "What is the S&P 500 going to do next quarter?",  # must decline
]:
    r = gemini.advisor_chat(fam, [], q)
    print(f"\n[{r['mode']}] Q: {q}\n  {r['text'][:280]}")
