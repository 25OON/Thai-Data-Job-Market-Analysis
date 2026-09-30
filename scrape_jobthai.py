import argparse
import csv
import re
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = "https://www.jobthai.com/jobsearch/computer-it,data-scientist-data-engineer-data-analyst"
BASE = "https://www.jobthai.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
}
DELAY_SECONDS = 3  # be polite: wait between page requests
MAX_PAGES = 200    # safety stop

# Tag-like labels on a card have ids ending in "-text" (e.g. onlineinterview-text).
# These two are real fields, not tags.
NOT_TAGS = {"location-text", "salary-text"}

COLUMNS = [
    "job_id", "job_title", "company_id", "company_name", "salary",
    "location", "location_is_transit", "tags", "posted_date",
    "job_url", "page", "scraped_at",
]


def text_of(element):
    return element.get_text(" ", strip=True) if element else ""


def parse_card(card, page, scraped_at):
    """Turn one job card (<a ga-job-id=...>) into a CSV row."""
    # Class names on this site are auto-generated and change often,
    # so we select by ids and attributes instead.
    title = card.find("h2")
    company = card.select_one('span[id^="job-list-company-name-"] h2')
    location = card.find(id="location-text")
    date = card.select_one('div[style*="text-align:right"] > span')

    tags = [text_of(el) for el in card.find_all(id=re.compile(r"-text$"))
            if el["id"] not in NOT_TAGS]
    if card.find(id="urgent-job"):
        tags.append(text_of(card.find(id="urgent-job")))

    # When a job is near BTS/MRT the card shows the station instead of district/province
    transit_icon = location.find_previous_sibling("img") if location else None

    return {
        "job_id": card.get("ga-job-id"),
        "job_title": text_of(title),
        "company_id": card.get("ga-company-id"),
        "company_name": text_of(company),
        "salary": text_of(card.find(id="salary-text")),
        "location": text_of(location),
        "location_is_transit": transit_icon is not None,
        "tags": "|".join(tags),
        "posted_date": text_of(date),
        "job_url": BASE + card.get("href", ""),
        "page": page,
        "scraped_at": scraped_at,
    }


def fetch_page(base_url, page):
    """Download one search results page and return its job cards."""
    url = f"{base_url.rstrip('/')}/{page}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return soup.select("a[ga-job-id]")


def main():
    parser = argparse.ArgumentParser(description="Scrape JobThai search results to CSV")
    parser.add_argument("--url", default=DEFAULT_URL, help="JobThai search URL (without page number)")
    parser.add_argument("--out", help="Output CSV path (default: jobthai_<timestamp>.csv)")
    args = parser.parse_args()

    # Drop a trailing page number if one was pasted in, e.g. .../data-analyst/4
    base_url = re.sub(r"/\d+/?$", "", args.url)
    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out_path = args.out or f"jobthai_{datetime.now():%Y%m%d_%H%M%S}.csv"

    rows = []
    seen_ids = set()
    for page in range(1, MAX_PAGES + 1):
        cards = fetch_page(base_url, page)
        new_rows = [parse_card(c, page, scraped_at) for c in cards
                    if c.get("ga-job-id") not in seen_ids]
        # Stop when a page is empty or only repeats jobs we already have
        if not new_rows:
            break

        seen_ids.update(r["job_id"] for r in new_rows)
        rows.extend(new_rows)
        print(f"page {page}: {len(new_rows)} jobs  (collected {len(rows)})")
        time.sleep(DELAY_SECONDS)

    # utf-8-sig so Excel shows Thai text correctly
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
