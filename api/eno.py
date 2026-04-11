"""Fetch Eno Sarris pitcher rankings from Google Sheets."""

import pandas as pd

from api.google_sheets import get_gspread_client
from player_evaluation.config import (
    INPUT_DATA_DIR,
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    GOOGLE_SHEETS_TOKEN_FILE,
)
from player_evaluation.utils import normalize_name_column

ENO_SPREADSHEET_ID = "1daR9RNic3GcfDb6FLsm2OZRBS8VkqucOqHSnIS7ru5c"


def _find_latest_worksheet(spreadsheet):
    """Find the most recent rankings worksheet tab in the Eno spreadsheet.

    The first (leftmost) tab with 'rank' in its name is the latest rankings.
    """
    worksheets = spreadsheet.worksheets()
    for ws in worksheets:
        if "rank" in ws.title.lower():
            return ws
    # Fall back to the first tab
    return worksheets[0]


def fetch_eno_rankings():
    """Download Eno pitcher rankings from Google Sheets and save as CSV."""
    print("Fetching Eno pitcher rankings from Google Sheets...")
    client = get_gspread_client(GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_TOKEN_FILE)
    spreadsheet = client.open_by_key(ENO_SPREADSHEET_ID)
    worksheet = _find_latest_worksheet(spreadsheet)
    print(f"  Using tab: {worksheet.title}")
    data = worksheet.get_all_values()

    if len(data) < 2:
        print("Warning: Eno rankings sheet appears empty")
        return

    df = pd.DataFrame(data[1:], columns=data[0])

    # Normalize column names to match what add_eno_rankings() expects
    rename_map = {}
    for col in df.columns:
        if col.lower() in ("eno", "rank"):
            rename_map[col] = "Rank"
        elif col.lower() in ("name", "player"):
            rename_map[col] = "Player"
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    if "Player" in df.columns:
        normalize_name_column(df, col="Player")

    filepath = f"{INPUT_DATA_DIR}/eno_rankings.csv"
    df.to_csv(filepath, index=False)
    print(f"  Saved {len(df)} rankings to {filepath}")
