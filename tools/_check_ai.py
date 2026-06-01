"""Verify the portfolio-chat guardrails + grounded mock answers (no API key)."""
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

fam = fixtures.seed_family()
p = fam["portfolios"]["principal"]
m = fam["members"]["principal"]

print("is_live():", gemini.is_live(), "| mode:", gemini.mode_label())
tests = [
    ("ON-TOPIC", "What has been my net return, including all trades, since I started?"),
    ("ON-TOPIC", "What is my asset allocation?"),
    ("ON-TOPIC", "What fees am I paying?"),
    ("OFF-TOPIC", "What is the S&P 500 going to do next quarter?"),
    ("OFF-TOPIC", "Should I buy more Nvidia stock?"),
    ("OFF-TOPIC", "What's the capital of France?"),
    ("OFF-TOPIC", "Give me a hot stock tip."),
]
ok = True
for kind, q in tests:
    r = gemini.portfolio_chat("principal", p, m, [], q)
    declined = r["mode"] == "guardrail"
    verdict = ("DECLINED" if declined else "ANSWERED")
    expected_decline = kind == "OFF-TOPIC"
    good = (declined == expected_decline)
    ok = ok and good
    flag = "OK " if good else "XX "
    print(f"\n{flag}[{kind} -> {verdict} · mode={r['mode']}]\n  Q: {q}\n  A: {r['text'][:150]}")

print("\nGUARDRAIL CHECK:", "PASSED" if ok else "FAILED")
