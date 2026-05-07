"""
run_index_history.py
--------------------
CLI entry point for scraping NEPSE index history from ShareSansar.
Mirrors the pattern of run_github_actions.py / run_daily.py in this repo.

Examples
--------
# Incremental update for NEPSE Index only (default)
python run_index_history.py

# Incremental update for ALL indices (add to GitHub Actions cron)
python run_index_history.py --all

# Full history scrape for one index
python run_index_history.py --index "Banking SubIndex" --full-scrape

# Full history scrape for all indices (first-time setup, takes a while)
python run_index_history.py --all --full-scrape

# Custom date range
python run_index_history.py --index "NEPSE Index" --from-date 2022-01-01 --to-date 2023-12-31

Output
------
data/index/{folder_name}/history.csv

    date, open, high, low, close, percent_change, turnover
    2024-01-15, 2100.45, 2145.30, 2098.10, 2130.20, +1.42%, 5234500000
"""

import sys
import os

# index_history.py lives in the same directory as this script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from index_history import main

if __name__ == "__main__":
    main()
