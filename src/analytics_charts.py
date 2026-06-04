"""Observable Plot chart builders for the analytics page.

Same approach as ``src/charts.py``: each function returns a self-contained HTML
snippet that imports Observable Plot from the jsDelivr ESM CDN, embeds its data as
JSON, and renders responsively. Dropped into Streamlit with ``components.html``.
"""

from __future__ import annotations

import json

import pandas as pd

PLOT_CDN = "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm"

# JS shell: defines `width` and `HEIGHT`, runs `render()` which must build `plot`.
_SHELL = """
<div id="__DIV__" class="plot-wrap"></div>
<style>
  body { margin: 0; }
  .plot-wrap { width: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  .plot-wrap figure { margin: 0; }
</style>
<script type="module">
  import * as Plot from "__CDN__";
  import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
  const el = document.getElementById("__DIV__");
  const HEIGHT = __HEIGHT__;
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
        "  width, height: HEIGHT,\n"
        "  marginLeft: 78, marginTop: 58, marginRight: 14, marginBottom: 6,\n"
        "  padding: 0.03,\n"
        "  x: { axis: 'top', domain, tickRotate: -40, label: null },\n"
        "  y: { domain, label: null },\n"
        "  color: { type: 'diverging', scheme: 'RdBu', domain: [-1, 1], pivot: 0, legend: true, label: 'Correlation (r)' },\n"
        "  marks: [\n"
        "    Plot.cell(data, { x: 'x', y: 'y', fill: 'r', inset: 0.5 }),\n"
        "    Plot.text(data, { x: 'x', y: 'y', text: d => d.r == null ? '' : d.r.toFixed(2),\n"
        "      fill: d => (d.r != null && Math.abs(d.r) > 0.55) ? 'white' : '#1a2230', fontSize: 11 }),\n"
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
        "  width, height: HEIGHT,\n"
        "  marginLeft: 54, marginBottom: 40, marginRight: 16, marginTop: 12,\n"
        "  grid: true,\n"
        "  x: { label: " + json.dumps(x_label + "  →") + " },\n"
        "  y: { label: " + json.dumps("↑  " + y_label) + " },\n"
        "  marks: [\n"
        "    Plot.ruleX([0], { stroke: '#e2e8f0' }), Plot.ruleY([0], { stroke: '#e2e8f0' }),\n"
        "    Plot.dot(data, { x: 'x', y: 'y', r: 2.6, fill: " + json.dumps(color) + ", fillOpacity: 0.45 }),\n"
        "    Plot.linearRegressionY(data, { x: 'x', y: 'y', stroke: '#0f172a', strokeWidth: 1.6 }),\n"
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
        "  width, height: HEIGHT,\n"
        "  marginLeft: 40, marginBottom: 26, marginRight: 14, marginTop: 12,\n"
        "  x: { type: 'utc', label: null, ticks: 6 },\n"
        "  y: { domain: [-1, 1], grid: true, label: null, ticks: 5 },\n"
        "  marks: [\n"
        "    Plot.ruleY([0], { stroke: '#9ca3af', strokeDasharray: '3,3' }),\n"
        "    Plot.areaY(data, { x: 'date', y: 'value', fill: " + json.dumps(color) + ", fillOpacity: 0.08 }),\n"
        "    Plot.lineY(data, { x: 'date', y: 'value', stroke: " + json.dumps(color) + ", strokeWidth: 1.6 }),\n"
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
        "  width, height: HEIGHT,\n"
        "  marginLeft: 40, marginBottom: 38, marginRight: 14, marginTop: 12,\n"
        "  x: { label: " + json.dumps("Lag (months) — positive ⇒ " + lead_label + " leads") + ", tickFormat: '+d' },\n"
        "  y: { domain: [-1, 1], grid: true, label: 'r' },\n"
        "  marks: [\n"
        "    Plot.ruleY([0], { stroke: '#94a3b8' }),\n"
        "    Plot.barY(data, { x: 'lag', y: 'corr',\n"
        "      fill: d => d.corr >= 0 ? '#2563eb' : '#dc2626',\n"
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
        "  width, height: HEIGHT,\n"
        "  marginLeft: 40, marginBottom: 26, marginRight: 16, marginTop: 12,\n"
        "  x: { type: 'utc', label: null, ticks: 6 },\n"
        "  y: { grid: true, label: 'z-score' },\n"
        "  color: { domain: " + json.dumps(labels) + ", range: " + json.dumps(colors) + ", legend: true },\n"
        "  marks: [\n"
        "    Plot.ruleY([0], { stroke: '#cbd5e1' }),\n"
        "    Plot.lineY(data, { x: 'date', y: 'value', stroke: 'series', strokeWidth: 1.5 }),\n"
        "  ],\n"
        "});\n"
    )
    return _wrap("zo", body, height)
