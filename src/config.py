"""Registry of the nine macro indicators tracked on the dashboard.

Each indicator maps to a single FRED series. The metadata here drives both the
data layer (which series to pull, how to transform it) and the presentation layer
(labels, units, value formatting, chart color). To add an indicator, append a
``Series`` entry below — nothing else needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Series:
    key: str            # short internal id, e.g. "m2"
    series_id: str      # FRED series id, e.g. "M2SL"
    label: str          # display title on the card
    units: str          # human-readable units shown under the chart
    frequency: str      # "Daily" / "Weekly" / "Monthly" / "Quarterly"
    transform: str | None  # None or "yoy" (year-over-year % change)
    color: str          # accent hex color for the chart
    prefix: str = ""    # value prefix, e.g. "$"
    suffix: str = ""    # value suffix, e.g. "%" / "T" / "K"
    scale: float = 1.0  # divide raw value by this before display (e.g. 1000 -> trillions)
    decimals: int = 2   # decimal places in the displayed value

    @property
    def fred_url(self) -> str:
        return f"https://fred.stlouisfed.org/series/{self.series_id}"

    def format_value(self, value: float | None) -> str:
        """Format a raw FRED value for display, e.g. 4.35 -> '4.35%'."""
        if value is None:
            return "—"
        return f"{self.prefix}{value / self.scale:,.{self.decimals}f}{self.suffix}"

    def format_delta(self, value: float | None) -> str | None:
        """Format a change-from-prior value with an explicit sign."""
        if value is None:
            return None
        scaled = value / self.scale
        return f"{scaled:+,.{self.decimals}f}{self.suffix}"


# The nine indicators, in display order. Series ids verified active on FRED.
SERIES: list[Series] = [
    Series(
        key="m2",
        series_id="M2SL",
        label="M2 Money Supply",
        units="Trillions of $ (seasonally adjusted)",
        frequency="Monthly",
        transform=None,
        color="#2563eb",
        prefix="$",
        suffix="T",
        scale=1000,  # FRED reports billions; show trillions
        decimals=2,
    ),
    Series(
        key="dgs10",
        series_id="DGS10",
        label="10-Year Treasury Rate",
        units="Percent yield (constant maturity)",
        frequency="Daily",
        transform=None,
        color="#dc2626",
        suffix="%",
        decimals=2,
    ),
    Series(
        key="cpi",
        series_id="CPIAUCSL",
        label="Headline CPI (YoY %)",
        units="Year-over-year % change, all items",
        frequency="Monthly",
        transform="yoy",
        color="#ea580c",
        suffix="%",
        decimals=1,
    ),
    Series(
        key="gdp",
        series_id="GDPC1",
        label="Real GDP",
        units="Trillions of chained 2017 $ (SAAR)",
        frequency="Quarterly",
        transform=None,
        color="#16a34a",
        prefix="$",
        suffix="T",
        scale=1000,  # FRED reports billions; show trillions
        decimals=2,
    ),
    Series(
        key="unrate",
        series_id="UNRATE",
        label="Unemployment Rate",
        units="Percent of labor force (seasonally adjusted)",
        frequency="Monthly",
        transform=None,
        color="#9333ea",
        suffix="%",
        decimals=1,
    ),
    Series(
        key="houst",
        series_id="HOUST",
        label="Housing Starts",
        units="Thousands of units (SAAR)",
        frequency="Monthly",
        transform=None,
        color="#0891b2",
        suffix="K",
        decimals=0,
    ),
    Series(
        key="stress",
        series_id="STLFSI4",
        label="Financial Stress Index",
        units="St. Louis Fed index (0 = average stress)",
        frequency="Weekly",
        transform=None,
        color="#b91c1c",
        decimals=2,
    ),
    Series(
        key="wti",
        series_id="DCOILWTICO",
        label="WTI Crude Oil",
        units="$ per barrel (Cushing, OK)",
        frequency="Daily",
        transform=None,
        color="#4d7c0f",
        prefix="$",
        decimals=2,
    ),
    Series(
        key="dollar",
        series_id="DTWEXBGS",
        label="US Dollar Index",
        units="Nominal Broad index (Jan 2006 = 100)",
        frequency="Daily",
        transform=None,
        color="#1d4ed8",
        decimals=2,
    ),
]
