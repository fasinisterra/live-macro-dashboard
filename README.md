# 📈 Live Macro Dashboard

A single-page dashboard that pulls nine U.S. macro indicators **live from the
[FRED API](https://fred.stlouisfed.org/docs/api/fred/)** and charts each one with
the [Observable Plot](https://observablehq.com/plot/) library, wrapped in
[Streamlit](https://streamlit.io). No more bouncing between FRED pages.

## Indicators

| Indicator | FRED series | Units | Frequency |
|---|---|---|---|
| M2 Money Supply | [`M2SL`](https://fred.stlouisfed.org/series/M2SL) | Billions of $ (SA) | Monthly |
| 10-Year Treasury Rate | [`DGS10`](https://fred.stlouisfed.org/series/DGS10) | Percent | Daily |
| Headline CPI (YoY %) | [`CPIAUCSL`](https://fred.stlouisfed.org/series/CPIAUCSL) | YoY % change | Monthly |
| Real GDP | [`GDPC1`](https://fred.stlouisfed.org/series/GDPC1) | Chained 2017 $ | Quarterly |
| Unemployment Rate | [`UNRATE`](https://fred.stlouisfed.org/series/UNRATE) | Percent | Monthly |
| Housing Starts | [`HOUST`](https://fred.stlouisfed.org/series/HOUST) | Thousands (SAAR) | Monthly |
| Financial Stress Index | [`STLFSI4`](https://fred.stlouisfed.org/series/STLFSI4) | Index | Weekly |
| WTI Crude Oil | [`DCOILWTICO`](https://fred.stlouisfed.org/series/DCOILWTICO) | $ / barrel | Daily |
| US Dollar Index | [`DTWEXBGS`](https://fred.stlouisfed.org/series/DTWEXBGS) | Broad index | Daily |

> The headline CPI card shows the year-over-year % change (the inflation rate),
> not the raw index. The dollar index uses the Fed's Nominal Broad trade-weighted
> index — the classic ICE "DXY" is not available on FRED.

## Project structure

```
.
├── app.py                     # Page 1 — the dashboard (layout + render loop)
├── pages/
│   └── 1_📊_Correlation_&_Analytics.py   # Page 2 — correlation & statistics
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   ├── config.toml            # theme + server config
│   └── secrets.toml.example   # template for your FRED key (copy to secrets.toml)
├── src/
│   ├── config.py              # the nine-series registry + value formatting
│   ├── fred.py                # FRED fetch, transforms, API-key loading
│   ├── data.py                # shared @st.cache_data loaders (used by both pages)
│   ├── charts.py              # Observable Plot HTML builder (dashboard)
│   ├── analytics.py           # panel alignment, correlation, rolling, lead/lag, regression
│   └── analytics_charts.py    # Observable Plot builders (heatmap, scatter, etc.)
└── scripts/
    └── preview_data.py        # pull every series live and print it (sanity check)
```

This is a **Streamlit multipage app**: `app.py` is the dashboard, and the file in
`pages/` becomes a second page in the sidebar nav.

## 1. Get a free FRED API key

Create a free account and request a key (delivered instantly):
👉 https://fredaccount.stlouisfed.org/apikeys

## 2. Run locally

```bash
# clone, then from the project root:
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# provide your key (either option works):
export FRED_API_KEY=your_key_here
#   ...or copy .streamlit/secrets.toml.example -> .streamlit/secrets.toml and edit it

# sanity-check the raw data first:
python scripts/preview_data.py

# launch the dashboard:
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## 3. Deploy on Streamlit Community Cloud (free)

1. Push this repo to GitHub.
2. Go to <https://share.streamlit.io>, click **New app**, and point it at this
   repo / branch / `app.py`.
3. Under **Advanced settings → Secrets**, paste:
   ```toml
   FRED_API_KEY = "your_key_here"
   ```
4. **Deploy.** Your dashboard goes live at `https://<your-app>.streamlit.app`.

Secrets are encrypted by Streamlit and injected at runtime — they are never in the
repo. `.streamlit/secrets.toml` is gitignored for the same reason.

## Correlation & Analytics page

The second page studies how the nine indicators *relate*. The key methodological
choice: every series is resampled to a **common monthly frequency** and you correlate
**changes** (year-over-year %, month-over-month %, or first differences) rather than
raw levels. Most of these series trend over time, so correlating levels would produce
spurious ~0.9 correlations driven purely by a shared time trend — correlating changes
measures whether they genuinely move together.

It includes:
- **Correlation heatmap** (9×9, diverging color, Pearson or Spearman)
- **Auto-insights** — strongest positive / inverse / largest-magnitude pairs
- **Pairwise explorer** — scatter with OLS regression line, R², slope, and a
  rolling-window correlation showing how a relationship evolves over time
- **Lead/lag** — cross-correlation across ±12 months to spot leading indicators
  (e.g. M2 money growth tends to lead CPI by roughly a year)
- **Standardized overlay** — z-scored series on one scale to compare regimes

All charts are Observable Plot. Controls (transform, method, lookback, rolling window)
live in the sidebar and recompute everything live.

## How it works

- **`src/fred.py`** reads the key from `st.secrets` or `FRED_API_KEY`, fetches each
  series via the [`fredapi`](https://github.com/mortada/fredapi) wrapper, and returns
  a tidy `date, value` DataFrame. Fetches are cached for one hour via
  `st.cache_data`, so the dashboard is live but doesn't hammer the API on every rerun.
- **`src/charts.py`** turns a series into a self-contained Observable Plot snippet —
  Plot is imported from the jsDelivr ESM CDN, the data is injected as JSON, and the
  chart renders responsively inside a Streamlit `components.html` iframe.
- **`app.py`** lays the nine indicators out in a two-column grid, each with a latest
  value, change-since-prior, and its chart. A sidebar controls the lookback window
  and forces a data refresh.
