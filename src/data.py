"""Shared, cached FRED loaders used by every page.

Both the dashboard (``app.py``) and the analytics page import from here so the
expensive FRED calls are fetched once and reused across pages and reruns. The
cache refreshes hourly, matching the "live but not hammering the API" goal.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .config import SERIES
from .fred import load_series


@st.cache_data(ttl=3600, show_spinner=False)
def load_one(series_id: str, start: str | None = None) -> pd.DataFrame:
    """Cached fetch of a single FRED series as a tidy ``date, value`` frame."""
    return load_series(series_id, start)


def load_frames(start: str | None = None) -> dict[str, pd.DataFrame]:
    """Fetch every configured series as raw (untransformed) tidy frames.

    Keyed by the series ``key`` (e.g. ``"m2"``). Used by the analytics page,
    which applies its own resampling/transforms on top.
    """
    return {s.key: load_one(s.series_id, start) for s in SERIES}
