"""Headless end-to-end verification with Streamlit's AppTest (views/ layout)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from streamlit.testing.v1 import AppTest  # noqa: E402


def run(path, family=None):
    at = AppTest.from_file(path, default_timeout=60)
    if family is not None:
        at.session_state["family"] = family
    at.run()
    assert not at.exception, f"{path} raised: {at.exception}"
    return at


print("1) Render checks (mock mode)…")
run("views/instructions.py"); print("   instructions OK")
run("views/principal.py"); print("   principal OK")
run("views/spouse.py"); print("   spouse OK")
run("views/heir.py"); print("   heir OK")
rm = run("views/rm.py"); print("   rm OK")

print("2) Hero flow…")
fam0 = rm.session_state["family"]
score0 = fam0["current_score"]["score"]
assert "nba-heir-savings" in [n["id"] for n in fam0["nbas"]], "savings NBA missing"

for b in rm.button:
    if b.key == "nba_nba-heir-savings":
        b.click(); break
rm.run()
fam1 = rm.session_state["family"]
assert any(m["with"] == "heir" and m["status"] == "requested" for m in fam1["meetings"]), "meeting not requested"
print("   RM sent meeting request · score =", fam1["current_score"]["score"])

heir = run("views/heir.py", family=fam1)
mid = [m for m in fam1["meetings"] if m["with"] == "heir"][0]["id"]
for b in heir.button:
    if b.key == f"cf_{mid}":
        b.click(); break
heir.run()
fam2 = heir.session_state["family"]
assert any(m["with"] == "heir" and m["status"] == "confirmed" for m in fam2["meetings"]), "meeting not confirmed"
score2 = fam2["current_score"]["score"]
print("   Heir confirmed meeting · score =", score2)
assert score2 < score0, f"score should fall: {score0} -> {score2}"

run("views/rm.py", family=fam2)  # RM reflects shared state
print(f"\nHERO FLOW OK · score {score0} -> {score2} (delta {score2 - score0})")
print("ALL VERIFICATION PASSED")
