"""Correlation & statistical analytics across the nine macro indicators.

A second page of the multipage app. Aligns every series to a common monthly
frequency, lets you correlate *changes* (to avoid spurious trend correlation),
and explores relationships with a heatmap, scatter/regression, rolling correlation,
lead/lag cross-correlation, and a standardized overlay — all in Observable Plot.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src import analytics as A
from src import analytics_charts as AC
from src.data import load_frames, load_one
from src.fred import MissingAPIKeyError

st.set_page_config(page_title="Macro Analytics", page_icon="📊", layout="wide")

KEYS = A.KEYS
LABEL = A.LABEL
SHORT = A.SHORT
COLOR = A.COLOR

TRANSFORM_UI = {
    "YoY % change": "yoy",
    "MoM % change": "mom",
    "First difference (Δ)": "diff",
    "Levels (z-scored)": "level",
}
LOOKBACKS = {"3Y": 3, "5Y": 5, "10Y": 10, "15Y": 15, "Max": None}


def _label_to_key(label: str) -> str:
    return next(k for k in KEYS if LABEL[k] == label)


# ----- Sidebar controls --------------------------------------------------------
st.sidebar.title("📊 Analytics controls")
transform = TRANSFORM_UI[st.sidebar.radio("Transform", list(TRANSFORM_UI), index=0,
                                          help="Correlate changes, not trending levels, to avoid spurious correlation.")]
method = st.sidebar.radio("Correlation method", ["pearson", "spearman"], index=0,
                          format_func=str.capitalize,
                          help="Pearson = linear; Spearman = rank/monotonic.").lower()
lookback_label = st.sidebar.radio("Lookback window", list(LOOKBACKS), index=2, horizontal=True)
window = st.sidebar.select_slider("Rolling-corr window (months)", options=[12, 24, 36], value=24)

if st.sidebar.button("🔄 Refresh data", use_container_width=True):
    load_one.clear()  # clears the cached FRED fetches shared by both pages
    st.rerun()

# ----- Load + build panel ------------------------------------------------------
st.title("Correlation & Statistical Analytics")

try:
    frames = load_frames(None)  # full history, cached; we slice the window in-memory
except MissingAPIKeyError as exc:
    st.error(str(exc))
    st.stop()

years = LOOKBACKS[lookback_label]
start = None if years is None else (pd.Timestamp.now() - pd.DateOffset(years=years))

panel_full = A.build_panel(frames, transform=transform)
panel = panel_full if start is None else panel_full.loc[panel_full.index >= start]
panel = panel.dropna(how="all")

n_obs = len(panel.dropna(how="any"))
win_start = panel.index.min()
win_end = panel.index.max()
st.caption(
    f"Monthly observations · transform: **{[k for k, v in TRANSFORM_UI.items() if v == transform][0]}** · "
    f"method: **{method.capitalize()}** · window: **{lookback_label}** "
    f"({win_start:%Y-%m} → {win_end:%Y-%m}, N≈{n_obs} aligned months)"
)

with st.expander("How this is computed (methodology)"):
    st.markdown(
        "- **Alignment** — every series is resampled to **month-end**; daily/weekly take the "
        "month's last value, and quarterly **GDP** is forward-filled across the quarter.\n"
        "- **Why changes, not levels** — M2, GDP, CPI and the dollar all *trend* over time, so "
        "their raw levels correlate ~0.9 just from sharing a time trend (spurious). Correlating "
        "**changes** (the default YoY %) measures whether they actually move together.\n"
        "- **Methods** — Pearson captures linear co-movement; Spearman captures any monotonic "
        "relationship (robust to outliers).\n"
        "- Correlations use pairwise-complete observations and recompute for the selected window."
    )

if transform == "level":
    st.warning(
        "You're correlating **z-scored levels**. These largely reflect shared time trends, so "
        "most pairs will look strongly positive. Switch to a change-based transform for a "
        "cleaner read of genuine co-movement."
    )

# ----- 1) Correlation heatmap --------------------------------------------------
st.subheader("Correlation matrix")
corr = A.correlation_matrix(panel, method=method)
components.html(AC.heatmap_html(corr, SHORT), height=500)
st.caption("Blue = move together · Red = move opposite · near-white = little linear relationship.")

# ----- 2) Auto insights --------------------------------------------------------
pairs = A.ranked_pairs(corr)
if pairs:
    most_neg = pairs[0]
    most_pos = pairs[-1]
    strongest = max(pairs, key=lambda t: abs(t[2]))
    c1, c2, c3 = st.columns(3)
    c1.metric("Strongest positive", f"{SHORT[most_pos[0]]} ↔ {SHORT[most_pos[1]]}", f"r = {most_pos[2]:+.2f}")
    c2.metric("Strongest inverse", f"{SHORT[most_neg[0]]} ↔ {SHORT[most_neg[1]]}", f"r = {most_neg[2]:+.2f}")
    c3.metric("Largest magnitude", f"{SHORT[strongest[0]]} ↔ {SHORT[strongest[1]]}", f"|r| = {abs(strongest[2]):.2f}")

st.divider()

# ----- 3) Pairwise explorer: scatter + regression + rolling corr ---------------
st.subheader("Pairwise explorer")
labels = [LABEL[k] for k in KEYS]
pc1, pc2 = st.columns(2)
x_key = _label_to_key(pc1.selectbox("X variable", labels, index=KEYS.index("m2")))
y_key = _label_to_key(pc2.selectbox("Y variable", labels, index=KEYS.index("cpi")))

if x_key == y_key:
    st.info("Pick two different variables to compare.")
else:
    reg = A.regression(panel, x_key, y_key)
    left, right = st.columns([3, 2])
    with left:
        pair = panel[[x_key, y_key]].dropna()
        pair.columns = ["x", "y"]
        components.html(
            AC.scatter_regression_html(pair, SHORT[x_key], SHORT[y_key], COLOR[y_key]),
            height=330,
        )
    with right:
        if reg:
            st.metric("Correlation (r)", f"{reg['r']:+.2f}")
            st.metric("R² (variance explained)", f"{reg['r2']:.0%}")
            st.metric("Slope", f"{reg['slope']:+.3f}")
            st.caption(f"OLS fit over N = {reg['n']} aligned months. Each point is one month's "
                       f"{SHORT[x_key]} vs {SHORT[y_key]} ({[k for k,v in TRANSFORM_UI.items() if v==transform][0]}).")
        else:
            st.info("Not enough overlapping data for a fit in this window.")

    st.markdown(f"**Rolling {window}-month correlation — {SHORT[x_key]} vs {SHORT[y_key]}**")
    roll = A.rolling_correlation(panel, x_key, y_key, window)
    if not roll.empty:
        components.html(AC.rolling_corr_html(roll, COLOR[y_key]), height=250)
        st.caption("How the relationship strengthens, weakens, or flips sign over time.")
    else:
        st.info("Not enough data for a rolling correlation in this window.")

    # ----- 4) Lead / lag -------------------------------------------------------
    st.markdown(f"**Lead / lag — does {SHORT[x_key]} lead {SHORT[y_key]}?**")
    cc = A.cross_correlation(panel, x_key, y_key, max_lag=12)
    cc_valid = cc.dropna()
    if not cc_valid.empty:
        peak_row = cc_valid.loc[cc_valid["corr"].abs().idxmax()]
        peak_lag = int(peak_row["lag"])
        components.html(AC.cross_corr_html(cc, SHORT[x_key], peak_lag), height=260)
        if peak_lag > 0:
            lead_msg = f"strongest at **+{peak_lag} months**, i.e. {SHORT[x_key]} **leads** {SHORT[y_key]}"
        elif peak_lag < 0:
            lead_msg = f"strongest at **{peak_lag} months**, i.e. {SHORT[y_key]} **leads** {SHORT[x_key]}"
        else:
            lead_msg = "strongest at **lag 0** (contemporaneous — no clear lead/lag)"
        st.caption(f"Cross-correlation {lead_msg} (r = {peak_row['corr']:+.2f}).")
    else:
        st.info("Not enough data for lead/lag in this window.")

st.divider()

# ----- 5) Standardized overlay -------------------------------------------------
st.subheader("Standardized overlay")
st.caption("Z-scored levels on a shared scale — compare regimes and co-movement directly.")
default_picks = ["m2", "cpi", "unrate"]
picked_labels = st.multiselect("Series to overlay", labels,
                               default=[LABEL[k] for k in default_picks])
picks = [_label_to_key(lbl) for lbl in picked_labels]

if picks:
    zpanel_full = A.build_panel(frames, transform="level")
    zpanel = zpanel_full if start is None else zpanel_full.loc[zpanel_full.index >= start]
    sub = zpanel[picks].reset_index().melt(id_vars="date", var_name="key", value_name="value").dropna()
    sub["series"] = sub["key"].map(SHORT)
    components.html(
        AC.zscore_overlay_html(sub, [SHORT[k] for k in picks], [COLOR[k] for k in picks]),
        height=320,
    )
else:
    st.info("Pick one or more series to overlay.")
