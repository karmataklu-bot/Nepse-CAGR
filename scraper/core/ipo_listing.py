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
        for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%A, %B %d, %Y', '%A, %b %d, %Y'):
            try:
                return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        logger.warning(f"Could not parse date '{raw}' — storing as-is.")
        return raw

    def _parse_symbol_from_text(self, text):
        """
        Extract stock symbol from event title. Tries two patterns:
          1. Symbol in brackets: "...Citizen Investment Trust (CIT)"
          2. ALL CAPS word after "of": "Shares of NABIL Now Listed"
        Returns None if no symbol found.
        """
        import re
        # Pattern 1: symbol in parentheses at end, e.g. (CIT), (SMB)
        match = re.search(r'\(([A-Z0-9]{2,12})\)', text)
        if match:
            return match.group(1)
        # Pattern 2: ALL CAPS word after "of"
        match = re.search(r'\bof\s+([A-Z]{2,10})\b', text)
        return match.group(1) if match else None

    def _is_ipo_listing(self, title):
        """
        Return True only if this event is a share listing (any type).
        Filters out mostly-Nepali entries only.
        We capture all listing types so the CSV is complete — callers can
        filter by type if needed using the company_name field.
        """
        title_lower = title.lower()

        # Must contain listing-related keyword
        if not any(w in title_lower for w in ['listing', 'listed', 'list']):
            return False

        # Exclude mostly-Nepali entries (heuristic: few ASCII chars)
        ascii_ratio = sum(1 for c in title if ord(c) < 128) / max(len(title), 1)
        if ascii_ratio < 0.5:
            return False

        return True

    def _parse_event_rows(self, soup):
        """
        Parse IPO listing events from ShareSansar's AJAX response HTML.

        Each event card structure:
          <div class="featured-news-list margin-bottom-15">
            <div class="col-lg-11 ...">
              <a href="/eventdetail/...">
                <h4 class="featured-event-title">Listing IPO Shares of NABIL</h4>
              </a>
              <p><span class="text-org">Wednesday, May 6, 2026</span></p>
            </div>
          </div>

        We filter to IPO/FPO-only entries, skipping bonus/right/debenture listings.
        Returns a list of dicts: {symbol, company_name, listing_date}
        """
        records = []

        for card in soup.find_all('div', class_='featured-news-list'):
            # Get title from h4.featured-event-title
            title_el = card.find('h4', class_='featured-event-title')
            if not title_el:
                continue
            title_text = title_el.get_text(strip=True)

            # Filter to IPO-only entries
            if not self._is_ipo_listing(title_text):
                continue

            # Get date from span.text-org
            date_el = card.find('span', class_='text-org')
            if not date_el:
                continue
            date_text = date_el.get_text(strip=True)

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
        page = 1

        logger.info("Starting IPO listing date scrape from ShareSansar...")

        # Step 1: load the page with plain headers to get CSRF token + cookies
        plain_session = requests.Session()
        plain_session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        base_response = plain_session.get(self.LISTINGS_URL, timeout=30)
        base_soup = BeautifulSoup(base_response.text, 'html.parser')

        csrf_token = ''
        token_el = base_soup.find('input', {'name': '_token'})
        if token_el:
            csrf_token = token_el.get('value', '')
        if not csrf_token:
            token_el = base_soup.find('meta', {'name': '_token'})
            if token_el:
                csrf_token = token_el.get('content', '')
        logger.info(f"  CSRF token: {csrf_token[:20]}..." if csrf_token else "  WARNING: No CSRF token found")

        # Step 2: add AJAX headers and hit the endpoint with same session (preserves cookies)
        plain_session.headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': self.LISTINGS_URL,
        })

        # AJAX endpoint: GET with date= and _token= params
        ajax_url = f"{self.LISTINGS_URL}?date=&_token={csrf_token}"

        while ajax_url:
            logger.info(f"  Fetching page {page}: {ajax_url}")
            try:
                response = plain_session.get(ajax_url, timeout=30)
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

                ajax_url = self._next_page_url(soup, ajax_url)
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
    import sys
    scraper = ShareSansarIPO_listingScraper()

    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        import requests
        from bs4 import BeautifulSoup
        print("Step 1: Loading page...")
        session = requests.Session()
        session.headers["User-Agent"] = "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"
        session.headers["Accept"] = "text/html,application/xhtml+xml,*/*"
        r = session.get("https://www.sharesansar.com/events/category/share-listed", timeout=30)
        print(f"  Status: {r.status_code}, Length: {len(r.text)}")
        soup = BeautifulSoup(r.text, "html.parser")
        token_el = soup.find("input", {"name": "_token"})
        token = token_el["value"] if token_el else ""
        print(f"  Token: {token[:25]}")
        print("Step 2: Fetching AJAX...")
        session.headers["X-Requested-With"] = "XMLHttpRequest"
        session.headers["Referer"] = "https://www.sharesansar.com/events/category/share-listed"
        r2 = session.get("https://www.sharesansar.com/events/category/share-listed?date=&_token=" + token, timeout=30)
        print(f"  Status: {r2.status_code}, Length: {len(r2.text)}")
        print(f"  First 300: {r2.text[:300]}")
        soup2 = BeautifulSoup(r2.text, "html.parser")
        cards = soup2.find_all("div", class_="featured-news-list")
        print(f"  Cards: {len(cards)}")
        records = scraper._parse_event_rows(soup2)
        print(f"  Records: {len(records)}")
        for rec in records[:5]:
            print(f"    {rec}")
    else:
        scraper.scrape_all_listings()
