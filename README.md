# The Bank — Meridian AI Prototype

An interactive **appendix artefact** for a University of St.Gallen examination paper
(course 8,182 *Private Banking and Wealth Management*). It makes three AI use cases
tangible for a fictional family-owned Swiss private bank, **"The Bank"**.

The branding runs through the prototype as follows:

- **Meridian** — the platform by The Bank (clients and the relationship manager).
  Its built-in AI assistant is surfaced as **Meridian (AI)** (chat + recommendations).
- **Dashboards** — clients use **My Wealth Intelligence**, the relationship
  manager uses the **Advisor Wealth Intelligence**, both *powered by Meridian*.

> Prototype only · synthetic data · illustrative AI output · **not investment advice**.

---

## Run locally

```bash
cd the-bank-prototype
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # optional, for live AI
streamlit run streamlit_app.py
```

Open **http://localhost:8501**. If 8501 is busy: `streamlit run streamlit_app.py --server.port 8502`.

**It runs with zero setup.** Without a Gemini key, Meridian's AI answers in a
clearly labelled **offline mock mode**. For live answers, paste a free key into
`.streamlit/secrets.toml` as `GEMINI_API_KEY` (locally) or into the app's
**Settings → Secrets** (on Streamlit Community Cloud).

Get a free key (no credit card) at <https://aistudio.google.com> → *Get API key*.

---

## Publishing to GitHub (it's safe)

- **No secrets are committed.** `.streamlit/secrets.toml`, `*.env`, `*.key` and
  `family_state.json` are in `.gitignore`. Only `secrets.toml.example` (a
  placeholder) is tracked. **Never commit your real `secrets.toml`.**
- **The app works for everyone** who clones it: it starts in mock mode, and live
  Meridian (AI) is enabled when a `GEMINI_API_KEY` is configured in secrets.
- **Adobe Fonts** ("Mendl Serif") loads via an Adobe *web project* kit id, which
  is **public by design** (it appears in the page source of any site using it),
  so it is fine to keep in the code. If the kit is unavailable, the UI falls back
  to Georgia automatically. Override the kit id via `ADOBE_FONTS_KIT_ID` in
  secrets if you use your own Adobe account.
- **Profile/asset images** live in `assets/`. They are fictional; replace freely.

### Deploy a public, password-protected demo (optional)

Push to GitHub, then on **Streamlit Community Cloud** (free) create an app from the
repo with **Main file path: `streamlit_app.py`**. In the app's **Settings → Secrets**
add (never in the code):

```
GEMINI_API_KEY = "your-free-key"
APP_PASSWORD   = "a-password-you-choose"
```

With `APP_PASSWORD` set, visitors must enter the password before the app opens, so it
is safe to embed your own key for an exam window (delete the app and/or rotate the key
afterwards). Without `APP_PASSWORD` the app is open, and the sidebar "bring your own
key" option lets visitors use their own key. The repo itself can be **private**;
Streamlit Cloud still deploys it and the app URL stays publicly reachable.

---

## The idea — one coupled system

The prototype follows the **Müller family** across four workspaces that share one
live state (`st.session_state`), wired with `st.navigation`:

| Workspace | Use case | Role |
|---|---|---|
| **Reto Wyss (Advisor)** | 4.1 Advisor Co-Pilot | Advisor Wealth Intelligence: family briefing, score, next-best-actions, calendar |
| **Hans Müller (Principal)** | 4.2 Personal Wealth OS | My Wealth Intelligence dashboard + Meridian (AI) |
| **Margrit Müller (Spouse)** | 4.2 Personal Wealth OS | Same platform, her own design + offers |
| **Lukas Müller (Son)** | 4.2 Personal Wealth OS | Next-gen: goals, deposits, Meridian (AI) |

**The hero flow (runs live):** the Son sets a goal / deposits → the rule-based
heir's **Engagement Score** rises and the family **Inheritance Score** falls (at-risk AUM falls) → the Advisor
sees the new score + an AI **next-best-action** → sends a meeting request → the
Son confirms → the score and every dashboard update together.

---

## Project structure

```
the-bank-prototype/
├── streamlit_app.py                  # entry / router (st.navigation, theme, shared state)
├── views/                  # one script per workspace
│   ├── instructions.py     # Prototype Instructions (landing)
│   ├── rm.py               # Advisor Wealth Intelligence (Reto Wyss) — 4.1
│   ├── principal.py        # My Wealth Intelligence — Hans (4.2)
│   ├── spouse.py           # My Wealth Intelligence — Margrit (4.2)
│   └── heir.py             # My Wealth Intelligence — Lukas (4.2)
├── app/
│   ├── bank_profile.py     # fixed facts about The Bank
│   ├── fixtures.py         # Müller family data (reconciles by construction) + strategy + meeting history
│   ├── state.py            # shared state + mutator helpers
│   ├── score.py            # rule-based Engagement Scores + Inheritance Score + NBAs (§4.1/4.2)
│   ├── strategy.py         # rule-based Client Strategy Monitor + flags (§4.3)
│   ├── gemini.py           # grounded, guardrailed Meridian AI layer (+ mock mode)
│   ├── dashboard.py        # shared configurable client dashboard
│   └── ui.py               # brand theme (CSS) + reusable components
├── .streamlit/             # config.toml (theme) + secrets.toml.example
├── assets/                 # logos (SVG) + profile photos
├── tools/                  # dev checks (_verify, _check_family, _check_advisor, …)
├── requirements.txt
└── README.md
```

### Data integrity
Holding weights and allocations are derived from holding values; the annualised
"net return incl. all trades" is the money-weighted XIRR of the dated cash flows.
Family total: Hans CHF 22.4m + Margrit CHF 3.4m + Lukas CHF 0.28m = **CHF 26.08m**.

### Developer checks
```powershell
.venv\Scripts\python.exe tools\_verify.py         # pages render + hero flow
.venv\Scripts\python.exe tools\_check_family.py   # totals + scenario math
.venv\Scripts\python.exe tools\_check_advisor.py  # Meridian AI context + guardrail (needs a key for live)
.venv\Scripts\python.exe tools\_check_strategy.py # Client Strategy Monitor: detection, stress test, rebalance, reset
```

---

## How each feature maps to the paper

| Prototype feature | Paper | Concept |
|---|---|---|
| Advisor Wealth Intelligence (Meridian AI) | §4.1 | RM efficiency; "high tech and high touch" |
| My Wealth Intelligence (Meridian) | §4.2 | One configurable platform, two+ generations |
| Client Strategy Monitor + market simulator | §4.3 | Continuous strategy-adherence monitoring; rule engine detects, Meridian AI explains |
| Engagement Scores + Inheritance Score + drivers | §4 | Generational wealth transfer; AUM retention |
| Next-best-actions by Meridian (AI) | §4 | Proactive, data-driven advisory |
| Engagement engine (goals/deposits move the score) | §1, §7 | Engaging heirs 10–15 years early |
| Discreet, personalised offers/nudges | §7 | "Discreet, highly personalised, not intrusive" |
| Confined portfolio chat ("net return incl. all trades") | §5a | Transparency under open architecture |
| Guardrails (declines market/forecasts/tax/general) | §5a | Suitability & conduct |
| Cross-border alert in the AI briefing | §5b | FIDLEG / German cross-border |
| Digital-asset sleeve | §0 | Crypto via Swiss partners (differentiator) |
| Swiss-hosted Unique simulated by Gemini | §0 | Data sovereignty / banking secrecy |
| Brand identity (#1F4F39, Mendl Serif, pediment) | §8 | Trusted-Advisor brand made visible |

---

## Academic integrity & disclaimers
Prototype for an academic appendix, not a product. All persons and figures are
**fictional and synthetic**. AI output is illustrative and **not investment, tax
or legal advice**. The engagement and inheritance scores are a transparent rule engine, not the
LLM. In production the AI would run on the Swiss-hosted **Unique** platform; here
it is simulated with Google Gemini, with AI use declared as required.
