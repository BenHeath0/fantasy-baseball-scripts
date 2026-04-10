"""Fetch CloserMonkey reliever rankings by scraping the latest rankings post."""

import requests
from bs4 import BeautifulSoup

from player_evaluation.config import INPUT_DATA_DIR
from player_evaluation.utils import normalize_player_name

RANKINGS_CATEGORY_URL = "https://closermonkey.com/category/rankings/"


def _get_latest_rankings_url():
    """Find the URL of the most recent rankings post."""
    response = requests.get(RANKINGS_CATEGORY_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Find the first link whose href contains "rankings" and a year
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "ranking" in href.lower() and "/202" in href and a.get_text(strip=True):
            return href
    raise RuntimeError("Could not find any rankings post URL on CloserMonkey")


def _parse_rankings_tables(url):
    """Parse the three rankings tables (saves, SOLDS, holds) from a rankings post.

    Returns a dict with keys 'saves', 'solds', 'holds', each mapping to a list
    of (rank, player_name) tuples.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table")
    if len(tables) < 3:
        raise RuntimeError(
            f"Expected 3 tables on CloserMonkey rankings page, found {len(tables)}"
        )

    # Order on the page: saves, SOLDS, holds
    table_names = ["saves", "solds", "holds"]
    results = {}

    for name, table in zip(table_names, tables[:3]):
        rows = []
        tbody = table.find("tbody")
        if tbody is None:
            tbody = table
        for tr in tbody.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) >= 2:
                rank = cells[0].get_text(strip=True)
                player_name = cells[1].get_text(strip=True)
                if rank.isdigit():
                    rows.append((int(rank), normalize_player_name(player_name)))
        results[name] = rows

    return results


def _save_rankings_tsv(rows, filename):
    """Save a list of (rank, player_name) tuples to a TSV file."""
    filepath = f"{INPUT_DATA_DIR}/{filename}"
    with open(filepath, "w") as f:
        f.write("Rank\tplayer_name\n")
        for rank, player_name in rows:
            f.write(f"{rank}\t{player_name}\n")
    print(f"  Saved {len(rows)} rankings to {filepath}")


def fetch_closermonkey_rankings():
    """Fetch the latest CloserMonkey rankings and save to TSV files."""
    print("Fetching CloserMonkey rankings...")
    url = _get_latest_rankings_url()
    print(f"  Latest rankings post: {url}")
    rankings = _parse_rankings_tables(url)

    file_mapping = {
        "saves": "closermonkey.tsv",
        "solds": "closermonkey_solds.tsv",
        "holds": "closermonkey_holds.tsv",
    }

    for key, filename in file_mapping.items():
        _save_rankings_tsv(rankings[key], filename)
