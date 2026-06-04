"""Statistical analytics over the nine macro indicators.

Pure pandas/numpy — no Streamlit — so it can be unit-tested or scripted directly.

The central idea: the nine series have different frequencies (daily → quarterly)
and most are *trending levels*. Correlating raw levels produces spurious ~0.9
correlations driven purely by shared time trends. So we (1) resample everything to
a common monthly frequency and (2) correlate *changes* (MoM %, YoY %, first
difference), which measures whether the indicators actually move together.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import SERIES

# Lookups derived from the single source of truth in config.py.
KEYS: list[str] = [s.key for s in SERIES]
LABEL: dict[str, str] = {s.key: s.label for s in SERIES}
COLOR: dict[str, str] = {s.key: s.color for s in SERIES}

# Compact labels for the heatmap axes and legends (long names don't fit a 9x9 grid).
SHORT: dict[str, str] = {
    "m2": "M2",
    "dgs10": "10Y UST",
    "cpi": "CPI",
    "gdp": "GDP",
    "unrate": "Unemp",
    "houst": "Housing",
    "stress": "Stress",
    "wti": "WTI",
    "dollar": "USD",
}

TRANSFORMS = {
    "yoy": "YoY % change",
    "mom": "MoM % change",
    "diff": "First difference (Δ)",
    "level": "Levels (z-scored)",
}


def _monthly_levels(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Resample every series to month-end levels and align into one wide frame.

    Daily/weekly series collapse to their last observation in the month; the
    quarterly GDP series is forward-filled across the two intra-quarter months so
    monthly rows are populated. Columns are series keys, index is month-end.
    """
    cols: dict[str, pd.Series] = {}
    for key, df in frames.items():
        if df is None or df.empty:
            continue
        s = df.set_index("date")["value"].sort_index()
        cols[key] = s.resample("ME").last()

    panel = pd.DataFrame(cols).sort_index()
    # Fill within-quarter gaps (GDP) up to two months — keeps monthly rows usable
    # without inventing data between quarters.
    return panel.ffill(limit=2)


def build_panel(frames: dict[str, pd.DataFrame], transform: str = "yoy") -> pd.DataFrame:
    """Aligned monthly panel with the chosen stationarity transform applied."""
    levels = _monthly_levels(frames)

    if transform == "level":
        return (levels - levels.mean()) / levels.std(ddof=0)
    if transform == "mom":
        return levels.pct_change() * 100.0
    if transform == "yoy":
        return levels.pct_change(12) * 100.0
    if transform == "diff":
        return levels.diff()
    raise ValueError(f"Unknown transform: {transform!r}")


def correlation_matrix(panel: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Pairwise correlation matrix (Pearson or Spearman), pairwise-complete."""
    return panel.corr(method=method, min_periods=12)


def rolling_correlation(panel: pd.DataFrame, a: str, b: str, window: int = 24) -> pd.Series:
    """Rolling-window correlation between two series over time."""
    return panel[a].rolling(window).corr(panel[b]).dropna()


def cross_correlation(panel: pd.DataFrame, a: str, b: str, max_lag: int = 12) -> pd.DataFrame:
    """Cross-correlation of ``a`` and ``b`` across lags −max_lag..+max_lag.

    A positive lag aligns ``a`` at time t with ``b`` at t+lag, so a peak at lag>0
    means ``a`` leads ``b`` (today's ``a`` co-moves with future ``b``).
    """
    x, y = panel[a], panel[b]
    rows = []
    for lag in range(-max_lag, max_lag + 1):
        rows.append({"lag": lag, "corr": float(x.corr(y.shift(-lag)))})
    return pd.DataFrame(rows)


def regression(panel: pd.DataFrame, x: str, y: str) -> dict | None:
    """OLS slope/intercept, R², Pearson r and sample size for a pair."""
    d = panel[[x, y]].dropna()
    if len(d) < 3:
        return None
    xs, ys = d[x].to_numpy(), d[y].to_numpy()
    slope, intercept = np.polyfit(xs, ys, 1)
    yhat = slope * xs + intercept
    ss_res = float(((ys - yhat) ** 2).sum())
    ss_tot = float(((ys - ys.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    r = float(np.corrcoef(xs, ys)[0, 1])
    return {"slope": float(slope), "intercept": float(intercept), "r2": r2, "r": r, "n": len(d)}


def ranked_pairs(corr: pd.DataFrame) -> list[tuple[str, str, float]]:
    """All unique pairs as (key_a, key_b, r), sorted ascending (most negative first)."""
    keys = list(corr.columns)
    pairs: list[tuple[str, str, float]] = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            r = corr.iloc[i, j]
            if pd.notna(r):
                pairs.append((keys[i], keys[j], float(r)))
    pairs.sort(key=lambda t: t[2])
    return pairs
