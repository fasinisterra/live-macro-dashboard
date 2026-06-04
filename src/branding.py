"""Wall Street Prompt visual identity for the Streamlit app.

Styling only — injects the firm's fonts, colors, and component treatments so both
pages match the WSP investment-outlook template. Call ``apply_branding()`` once at
the top of each page, and use ``header()`` for the page title block.

Brand tokens (from the template):
  green #37A686 · mint #52F2B8 · slate #2C403A · sage #6B8F89
  ink #0D0D0D · muted #6B7672 · border #E2E5E3 · fog #EEF1F0 · bg #F2F2F2
  display = Newsreader (serif) · sans = Montserrat · body = Source Serif 4
"""

from __future__ import annotations

import streamlit as st

GREEN = "#37A686"
MINT = "#52F2B8"
SLATE = "#2C403A"
SAGE = "#6B8F89"
INK = "#0D0D0D"
MUTED = "#6B7672"
BORDER = "#E2E5E3"
FOG = "#EEF1F0"
BG = "#F2F2F2"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500;6..72,600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');

:root{
  --wsp-green:#37A686; --wsp-mint:#52F2B8; --wsp-slate:#2C403A; --wsp-sage:#6B8F89;
  --wsp-ink:#0D0D0D; --wsp-muted:#6B7672; --wsp-border:#E2E5E3; --wsp-fog:#EEF1F0; --wsp-bg:#F2F2F2;
  --wsp-sans:"Montserrat","Helvetica Neue",Arial,sans-serif;
  --wsp-display:"Newsreader",Georgia,"Times New Roman",serif;
}

/* ---- base ---- */
html, body, .stApp, [data-testid="stAppViewContainer"]{
  font-family:var(--wsp-sans); color:var(--wsp-ink);
}
.stApp{ background:var(--wsp-bg); }
[data-testid="stMain"] .stMarkdown p,
[data-testid="stMain"] li{ font-family:var(--wsp-sans); }

/* ---- headings in Newsreader ---- */
h1, h2, h3, h4, [data-testid="stHeading"]{
  font-family:var(--wsp-display) !important; font-weight:400 !important;
  color:var(--wsp-ink); letter-spacing:-.01em;
}

/* ---- page header block (eyebrow + title + gradient rule) ---- */
.wsp-eyebrow{ font-family:var(--wsp-sans); text-transform:uppercase; letter-spacing:.14em;
  font-size:11px; font-weight:700; color:var(--wsp-green); margin:.1rem 0 .4rem; }
.wsp-title{ font-family:var(--wsp-display); font-weight:400; font-size:40px; line-height:1.08;
  letter-spacing:-.01em; color:var(--wsp-ink); margin:0; }
.wsp-rule{ height:3px; width:64px; border:0; margin:.55rem 0 .2rem;
  background:linear-gradient(90deg,var(--wsp-green),var(--wsp-mint)); }

/* ---- sidebar ---- */
[data-testid="stSidebar"]{ background:var(--wsp-fog); border-right:1px solid var(--wsp-border); }
[data-testid="stSidebar"] *{ font-family:var(--wsp-sans); }

/* ---- "figure" cards: white on soft gray, like the report ---- */
div[data-testid="stVerticalBlockBorderWrapper"][style*="border"]{
  background:#fff; border:1px solid var(--wsp-border) !important; border-radius:3px;
  box-shadow:0 1px 10px rgba(13,13,13,.05); padding-top:.2rem;
}

/* ---- metrics: big light-green Newsreader numerals, like stat-num ---- */
[data-testid="stMetricValue"]{ font-family:var(--wsp-display) !important; font-weight:400;
  color:var(--wsp-green); }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *{
  font-family:var(--wsp-sans); color:var(--wsp-muted); font-weight:600; }
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] *{
  color:var(--wsp-slate) !important; fill:var(--wsp-slate) !important; font-family:var(--wsp-sans); }

/* ---- buttons ---- */
.stButton > button{ font-family:var(--wsp-sans); font-weight:600; color:var(--wsp-green);
  background:#fff; border:1px solid var(--wsp-green); border-radius:2px; }
.stButton > button:hover{ color:#fff; background:var(--wsp-green); border-color:var(--wsp-green); }

/* ---- captions, links, widget labels ---- */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *{
  font-family:var(--wsp-sans); color:var(--wsp-muted); }
[data-testid="stMain"] a, [data-testid="stSidebar"] a{ color:var(--wsp-green); }
[data-testid="stWidgetLabel"] *{ font-family:var(--wsp-sans); color:var(--wsp-ink); }

/* ---- accents ---- */
[data-testid="stExpander"] summary{ font-family:var(--wsp-sans); }
hr{ border-color:var(--wsp-border); }
</style>
"""


def apply_branding() -> None:
    """Inject the WSP stylesheet. Call once near the top of each page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def header(title: str, eyebrow: str = "Wall Street Prompt Research") -> None:
    """Render the branded page header: eyebrow, Newsreader title, gradient rule."""
    st.markdown(
        f'<div class="wsp-eyebrow">{eyebrow}</div>'
        f'<div class="wsp-title">{title}</div>'
        f'<hr class="wsp-rule">',
        unsafe_allow_html=True,
    )
