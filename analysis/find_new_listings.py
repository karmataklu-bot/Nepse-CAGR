#!/usr/bin/env python3
"""
Find all NEPSE stocks listed after a given date, calculate CAGR for each,
and save results to a CSV file.

Usage:
    python3 find_new_listings.py
    python3 find_new_listings.py --after 2022-09-25 --data-dir ./data --output new_listings_cagr.csv
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# ── Import from your existing nepse_cagr.py ──────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
from nepse_cagr import calculate_cagr, get_all_symbols

DEFAULT_DATA_DIR  = Path(__file__).parent.parent / "data"
DEFAULT_AFTER     = date(2022, 9, 25)
DEFAULT_OUTPUT    = "new_listings_cagr.csv"
DEFAULT_INVESTMENT = 100_000


def get_first_trading_date(symbol: str, data_dir: Path) -> date | None:
    """Return the earliest date in prices.csv for this symbol."""
    path = data_dir / "company-wise" / symbol / "prices.csv"
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, parse_dates=["date"], usecols=["date"])
        return df["date"].min().date()
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="CAGR for stocks listed after a given date.")
    parser.add_argument("--after",      default=str(DEFAULT_AFTER),
                        help=f"Only include stocks first listed after this date (default: {DEFAULT_AFTER})")
    parser.add_argument("--data-dir",   type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output",     default=DEFAULT_OUTPUT,
                        help=f"Output CSV filename (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--investment", type=float, default=DEFAULT_INVESTMENT)
    args = parser.parse_args()

    try:
        cutoff = datetime.strptime(args.after, "%Y-%m-%d").date()
    except ValueError:
        sys.exit("❌  --after must be YYYY-MM-DD")

    end_date = date.today()

    print(f"\n  Finding stocks first listed after : {cutoff}")
    print(f"  Data directory                    : {args.data_dir}")
    print(f"  Investment                        : Rs. {args.investment:,.0f}")
    print(f"  Output                            : {args.output}\n")

    all_symbols = get_all_symbols(args.data_dir)
    total       = len(all_symbols)

    # ── Step 1: Filter to stocks listed after cutoff ──────────────────────
    print(f"  Scanning {total} stocks for first listing date...\n")
    new_listings = []
    for sym in all_symbols:
        first_date = get_first_trading_date(sym, args.data_dir)
        if first_date and first_date > cutoff:
            new_listings.append((sym, first_date))

    new_listings.sort(key=lambda x: x[1])  # sort by listing date
    print(f"  Found {len(new_listings)} stocks listed after {cutoff}:\n")
    for sym, fd in new_listings:
        print(f"    {sym:<16}  first trade: {fd}")

    if not new_listings:
        sys.exit("\n  No new listings found. Exiting.")

    # ── Step 2: Calculate CAGR for each ──────────────────────────────────
    print(f"\n  Calculating CAGR for {len(new_listings)} stocks...\n")
    results = []
    skipped = []

    for i, (sym, first_date) in enumerate(new_listings, 1):
        print(f"  [{i:>3}/{len(new_listings)}]  {sym:<16}", end="\r", flush=True)
        try:
            r = calculate_cagr(
                symbol=sym,
                start_date=first_date,       # start from actual listing date
                initial_investment=args.investment,
                data_dir=args.data_dir,
                verbose=False,
                end_date=None,               # through today
            )
            results.append({
                "symbol":            r["symbol"],
                "listing_date":      first_date,
                "end_date":          r["end_date"],
                "years":             r["years"],
                "start_price":       r["start_price"],
                "ltp":               r["ltp"],
                "initial_investment":r["initial_investment"],
                "total_units":       r["total_units_today"],
                "market_value":      r["market_value"],
                "cash_dividends":    r["total_cash_dividends"],
                "right_share_cost":  r["total_right_share_cost"],
                "total_invested":    r["total_invested"],
                "total_value":       r["todays_value"],
                "cagr_pct":          r["cagr_pct"],
            })
        except Exception as e:
            skipped.append((sym, str(e)))

    print(" " * 60, end="\r")  # clear progress line

    # ── Step 3: Sort by CAGR and save ────────────────────────────────────
    df_out = pd.DataFrame(results)
    df_out.sort_values("cagr_pct", ascending=False, inplace=True)
    df_out.reset_index(drop=True, inplace=True)

    output_path = Path(args.output)
    df_out.to_csv(output_path, index=False, float_format="%.2f")

    # ── Step 4: Print summary ─────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  New Listings CAGR  |  Listed after {cutoff}")
    print(f"{'='*55}")
    print(f"  {'#':<4} {'Symbol':<14} {'Listed':<12} {'Years':>5} {'CAGR':>8}")
    print(f"  {'-'*50}")
    for rank, row in df_out.iterrows():
        arrow = "▲" if row["cagr_pct"] >= 0 else "▼"
        print(f"  {rank+1:<4} {row['symbol']:<14} {str(row['listing_date']):<12} "
              f"{row['years']:>5.1f}  {arrow} {row['cagr_pct']:>6.2f}%")
    print(f"{'='*55}")

    if skipped:
        print(f"\n  ⚠️  Skipped {len(skipped)} stocks:")
        for sym, err in skipped:
            print(f"    {sym:<14}  {err}")

    print(f"\n  ✅  Results saved to: {output_path.resolve()}\n")


if __name__ == "__main__":
    main()
