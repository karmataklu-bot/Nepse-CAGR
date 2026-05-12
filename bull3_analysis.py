#!/usr/bin/env python3
"""
Bull 3 Analysis — All stocks over Bull 3 period.
Bottom: 2012-03-29  →  Top: 2016-07-27

Total_Return_% and Cagr_% include dividends, bonus shares, and rights.

Run with: python3 bull3_analysis.py
Output saved to: Research/bull3_all_stocks.csv
"""

import sys
import json
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from nepse_cagr import calculate_cagr, get_all_symbols

# ── Config ────────────────────────────────────────────────────────────────────

BULL3_START        = date(2012, 3, 29)   # Bear bottom — Bull 3 starts
BULL3_END          = date(2016, 7, 27)   # Bull top    — Bull 3 ends

DEFAULT_DATA_DIR   = Path(__file__).parent / "data"
DEFAULT_INVESTMENT = 100_000
RESEARCH_DIR       = Path(__file__).parent / "Research"
OUTPUT_FILENAME    = "bull3_all_stocks.csv"

# Load company names
_NAMES_PATH = Path(__file__).parent / "data" / "company_names.json"
_COMPANY_NAMES: dict = {}
if _NAMES_PATH.exists():
    with open(_NAMES_PATH) as f:
        _COMPANY_NAMES = json.load(f)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_stock_name(symbol: str) -> str:
    return _COMPANY_NAMES.get(symbol, symbol)


def get_actual_dates(symbol: str, data_dir: Path) -> tuple[date, date] | None:
    """
    Return (actual_start_date, actual_end_date).
    Start: on or after BULL3_START (stock may have listed later).
    End:   on or before BULL3_END  (never cross the bull top).
    """
    path = data_dir / "company-wise" / symbol / "prices.csv"
    try:
        df = pd.read_csv(path, parse_dates=["date"], usecols=["date", "ltp"])
        df.sort_values("date", ascending=True, inplace=True)

        after_start      = df[df["date"] >= pd.Timestamp(BULL3_START)]
        on_or_before_end = df[df["date"] <= pd.Timestamp(BULL3_END)]

        if after_start.empty or on_or_before_end.empty:
            return None

        actual_start = after_start.iloc[0]["date"].date()
        actual_end   = on_or_before_end.iloc[-1]["date"].date()
        return actual_start, actual_end
    except Exception:
        return None


def divider(char="=", width=62):
    print(f"\n  {char * width}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    data_dir = DEFAULT_DATA_DIR
    RESEARCH_DIR.mkdir(exist_ok=True)
    output_path = RESEARCH_DIR / OUTPUT_FILENAME

    divider()
    print(f"  NEPSE Bull 3 Analysis — All Stocks")
    print(f"  Period      : {BULL3_START}  →  {BULL3_END}")
    print(f"  Output      : Research/{OUTPUT_FILENAME}")
    print(f"  Returns     : Total return including div + bonus + rights")
    divider()

    all_symbols = get_all_symbols(data_dir)
    print(f"  Total symbols found: {len(all_symbols)}\n")

    results = []
    skipped = []

    for i, sym in enumerate(sorted(all_symbols), 1):
        print(f"  [{i:>4}/{len(all_symbols)}]  {sym:<16}", end="\r", flush=True)

        dates = get_actual_dates(sym, data_dir)
        if dates is None:
            skipped.append((sym, "no price data within Bull 3 window"))
            continue

        actual_start_date, actual_end_date = dates

        try:
            r = calculate_cagr(
                symbol=sym,
                start_date=actual_start_date,
                initial_investment=DEFAULT_INVESTMENT,
                data_dir=data_dir,
                verbose=False,
                end_date=actual_end_date,
            )
        except Exception as e:
            skipped.append((sym, f"could not calculate CAGR: {e}"))
            continue

        total_return_pct = round(
            (r["todays_value"] / r["total_invested"] - 1) * 100, 2
        )

        results.append({
            "#":             None,
            "ticker":        sym,
            "name":          get_stock_name(sym),
            "start_date":    actual_start_date,
            "end_date":      actual_end_date,
            "start_price":   r["start_price"],
            "end_price":     r["ltp"],
            "total_return_%": total_return_pct,
            "cagr_%":        r["cagr_pct"],
        })

    print(" " * 60, end="\r")

    if not results:
        print("  No results. Check your data directory.")
        return

    # Sort by cagr_% descending
    df_out = pd.DataFrame(results)
    df_out.sort_values("cagr_%", ascending=False, inplace=True)
    df_out.reset_index(drop=True, inplace=True)
    df_out["#"] = df_out.index + 1
    cols = ["#"] + [c for c in df_out.columns if c != "#"]
    df_out = df_out[cols]

    df_out.to_csv(output_path, index=False, float_format="%.2f")

    # ── Terminal table ────────────────────────────────────────────────────
    divider("=")
    print(f"  {'#':<5} {'Ticker':<10} {'Name':<26} {'Start Date':<13} {'End Date':<13} "
          f"{'Start Px':>10} {'End Px':>10} {'Total Ret':>11} {'CAGR %':>9}")
    print(f"  {'-'*110}")

    for _, row in df_out.iterrows():
        arrow  = "▲" if row["cagr_%"] >= 0 else "▼"
        name_t = str(row["name"])[:24]
        print(f"  {int(row['#']):<5} {row['ticker']:<10} {name_t:<26} "
              f"{str(row['start_date']):<13} {str(row['end_date']):<13} "
              f"{row['start_price']:>10.2f} {row['end_price']:>10.2f} "
              f"{row['total_return_%']:>10.2f}% {arrow}{row['cagr_%']:>7.2f}%")

    divider("=")
    print(f"  {len(results)} stocks analysed over Bull 3  ({BULL3_START} → {BULL3_END})")

    cagrs = df_out["cagr_%"]
    print(f"\n  Median CAGR : {cagrs.median():.2f}%")
    print(f"  Mean CAGR   : {cagrs.mean():.2f}%")
    print(f"  Best        : {df_out.iloc[0]['ticker']}  {cagrs.iloc[0]:.2f}%")
    print(f"  Worst       : {df_out.iloc[-1]['ticker']}  {cagrs.iloc[-1]:.2f}%")
    print(f"  +ve CAGR    : {(cagrs > 0).sum()} stocks")
    print(f"  -ve CAGR    : {(cagrs < 0).sum()} stocks")

    if skipped:
        print(f"\n  Skipped {len(skipped)} stocks:")
        for sym, reason in skipped:
            print(f"    {sym:<16}  {reason}")

    print(f"\n  Saved → {output_path.resolve()}\n")


if __name__ == "__main__":
    main()
