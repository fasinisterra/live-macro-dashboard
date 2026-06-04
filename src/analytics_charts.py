"""Observable Plot chart builders for the analytics page (Wall Street Prompt skin).

Same approach as ``src/charts.py``: each function returns a self-contained HTML
snippet that imports Observable Plot from the jsDelivr ESM CDN, embeds its data as
JSON, and renders responsively. Styled to the WSP template — Montserrat type,
slate axes, and a slate→green diverging palette for correlations.
"""

from __future__ import annotations

import json

import pandas as pd

PLOT_CDN = "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm"

# Brand tokens (mirror src/branding.py).
GREEN = "#37A686"
MINT = "#52F2B8"
SLATE = "#2C403A"
FOG = "#EEF1F0"
BORDER = "#E2E5E3"

# JS shell: defines `width`, `HEIGHT`, and `BASE_STYLE`; runs `render()` which
# must build `plot`.
_SHELL = """
<div id="__DIV__" class="plot-wrap"></div>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
  body { margin: 0; }
  .plot-wrap { width: 100%; font-family: "Montserrat", "Helvetica Neue", Arial, sans-serif; }
  .plot-wrap figure { margin: 0; }
</style>
<script type="module">
  import * as Plot from "__CDN__";
  const el = document.getElementById("__DIV__");
  const HEIGHT = __HEIGHT__;
  const BASE_STYLE = { background: "transparent", color: "#2C403A", fontSize: "11px", fontFamily: "Montserrat, sans-serif" };
  function render() {
    const width = el.clientWidth || 700;
    let plot;
__BODY__
    el.replaceChildren(plot);
  }
  render();
  if (window.ResizeObserver) new ResizeObserver(render).observe(el);
</script>
"""


def _wrap(div_id: str, body: str, height: int) -> str:
    return (
        _SHELL.replace("__DIV__", div_id)
        .replace("__CDN__", PLOT_CDN)
        .replace("__HEIGHT__", str(height))
        .replace("__BODY__", body)
    )


def heatmap_html(corr: pd.DataFrame, short: dict[str, str], height: int = 470) -> str:
    """Correlation matrix as a diverging cell heatmap with value labels."""
    keys = list(corr.columns)
    domain = [short[k] for k in keys]
    records = []
    for rk in keys:
        for ck in keys:
            r = corr.loc[rk, ck]
            records.append({"x": short[ck], "y": short[rk], "r": None if pd.isna(r) else round(float(r), 3)})

    body = (
        "const data = " + json.dumps(records) + ";\n"
        "const domain = " + json.dumps(domain) + ";\n"
        "plot = Plot.plot({\n"
        "  width, height: HEIGHT, style: BASE_STYLE,\n"
        "  marginLeft: 78, marginTop: 58, marginRight: 14, marginBottom: 6,\n"
        "  padding: 0.03,\n"
        "  x: { axis: 'top', domain, tickRotate: -40, label: null },\n"
        "  y: { domain, label: null },\n"
        "  color: { type: 'linear', domain: [-1, 0, 1], range: ['#2C403A', '#EEF1F0', '#37A686'],\n"
        "    legend: true, label: 'Correlation (r)' },\n"
        "  marks: [\n"
        "    Plot.cell(data, { x: 'x', y: 'y', fill: 'r', inset: 0.5 }),\n"
        "    Plot.text(data, { x: 'x', y: 'y', text: d => d.r == null ? '' : d.r.toFixed(2),\n"
        "      fill: d => (d.r != null && Math.abs(d.r) > 0.5) ? 'white' : '#2C403A', fontSize: 11 }),\n"
        "  ],\n"
        "});\n"
    )
    return _wrap("hm", body, height)


def scatter_regression_html(df: pd.DataFrame, x_label: str, y_label: str, color: str, height: int = 320) -> str:
    """Scatter of two transformed series with an OLS regression line + CI band."""
    records = [{"x": round(float(a), 5), "y": round(float(b), 5)} for a, b in zip(df["x"], df["y"])]
    body = (
        "const data = " + json.dumps(records) + ";\n"
        "plot = Plot.plot({\n"
        "  width, height: HEIGHT, style: BASE_STYLE,\n"
        "  marginLeft: 54, marginBottom: 40, marginRight: 16, marginTop: 12,\n"
        "  grid: true,\n"
        "  x: { label: " + json.dumps(x_label + "  →") + " },\n"
        "  y: { label: " + json.dumps("↑  " + y_label) + " },\n"
        "  marks: [\n"
        "    Plot.ruleX([0], { stroke: '#E2E5E3' }), Plot.ruleY([0], { stroke: '#E2E5E3' }),\n"
        "    Plot.dot(data, { x: 'x', y: 'y', r: 2.6, fill: " + json.dumps(color) + ", fillOpacity: 0.5 }),\n"
        "    Plot.linearRegressionY(data, { x: 'x', y: 'y', stroke: '#2C403A', strokeWidth: 1.6 }),\n"
        "  ],\n"
        "});\n"
    )
    return _wrap("sc", body, height)


def rolling_corr_html(s: pd.Series, color: str, height: int = 240) -> str:
    """Rolling correlation through time, bounded to [-1, 1] with a zero rule."""
    records = [{"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 4)} for d, v in s.items()]
    body = (
        "const raw = " + json.dumps(records) + ";\n"
        "const data = raw.map(d => ({ date: new Date(d.date + 'T00:00:00Z'), value: d.value }));\n"
        "plot = Plot.plot({\n"
        "  width, height: HEIGHT, style: BASE_STYLE,\n"
        "  marginLeft: 40, marginBottom: 26, marginRight: 14, marginTop: 12,\n"
        "  x: { type: 'utc', label: null, ticks: 6 },\n"
        "  y: { domain: [-1, 1], grid: true, label: null, ticks: 5 },\n"
        "  marks: [\n"
        "    Plot.ruleY([0], { stroke: '#2C403A', strokeOpacity: 0.4, strokeDasharray: '3,3' }),\n"
        "    Plot.areaY(data, { x: 'date', y: 'value', fill: " + json.dumps(color) + ", fillOpacity: 0.10 }),\n"
        "    Plot.lineY(data, { x: 'date', y: 'value', stroke: " + json.dumps(color) + ", strokeWidth: 1.8 }),\n"
        "  ],\n"
        "});\n"
    )
    return _wrap("rc", body, height)


def cross_corr_html(df: pd.DataFrame, lead_label: str, peak_lag: int, height: int = 260) -> str:
    """Cross-correlation bar chart across lags; the peak lag is highlighted."""
    records = [{"lag": int(l), "corr": None if pd.isna(c) else round(float(c), 4)} for l, c in zip(df["lag"], df["corr"])]
    body = (
        "const data = " + json.dumps(records) + ";\n"
        "const peak = " + json.dumps(int(peak_lag)) + ";\n"
        "plot = Plot.plot({\n"
        "  width, height: HEIGHT, style: BASE_STYLE,\n"
        "  marginLeft: 40, marginBottom: 38, marginRight: 14, marginTop: 12,\n"
        "  x: { label: " + json.dumps("Lag (months) — positive ⇒ " + lead_label + " leads") + ", tickFormat: '+d' },\n"
        "  y: { domain: [-1, 1], grid: true, label: 'r' },\n"
        "  marks: [\n"
        "    Plot.ruleY([0], { stroke: '#2C403A' }),\n"
        "    Plot.barY(data, { x: 'lag', y: 'corr',\n"
        "      fill: d => d.corr >= 0 ? '#37A686' : '#2C403A',\n"
        "      fillOpacity: d => d.lag === peak ? 1 : 0.5 }),\n"
        "  ],\n"
        "});\n"
    )
    return _wrap("cc", body, height)


def zscore_overlay_html(long_df: pd.DataFrame, labels: list[str], colors: list[str], height: int = 300) -> str:
    """Standardized (z-scored) multi-series overlay for comparing regimes."""
    records = [
        {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 4), "series": str(name)}
        for d, v, name in zip(long_df["date"], long_df["value"], long_df["series"])
    ]
    body = (
        "const raw = " + json.dumps(records) + ";\n"
        "const data = raw.map(d => ({ ...d, date: new Date(d.date + 'T00:00:00Z') }));\n"
        "plot = Plot.plot({\n"
        "  width, height: HEIGHT, style: BASE_STYLE,\n"
        "  marginLeft: 40, marginBottom: 26, marginRight: 16, marginTop: 12,\n"
        "  x: { type: 'utc', label: null, ticks: 6 },\n"
        "  y: { grid: true, label: 'z-score' },\n"
        "  color: { domain: " + json.dumps(labels) + ", range: " + json.dumps(colors) + ", legend: true },\n"
        "  marks: [\n"
        "    Plot.ruleY([0], { stroke: '#C9D2CE' }),\n"
        "    Plot.lineY(data, { x: 'date', y: 'value', stroke: 'series', strokeWidth: 1.6 }),\n"
        "  ],\n"
        "});\n"
    )
    return _wrap("zo", body, height)
