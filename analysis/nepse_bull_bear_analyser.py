#!/usr/bin/env python3
"""
NEPSE Bull/Bear Analyser
========================
Stock-level CAGR analysis across NEPSE market cycles.

Cycles (from memory/nepse_cycles.md):
  Bull 1: 1994-01-13 → 2000-11-23   (index   100 →   545.82)
  Bear 1: 2000-11-23 → 2002-03-15   (index 545.82 →   186.22)
  Bull 2: 2002-03-15 → 2008-08-31   (index 186.22 → 1,175.38)
  Bear 2: 2008-08-31 → 2012-03-29   (index 1,175.38 → 298.90)
  Bull 3: 2012-03-29 → 2016-07-27   (index 298.90 → 1,881.45)
  Bear 3: 2016-07-27 → 2019-03-05   (index 1,881.45 → 1,098.95)
  Bull 4: 2019-03-05 → 2021-08-18   (index 1,098.95 → 3,198.60)
  Bear 4: 2021-08-18 → 2022-09-25   (index 3,198.60 → 1,815.13)
  Bull 5: 2022-09-25 → today        (in progress, top not yet reached)

Per stock, output columns:
  #, Ticker, Name, Start_Date, End_Date, Start_Price, End_Price,
  Total_Return_%, Cagr_%, # of Yrs, Multiple

CAGR includes dividends + bonus shares + right shares (from nepse_cagr.py).

Window mode:
  full    — entire selected period
  shaved  — skip bottom-15% of index move + top-15% of index move
            (price-based using NEPSE index history.csv; falls back to
             time-based shave when no daily index data exists pre-2011)

Output: .xlsx workbook with one sheet per cycle x mode and an
        Analysis sheet comparing full vs shaved for each cycle.

Usage:
  python3 nepse_bull_bear_analyser.py                       # interactive
  python3 nepse_bull_bear_analyser.py --period bull4 --mode both
  python3 nepse_bull_bear_analyser.py --period bull3,bull4 --mode full
  python3 nepse_bull_bear_analyser.py --period all --mode shaved
"""

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from nepse_cagr import calculate_cagr, get_all_symbols

# Config

DEFAULT_DATA_DIR    = Path(__file__).parent.parent / "data"
DEFAULT_INVESTMENT  = 100_000
RESEARCH_DIR        = Path(__file__).parent.parent / "Research"
INDEX_HISTORY_PATH  = DEFAULT_DATA_DIR / "index" / "nepse" / "history.csv"
SHAVE_FRACTION      = 0.15
NAMES_PATH          = DEFAULT_DATA_DIR / "company_names.json"

CYCLES = {
    "bull1": {
        "label": "Bull 1", "kind": "bull",
        "start_date": date(1994, 1, 13), "end_date": date(2000, 11, 23),
        "start_index": 100.0,  "end_index": 545.82,
    },
    "bear1": {
        "label": "Bear 1", "kind": "bear",
        "start_date": date(2000, 11, 23), "end_date": date(2002, 3, 15),
        "start_index": 545.82, "end_index": 186.22,
    },
    "bull2": {
        "label": "Bull 2", "kind": "bull",
        "start_date": date(2002, 3, 15), "end_date": date(2008, 8, 31),
        "start_index": 186.22, "end_index": 1175.38,
    },
    "bear2": {
        "label": "Bear 2", "kind": "bear",
        "start_date": date(2008, 8, 31), "end_date": date(2012, 3, 29),
        "start_index": 1175.38, "end_index": 298.90,
    },
    "bull3": {
        "label": "Bull 3", "kind": "bull",
        "start_date": date(2012, 3, 29), "end_date": date(2016, 7, 27),
        "start_index": 298.90, "end_index": 1881.45,
    },
    "bear3": {
        "label": "Bear 3", "kind": "bear",
        "start_date": date(2016, 7, 27), "end_date": date(2019, 3, 5),
        "start_index": 1881.45, "end_index": 1098.95,
    },
    "bull4": {
        "label": "Bull 4", "kind": "bull",
        "start_date": date(2019, 3, 5), "end_date": date(2021, 8, 18),
        "start_index": 1098.95, "end_index": 3198.60,
    },
    "bear4": {
        "label": "Bear 4", "kind": "bear",
        "start_date": date(2021, 8, 18), "end_date": date(2022, 9, 25),
        "start_index": 3198.60, "end_index": 1815.13,
    },
    "bull5": {
        "label": "Bull 5 (in progress)", "kind": "bull",
        "start_date": date(2022, 9, 25), "end_date": date.today(),
        "start_index": 1815.13, "end_index": None,
    },
}

ENTIRE_KEY = "all"
ENTIRE_DEF = {
    "label": "Entire NEPSE History",
    "kind": "all",
    "start_date": date(1994, 1, 13),
    "end_date": date.today(),
    "start_index": 100.0,
    "end_index": None,
}


# Helpers

_COMPANY_NAMES: dict = {}
if NAMES_PATH.exists():
    try:
        with open(NAMES_PATH) as f:
            _COMPANY_NAMES = json.load(f)
    except Exception:
        _COMPANY_NAMES = {}


def _clean_company_name(name: str) -> str:
    """
    Remove trailing ticker symbol in parentheses from company names.
    e.g. "CYC Nepal Laghubitta Bittiya Sanstha Limited ( CYCL )" -> "CYC Nepal Laghubitta Bittiya Sanstha Limited"
    Handles patterns like "( TICKER )" with varying whitespace at the end of the string.
    """
    cleaned = re.sub(r'\s*\(\s*[A-Z0-9]+\s*\)\s*$', '', name).strip()
    return cleaned if cleaned else name


def get_stock_name(symbol: str) -> str:
    raw = _COMPANY_NAMES.get(symbol, symbol)
    return _clean_company_name(raw)


def get_cycle(key: str) -> dict:
    if key == ENTIRE_KEY:
        return ENTIRE_DEF
    return CYCLES[key]


def load_index_history(path: Path = INDEX_HISTORY_PATH):
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, parse_dates=["date"], usecols=["date", "close"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception:
        return None


# Shave window resolution

def resolve_shaved_window(cycle: dict, index_df) -> tuple[date, date, str]:
    """
    Price-based shave (preferred):
      threshold_low  = start_index + 0.15 * (end_index - start_index)
      threshold_high = end_index   - 0.15 * (end_index - start_index)
      For bulls:  shaved_start = first date >= start_date where index >= low
                  shaved_end   = last  date <= end_date   where index >= high
      For bears:  shaved_start = first date >= start_date where index <= low
                  shaved_end   = last  date <= end_date   where index <= high

    Time-based fallback when no index data available:
      shaved_start = start_date + 15% of date span
      shaved_end   = end_date   - 15% of date span
    """
    full_start = cycle["start_date"]
    full_end   = cycle["end_date"]
    start_idx  = cycle["start_index"]
    end_idx    = cycle["end_index"]

    if start_idx is None or end_idx is None or index_df is None:
        return _time_based_shave(full_start, full_end)

    sub = index_df[
        (index_df["date"].dt.date >= full_start) &
        (index_df["date"].dt.date <= full_end)
    ]
    if sub.empty:
        return _time_based_shave(full_start, full_end)

    move          = end_idx - start_idx
    threshold_low = start_idx + SHAVE_FRACTION * move
    threshold_hi  = end_idx   - SHAVE_FRACTION * move
    kind          = cycle["kind"]

    if kind == "bull":
        crossed_low = sub[sub["close"] >= threshold_low]
        below_hi    = sub[sub["close"] <= threshold_hi]
    else:
        crossed_low = sub[sub["close"] <= threshold_low]
        below_hi    = sub[sub["close"] >= threshold_hi]

    if crossed_low.empty or below_hi.empty:
        return _time_based_shave(full_start, full_end)

    shaved_start = crossed_low.iloc[0]["date"].date()
    shaved_end   = below_hi.iloc[-1]["date"].date()

    if shaved_start >= shaved_end:
        return _time_based_shave(full_start, full_end)

    note = (f"price-based: index {threshold_low:.2f} -> {threshold_hi:.2f}; "
            f"dates {shaved_start} -> {shaved_end}")
    return shaved_start, shaved_end, note


def _time_based_shave(start: date, end: date) -> tuple[date, date, str]:
    span_days    = (end - start).days
    shave_days   = int(round(span_days * SHAVE_FRACTION))
    shaved_start = start + timedelta(days=shave_days)
    shaved_end   = end   - timedelta(days=shave_days)
    note = f"time-based: shave {shave_days}d each end ({shaved_start} -> {shaved_end})"
    return shaved_start, shaved_end, note


# Per-stock window resolver

def actual_stock_window(symbol: str, win_start: date, win_end: date,
                        data_dir: Path):
    """
    Clip the window to dates actually present in the stock's prices.csv.
    Returns (actual_start, actual_end) or None if no overlap.
    """
    path = data_dir / "company-wise" / symbol / "prices.csv"
    try:
        df = pd.read_csv(path, parse_dates=["date"], usecols=["date", "ltp"])
        df.sort_values("date", inplace=True)
        after_start = df[df["date"] >= pd.Timestamp(win_start)]
        before_end  = df[df["date"] <= pd.Timestamp(win_end)]
        if after_start.empty or before_end.empty:
            return None
        a_start = after_start.iloc[0]["date"].date()
        a_end   = before_end.iloc[-1]["date"].date()
        if a_start >= a_end:
            return None
        return a_start, a_end
    except Exception:
        return None


# Per-cycle stock-level analyser

def analyse_cycle(win_start: date, win_end: date,
                  data_dir: Path,
                  investment: float,
                  show_progress: bool = True) -> tuple[pd.DataFrame, list]:
    all_symbols = get_all_symbols(data_dir)
    results = []
    skipped = []

    for i, sym in enumerate(sorted(all_symbols), 1):
        if show_progress:
            print(f"  [{i:>4}/{len(all_symbols)}]  {sym:<16}", end="\r", flush=True)

        win = actual_stock_window(sym, win_start, win_end, data_dir)
        if win is None:
            skipped.append((sym, "no price data within window"))
            continue
        s_start, s_end = win

        try:
            r = calculate_cagr(
                symbol=sym,
                start_date=s_start,
                initial_investment=investment,
                data_dir=data_dir,
                verbose=False,
                end_date=s_end,
            )
        except Exception as e:
            skipped.append((sym, f"cagr error: {e}"))
            continue

        total_ret = (r["todays_value"] / r["total_invested"] - 1) * 100
        multiple  = r["todays_value"] / r["total_invested"]

        results.append({
            "#":              None,
            "Ticker":         sym,
            "Name":           get_stock_name(sym),
            "Start_Date":     r["start_date"],
            "End_Date":       r["end_date"],
            "Start_Price":    round(r["start_price"], 2),
            "End_Price":      round(r["ltp"], 2),
            "Total_Return_%": round(total_ret, 2),
            "Cagr_%":         round(r["cagr_pct"], 2),
            "# of Yrs":       round(r["years"], 2),
            "Multiple":       round(multiple, 2),
        })

    if show_progress:
        print(" " * 60, end="\r")

    if not results:
        return pd.DataFrame(), skipped

    df = pd.DataFrame(results)
    df.sort_values("Cagr_%", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["#"] = df.index + 1
    return df, skipped


# Analysis sheet

def build_analysis_rows(cycle: dict,
                        full_df: pd.DataFrame,
                        shaved_df: pd.DataFrame,
                        full_window: tuple[date, date],
                        shaved_window: tuple[date, date],
                        shaved_note: str) -> pd.DataFrame:
    rows: list[dict] = []

    def stat(df, col, fn):
        return fn(df[col]) if not df.empty and col in df.columns else None

    rows.append({"Metric": "Cycle",            "Full Window": cycle["label"],     "Shaved (15%)": cycle["label"]})
    rows.append({"Metric": "Start Date",       "Full Window": str(full_window[0]), "Shaved (15%)": str(shaved_window[0])})
    rows.append({"Metric": "End Date",         "Full Window": str(full_window[1]), "Shaved (15%)": str(shaved_window[1])})
    rows.append({"Metric": "Shave method",     "Full Window": "—",                 "Shaved (15%)": shaved_note})
    rows.append({"Metric": "Stocks analysed",  "Full Window": len(full_df),        "Shaved (15%)": len(shaved_df)})
    rows.append({"Metric": "Median CAGR %",
                 "Full Window": stat(full_df, "Cagr_%", lambda s: round(s.median(), 2)),
                 "Shaved (15%)": stat(shaved_df, "Cagr_%", lambda s: round(s.median(), 2))})
    rows.append({"Metric": "Mean CAGR %",
                 "Full Window": stat(full_df, "Cagr_%", lambda s: round(s.mean(), 2)),
                 "Shaved (15%)": stat(shaved_df, "Cagr_%", lambda s: round(s.mean(), 2))})
    rows.append({"Metric": "Median Total Return %",
                 "Full Window": stat(full_df, "Total_Return_%", lambda s: round(s.median(), 2)),
                 "Shaved (15%)": stat(shaved_df, "Total_Return_%", lambda s: round(s.median(), 2))})
    rows.append({"Metric": "Median Multiple (x)",
                 "Full Window": stat(full_df, "Multiple", lambda s: round(s.median(), 2)),
                 "Shaved (15%)": stat(shaved_df, "Multiple", lambda s: round(s.median(), 2))})
    rows.append({"Metric": "+ve CAGR count",
                 "Full Window": stat(full_df, "Cagr_%", lambda s: int((s > 0).sum())),
                 "Shaved (15%)": stat(shaved_df, "Cagr_%", lambda s: int((s > 0).sum()))})
    rows.append({"Metric": "-ve CAGR count",
                 "Full Window": stat(full_df, "Cagr_%", lambda s: int((s < 0).sum())),
                 "Shaved (15%)": stat(shaved_df, "Cagr_%", lambda s: int((s < 0).sum()))})

    if not full_df.empty:
        top = full_df.iloc[0]
        rows.append({"Metric": "Top performer (CAGR)",
                     "Full Window": f"{top['Ticker']}  {top['Cagr_%']:.2f}%",
                     "Shaved (15%)": ""})
    if not shaved_df.empty:
        top_s = shaved_df.iloc[0]
        rows[-1]["Shaved (15%)"] = f"{top_s['Ticker']}  {top_s['Cagr_%']:.2f}%"

    top_full   = set(full_df.head(10)["Ticker"])   if not full_df.empty   else set()
    top_shaved = set(shaved_df.head(10)["Ticker"]) if not shaved_df.empty else set()
    overlap    = sorted(top_full & top_shaved)
    rows.append({
        "Metric": "Top-10 overlap (full intersect shaved)",
        "Full Window": f"{len(overlap)}/10",
        "Shaved (15%)": ", ".join(overlap) if overlap else "(none)",
    })

    if not full_df.empty and not shaved_df.empty:
        merged = full_df.merge(shaved_df[["Ticker", "Cagr_%"]],
                                on="Ticker", suffixes=("_full", "_shaved"))
        if not merged.empty:
            merged["delta"] = merged["Cagr_%_shaved"] - merged["Cagr_%_full"]
            best  = merged.sort_values("delta", ascending=False).iloc[0]
            worst = merged.sort_values("delta", ascending=True).iloc[0]
            rows.append({
                "Metric": "Biggest CAGR boost from shaving",
                "Full Window": f"{best['Ticker']}: {best['Cagr_%_full']:.2f}% -> {best['Cagr_%_shaved']:.2f}%",
                "Shaved (15%)": f"delta +{best['delta']:.2f}pp",
            })
            rows.append({
                "Metric": "Worst CAGR drop from shaving",
                "Full Window": f"{worst['Ticker']}: {worst['Cagr_%_full']:.2f}% -> {worst['Cagr_%_shaved']:.2f}%",
                "Shaved (15%)": f"delta {worst['delta']:.2f}pp",
            })

    return pd.DataFrame(rows)


# Excel writer

def _truncate_sheet_name(name: str) -> str:
    bad = '[]:*?/\\'
    cleaned = "".join(c for c in name if c not in bad)
    return cleaned[:31]


def write_workbook(output_path: Path,
                   sheets: list[tuple[str, pd.DataFrame]]) -> None:
    output_path.parent.mkdir(exist_ok=True, parents=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        used_names = set()
        for raw_name, df in sheets:
            name = _truncate_sheet_name(raw_name)
            base = name
            suffix = 2
            while name in used_names:
                name = _truncate_sheet_name(f"{base[:28]}_{suffix}")
                suffix += 1
            used_names.add(name)
            if df.empty:
                pd.DataFrame({"Note": ["(no data)"]}).to_excel(writer, sheet_name=name, index=False)
            else:
                df.to_excel(writer, sheet_name=name, index=False)


# Single-cycle runner

def run_cycle(cycle_key: str, mode: str,
              data_dir: Path,
              investment: float,
              index_df) -> dict:
    cycle = get_cycle(cycle_key)
    full_start, full_end = cycle["start_date"], cycle["end_date"]
    label = cycle["label"]

    out = {"key": cycle_key, "label": label, "sheets": [], "analysis_df": None}

    full_df = shaved_df = None
    full_window = shaved_window = (None, None)
    shaved_note = ""

    if mode in ("full", "both"):
        print(f"\n  Analysing {label} — FULL window  ({full_start} -> {full_end})")
        full_df, skipped_f = analyse_cycle(full_start, full_end, data_dir, investment)
        full_window = (full_start, full_end)
        out["sheets"].append((f"{label} — Full", full_df))
        print(f"  done  {len(full_df)} stocks  ({len(skipped_f)} skipped)")

    if mode in ("shaved", "both"):
        s_start, s_end, note = resolve_shaved_window(cycle, index_df)
        shaved_note = note
        print(f"\n  Analysing {label} — SHAVED 15% window  ({s_start} -> {s_end})")
        print(f"    method: {note}")
        shaved_df, skipped_s = analyse_cycle(s_start, s_end, data_dir, investment)
        shaved_window = (s_start, s_end)
        out["sheets"].append((f"{label} — Shaved 15%", shaved_df))
        print(f"  done  {len(shaved_df)} stocks  ({len(skipped_s)} skipped)")

    if mode == "both" and full_df is not None and shaved_df is not None:
        out["analysis_df"] = build_analysis_rows(
            cycle, full_df, shaved_df, full_window, shaved_window, shaved_note
        )

    return out


# Interactive prompts

def prompt_periods() -> list[str]:
    print("\n  Which period do you want to analyse?")
    print("  " + "-" * 56)
    print("  [0]  Entire NEPSE history (1994 -> today)")
    print("  [1]  A particular bull")
    print("  [2]  A particular bear")
    print("  [3]  A combo (multiple cycles)")
    choice = input("\n  Enter 0, 1, 2, or 3: ").strip()

    if choice == "0":
        return ["all"]

    if choice == "1":
        print("\n  Bulls:  bull1, bull2, bull3, bull4, bull5")
        raw = input("  Pick one (e.g. bull4): ").strip().lower()
        if raw not in CYCLES or CYCLES[raw]["kind"] != "bull":
            sys.exit(f"❌  Invalid bull key: {raw!r}")
        return [raw]

    if choice == "2":
        print("\n  Bears:  bear1, bear2, bear3, bear4")
        raw = input("  Pick one (e.g. bear3): ").strip().lower()
        if raw not in CYCLES or CYCLES[raw]["kind"] != "bear":
            sys.exit(f"❌  Invalid bear key: {raw!r}")
        return [raw]

    if choice == "3":
        print("\n  Available keys: bull1, bull2, bull3, bull4, bull5,")
        print("                  bear1, bear2, bear3, bear4")
        raw = input("  Comma-separated list (e.g. bull3,bull4,bull5): ").strip().lower()
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        for k in keys:
            if k not in CYCLES:
                sys.exit(f"❌  Invalid key: {k!r}")
        if not keys:
            sys.exit("❌  No periods selected.")
        return keys

    sys.exit("❌  Invalid choice.")


def prompt_mode() -> str:
    print("\n  Window mode within the selected period?")
    print("  " + "-" * 56)
    print("  [1]  Entire time (full window)")
    print("  [2]  15% shaved off bottom AND 15% shaved off top")
    print("  [3]  Both (produces full + shaved + analysis tab)")
    choice = input("\n  Enter 1, 2, or 3: ").strip()
    mapping = {"1": "full", "2": "shaved", "3": "both"}
    if choice not in mapping:
        sys.exit("❌  Invalid choice.")
    return mapping[choice]


def prompt_investment() -> float:
    raw = input(f"\n  Initial investment in Rs. (Enter for default {DEFAULT_INVESTMENT:,}): ").strip()
    return float(raw) if raw else float(DEFAULT_INVESTMENT)


def prompt_output_name(default: str) -> str:
    raw = input(f"\n  Output filename (Enter for default '{default}'): ").strip()
    return raw if raw else default


def default_output_filename(period_keys: list[str], mode: str) -> str:
    parts = "_".join(period_keys)
    return f"{parts}_{mode}.xlsx"


# Main

def parse_period_arg(raw: str) -> list[str]:
    keys = [k.strip().lower() for k in raw.split(",") if k.strip()]
    for k in keys:
        if k == ENTIRE_KEY:
            continue
        if k not in CYCLES:
            sys.exit(f"❌  Invalid period key: {k!r}.  "
                     f"Valid: all, bull1..bull5, bear1..bear4")
    return keys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NEPSE Bull/Bear stock-level CAGR analyser.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--period", help="all | bullN | bearN | comma-separated combo")
    parser.add_argument("--mode",   choices=["full", "shaved", "both"], help="Window mode")
    parser.add_argument("--investment", type=float, default=None,
                        help=f"Initial investment Rs. (default: {DEFAULT_INVESTMENT:,})")
    parser.add_argument("--data-dir",   type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output",     type=str,  default=None,
                        help="Output xlsx filename (saved under Research/)")
    args = parser.parse_args()

    print("\n  " + "=" * 60)
    print("  NEPSE Bull/Bear Analyser")
    print("  " + "=" * 60)

    if args.period:
        period_keys = parse_period_arg(args.period)
    else:
        period_keys = prompt_periods()

    mode = args.mode or prompt_mode()

    if args.investment is not None:
        investment = args.investment
    elif sys.stdin.isatty():
        investment = prompt_investment()
    else:
        investment = float(DEFAULT_INVESTMENT)

    default_name = default_output_filename(period_keys, mode)
    if args.output:
        output_name = args.output
    elif sys.stdin.isatty():
        output_name = prompt_output_name(default_name)
    else:
        output_name = default_name
    if not output_name.lower().endswith(".xlsx"):
        output_name += ".xlsx"
    output_path = RESEARCH_DIR / output_name

    index_df = load_index_history()
    if index_df is None and mode in ("shaved", "both"):
        print("\n  Warning: NEPSE index history not found — shaved windows use time-based fallback.")

    print(f"\n  Periods    : {', '.join(period_keys)}")
    print(f"  Mode       : {mode}")
    print(f"  Investment : Rs. {investment:,.0f}")
    print(f"  Output     : Research/{output_name}")

    all_sheets: list[tuple[str, pd.DataFrame]] = []
    analysis_rows: list[pd.DataFrame] = []

    for key in period_keys:
        result = run_cycle(key, mode, args.data_dir, investment, index_df)
        all_sheets.extend(result["sheets"])
        if result["analysis_df"] is not None:
            sep = pd.DataFrame([{"Metric": "", "Full Window": "", "Shaved (15%)": ""}])
            analysis_rows.append(result["analysis_df"])
            analysis_rows.append(sep)

    if analysis_rows:
        combined = pd.concat(analysis_rows, ignore_index=True)
        all_sheets.append(("Analysis", combined))

    write_workbook(output_path, all_sheets)

    print(f"\n  done  Saved -> {output_path.resolve()}")
    print(f"        Sheets: {', '.join(_truncate_sheet_name(n) for n, _ in all_sheets)}\n")


if __name__ == "__main__":
    main()
