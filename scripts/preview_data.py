"""Step 3 — pull every indicator live from FRED and print what comes back.

Run this BEFORE charting to confirm the raw data is solid:

    export FRED_API_KEY=your_key_here
    python scripts/preview_data.py

For each of the nine series it prints the row count, date range, latest value,
and the last few observations.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make ``src`` importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SERIES  # noqa: E402
from src.fred import apply_transform, latest_and_delta, load_series  # noqa: E402


def main() -> int:
    print(f"Pulling {len(SERIES)} series live from FRED...\n")
    failures = 0

    for s in SERIES:
        header = f"{s.label}  [{s.series_id}]"
        print("=" * 72)
        print(header)
        print("-" * 72)
        try:
            df = load_series(s.series_id)
            df = apply_transform(df, s.transform)

            if df.empty:
                print("  !! No observations returned.")
                failures += 1
                continue

            start = df["date"].iloc[0].date()
            end = df["date"].iloc[-1].date()
            latest, delta = latest_and_delta(df)

            print(f"  rows:        {len(df):,}")
            print(f"  date range:  {start}  ->  {end}")
            print(f"  units:       {s.units}  ({s.frequency})")
            print(f"  latest:      {s.format_value(latest)}"
                  + (f"   (Δ {s.format_delta(delta)} vs prior)" if delta is not None else ""))
            print("  last 5 observations:")
            tail = df.tail(5)
            for d, v in zip(tail["date"], tail["value"]):
                print(f"     {d.date()}   {v:,.4f}")
        except Exception as exc:  # noqa: BLE001 — surface any per-series failure
            print(f"  !! FAILED: {type(exc).__name__}: {exc}")
            failures += 1
        print()

    print("=" * 72)
    if failures:
        print(f"Done with {failures} failure(s).")
        return 1
    print("All series pulled successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
