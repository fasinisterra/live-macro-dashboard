"""Live Macro Dashboard — Streamlit entry point.

Pulls nine macro indicators live from FRED and renders each as its own Observable
Plot chart. Run with:  streamlit run app.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.branding import apply_branding, header
from src.charts import CHART_HEIGHT, observable_plot_html
from src.config import SERIES
from src.data import load_one
from src.fred import MissingAPIKeyError, apply_transform, latest_and_delta

st.set_page_config(page_title="Macro Dashboard", layout="wide")
apply_branding()

LOOKBACKS = {"1Y": 1, "3Y": 3, "5Y": 5, "10Y": 10, "Max": None}


def start_date_for(years: int | None) -> str | None:
    if years is None:
        return None
    return (datetime.now(timezone.utc).date() - timedelta(days=365 * years)).isoformat()


# ----- Sidebar -----------------------------------------------------------------
st.sidebar.title("Macro Dashboard")
st.sidebar.caption("Live U.S. macro indicators, straight from FRED.")

lookback_label = st.sidebar.radio("Lookback window", list(LOOKBACKS), index=2, horizontal=True)
start = start_date_for(LOOKBACKS[lookback_label])

if st.sidebar.button("Refresh data", use_container_width=True):
    load_one.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Source:** [FRED](https://fred.stlouisfed.org) · Federal Reserve Bank of St. Louis")
st.sidebar.caption("Data cached for 1 hour. Charts rendered with Observable Plot.")

# ----- Header ------------------------------------------------------------------
header("Live Macro Dashboard")
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.caption(f"Nine indicators · lookback {lookback_label} · refreshed {now}")

# ----- Body --------------------------------------------------------------------
cols = st.columns(2, gap="medium")

for i, s in enumerate(SERIES):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"#### {s.label}")
            try:
                df = load_one(s.series_id, start)
                df = apply_transform(df, s.transform)
            except MissingAPIKeyError as exc:
                st.error(str(exc))
                st.stop()
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Could not load {s.series_id}: {exc}")
                continue

            if df.empty:
                st.info("No observations in the selected window.")
                continue

            latest, delta = latest_and_delta(df)
            as_of = df["date"].iloc[-1].date()
            st.metric(
                label=f"Latest · {as_of}",
                value=s.format_value(latest),
                delta=s.format_delta(delta),
            )
            components.html(observable_plot_html(df, s), height=CHART_HEIGHT + 8)
            st.caption(f"{s.units} · {s.frequency} · [{s.series_id}]({s.fred_url})")
