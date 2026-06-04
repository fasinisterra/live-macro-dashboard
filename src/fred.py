"""FRED data access layer.

Pulls live time series from the FRED API via the ``fredapi`` wrapper and returns
tidy ``date, value`` DataFrames. The API key is read from (in order):

1. Streamlit secrets  -> ``st.secrets["FRED_API_KEY"]`` or ``[fred] api_key``
2. Environment        -> ``FRED_API_KEY``

This module is deliberately free of any Streamlit import at module load so the
preview script can use it without a running Streamlit server. Caching is layered
on top in ``app.py`` with ``st.cache_data``.
"""

from __future__ import annotations

import os

import pandas as pd
from fredapi import Fred


class MissingAPIKeyError(RuntimeError):
    """Raised when no FRED API key can be found in secrets or the environment."""


def get_api_key() -> str:
    """Locate the FRED API key from Streamlit secrets or the environment."""
    # Try Streamlit secrets first, but only if Streamlit is importable AND a
    # secrets file exists (accessing st.secrets with no file raises).
    try:
        import streamlit as st  # local import: keep this module Streamlit-free

        try:
            if "FRED_API_KEY" in st.secrets:
                return str(st.secrets["FRED_API_KEY"])
            if "fred" in st.secrets and "api_key" in st.secrets["fred"]:
                return str(st.secrets["fred"]["api_key"])
        except Exception:
            pass  # no secrets.toml present — fall through to env var
    except ModuleNotFoundError:
        pass

    key = os.environ.get("FRED_API_KEY")
    if key:
        return key

    raise MissingAPIKeyError(
        "No FRED API key found. Set the FRED_API_KEY environment variable, or add "
        "it to .streamlit/secrets.toml (see .streamlit/secrets.toml.example). "
        "Get a free key at https://fredaccount.stlouisfed.org/apikeys"
    )


def load_series(series_id: str, observation_start: str | None = None) -> pd.DataFrame:
    """Fetch a FRED series and return a tidy DataFrame with ``date`` and ``value``.

    Parameters
    ----------
    series_id : str
        FRED series id, e.g. ``"DGS10"``.
    observation_start : str | None
        ISO date ``"YYYY-MM-DD"`` to start from, or ``None`` for full history.
    """
    fred = Fred(api_key=get_api_key())
    raw = fred.get_series(series_id, observation_start=observation_start)

    df = raw.reset_index()
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"]).reset_index(drop=True)
    return df


def apply_transform(df: pd.DataFrame, transform: str | None) -> pd.DataFrame:
    """Apply an optional transform to a tidy series DataFrame.

    Currently supports ``"yoy"`` — year-over-year % change for monthly data
    (12-period change). Returns the input unchanged for ``None``.
    """
    if transform is None or df.empty:
        return df

    if transform == "yoy":
        out = df.copy()
        out["value"] = out["value"].pct_change(periods=12) * 100.0
        return out.dropna(subset=["value"]).reset_index(drop=True)

    raise ValueError(f"Unknown transform: {transform!r}")


def latest_and_delta(df: pd.DataFrame) -> tuple[float | None, float | None]:
    """Return the most recent value and its change from the prior observation."""
    if df.empty:
        return None, None
    latest = float(df["value"].iloc[-1])
    delta = float(df["value"].iloc[-1] - df["value"].iloc[-2]) if len(df) > 1 else None
    return latest, delta
