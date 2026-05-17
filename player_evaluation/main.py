#!/usr/bin/env python3
"""
Fantasy Baseball Player Evaluation Tool

This script helps evaluate fantasy baseball players by:
1. Fetching projection data from Fangraphs APIs
2. Augmenting with additional data sources (Stuff+, Statcast, etc.)
3. Analyzing keeper decisions
4. Identifying top available players

Usage:
    python main.py --keepers                    # Analyze keeper decisions
    python main.py --draft --league bush        # Generate draft sheet for bush league
    python main.py --use-cache                  # Use cached data instead of fetching fresh
"""

import argparse
from datetime import datetime
import sys
from .config import (
    CURRENT_SEASON,
    ESPN_LEAGUE_ID,
    INPUT_DATA_DIR,
    OUTPUT_DIR,
    PROJECTION_SYSTEMS,
    GOOGLE_SHEETS_SPREADSHEET_IDS,
    GOOGLE_SHEETS_HITTERS_TAB,
    GOOGLE_SHEETS_PITCHERS_TAB,
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    GOOGLE_SHEETS_TOKEN_FILE,
    YAHOO_LEAGUE_KEY,
)
from .data_fetchers import get_or_fetch_fangraphs_data
from .data_processors import (
    add_fantasy_team,
    add_hitter_supplemental_data,
    add_pitcher_supplemental_data,
    add_nfbc_data,
)


def print_startup_banner():
    """Print a nice startup banner"""
    print("=" * 60)
    print("🏆 Fantasy Baseball Player Evaluation Tool 🏆")
    print("=" * 60)
    print(f"Using projection systems: {', '.join(PROJECTION_SYSTEMS)}")
    print("-" * 60)


def init_parser():
    parser = argparse.ArgumentParser(
        description="Fantasy Baseball Player Evaluation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--draft",
        action="store_true",
        help="Add additional data sources for draft preparation",
    )

    parser.add_argument(
        "--league",
        type=str,
        default="bush",
        choices=["bush", "nfbc", "yahoo", "espn"],
        help="Specify the league type (default: bush)",
    )

    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached data instead of fetching fresh from APIs",
    )

    parser.add_argument(
        "--ros",
        action="store_true",
        default=True,
        help="Use rest-of-season projections (default: True)",
    )

    parser.add_argument(
        "--sort",
        type=str,
        default=None,
        help="Sort results by specified column (default: ratcdc for ROS, atc for preseason)",
    )

    parser.add_argument(
        "--no-google",
        action="store_true",
        help="Skip uploading to Google Sheets",
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        default=True,
        help="Refresh external data (CloserMonkey, Eno) before running",
    )

    args = parser.parse_args()
    if args.sort is None:
        args.sort = "ratcdc" if args.ros else "atc"
    return args


def apply_league_data(hitters_df, pitchers_df, args):
    """Merge league-specific roster/ADP data into the projection dataframes."""
    if args.league == "bush":
        hitters_df = add_fantasy_team(hitters_df, league="bush")
        pitchers_df = add_fantasy_team(pitchers_df, league="bush")

    elif args.league == "nfbc":
        hitters_df = add_nfbc_data(hitters_df)
        pitchers_df = add_nfbc_data(pitchers_df)

    elif args.league == "espn":
        if not args.use_cache:
            from api.espn import fetch_espn_roster_csv

            fetch_espn_roster_csv(
                ESPN_LEAGUE_ID,
                CURRENT_SEASON,
                f"{INPUT_DATA_DIR}/rosters/espn_roster.csv",
            )
        hitters_df = add_fantasy_team(hitters_df, league="espn")
        pitchers_df = add_fantasy_team(pitchers_df, league="espn")

    elif args.league == "yahoo":
        if not args.use_cache:
            from api.yahoo import fetch_yahoo_roster_csv

            fetch_yahoo_roster_csv(
                YAHOO_LEAGUE_KEY,
                CURRENT_SEASON,
                f"{INPUT_DATA_DIR}/rosters/yahoo_roster.csv",
            )
        hitters_df = add_fantasy_team(hitters_df, league="yahoo")
        pitchers_df = add_fantasy_team(pitchers_df, league="yahoo")

    return hitters_df, pitchers_df


def main():
    """Main entry point"""
    args = init_parser()
    print_startup_banner()

    print("args.league:", args.league)
    print("args.use_cache:", args.use_cache)

    if args.refresh:
        from .data_refresh import refresh_all

        refresh_all()

    try:
        # Get all projection data
        hitters_df, pitchers_df = get_or_fetch_fangraphs_data(
            use_cache=args.use_cache,
            use_ros_projections=args.ros,
            league=args.league,
        )
        hitters_df, pitchers_df = apply_league_data(hitters_df, pitchers_df, args)

        if args.draft:
            hitters_df.insert(
                hitters_df.columns.get_loc("player_name") + 1, "is_drafted", ""
            )
            pitchers_df.insert(
                pitchers_df.columns.get_loc("player_name") + 1, "is_drafted", ""
            )

        hitters_df = add_hitter_supplemental_data(hitters_df, use_cache=args.use_cache)
        pitchers_df = add_pitcher_supplemental_data(
            pitchers_df, use_cache=args.use_cache
        )

        hitters_df = hitters_df.sort_values(by=args.sort, ascending=False)
        pitchers_df = pitchers_df.sort_values(by=args.sort, ascending=False)

        current_date = datetime.now().strftime("%Y-%m-%d")
        hitters_file = f"{OUTPUT_DIR}/{current_date}_hitters.csv"
        pitchers_file = f"{OUTPUT_DIR}/{current_date}_pitchers.csv"
        hitters_df.to_csv(hitters_file, index=False)
        pitchers_df.to_csv(pitchers_file, index=False)
        print(f"\n✅ Results saved to: {hitters_file} and {pitchers_file}")
        print(f"📊 Hitters: {len(hitters_df)}, Pitchers: {len(pitchers_df)}")

        # Upload to Google Sheets
        if not args.no_google:
            try:
                from api.google_sheets import upload_to_google_sheets

                upload_to_google_sheets(
                    hitters_df,
                    GOOGLE_SHEETS_SPREADSHEET_IDS[args.league],
                    GOOGLE_SHEETS_HITTERS_TAB,
                    GOOGLE_SHEETS_CREDENTIALS_FILE,
                    GOOGLE_SHEETS_TOKEN_FILE,
                )
                upload_to_google_sheets(
                    pitchers_df,
                    GOOGLE_SHEETS_SPREADSHEET_IDS[args.league],
                    GOOGLE_SHEETS_PITCHERS_TAB,
                    GOOGLE_SHEETS_CREDENTIALS_FILE,
                    GOOGLE_SHEETS_TOKEN_FILE,
                )
                sheet_id = GOOGLE_SHEETS_SPREADSHEET_IDS[args.league]
                print(
                    f"📤 Uploaded to Google Sheets tabs: {GOOGLE_SHEETS_HITTERS_TAB}, {GOOGLE_SHEETS_PITCHERS_TAB}"
                )
                print(f"🔗 https://docs.google.com/spreadsheets/d/{sheet_id}")
            except FileNotFoundError:
                print(
                    f"\n⚠️  Google Sheets upload skipped: {GOOGLE_SHEETS_CREDENTIALS_FILE} not found. "
                    "Download OAuth credentials from Google Cloud Console."
                )
            except ImportError:
                print(
                    "\n⚠️  Google Sheets upload skipped: gspread not installed. "
                    "Run: pip install gspread google-auth-oauthlib"
                )
            except Exception as e:
                print(f"\n⚠️  Google Sheets upload failed: {e}")
                print("CSVs were saved successfully.")

        # Show top players
        display_cols = ["player_name", "team", "position"] + PROJECTION_SYSTEMS

        print(f"\n🏆 Top 20 Hitters:")
        print("-" * 50)
        available_cols = [col for col in display_cols if col in hitters_df.columns]
        print(hitters_df.head(20)[available_cols].to_string(index=False))

        print(f"\n🏆 Top 20 Pitchers:")
        print("-" * 50)
        available_cols = [col for col in display_cols if col in pitchers_df.columns]
        print(pitchers_df.head(20)[available_cols].to_string(index=False))

    except KeyboardInterrupt:
        print(f"\n⚠️  Analysis interrupted by user")
        sys.exit(1)

    print(f"\n✅ Analysis completed successfully!")


if __name__ == "__main__":
    main()
