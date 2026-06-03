"""Brand theme + reusable UI components (paper §8).

Platform brand: **Meridian** (the client & RM platform), by **The Bank**.
The AI assistant is part of Meridian (chat + recommendations); it is surfaced as
"Meridian AI".

Typography is the Adobe Fonts serif **mendl-serif-dusk** (kit fgs4ozu):
  600 → main wordmark · 300 → secondary logo · 400 → headings · 200 → body text.
Graceful fallback to Georgia if the kit fails to load.
"""

from __future__ import annotations

import base64
import html
import io
import os
import textwrap
from datetime import datetime

import streamlit as st

from app.bank_profile import BANK_TAGLINE, DISCLAIMER_SHORT

# Default Adobe Fonts kit (public id; overridable via secrets).
DEFAULT_KIT_ID = "fgs4ozu"
FONT_FAMILY = "mendl-serif-dusk"

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------
PALETTE = {
    "green": "#1F4F39",
    "green_dark": "#163A2A",
    "tint": "#EAF1ED",
    "tint_deep": "#D6E2DB",
    "gold": "#C9A24B",
    "bg": "#FAFAF8",
    "ink": "#1A1A1A",
    "muted": "#3C5A4B",      # dark green (readable) — not grey
    "hairline": "#E2E2DC",
    "alert": "#9C3B2E",
}

ACCENTS = {
    "Pine (default)": "#1F4F39",
    "Slate blue": "#34577C",
    "Burgundy": "#7C3340",
    "Teal": "#176B63",
    "Gold": "#B8860B",
    "Graphite": "#3A3A3A",
}

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_BANK_LOGO = os.path.join(_ASSETS, "The Bank Logo.svg")
_MERIDIAN_LOGO = os.path.join(_ASSETS, "Meridian Logo.svg")

_ROLE_NAME = {"rm": "Mr. Reto Wyss", "principal": "Hans Müller",
              "spouse": "Margrit Müller", "heir": "Lukas Müller"}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def money(x: float, currency: str = "CHF") -> str:
    x = float(x)
    if abs(x) >= 1_000_000:
        return f"{currency} {x / 1e6:.1f}m"
    if abs(x) >= 10_000:
        return f"{currency} {x / 1e3:.0f}k"
    return f"{currency} {x:,.0f}"


def money_full(x: float, currency: str = "CHF") -> str:
    return f"{currency} {float(x):,.0f}"


def pct(x: float) -> str:
    return f"{x:+.1f}%"


def _esc(text: str) -> str:
    return html.escape(str(text)).replace("\n", "<br>")


# ---------------------------------------------------------------------------
# Assets: data URIs, logos, resized avatars
# ---------------------------------------------------------------------------
def _data_uri(path: str) -> str | None:
    try:
        if not os.path.exists(path):
            return None
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "svg": "svg+xml"}.get(ext, "png")
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        return f"data:image/{mime};base64,{b64}"
    except Exception:
        return None


_avatar_cache: dict = {}


def _avatar_uri(filename: str, px: int = 192) -> str | None:
    """Center-crop + resize a portrait to a small square data URI (perf)."""
    path = os.path.join(_ASSETS, filename)
    if not os.path.exists(path):
        return None
    try:
        key = (path, os.path.getmtime(path), px)
        if key in _avatar_cache:
            return _avatar_cache[key]
        from PIL import Image

        img = Image.open(path).convert("RGB")
        w, h = img.size
        s = min(w, h)
        img = img.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
        img = img.resize((px, px), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=84)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        _avatar_cache[key] = uri
        return uri
    except Exception:
        return _data_uri(path)


def _svg_pediment(fill: str, accent: str, h: int = 40) -> str:
    return (f'<svg viewBox="0 0 120 96" height="{h}" role="img" aria-label="The Bank">'
            f'<polygon points="60,6 114,48 6,48" fill="{fill}"/>'
            f'<text x="60" y="44" text-anchor="middle" font-family="Georgia,serif" '
            f'font-size="36" font-weight="700" fill="{accent}">B</text>'
            f'<rect x="6" y="52" width="108" height="7" fill="{fill}"/>'
            f'<rect x="8" y="88" width="104" height="6" fill="{fill}"/></svg>')


def _logo_img(path: str, h: int) -> str:
    uri = _data_uri(path)
    if uri:
        return f'<img src="{uri}" height="{h}" style="display:inline-block;vertical-align:middle" alt="logo"/>'
    return _svg_pediment("#FFFFFF", PALETTE["green"], h)


def _plate(inner: str) -> str:
    return (f'<span style="background:#fff;border-radius:8px;padding:6px 11px;'
            f'display:inline-flex;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,.18)">{inner}</span>')


def bank_logo(h: int = 42, plate: bool = False) -> str:
    img = _logo_img(_BANK_LOGO, h)
    return _plate(img) if plate else img


def meridian_logo(h: int = 24, plate: bool = False) -> str:
    img = _logo_img(_MERIDIAN_LOGO, h)
    return _plate(img) if plate else img


def logo_html(h: int = 42, on_dark: bool = True) -> str:  # back-compat
    return bank_logo(h)


def avatar_html(path: str | None, initials: str, size: int = 96, ring: str | None = None) -> str:
    ring = ring or "var(--tb-green)"  # follows the active accent unless overridden
    uri = _avatar_uri(path, px=max(96, size * 2)) if path else None
    common = (
        f"width:{size}px;height:{size}px;border-radius:50%;"
        f"border:3px solid {ring};box-shadow:0 1px 4px rgba(0,0,0,.16);"
        "display:inline-flex;align-items:center;justify-content:center;"
        "overflow:hidden;flex:0 0 auto;background:#fff;vertical-align:middle;"
    )
    if uri:
        return (f'<span style="{common}">'
                f'<img src="{uri}" style="width:100%;height:100%;object-fit:cover"/></span>')
    fs = max(12, int(size * 0.36))
    return (f'<span style="{common}background:{PALETTE["tint"]};color:var(--tb-green);'
            f'font-family:Georgia,serif;font-weight:600;font-size:{fs}px;">{_esc(initials)}</span>')


def avatar(path: str | None, initials: str, size: int = 96) -> None:
    st.markdown(avatar_html(path, initials, size), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Theme injection (CSS)
# ---------------------------------------------------------------------------
def _kit_id() -> str:
    try:
        kit = str(st.secrets.get("ADOBE_FONTS_KIT_ID", "") or "")
    except Exception:
        kit = ""
    return kit or DEFAULT_KIT_ID


def inject_brand() -> None:
    kit = _kit_id()
    typekit = f'<link rel="stylesheet" href="https://use.typekit.net/{kit}.css">' if kit else ""
    P = PALETTE
    ff = f'"{FONT_FAMILY}", Georgia, "Times New Roman", serif'
    if typekit:
        st.markdown(typekit, unsafe_allow_html=True)
    st.markdown(
        textwrap.dedent(f"""
        <style>
        :root {{
          --tb-green:{P['green']}; --tb-green-dark:{P['green_dark']};
          --tb-tint:{P['tint']}; --tb-gold:{P['gold']};
          --tb-ink:{P['ink']}; --tb-muted:{P['muted']}; --tb-hairline:{P['hairline']};
          --tb-serif:{ff};
        }}

        /* Everything in the brand serif */
        html, body, [class*="css"], .stMarkdown, p, li, label, span, div, input, textarea, select,
        button, [data-testid="stWidgetLabel"] {{ font-family:var(--tb-serif); color:var(--tb-ink); }}

        /* body text */
        body, p, li, .stMarkdown,
        .tb-chat-text, .tb-metric-sub, .tb-offer .b {{ font-weight:300; }}
        /* captions: dark + a touch heavier so they read clearly on white */
        .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
        [data-testid="stCaptionContainer"] span {{ color:#313D37 !important; font-weight:400 !important; }}

        /* 400 → headings & figures */
        h1, h2, h3, h4, .brand-serif,
        [data-testid="stHeading"] h1, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3,
        .tb-pediment .txt, .tb-metric-value, .tb-offer .h, .tb-ai-head .t, .tb-header .tb-title {{
          font-family:var(--tb-serif) !important; font-weight:400; color:var(--tb-green) !important; letter-spacing:.2px; }}
        .tb-metric-label, .tb-chip, .tb-chat-who {{ font-weight:400; }}

        /* 300 → secondary wordmark · 600 → main wordmark */
        .tb-wordmark {{ font-weight:300; }}
        .tb-wordmark-main {{ font-weight:600; }}

        .block-container {{ padding-top:1.3rem; padding-bottom:2rem; max-width:1180px; }}

        /* Header lintel */
        .tb-header {{ background:var(--tb-green); color:#fff; border-radius:8px; padding:16px 22px;
          margin:0 0 16px 0; display:flex; align-items:center; gap:18px;
          box-shadow:0 3px 10px rgba(22,58,42,.18); border-bottom:4px solid var(--tb-gold); }}
        .tb-header .tb-title {{ font-size:1.5rem; line-height:1.1; color:#fff !important; margin:0; }}
        .tb-header .tb-sub {{ color:#EAF2EC; font-size:.86rem; font-weight:300; margin-top:3px; }}
        .tb-header-right {{ margin-left:auto; text-align:right; display:flex; align-items:center; gap:12px; }}
        .tb-wordmark {{ font-size:1.2rem; letter-spacing:3px; color:#fff; text-transform:uppercase; }}

        /* Pediment section header */
        .tb-pediment {{ display:flex; align-items:center; gap:10px; margin:18px 0 8px; }}
        .tb-pediment .tri {{ width:0;height:0;border-left:9px solid transparent;
          border-right:9px solid transparent;border-bottom:14px solid var(--tb-green); }}
        .tb-pediment .txt {{ font-size:1.22rem; color:var(--tb-green); }}
        .tb-pediment .rule {{ flex:1; height:1px; background:var(--tb-hairline); margin-left:6px; }}

        /* Cards */
        .tb-card {{ background:#fff; border:1px solid var(--tb-hairline); border-radius:8px;
          padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.04); height:100%; }}
        .tb-card.accent {{ border-top:3px solid var(--tb-green); }}
        .tb-metric-label {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.6px;
          color:var(--tb-muted); margin-bottom:4px; }}
        .tb-metric-value {{ font-size:1.7rem; color:var(--tb-green); line-height:1.1; }}
        .tb-metric-sub {{ font-size:.8rem; color:var(--tb-muted); margin-top:3px; }}

        /* Chips */
        .tb-chip {{ display:inline-block; padding:2px 11px; border-radius:999px; font-size:.74rem;
          border:1px solid var(--tb-hairline); background:var(--tb-tint); color:var(--tb-green); margin:2px 5px 2px 0; }}
        .tb-chip.gold {{ background:#F6EDD7; color:#8A6D1F; border-color:#E4D3A3; }}
        .tb-chip.alert {{ background:#F4E4E1; color:{P['alert']}; border-color:#E2C3BD; }}
        .tb-chip.solid {{ background:var(--tb-green); color:#fff; border-color:var(--tb-green); }}

        /* Offer / nudge card */
        .tb-offer {{ background:linear-gradient(180deg,#fff,#FBFCFB); border:1px solid var(--tb-hairline);
          border-left:4px solid var(--tb-green); border-radius:8px; padding:15px 17px; margin:4px 0 8px;
          box-shadow:0 1px 3px rgba(0,0,0,.04); }}
        .tb-offer .tag {{ font-size:.66rem; text-transform:uppercase; letter-spacing:.8px; color:var(--tb-muted); margin-bottom:6px; }}
        .tb-offer .h {{ color:var(--tb-green); font-size:1.06rem; margin-bottom:4px; }}
        .tb-offer .b {{ font-size:.9rem; color:var(--tb-ink); line-height:1.45; }}

        /* AI panel header */
        .tb-ai-head {{ display:flex; align-items:center; gap:10px; margin:-4px -4px 8px -4px;
          padding:10px 14px; background:var(--tb-green); color:#fff; border-radius:7px; }}
        .tb-ai-head .t {{ font-size:1.05rem; color:#fff !important; }}
        .tb-ai-head .s {{ font-size:.74rem; color:#EAF2EC; margin-left:auto; font-weight:300; }}

        /* Chat bubbles */
        .tb-chat-ai {{ background:var(--tb-tint); border:1px solid #CBDAD1; border-left:4px solid var(--tb-green);
          border-radius:9px; padding:11px 14px; margin:7px 0; }}
        .tb-chat-user {{ background:#fff; border:1px solid var(--tb-hairline); border-radius:9px;
          padding:11px 14px; margin:7px 0 7px 48px; }}
        .tb-chat-human {{ background:#F8F2E3; border:1px solid #E4D3A3; border-left:4px solid var(--tb-gold);
          border-radius:9px; padding:11px 14px; margin:7px 0; }}
        .tb-chat-who {{ font-size:.68rem; text-transform:uppercase; letter-spacing:.6px; color:var(--tb-muted); margin-bottom:3px; }}
        .tb-chat-text {{ font-size:.94rem; color:var(--tb-ink); line-height:1.5; }}

        /* Profile (logged-in) strip */
        .tb-profile {{ display:flex; align-items:center; gap:11px; padding:6px 0 2px; }}
        .tb-profile .n {{ font-weight:400; color:var(--tb-ink); line-height:1.1; }}
        .tb-profile .r {{ font-size:.78rem; color:var(--tb-muted); }}

        /* Footer */
        .tb-footer {{ background:var(--tb-green); color:#FFFFFF; border-radius:8px; padding:14px 22px;
          margin-top:28px; border-top:4px solid var(--tb-gold); font-size:.8rem; display:flex;
          justify-content:space-between; gap:14px; flex-wrap:wrap; }}
        .tb-footer .wm {{ letter-spacing:2px; color:#fff; text-transform:uppercase; font-weight:600; }}

        /* Buttons — PRIMARY = green bg + WHITE text */
        button[data-testid^="stBaseButton"] {{ border-radius:6px; font-weight:400; padding:.46rem 1.05rem; }}
        button[data-testid^="stBaseButton-primary"] {{
          background:var(--tb-green) !important; color:#fff !important; border:1px solid var(--tb-green) !important; }}
        button[data-testid^="stBaseButton-primary"]:hover {{
          background:var(--tb-green-dark) !important; border-color:var(--tb-green-dark) !important; }}
        button[data-testid^="stBaseButton-primary"] *, button[data-testid^="stBaseButton-primary"] p {{ color:#fff !important; }}
        button[data-testid^="stBaseButton-secondary"] {{
          background:#fff !important; color:var(--tb-green) !important; border:1px solid var(--tb-green) !important; }}
        button[data-testid^="stBaseButton-secondary"]:hover {{ background:var(--tb-tint) !important; color:var(--tb-green-dark) !important; }}
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
          background:var(--tb-green) !important; color:#fff !important; border-color:var(--tb-green) !important; }}
        .stButton > button[kind="primary"] *, .stFormSubmitButton > button[kind="primary"] * {{ color:#fff !important; }}
        /* Hover: lift + shadow so buttons clearly read as clickable */
        button[data-testid^="stBaseButton"], .stButton > button, .stFormSubmitButton > button {{
          transition:transform .12s ease, box-shadow .12s ease; cursor:pointer; }}
        button[data-testid^="stBaseButton"]:hover, .stButton > button:hover, .stFormSubmitButton > button:hover {{
          transform:translateY(-1px); box-shadow:0 3px 10px rgba(22,58,42,.20); }}
        /* Overview back button — bold & prominent */
        .st-key-back_overview button {{ font-weight:700 !important; letter-spacing:1px;
          border:1.5px solid var(--tb-green) !important; color:var(--tb-green) !important; }}
        .st-key-back_overview button:hover {{ background:var(--tb-tint) !important; }}
        /* Expander titles — bold & readable (the body font is very light) */
        [data-testid="stExpander"] summary {{ font-weight:700 !important; }}
        [data-testid="stExpander"] summary p {{ font-weight:700 !important; font-size:1rem;
          color:var(--tb-green) !important; }}
        [data-testid="stExpander"] summary svg {{ fill:var(--tb-green) !important; }}
        /* The two engine expanders wear their source colour as a chip-style header */
        .st-key-exp_engagement [data-testid="stExpander"] summary {{ background:#34577C !important; border-radius:7px; }}
        .st-key-exp_strategy [data-testid="stExpander"] summary {{ background:#176B63 !important; border-radius:7px; }}
        .st-key-exp_engagement [data-testid="stExpander"] summary *,
        .st-key-exp_strategy [data-testid="stExpander"] summary * {{ color:#fff !important; fill:#fff !important; }}
        /* Multiselect (filter) pills: brand green with white text so they read clearly */
        [data-baseweb="tag"] {{ background:var(--tb-green) !important; }}
        [data-baseweb="tag"] span, [data-baseweb="tag"] div {{ color:#fff !important; }}
        [data-baseweb="tag"] svg {{ fill:#fff !important; }}

        /* Sidebar */
        [data-testid="stSidebar"] {{ background:#fff; border-right:1px solid var(--tb-hairline); }}
        .tb-side {{ text-align:center; padding:8px 0 12px; border-bottom:1px solid var(--tb-hairline); margin-bottom:8px; }}
        .tb-side .sub {{ font-size:.72rem; color:var(--tb-muted); margin-top:6px; }}

        /* Bars / gauge */
        .tb-gauge {{ height:13px; border-radius:7px; background:var(--tb-tint); overflow:hidden; border:1px solid var(--tb-hairline); }}
        .tb-gauge > span {{ display:block; height:100%; }}
        .tb-bar-row {{ display:flex; align-items:center; gap:10px; margin:6px 0; }}
        .tb-bar-label {{ width:180px; font-size:.83rem; }}
        .tb-bar-track {{ flex:1; height:10px; background:var(--tb-tint); border-radius:5px; overflow:hidden; }}
        .tb-bar-fill {{ height:100%; }}
        .tb-bar-val {{ width:48px; text-align:right; font-size:.8rem; color:var(--tb-muted); }}

        footer {{ visibility:hidden; height:0; }}
        #MainMenu {{ visibility:hidden; }}
        </style>
        """),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Page setup + structure
# ---------------------------------------------------------------------------
def page_setup(page_title: str, layout: str = "wide") -> None:
    st.set_page_config(page_title=f"Meridian · {page_title}", page_icon="🏛️",
                       layout=layout, initial_sidebar_state="expanded")
    inject_brand()
    sidebar_brand()


def sidebar_brand() -> None:
    with st.sidebar:
        st.markdown(
            f'<div class="tb-side">{bank_logo(h=58)}'
            f'<div class="sub"><span class="tb-wordmark-main">MERIDIAN</span> by The Bank</div>'
            f'<div class="sub">{_esc(BANK_TAGLINE)}</div></div>',
            unsafe_allow_html=True,
        )


def password_gate() -> bool:
    """Optional access password. Returns True if access is granted.

    Active only when APP_PASSWORD is set in secrets (e.g. Streamlit Cloud). With no
    APP_PASSWORD configured (local/dev) the app is open. The password lives only in
    server-side secrets, never in the repository.
    """
    try:
        pw = str(st.secrets.get("APP_PASSWORD", "") or "")
    except Exception:
        pw = ""
    if not pw:
        return True
    if st.session_state.get("auth_ok"):
        return True
    mid = st.columns([1, 1.3, 1])[1]
    with mid:
        st.markdown('<div style="height:7vh"></div>', unsafe_allow_html=True)
        # Branded login panel — green background so the white Meridian logo shows.
        st.markdown(
            f'<div style="background:var(--tb-green);border-radius:14px;padding:30px 26px 24px;'
            f'text-align:center;border-bottom:5px solid var(--tb-gold);'
            f'box-shadow:0 8px 24px rgba(22,58,42,.25)">{meridian_logo(h=30)}'
            f'<div style="color:#fff;font-weight:300;letter-spacing:1.5px;margin-top:14px;'
            f'font-size:.8rem;text-transform:uppercase">Prototype access</div>'
            f'<div style="color:#EAF2EC;font-size:.78rem;margin-top:4px">by The Bank · Zurich</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<p style="text-align:center;color:#3C5A4B;margin-top:16px;font-size:.9rem">'
                    'Please enter the access password to open the Meridian prototype.</p>',
                    unsafe_allow_html=True)
        with st.form("login_form"):
            entered = st.text_input("Password", type="password", placeholder="Access password",
                                    label_visibility="collapsed")
            ok = st.form_submit_button("Enter", type="primary", width="stretch")
        if ok:
            if entered == pw:
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False


def sidebar_controls(show_unread_for: str | None = None) -> None:
    from app import state
    from app.gemini import mode_label

    with st.sidebar:
        live = mode_label().startswith("Live")
        dot = PALETTE["green"] if live else PALETTE["gold"]
        st.markdown(
            f'<div style="font-size:.8rem;color:{PALETTE["muted"]};margin-bottom:4px;">'
            f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
            f'background:{dot};margin-right:6px;"></span>Meridian AI: {_esc(mode_label())}</div>',
            unsafe_allow_html=True,
        )
        if show_unread_for:
            n = state.unread_count(show_unread_for)
            if n:
                st.markdown(chip(f"{n} new message(s)", "gold"), unsafe_allow_html=True)
        st.markdown("---")
        if st.button("↻ Reset demo", width="stretch", key="sb_reset"):
            state.reset_state()
            st.rerun()
        st.caption(DISCLAIMER_SHORT)


def header_bar(title: str, subtitle: str = "", right_html: str = "", logo: str = "meridian") -> None:
    # The header background is brand green: the white Meridian logo sits on it
    # directly (no white plate), while the green Bank logo needs a white plate.
    if logo == "meridian":
        lg = meridian_logo(h=30, plate=False)
    elif logo == "bank":
        lg = bank_logo(h=40, plate=True)
    else:
        lg = ""
    right = f'<div class="tb-header-right">{right_html}</div>' if right_html else ""
    sub = f'<div class="tb-sub">{_esc(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="tb-header">{lg}'
        f'<div><div class="tb-title">{_esc(title)}</div>{sub}</div>{right}</div>',
        unsafe_allow_html=True,
    )


def back_to_overview() -> None:
    """Prominent top-left button back to the Prototype Instructions hub."""
    if st.button("⟵  OVERVIEW", key="back_overview", help="Back to the Prototype Instructions"):
        try:
            st.switch_page("views/instructions.py")
        except Exception:
            pass


def pediment(text: str) -> None:
    st.markdown(
        f'<div class="tb-pediment"><span class="tri"></span>'
        f'<span class="txt">{_esc(text)}</span><span class="rule"></span></div>',
        unsafe_allow_html=True,
    )


def footer() -> None:
    yr = datetime.now().year
    st.markdown(
        f'<div class="tb-footer" style="color:#fff">'
        f'<div style="color:#fff;display:flex;align-items:center;gap:9px">{meridian_logo(h=17)}'
        f'<span style="color:#fff">by The Bank, Zurich {yr}</span></div>'
        f'<div style="color:#fff">{_esc(DISCLAIMER_SHORT)}</div></div>',
        unsafe_allow_html=True,
    )


def disclaimer_note() -> None:
    st.caption(
        "Prototype with fictional, synthetic data. Meridian's AI output is illustrative and **not "
        "investment advice**. In production the AI runs on the Swiss-hosted Unique platform; here "
        "it is simulated with Google Gemini."
    )


# ---------------------------------------------------------------------------
# Profile strip + family picker (RM page)
# ---------------------------------------------------------------------------
def logged_in_strip(name: str, role: str, avatar_file: str | None, initials: str) -> None:
    av = avatar_html(avatar_file, initials, size=64, ring=PALETTE["gold"])
    st.markdown(
        f'<div class="tb-profile" style="gap:14px">{av}<div>'
        f'<div class="r" style="font-size:.72rem;text-transform:uppercase;letter-spacing:.6px">Logged in as</div>'
        f'<div class="n" style="font-size:1.3rem">{_esc(name)}</div>'
        f'<div class="r" style="font-size:.9rem">{_esc(role)}</div></div></div>',
        unsafe_allow_html=True,
    )


def family_picker() -> str:
    st.markdown(
        '<div style="font-weight:600;color:var(--tb-green);font-size:1rem;margin-bottom:2px">'
        '◆ Client family</div>', unsafe_allow_html=True)
    options = ["Müller Family", "Weber Family (coming soon)", "Schneider Family (coming soon)"]
    choice = st.selectbox("Client family", options, index=0, key="rm_family_pick",
                          label_visibility="collapsed")
    if "coming soon" in choice:
        st.info("Only the Müller family is available in this prototype.")
    return "mueller"


# ---------------------------------------------------------------------------
# Content components
# ---------------------------------------------------------------------------
def metric_card(label: str, value: str, sub: str = "", accent: str | None = None) -> None:
    val_color = accent or "var(--tb-green)"
    sub_html = f'<div class="tb-metric-sub">{_esc(sub)}</div>' if sub else ""
    st.markdown(
        f'<div class="tb-card accent"><div class="tb-metric-label">{_esc(label)}</div>'
        f'<div class="tb-metric-value" style="color:{val_color}">{_esc(value)}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


def chip(text: str, kind: str = "") -> str:
    cls = "tb-chip" + (f" {kind}" if kind else "")
    return f'<span class="{cls}">{_esc(text)}</span>'


def chips(items: list[str], kind: str = "") -> None:
    st.markdown("".join(chip(i, kind) for i in items), unsafe_allow_html=True)


def hbar(label: str, value: float, max_value: float = 100.0, color: str | None = None, suffix: str = "") -> None:
    color = color or PALETTE["green"]
    w = max(0.0, min(100.0, value / max_value * 100.0))
    st.markdown(
        f'<div class="tb-bar-row"><div class="tb-bar-label">{_esc(label)}</div>'
        f'<div class="tb-bar-track"><div class="tb-bar-fill" style="width:{w:.0f}%;background:{color}"></div></div>'
        f'<div class="tb-bar-val">{value:.0f}{suffix}</div></div>',
        unsafe_allow_html=True,
    )


def gauge(value: float, color: str, max_value: float = 100.0) -> None:
    w = max(0.0, min(100.0, value / max_value * 100.0))
    st.markdown(f'<div class="tb-gauge"><span style="width:{w:.0f}%;background:{color}"></span></div>',
                unsafe_allow_html=True)


def _offer_svg(kind: str) -> str:
    """Elegant line illustration per offer type (follows the active accent)."""
    c = "var(--tb-green)"
    if kind == "house":
        body = (f'<path d="M9 32 L32 13 L55 32" fill="none" stroke="{c}" stroke-width="3.2" stroke-linejoin="round"/>'
                f'<path d="M16 30 V52 H48 V30" fill="none" stroke="{c}" stroke-width="3.2" stroke-linejoin="round"/>'
                f'<rect x="28" y="40" width="10" height="12" fill="{c}"/>'
                f'<rect x="20" y="34" width="7" height="7" fill="none" stroke="{c}" stroke-width="2.4"/>')
    elif kind == "art":
        body = (f'<rect x="9" y="12" width="46" height="34" rx="2" fill="none" stroke="{c}" stroke-width="3.2"/>'
                f'<circle cx="42" cy="22" r="3.2" fill="{c}"/>'
                f'<path d="M13 40 L25 27 L33 35 L43 23 L51 40" fill="none" stroke="{c}" stroke-width="3" stroke-linejoin="round"/>'
                f'<path d="M24 52 h16" stroke="{c}" stroke-width="3" stroke-linecap="round"/>')
    elif kind == "savings":
        body = (f'<path d="M13 51 V35 M27 51 V27 M41 51 V31 M53 51 V21" stroke="{c}" stroke-width="4.2" stroke-linecap="round"/>'
                f'<path d="M11 25 L26 31 L38 23 L53 14" fill="none" stroke="{c}" stroke-width="2.6" stroke-linejoin="round"/>'
                f'<path d="M45 14 h9 v9" fill="none" stroke="{c}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    elif kind == "foundation":
        body = f'<path d="M32 50 C 9 33, 16 13, 32 24 C 48 13, 55 33, 32 50 Z" fill="none" stroke="{c}" stroke-width="3.2" stroke-linejoin="round"/>'
    elif kind == "books":
        body = (f'<path d="M32 18 C 24 13, 14 14, 11 16 V47 C 14 45, 24 44, 32 49 C 40 44, 50 45, 53 47 V16 C 50 14, 40 13, 32 18 Z" '
                f'fill="none" stroke="{c}" stroke-width="3.2" stroke-linejoin="round"/><path d="M32 18 V49" stroke="{c}" stroke-width="2.6"/>')
    elif kind == "governance":
        body = (f'<polygon points="32,11 56,27 8,27" fill="{c}"/><rect x="12" y="29" width="40" height="3.4" fill="{c}"/>'
                f'<rect x="15" y="34" width="4.5" height="15" fill="{c}"/><rect x="29.5" y="34" width="4.5" height="15" fill="{c}"/>'
                f'<rect x="44" y="34" width="4.5" height="15" fill="{c}"/><rect x="11" y="50" width="42" height="3.4" fill="{c}"/>')
    elif kind == "review":
        body = (f'<rect x="15" y="10" width="34" height="44" rx="3" fill="none" stroke="{c}" stroke-width="3.2"/>'
                f'<path d="M22 22 h20 M22 30 h20 M22 38 h12" stroke="{c}" stroke-width="2.6" stroke-linecap="round"/>'
                f'<path d="M33 41 l4 4 l9 -10" fill="none" stroke="{c}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
    else:
        return ""
    return f'<svg viewBox="0 0 64 64" width="100%" height="100%" aria-hidden="true">{body}</svg>'


_OFFER_KIND = [("realestate", "house"), ("art", "art"), ("savings", "savings"),
               ("foundation", "foundation"), ("academy", "books"), ("gov", "governance"),
               ("planning", "review")]


def offer_card(key: str, title: str, body: str, cta_label: str | None = None,
               tag: str = "For you", icon: str = "", dismissible: bool = True) -> bool:
    flags = st.session_state.setdefault("ui_flags", {})
    dismissed = flags.setdefault("dismissed_nudges", [])
    if dismissible and key in dismissed:
        return False
    head = f"{icon} {title}" if icon else title
    kind = next((v for k, v in _OFFER_KIND if k in key), "")
    # Prefer a real photo at assets/offer_<kind>.jpg if present, else the SVG.
    photo = _avatar_uri(f"offer_{kind}.jpg", px=220) if kind else None
    if photo:
        inner = f'<img src="{photo}" style="width:100%;height:100%;object-fit:cover;border-radius:8px"/>'
    else:
        inner = _offer_svg(kind)
    thumb = (f'<div style="flex:0 0 78px;width:78px;height:78px;border-radius:10px;'
             f'background:var(--tb-tint);border:1px solid var(--tb-hairline);padding:9px;'
             f'display:flex;align-items:center;justify-content:center">{inner}</div>') if inner else ""
    st.markdown(
        f'<div class="tb-offer" style="display:flex;gap:14px;align-items:center">'
        f'<div style="flex:1"><div class="tag">{_esc(tag)}</div>'
        f'<div class="h">{_esc(head)}</div><div class="b">{_esc(body)}</div></div>{thumb}</div>',
        unsafe_allow_html=True,
    )
    clicked = False
    if cta_label or dismissible:
        c1, c2, _ = st.columns([0.34, 0.20, 0.46])
        if cta_label:
            clicked = c1.button(cta_label, key=f"offer_cta_{key}", type="primary", width="stretch")
        if dismissible and c2.button("Dismiss", key=f"offer_dismiss_{key}", width="stretch"):
            dismissed.append(key)
            st.rerun()
    return clicked


# ---------------------------------------------------------------------------
# Interactive charts (Altair)
# ---------------------------------------------------------------------------
def allocation_chart(portfolio: dict, color: str | None = None) -> None:
    import altair as alt
    import pandas as pd

    color = color or PALETTE["green"]
    df = pd.DataFrame(portfolio["asset_allocation"])
    chart = (
        alt.Chart(df).mark_bar(cornerRadiusEnd=3, color=color)
        .encode(x=alt.X("weight_pct:Q", title="Weight %"),
                y=alt.Y("asset_class:N", sort="-x", title=None),
                tooltip=[alt.Tooltip("asset_class:N", title="Asset class"),
                         alt.Tooltip("weight_pct:Q", title="Weight %", format=".1f"),
                         alt.Tooltip("value_chf:Q", title="Value (CHF)", format=",.0f")])
        .properties(width="container", height=max(170, len(df) * 34))
    )
    st.altair_chart(chart, theme="streamlit")


def performance_chart(portfolio: dict, color: str | None = None, height: int = 250,
                      show_benchmark: bool = True, chart_type: str = "bar") -> None:
    import altair as alt
    import pandas as pd

    color = color or PALETTE["green"]
    rows = portfolio["performance_annual"]
    data = [{"Year": r["year"], "Series": "Portfolio", "Return": r["portfolio_pct"]} for r in rows]
    if show_benchmark:
        data += [{"Year": r["year"], "Series": "Benchmark", "Return": r["benchmark_pct"]} for r in rows]
    df = pd.DataFrame(data)
    scale = alt.Scale(domain=["Portfolio", "Benchmark"], range=[color, PALETTE["gold"]])
    color_enc = alt.Color("Series:N", title=None, scale=scale, legend=alt.Legend(orient="top"))
    tip = [alt.Tooltip("Year:N"), alt.Tooltip("Series:N"), alt.Tooltip("Return:Q", format="+.1f")]
    if chart_type == "line":
        chart = (alt.Chart(df).mark_line(point=True, strokeWidth=2.5)
                 .encode(x=alt.X("Year:N", title=None), y=alt.Y("Return:Q", title="Annual return %"),
                         color=color_enc, tooltip=tip))
    else:
        chart = (alt.Chart(df).mark_bar()
                 .encode(x=alt.X("Year:N", title=None), xOffset="Series:N",
                         y=alt.Y("Return:Q", title="Annual return %"), color=color_enc, tooltip=tip))
    st.altair_chart(chart.properties(width="container", height=height), theme="streamlit")


def projection_chart(start_value: float, annual_return_pct: float, monthly_contribution: float,
                     years: int, vol_pct: float, color: str | None = None, height: int = 280) -> float:
    import altair as alt
    import pandas as pd

    color = color or PALETTE["green"]

    def path(rate: float) -> list[float]:
        r_m = (1 + rate / 100.0) ** (1 / 12) - 1
        v, out = start_value, []
        for m in range(years * 12 + 1):
            if m > 0:
                v = v * (1 + r_m) + monthly_contribution
            out.append(v)
        return out

    exp, opt, pess = path(annual_return_pct), path(annual_return_pct + vol_pct), path(max(-50.0, annual_return_pct - vol_pct))
    xs = [m / 12.0 for m in range(years * 12 + 1)]
    df = pd.DataFrame({"Year": xs, "Expected": exp, "Optimistic": opt, "Pessimistic": pess})
    band = (alt.Chart(df).mark_area(opacity=0.16, color=color)
            .encode(x=alt.X("Year:Q", title="Years from today"),
                    y=alt.Y("Pessimistic:Q", title="Projected value (CHF)"), y2="Optimistic:Q"))
    line = (alt.Chart(df).mark_line(color=color, strokeWidth=2.5)
            .encode(x="Year:Q", y="Expected:Q",
                    tooltip=[alt.Tooltip("Year:Q", format=".1f"),
                             alt.Tooltip("Expected:Q", title="Expected (CHF)", format=",.0f"),
                             alt.Tooltip("Optimistic:Q", title="Optimistic", format=",.0f"),
                             alt.Tooltip("Pessimistic:Q", title="Pessimistic", format=",.0f")]))
    st.altair_chart((band + line).properties(width="container", height=height), theme="streamlit")
    return exp[-1]


# ---------------------------------------------------------------------------
# Chat (Meridian AI)
# ---------------------------------------------------------------------------
def chat_bubble(who: str, text: str, kind: str = "ai") -> None:
    cls = {"ai": "tb-chat-ai", "user": "tb-chat-user", "human": "tb-chat-human"}.get(kind, "tb-chat-ai")
    st.markdown(
        f'<div class="{cls}"><div class="tb-chat-who">{_esc(who)}</div>'
        f'<div class="tb-chat-text">{_esc(text)}</div></div>',
        unsafe_allow_html=True,
    )


def ai_chat_panel(person_key: str, portfolio: dict, member: dict, state_key: str,
                  suggestions: list[tuple[str, str]] | None = None,
                  title: str = "Meridian AI", scope: str = "Your personal AI assistant",
                  placeholder: str = "Ask Meridian about your portfolio…") -> None:
    from app import gemini

    hist_key = f"{state_key}_history"
    mode_key = f"{state_key}_mode"
    history: list = st.session_state.setdefault(hist_key, [])

    with st.container(border=True):
        st.markdown(f'<div class="tb-ai-head"><span class="t">✦ {_esc(title)}</span>'
                    f'<span class="s">{_esc(scope)}</span></div>', unsafe_allow_html=True)
        if not history:
            chat_bubble("Meridian AI", f"Grüezi {gemini.PERSONA[person_key]['salutation']}, I'm the "
                        f"Meridian assistant. Ask me anything about your own portfolio: returns, "
                        f"holdings, fees, trades or the digital-asset sleeve.", "ai")
        for role, text in history:
            chat_bubble("Meridian AI" if role == "model" else "You", text,
                        "ai" if role == "model" else "user")

        pending: str | None = None
        if suggestions:
            cols = st.columns(len(suggestions))
            for col, (label, query) in zip(cols, suggestions):
                if col.button(label, key=f"{state_key}_sg_{label[:14]}", width="stretch"):
                    pending = query
        with st.form(key=f"{state_key}_form", clear_on_submit=True):
            ic, sc = st.columns([0.82, 0.18])
            msg = ic.text_input("Ask", key=f"{state_key}_inp", label_visibility="collapsed", placeholder=placeholder)
            sent = sc.form_submit_button("Send", type="primary", width="stretch")
        if sent and msg and msg.strip():
            pending = msg.strip()
        if pending:
            with st.spinner("Meridian is reading your portfolio…"):
                res = gemini.portfolio_chat(person_key, portfolio, member, history, pending)
            history.append(("user", pending))
            history.append(("model", res["text"]))
            st.session_state[mode_key] = res
            st.rerun()
        res = st.session_state.get(mode_key)
        cc1, cc2 = st.columns([0.7, 0.3])
        if res and res.get("note"):
            cc1.caption("ℹ " + res["note"])
        if history and cc2.button("Clear", key=f"{state_key}_clear", width="stretch"):
            st.session_state[hist_key] = []
            st.rerun()


def advisor_chat_panel(state_key: str, suggestions: list[tuple[str, str]] | None = None,
                       title: str = "Chat with Meridian (AI)",
                       scope: str = "Whole Müller-family database") -> None:
    from app import gemini, state

    hist_key = f"{state_key}_history"
    mode_key = f"{state_key}_mode"
    history: list = st.session_state.setdefault(hist_key, [])

    with st.container(border=True):
        st.markdown(f'<div class="tb-ai-head"><span class="t">✦ {_esc(title)}</span>'
                    f'<span class="s">{_esc(scope)}</span></div>', unsafe_allow_html=True)
        if not history:
            chat_bubble("Meridian AI", "I have the full Müller-family database, covering all members "
                        "(Hans, Margrit and Lukas), portfolios, CRM, the engagement score and "
                        "next-best-actions. Ask me anything to prepare.", "ai")
        for role, text in history:
            chat_bubble("Meridian AI" if role == "model" else "Mr. Reto Wyss", text,
                        "ai" if role == "model" else "user")

        pending: str | None = None
        if suggestions:
            cols = st.columns(len(suggestions))
            for col, (label, query) in zip(cols, suggestions):
                if col.button(label, key=f"{state_key}_sg_{label[:14]}", width="stretch"):
                    pending = query
        with st.form(key=f"{state_key}_form", clear_on_submit=True):
            ic, sc = st.columns([0.82, 0.18])
            msg = ic.text_input("Ask", key=f"{state_key}_inp", label_visibility="collapsed",
                                placeholder="e.g. What's the wealth-transfer risk and what should I do next?")
            sent = sc.form_submit_button("Send", type="primary", width="stretch")
        if sent and msg and msg.strip():
            pending = msg.strip()
        if pending:
            with st.spinner("Meridian is consulting the family database…"):
                res = gemini.advisor_chat(state.get_family(), history, pending)
            history.append(("user", pending))
            history.append(("model", res["text"]))
            st.session_state[mode_key] = res
            st.rerun()
        res = st.session_state.get(mode_key)
        cc1, cc2 = st.columns([0.7, 0.3])
        if res and res.get("note"):
            cc1.caption("ℹ " + res["note"])
        if history and cc2.button("Clear", key=f"{state_key}_clear", width="stretch"):
            st.session_state[hist_key] = []
            st.rerun()


# ---------------------------------------------------------------------------
# Family-side widgets
# ---------------------------------------------------------------------------
def meetings_widget(role: str) -> None:
    from app import state

    fam = state.get_family()
    mtgs = [m for m in fam["meetings"] if m["with"] == role]
    if not mtgs:
        st.caption("No meetings yet. Requests from Mr. Reto Wyss appear here to confirm.")
        return
    for m in mtgs:
        with st.container(border=True):
            st.markdown(f"**{m['topic']}**")
            st.caption(f"Proposed: {m['proposed_ts']}")
            if m["status"] == "requested":
                c1, c2, _ = st.columns([0.3, 0.3, 0.4])
                if c1.button("Confirm", key=f"cf_{m['id']}", type="primary", width="stretch"):
                    state.confirm_meeting(m["id"])
                    st.success("Confirmed. Mr. Reto Wyss has been notified.")
                    st.rerun()
                if c2.button("Decline", key=f"dc_{m['id']}", width="stretch"):
                    state.decline_meeting(m["id"])
                    st.rerun()
            elif m["status"] == "confirmed":
                st.markdown(chip("Confirmed ✓", "gold"), unsafe_allow_html=True)
            else:
                st.markdown(chip("Declined"), unsafe_allow_html=True)


def secure_messaging_widget(role: str) -> None:
    from app import state

    fam = state.get_family()
    convo = [m for m in fam["messages"]
             if (m["from"] == role and m["to"] == "rm") or (m["from"] == "rm" and m["to"] == role)]
    if not convo:
        st.caption("No messages yet.")
    for m in convo:
        who = _ROLE_NAME.get(m["from"], m["from"])
        chat_bubble(f"{who}, {m['ts'][:16].replace('T', ' ')}", m["text"], "human")
    with st.form(key=f"msg_{role}", clear_on_submit=True):
        ic, sc = st.columns([0.82, 0.18])
        txt = ic.text_input("Message", key=f"msg_inp_{role}", label_visibility="collapsed",
                            placeholder="Write a secure message to Mr. Reto Wyss…")
        if sc.form_submit_button("Send", type="primary", width="stretch") and txt.strip():
            state.add_message(role, "rm", txt.strip())
            st.success("Message sent to Mr. Reto Wyss.")
            st.rerun()


# ---------------------------------------------------------------------------
# Dashboard personalisation
# ---------------------------------------------------------------------------
def _darken(hex_color: str, factor: float = 0.78) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


def accent_for(persona_key: str) -> str:
    return st.session_state.get(f"accent_{persona_key}", PALETTE["green"])


def apply_accent(persona_key: str) -> None:
    """Re-theme the WHOLE Meridian interface for this client to their chosen accent.

    Overrides the --tb-green CSS variable, so the header, buttons, pediments, chips,
    cards, charts and figures all pick up the accent colour.
    """
    accent = accent_for(persona_key)
    if accent and accent.lower() != PALETTE["green"].lower():
        st.markdown(
            f"<style>:root{{--tb-green:{accent};--tb-green-dark:{_darken(accent)};}}</style>",
            unsafe_allow_html=True,
        )


def past_meetings(role: str | None = None, limit: int | None = None) -> None:
    """Render the history of past meetings (optionally filtered to one attendee)."""
    from app import state

    hist = list(state.get_family().get("meeting_history", []))
    if role:
        hist = [m for m in hist if role in m.get("attendees", [])]
    hist.sort(key=lambda m: m["date"], reverse=True)
    if limit:
        hist = hist[:limit]
    if not hist:
        st.caption("No past meetings on record.")
        return
    for m in hist:
        att = ", ".join(_ROLE_NAME.get(a, a) for a in m.get("attendees", []))
        with st.container(border=True):
            st.markdown(f"**{m['date']}: {m['topic']}**")
            st.markdown(
                chip(m.get("mode", ""), "gold") + chip(f"RM: {m['rm']}")
                + chip(f"Present: {att}"),
                unsafe_allow_html=True,
            )
            st.write(m["summary"])


def accent_picker(persona_key: str) -> str:
    names = list(ACCENTS.keys())
    current = st.session_state.get(f"accent_name_{persona_key}", names[0])
    chosen = st.selectbox("Accent colour", names, index=names.index(current), key=f"accentsel_{persona_key}")
    st.session_state[f"accent_name_{persona_key}"] = chosen
    st.session_state[f"accent_{persona_key}"] = ACCENTS[chosen]
    return ACCENTS[chosen]
