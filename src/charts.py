"""Observable Plot chart rendering for Streamlit.

Observable Plot is a JavaScript library, so each chart is a self-contained HTML
snippet that imports Plot from the jsDelivr ESM CDN, receives its data as injected
JSON, and renders a responsive line/area chart into a div. The snippet is dropped
into the Streamlit app with ``st.components.v1.html``.
"""

from __future__ import annotations

import json

import pandas as pd

from .config import Series

PLOT_CDN = "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm"
CHART_HEIGHT = 230  # px drawn by Plot; the iframe is sized a touch taller in app.py

_TEMPLATE = r"""
<div id="__DIVID__" class="plot-wrap"></div>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
  body { margin: 0; }
  .plot-wrap {
    width: 100%;
    font-family: "Montserrat", "Helvetica Neue", Arial, sans-serif;
  }
  .plot-wrap figure { margin: 0; }
</style>
<script type="module">
  import * as Plot from "__PLOT_CDN__";

  const raw = __DATA__;
  const data = raw.map(d => ({ date: new Date(d.date + "T00:00:00Z"), value: d.value }));
  const el = document.getElementById("__DIVID__");
  const color = "__COLOR__";
  const height = __HEIGHT__;
  const zeroLine = __ZEROLINE__;
  const last = data[data.length - 1];

  function render() {
    if (!data.length) return;
    const width = el.clientWidth || 600;

    // Zoom the y-axis to the data range (don't force a zero baseline), so series
    // that move in a narrow band still show their variation. The area still fills
    // to y=0, which falls below the frame and reads as a fill from the bottom edge.
    let lo = Infinity, hi = -Infinity;
    for (const d of data) { if (d.value < lo) lo = d.value; if (d.value > hi) hi = d.value; }
    if (zeroLine) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
    const span = hi - lo;
    const pad = span > 0 ? span * 0.10 : (Math.abs(hi) * 0.10 || 1);
    const domain = [lo - pad, hi + pad];

    const marks = [
      Plot.areaY(data, { x: "date", y: "value", fill: color, fillOpacity: 0.10 }),
      Plot.lineY(data, { x: "date", y: "value", stroke: color, strokeWidth: 1.75 }),
    ];
    if (zeroLine) {
      marks.push(Plot.ruleY([0], { stroke: "#2C403A", strokeOpacity: 0.4, strokeWidth: 1, strokeDasharray: "3,3" }));
    }
    marks.push(Plot.dot([last], { x: "date", y: "value", fill: color, r: 3.5, stroke: "white", strokeWidth: 1.5 }));
    marks.push(Plot.tip(data, Plot.pointerX({ x: "date", y: "value" })));

    const plot = Plot.plot({
      width, height,
      marginLeft: 54, marginRight: 14, marginTop: 12, marginBottom: 26,
      style: { background: "transparent", color: "#2C403A", fontSize: "11px", fontFamily: "Montserrat, sans-serif" },
      x: { type: "utc", label: null, grid: false, ticks: 5 },
      y: { label: null, grid: true, ticks: 5, domain },
      marks,
    });
    el.replaceChildren(plot);
  }

  render();
  if (window.ResizeObserver) new ResizeObserver(render).observe(el);
</script>
"""


def _records(df: pd.DataFrame, scale: float) -> list[dict]:
    """Convert a tidy DataFrame into JSON-friendly {date, value} records."""
    return [
        {"date": d.strftime("%Y-%m-%d"), "value": round(float(v) / scale, 4)}
        for d, v in zip(df["date"], df["value"])
    ]


def observable_plot_html(df: pd.DataFrame, series: Series, height: int = CHART_HEIGHT) -> str:
    """Build a self-contained Observable Plot HTML snippet for one indicator."""
    records = _records(df, series.scale)
    zero_line = bool(df["value"].min() < 0) if not df.empty else False

    return (
        _TEMPLATE
        .replace("__PLOT_CDN__", PLOT_CDN)
        .replace("__DIVID__", f"plot-{series.key}")
        .replace("__DATA__", json.dumps(records))
        .replace("__COLOR__", series.color)
        .replace("__HEIGHT__", str(height))
        .replace("__ZEROLINE__", "true" if zero_line else "false")
    )
