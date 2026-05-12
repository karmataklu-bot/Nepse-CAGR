import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import logging
import random
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShareSansarIPO_listingScraper:
    """
    Scrapes IPO listing dates from ShareSansar's 'Share Listed' events page:
        https://www.sharesansar.com/events/category/share-listed

    Saves results to:
        data/ipo_listings.csv

    CSV columns: symbol, company_name, listing_date
    """

    BASE_URL = "https://www.sharesansar.com"
    LISTINGS_URL = f"{BASE_URL}/events/category/share-listed"
    OUTPUT_FILE = "ipo_listings.csv"
    FIELDNAMES = ["symbol", "company_name", "listing_date"]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="120", "Google Chrome";v="120"',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Dest': 'document',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        # Resolve data dir relative to this file's location (mirrors history.py)
        self.data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        self.output_path = self.data_dir / self.OUTPUT_FILE

    # ------------------------------------------------------------------
    # CSV helpers
    # ------------------------------------------------------------------

    def _load_existing(self):
        """Return a set of symbols already saved in ipo_listings.csv."""
        if not self.output_path.exists():
            return set()
        try:
            with open(self.output_path, newline='') as f:
                reader = csv.DictReader(f)
                return {row['symbol'] for row in reader if row.get('symbol')}
        except Exception as e:
            logger.warning(f"Could not read existing ipo_listings.csv: {e}")
            return set()

    def _save_records(self, records):
        """
        Append new records to ipo_listings.csv, skipping duplicates by symbol.
        Creates the file with a header if it doesn't exist yet.
        """
        existing_symbols = self._load_existing()
        new_records = [r for r in records if r['symbol'] not in existing_symbols]

        if not new_records:
            logger.info("No new IPO listing records to save.")
            return 0

        file_exists = self.output_path.exists() and self.output_path.stat().st_size > 0
        self.data_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.output_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_records)
            logger.info(f"[OK] Saved {len(new_records)} new IPO listing records.")
            return len(new_records)
        except Exception as e:
            logger.error(f"Failed to write ipo_listings.csv: {e}")
            return 0

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_listing_date(self, raw):
        """
        Normalise whatever date string ShareSansar uses to YYYY-MM-DD.
        Tries common formats; returns raw string on failure so no data is lost.
        """
        raw = raw.strip()
        for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%B %d, %Y', '%b %d, %Y', '%d %B %Y'):
            try:
                return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        logger.warning(f"Could not parse date '{raw}' — storing as-is.")
        return raw

    def _parse_symbol_from_text(self, text):
        """
        ShareSansar event titles look like:
            'IPO Shares of NABIL Now Listed in NEPSE; ...'
            'Bonus Share of HIDCL Have Been Listed in NEPSE'
        Extract the stock symbol (uppercase word after 'of ').
        Returns None if no symbol can be found.
        """
        import re
        # Look for a word in ALL CAPS (2-10 chars) after the word 'of'
        match = re.search(r'\bof\s+([A-Z]{2,10})\b', text)
        return match.group(1) if match else None

    def _parse_event_rows(self, soup):
        """
        Parse listing events from the page HTML.

        ShareSansar's /events/category/share-listed page renders a list of
        event cards or table rows.  We try two strategies:
          1. A <table> with rows containing date + title columns (most common).
          2. Event card <div>s with a date and title element.

        Returns a list of dicts: {symbol, company_name, listing_date}
        """
        records = []

        # --- Strategy 1: table rows ---
        table = soup.find('table')
        if table:
            for row in table.find_all('tr')[1:]:  # skip header
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue

                # Heuristic: first col with a date-like string, second with title
                date_text = cols[0].get_text(strip=True)
                title_text = cols[1].get_text(strip=True)

                symbol = self._parse_symbol_from_text(title_text)
                if not symbol:
                    continue

                records.append({
                    'symbol': symbol,
                    'company_name': title_text,
                    'listing_date': self._parse_listing_date(date_text),
                })
            if records:
                return records

        # --- Strategy 2: event cards ---
        # ShareSansar sometimes uses article/div cards
        for card in soup.select('.event-item, .news-item, article, .card'):
            title_el = card.select_one('h2, h3, h4, .title, .event-title')
            date_el = card.select_one('time, .date, .event-date, [datetime]')

            if not title_el or not date_el:
                continue

            title_text = title_el.get_text(strip=True)
            # <time datetime="YYYY-MM-DD"> is the cleanest source
            date_text = date_el.get('datetime') or date_el.get_text(strip=True)

            symbol = self._parse_symbol_from_text(title_text)
            if not symbol:
                continue

            records.append({
                'symbol': symbol,
                'company_name': title_text,
                'listing_date': self._parse_listing_date(date_text),
            })

        return records

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def _next_page_url(self, soup, current_url):
        """
        Return the URL of the next page, or None if we're on the last page.
        ShareSansar uses a ?cursor=... query param for pagination.
        """
        # Look for a 'Next' link or pagination element
        next_link = soup.find('a', string=lambda s: s and 'next' in s.lower())
        if next_link and next_link.get('href'):
            href = next_link['href']
            return href if href.startswith('http') else self.BASE_URL + href

        # Also check rel="next"
        rel_next = soup.find('link', rel='next') or soup.find('a', rel='next')
        if rel_next and rel_next.get('href'):
            href = rel_next['href']
            return href if href.startswith('http') else self.BASE_URL + href

        return None

    # ------------------------------------------------------------------
    # Main scrape method
    # ------------------------------------------------------------------

    def scrape_all_listings(self, stop_on_existing=True):
        """
        Scrape all paginated IPO listing events from ShareSansar.

        :param stop_on_existing: Stop pagination early once we hit symbols
                                 already saved in ipo_listings.csv (fast
                                 incremental updates — same pattern as history.py).
        :returns: list of new record dicts saved to CSV.
        """
        existing_symbols = self._load_existing()
        all_records = []
        url = self.LISTINGS_URL
        page = 1

        logger.info("Starting IPO listing date scrape from ShareSansar...")

        while url:
            logger.info(f"  Fetching page {page}: {url}")
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code != 200:
                    logger.error(f"  HTTP {response.status_code} — stopping.")
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                records = self._parse_event_rows(soup)

                if not records:
                    logger.info("  No records found on this page — stopping.")
                    break

                logger.info(f"  Found {len(records)} records on page {page}.")

                new_on_page = []
                hit_existing = False
                for r in records:
                    if r['symbol'] in existing_symbols:
                        logger.info(
                            f"  Reached already-saved symbol {r['symbol']} — stopping early."
                        )
                        hit_existing = True
                        break
                    new_on_page.append(r)

                all_records.extend(new_on_page)

                if stop_on_existing and hit_existing:
                    break

                url = self._next_page_url(soup, url)
                page += 1
                time.sleep(random.uniform(1.0, 2.5))  # polite delay

            except Exception as e:
                logger.error(f"  Error on page {page}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                break

        saved = self._save_records(all_records)
        logger.info(f"[DONE] IPO listing scrape complete. {saved} new records saved.")
        return all_records

    def scrape_single(self, symbol):
        """
        Convenience method: look up a single symbol in ipo_listings.csv.
        Returns the listing_date string, or None if not found.
        Does NOT re-scrape — call scrape_all_listings() first to populate.
        """
        if not self.output_path.exists():
            return None
        try:
            with open(self.output_path, newline='') as f:
                for row in csv.DictReader(f):
                    if row.get('symbol', '').upper() == symbol.upper():
                        return row.get('listing_date')
        except Exception as e:
            logger.error(f"Could not read ipo_listings.csv: {e}")
        return None


if __name__ == "__main__":
    scraper = ShareSansarIPO_listingScraper()
    scraper.scrape_all_listings()
