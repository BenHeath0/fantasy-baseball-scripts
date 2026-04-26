"""Draft-and-hold league roster evaluation.

Fetches season-to-date stats, recent performance (last 14 and 30 days),
and ROS projections for an NFBC draft-and-hold roster.

Usage:
    python -m draft_and_hold.main
    python -m draft_and_hold.main --no-google
"""

import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd

from api.fangraphs import get_player_rater_values
from player_evaluation.config import (
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    GOOGLE_SHEETS_TOKEN_FILE,
    INPUT_DATA_DIR,
    TEAM_ABBREV_TO_FANGRAPHS,
)
from player_evaluation.data_fetchers import fetch_fangraphs_projections
from player_evaluation.utils import normalize_name_column

GOOGLE_SHEETS_SPREADSHEET_ID = "1tcRJlmGCWsCroc1LbcPFCqWJ0yoPDvbwiPZMnLBwyVM"
HITTERS_TAB = "DH Hitters"
PITCHERS_TAB = "DH Pitchers"

OUTPUT_DIR = "draft_and_hold/output"

HITTER_STATS = ["AVG", "HR", "RBI", "R", "SB"]
PITCHER_STATS = ["W", "SO", "SV", "ERA", "WHIP"]

ATC_HITTER_PROJECTIONS = ["PA", "HR", "R", "RBI", "SB", "AVG", "OBP", "SLG"]
OOPSY_PITCHER_PROJECTIONS = ["IP", "W", "SV", "SO", "ERA", "WHIP"]

PLAYER_RATER_TIMEFRAMES = ["season", "last14", "last30"]


def load_nfbc_roster():
    """Load the NFBC draft-and-hold roster."""
    filepath = f"{INPUT_DATA_DIR}/rosters/nfbc_roster.csv"
    df = pd.read_csv(filepath, usecols=["PLAYER NAME", "TEAM"])
    df.rename(columns={"PLAYER NAME": "player_name", "TEAM": "team"}, inplace=True)
    df["team"] = df["team"].replace(TEAM_ABBREV_TO_FANGRAPHS)
    normalize_name_column(df)
    return df


def fetch_player_rater_data():
    """Fetch player rater dollar values and stats for all timeframes.

    Returns (hitters_df, pitchers_df) with columns for each timeframe's
    dollar value and raw stats.
    """
    hitters_frames = []
    pitchers_frames = []

    with ThreadPoolExecutor() as executor:
        responses = dict(
            zip(
                PLAYER_RATER_TIMEFRAMES,
                executor.map(get_player_rater_values, PLAYER_RATER_TIMEFRAMES),
            )
        )

    for timeframe in PLAYER_RATER_TIMEFRAMES:
        response = responses[timeframe]
        hitter_rows = []
        pitcher_rows = []

        for player in response["data"]:
            base = {
                "player_name": player["playerName"],
                "team": player["auction"]["AbbName"],
                "position": player["auction"]["Position"].rstrip("/"),
            }

            dollars = player["auction"]["Dollars"]

            if player["auction"]["PosType"] == "bat":
                row = {**base, f"{timeframe}_dollars": dollars}
                if player["statsBat"]:
                    for stat in HITTER_STATS:
                        row[f"{timeframe}_{stat}"] = player["statsBat"].get(stat)
                hitter_rows.append(row)
            else:
                row = {**base, f"{timeframe}_dollars": dollars}
                if player["statsPit"]:
                    for stat in PITCHER_STATS:
                        row[f"{timeframe}_{stat}"] = player["statsPit"].get(stat)
                pitcher_rows.append(row)

        hdf = pd.DataFrame(hitter_rows)
        normalize_name_column(hdf)
        hitters_frames.append(hdf)

        pdf = pd.DataFrame(pitcher_rows)
        normalize_name_column(pdf)
        pitchers_frames.append(pdf)

    merged_hitters = hitters_frames[0]
    for frame in hitters_frames[1:]:
        cols_to_merge = [c for c in frame.columns if c not in ["position"]]
        merged_hitters = merged_hitters.merge(
            frame[cols_to_merge], how="outer", on=["player_name", "team"]
        )

    merged_pitchers = pitchers_frames[0]
    for frame in pitchers_frames[1:]:
        cols_to_merge = [c for c in frame.columns if c not in ["position"]]
        merged_pitchers = merged_pitchers.merge(
            frame[cols_to_merge], how="outer", on=["player_name", "team"]
        )

    return merged_hitters, merged_pitchers


def fetch_ros_projections():
    """Fetch ROS projections: ATC for hitters, oopsy for pitchers."""
    print("Fetching ROS projections...")

    with ThreadPoolExecutor() as executor:
        hitters_future = executor.submit(
            fetch_fangraphs_projections, "ratcdc", "bat", ATC_HITTER_PROJECTIONS
        )
        pitchers_future = executor.submit(
            fetch_fangraphs_projections, "roopsydc", "pit", OOPSY_PITCHER_PROJECTIONS
        )
        hitters_df = hitters_future.result()
        pitchers_df = pitchers_future.result()

    hitters_df = hitters_df.rename(
        columns={s: f"ros_{s}" for s in ATC_HITTER_PROJECTIONS}
    )
    pitchers_df = pitchers_df.rename(
        columns={s: f"ros_{s}" for s in OOPSY_PITCHER_PROJECTIONS}
    )

    return hitters_df, pitchers_df


def build_roster_report():
    """Build the full draft-and-hold roster report."""
    roster = load_nfbc_roster()
    print(f"Loaded {len(roster)} players from NFBC roster")

    rater_hitters, rater_pitchers = fetch_player_rater_data()
    ros_hitters, ros_pitchers = fetch_ros_projections()

    roster_hitters = roster.merge(rater_hitters, on=["player_name", "team"], how="left")
    roster_pitchers = roster.merge(
        rater_pitchers, on=["player_name", "team"], how="left"
    )

    roster_hitters = roster_hitters.dropna(subset=["position"])
    roster_pitchers = roster_pitchers.dropna(subset=["position"])

    roster_hitters = roster_hitters.merge(
        ros_hitters, on=["player_name", "team"], how="left"
    )
    roster_pitchers = roster_pitchers.merge(
        ros_pitchers, on=["player_name", "team"], how="left"
    )

    roster_hitters = roster_hitters.sort_values(
        "season_dollars", ascending=False, na_position="last"
    )
    roster_pitchers = roster_pitchers.sort_values(
        "season_dollars", ascending=False, na_position="last"
    )

    return roster_hitters, roster_pitchers


def main():
    parser = argparse.ArgumentParser(description="Draft-and-hold roster evaluation")
    parser.add_argument(
        "--no-google", action="store_true", help="Skip uploading to Google Sheets"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Draft-and-Hold Roster Evaluation")
    print("=" * 60)

    hitters_df, pitchers_df = build_roster_report()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    current_date = datetime.now().strftime("%Y-%m-%d")
    hitters_file = f"{OUTPUT_DIR}/{current_date}_hitters.csv"
    pitchers_file = f"{OUTPUT_DIR}/{current_date}_pitchers.csv"
    hitters_df.to_csv(hitters_file, index=False)
    pitchers_df.to_csv(pitchers_file, index=False)
    print(f"\nSaved to: {hitters_file} and {pitchers_file}")

    if not args.no_google:
        try:
            from api.google_sheets import upload_to_google_sheets

            upload_to_google_sheets(
                hitters_df,
                GOOGLE_SHEETS_SPREADSHEET_ID,
                HITTERS_TAB,
                GOOGLE_SHEETS_CREDENTIALS_FILE,
                GOOGLE_SHEETS_TOKEN_FILE,
            )
            upload_to_google_sheets(
                pitchers_df,
                GOOGLE_SHEETS_SPREADSHEET_ID,
                PITCHERS_TAB,
                GOOGLE_SHEETS_CREDENTIALS_FILE,
                GOOGLE_SHEETS_TOKEN_FILE,
            )
            print(
                f"Uploaded to Google Sheets: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_SPREADSHEET_ID}"
            )
        except Exception as e:
            print(f"Google Sheets upload failed: {e}")
            print("CSVs were saved successfully.")

    print(f"\nHitters ({len(hitters_df)}):")
    print("-" * 80)
    display_cols = [
        "player_name",
        "team",
        "position",
        "season_dollars",
        "last14_dollars",
        "last30_dollars",
    ]
    available = [c for c in display_cols if c in hitters_df.columns]
    print(hitters_df[available].to_string(index=False))

    print(f"\nPitchers ({len(pitchers_df)}):")
    print("-" * 80)
    print(pitchers_df[available].to_string(index=False))


if __name__ == "__main__":
    main()
