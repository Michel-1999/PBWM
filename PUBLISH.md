# How to publish this prototype (password-protected) — step by step

Target repo: `Michel-1999/PBWM`. Goal: a password-protected Streamlit web app that
uses your own Gemini key (which you delete/rotate after the exam window).

## What is safe (verified)
- Your Gemini key is **only** in `.streamlit/secrets.toml`, which is git-ignored.
- `.gitignore` excludes `secrets.toml`, `.venv/`, `__pycache__/`, `family_state.json`.
- No key is hard-coded anywhere in the code.

## NEVER upload these
- `.streamlit/secrets.toml`  (your key!)
- `.venv/`  (huge, machine-specific)
- `__pycache__/`, `family_state.json`

> Tip: use **GitHub Desktop** (or git), which respect `.gitignore`. Do **not** use
> the github.com browser "Upload files" button — it ignores `.gitignore`.

---

## Step A — Put the project into your PBWM repo (GitHub Desktop)
1. Install **GitHub Desktop** (https://desktop.github.com) and sign in.
2. **File → Clone repository →** select `Michel-1999/PBWM` → clone to e.g. `Documents\PBWM`.
3. In Windows Explorer, copy **everything inside** `the-bank-prototype\` into the
   cloned `PBWM` folder **except** the `.venv` folder, overwriting the template
   `streamlit_app.py` and `README.md` when asked. (Make sure hidden files like
   `.gitignore` and the `.streamlit\` folder are copied too — enable
   "View → Hidden items" in Explorer.)
4. Back in **GitHub Desktop**, review the **Changes** list and confirm that
   `.streamlit/secrets.toml` and `.venv` are **NOT** listed. (They won't be, thanks
   to `.gitignore`.)
5. Enter a summary (e.g. "Meridian prototype") → **Commit to main** → **Push origin**.
6. (Recommended) On github.com → repo **Settings → General → Danger Zone →
   Change visibility → Private**. The app will still deploy.

## Step B — Deploy the web app (Streamlit Community Cloud)
1. Go to https://share.streamlit.io and sign in with GitHub (allow access to PBWM).
2. **Create app → Deploy from repo:** repo `Michel-1999/PBWM`, branch `main`,
   **Main file path: `streamlit_app.py`** → **Deploy**.
3. Open the app's **Settings → Secrets** and add both values:
   ```
   APP_PASSWORD   = "HSG2026"
   GEMINI_API_KEY = "your-free-key"
   ```
   Save. The login screen then asks only for the **password**; the embedded key powers
   live Meridian (AI) for everyone who has the URL and the password.
4. Share the app URL and the password (**HSG2026**) with your examiner.

## Step C — After the exam window (~2 months)
- Delete the app in Streamlit Cloud (or set it to sleep), and/or
- Rotate/delete the Gemini key in Google AI Studio, and/or
- Remove `GEMINI_API_KEY` from the app's Secrets.

## Notes
- The repo can be private; the deployed app URL is still publicly reachable, but the
  `APP_PASSWORD` gate protects it.
- Heavy use shares your free Gemini quota; if it rate-limits, Meridian shows a grounded
  offline answer and recovers automatically.
- Local development stays open (no `APP_PASSWORD` in your local `secrets.toml`).
