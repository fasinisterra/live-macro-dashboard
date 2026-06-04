"""Macro Dashboard — Streamlit multipage app router.

Applies the Wall Street Prompt branding and logo, defines the two pages
("Data Sources" and "Analytics"), and runs the selected one.
Run with:  streamlit run app.py
"""

from __future__ import annotations

import pathlib

import streamlit as st

from src.branding import apply_branding, render_logo

st.set_page_config(page_title="Macro Dashboard", layout="wide")
apply_branding()

# WSP wordmark at the very top of the sidebar (above the nav).
_LOGO = pathlib.Path(__file__).resolve().parent / "assets" / "wsp-logo.svg"
try:
    st.logo(str(_LOGO), size="large", link="https://wallstreetprompt.com")
except Exception:  # noqa: BLE001 — fall back to an inline-SVG logo if st.logo can't
    render_logo()

pages = st.navigation([
    st.Page("views/data_sources.py", title="Data Sources", default=True),
    st.Page("views/analytics.py", title="Analytics"),
])
pages.run()
