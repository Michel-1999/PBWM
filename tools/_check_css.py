"""Confirm inject_brand emits a raw <style> block starting at column 0."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import streamlit as st  # noqa: E402

captured = []
st.markdown = lambda body, **k: captured.append(body)  # type: ignore

from app import ui  # noqa: E402

ui.inject_brand()
print("calls captured:", len(captured))
for i, c in enumerate(captured):
    first = c.lstrip("\n")[:50]
    print(f"[{i}] starts with: {first!r}")
    print(f"    leading-space lines? ", any(ln.startswith(("    ", "\t")) and ln.strip() for ln in c.splitlines()[:6]))
