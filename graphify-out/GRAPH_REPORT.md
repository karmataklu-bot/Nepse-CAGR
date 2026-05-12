# Graph Report - .  (2026-05-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 691 nodes · 2186 edges · 23 communities (22 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b586bc79`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]

## God Nodes (most connected - your core abstractions)
1. `update()` - 108 edges
2. `an()` - 57 edges
3. `ns()` - 54 edges
4. `draw()` - 46 edges
5. `constructor()` - 43 edges
6. `n()` - 36 edges
7. `updateElements()` - 33 edges
8. `no` - 32 edges
9. `parse()` - 30 edges
10. `s()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `calculate_cagr()` --calls--> `main()`  [EXTRACTED]
  nepse_cagr.py → scraper/run_daily.py
- `get_latest_date_in_csv()` --rationale_for--> `Read the latest (most recent) date already saved in prices.csv.         Returns`  [EXTRACTED]
  index_history.py → scraper/core/history.py
- `_auto_detect_data_dir()` --calls--> `main()`  [EXTRACTED]
  index_history.py → scraper/run_daily.py
- `read_message()` --calls--> `main()`  [EXTRACTED]
  nepse_host.py → scraper/run_daily.py
- `send_message()` --calls--> `main()`  [EXTRACTED]
  nepse_host.py → scraper/run_daily.py

## Communities (23 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (26): afterDatasetsUpdate(), afterEvent(), afterUpdate(), an(), As(), beforeUpdate(), c(), cn() (+18 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (24): Fetch today's data and update all company CSVs, addBox(), addElements(), bn, bt, constructor(), cs, de (+16 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (19): bs, _calculateBarValuePixels(), fs(), generateLabels(), getLabelAndValue(), getMaxOverflow(), gn, hn() (+11 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (35): DailySummaryUpdater, Updates daily stock price data for all companies using ShareSansar's Today Price, a(), beforeLayout(), bo, buildLookupTable(), buildTicks(), determineDataLimits() (+27 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (27): afterDraw(), ba(), draw(), ea(), ee, eo(), fe(), ft() (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (50): FloorsheetScraper, Read the latest (most recent) date already saved in prices.csv.         Returns, findPort(), _auto_detect_data_dir(), clean_dataframe(), get_latest_date_in_csv(), _print_row(), prompt_for_date() (+42 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (38): backDestination, bearBottoms, buildChart(), bullCyclePlugin, bullCycles, bullTops, chartLabels, chartValues (+30 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (18): at(), Bi(), ci(), fi, gt(), ii(), jt(), kt() (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (13): es(), Io, is(), ot, qi, se, ss(), {start:d,count:u} (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (12): DailyScraperManager, Run the daily update:           - Refresh company ID mapping (catches new IPOs), Manages daily scraping tasks for priority companies (company_list.json):       -, Load the priority company list from company_list.json., Return symbols that already have a prices.csv., Scrape / update prices.csv for the given symbols., Parse a table row into a dict, Scrape data via POST to AJAX endpoint with DataTables pagination.         Stops (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (14): beforeDatasetDraw(), beforeDatasetsDraw(), beforeDraw(), ca(), da(), fa(), ga(), getBasePixel() (+6 more)

### Community 11 - "Community 11"
Cohesion: 0.16
Nodes (13): be(), ct(), ds(), ge(), ls, me(), ms(), pe() (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.19
Nodes (16): _(), aa(), b(), ce(), configure(), g(), m(), n() (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (11): BaseHTTPRequestHandler, calculate_cagr(), get_cagr(), load_dividends(), load_prices(), load_right_shares(), nearest_price(), NEPSE Stock CAGR Calculator ============================ Uses data from: https:/ (+3 more)

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (14): ao(), co(), Do(), getCenterPoint(), ho(), Hs, inRange(), inXRange() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.21
Nodes (12): _calculateBarIndexPixels(), getPixelForTick(), getPixelForValue(), _getRuler(), _getStackCount(), _getStackIndex(), _getStacks(), getValueForPixel() (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.22
Nodes (8): Ae(), ai(), it(), j(), la(), pt(), q(), ro()

### Community 17 - "Community 17"
Cohesion: 0.43
Nodes (7): dataset(), index(), ji(), nearest(), re, ve(), yi()

### Community 18 - "Community 18"
Cohesion: 0.32
Nodes (8): ei(), getRange(), h(), hi(), li(), ni(), ri(), ui()

### Community 19 - "Community 19"
Cohesion: 0.33
Nodes (6): et(), i, je(), qe(), st(), ti()

### Community 20 - "Community 20"
Cohesion: 0.4
Nodes (4): gi(), mi(), un(), vi()

## Knowledge Gaps
- **66 isolated node(s):** `run_index_history.py -------------------- CLI entry point for scraping NEPSE ind`, `NEPSE Stock CAGR Calculator ============================ Uses data from: https:/`, `Load right-share.csv for the given symbol.     Columns: ratio, total_units, issu`, `Importable function. Returns a dict with full breakdown + cagr_pct.      Example`, `index_history.py ---------------- Scrapes historical NEPSE index / sub-index dat` (+61 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `init()` connect `Community 3` to `Community 4`, `Community 5`, `Community 7`, `Community 8`, `Community 9`?**
  _High betweenness centrality (0.269) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 5` to `Community 9`, `Community 13`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `DailyScraperManager` connect `Community 9` to `Community 3`, `Community 5`?**
  _High betweenness centrality (0.210) - this node is a cross-community bridge._
- **What connects `run_index_history.py -------------------- CLI entry point for scraping NEPSE ind`, `NEPSE Stock CAGR Calculator ============================ Uses data from: https:/`, `Load right-share.csv for the given symbol.     Columns: ratio, total_units, issu` to the rest of the system?**
  _66 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._