# ============================================================
# Changes to integrate IPO listing scraper into daily.py
# Apply these three edits to your existing daily.py file.
# ============================================================

# ── EDIT 1 ── add import at the top (alongside the history import)
# BEFORE:
from .history import ShareSansarHistoryScraper

# AFTER:
from .history import ShareSansarHistoryScraper
from .ipo_listing import ShareSansarIPO_listingScraper


# ── EDIT 2 ── instantiate scraper in DailyScraperManager.__init__
# BEFORE:
def __init__(self, base_dir="data"):
    self.price_scraper = ShareSansarHistoryScraper()
    ...

# AFTER:
def __init__(self, base_dir="data"):
    self.price_scraper = ShareSansarHistoryScraper()
    self.ipo_scraper = ShareSansarIPO_listingScraper()
    ...


# ── EDIT 3 ── add IPO update step inside run_daily_update()
# BEFORE:
    def run_daily_update(self, check_new_only=False, force_full=False, priority_only=True):
        logger.info("=== Daily Update Started ===")

        target = self.get_priority_companies()
        logger.info(f"Priority companies: {len(target)}")

        if not check_new_only:
            logger.info("--- Updating prices ---")
            self._update_prices(target, force_full=force_full)
        else:
            logger.info("--- New companies only (prices) ---")
            existing = self.get_existing_companies()
            new_only = target - existing
            self._update_prices(new_only, force_full=False)

        logger.info("=== Daily Update Completed ===")

# AFTER:
    def run_daily_update(self, check_new_only=False, force_full=False, priority_only=True):
        logger.info("=== Daily Update Started ===")

        target = self.get_priority_companies()
        logger.info(f"Priority companies: {len(target)}")

        if not check_new_only:
            logger.info("--- Updating prices ---")
            self._update_prices(target, force_full=force_full)
        else:
            logger.info("--- New companies only (prices) ---")
            existing = self.get_existing_companies()
            new_only = target - existing
            self._update_prices(new_only, force_full=False)

        # Incrementally update IPO listing dates (fast: stops on first known symbol)
        logger.info("--- Updating IPO listing dates ---")
        try:
            self.ipo_scraper.scrape_all_listings(stop_on_existing=True)
        except Exception as e:
            logger.error(f"IPO listing scrape failed: {e}")

        logger.info("=== Daily Update Completed ===")
