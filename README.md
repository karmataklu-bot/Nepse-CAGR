# Nepse-CAGR

A tool to calculate the CAGR (Compound Annual Growth Rate) of any NEPSE stock.

Forked from [SamirWagle/Nepse-All-Scraper](https://github.com/SamirWagle/Nepse-All-Scraper) — which handles all data scraping automatically via GitHub Actions every weekday.

---

## What I Added

A Python script `nepse_cagr.py` that calculates the CAGR of any NEPSE stock using the scraped data, accounting for:
- Bonus shares
- Right shares (units added + cost added to total investment)
- Cash dividends

---

## CAGR Formula

(Today's Value / Total Invested) ^ (1 / years) - 1

Where:
- **Today's Value** = (total units today × LTP) + total cash dividends received
- **Total Invested** = initial investment + right share costs paid
- Units grow with each bonus share and right share
- Cash dividends = cumulative units × face value (Rs. 100) × cash %
- Cash dividend is calculated on units *before* bonus shares are applied on the same date

---

## Data Sources

Data is scraped automatically from NEPSE every weekday via GitHub Actions and stored in:

data/company-wise/{SYMBOL}/prices.csv
data/company-wise/{SYMBOL}/dividend.csv
data/company-wise/{SYMBOL}/right-share.csv

> **Note:** Data updates at ~8:30 PM NPT on weekdays, so LTP is always the previous day's closing price.

---

## How to Use

### Setup
```bash
git clone https://github.com/karmataklu-bot/Nepse-CAGR.git
cd Nepse-CAGR
pip install pandas
```

### Run
```bash
# Interactive mode
python nepse_cagr.py

# With flags
python nepse_cagr.py --symbol NABIL --years 5
python nepse_cagr.py --symbol NABIL --start-date 2018-01-15
python nepse_cagr.py --symbol NABIL --start-date 2018-01-15 --investment 200000
```

### Flags

| Flag | Description | Default |
|---|---|---|
| `--symbol` | Stock symbol e.g. `NABIL` | prompted |
| `--years` | Years back from today e.g. `5` | prompted |
| `--start-date` | Specific start date `YYYY-MM-DD` | prompted |
| `--investment` | Initial investment in Rs. | 100,000 |
| `--data-dir` | Path to data folder | auto |
| `--quiet` | Print only the CAGR result | off |

---

## Automation

GitHub Actions scrapes fresh data every weekday at ~8:30 PM NPT automatically.

To keep your local clone updated, set up a cron job:

```bash
30 21 * * 0-4 cd ~/CodingProjects/Nepse-CAGR && git pull
```

---

## Credits

- Data scraping by [SamirWagle/Nepse-All-Scraper](https://github.com/SamirWagle/Nepse-All-Scraper)
- Sources: ShareSansar, Merolagani
