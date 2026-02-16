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
    OUTPUT_DIR,
    PROJECTION_SYSTEMS,
    GOOGLE_SHEETS_SPREADSHEET_IDS,
    GOOGLE_SHEETS_HITTERS_TAB,
    GOOGLE_SHEETS_PITCHERS_TAB,
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    GOOGLE_SHEETS_TOKEN_FILE,
)
from .data_fetchers import get_or_fetch_fangraphs_data
from .data_processors import (
    filter_available_players,
    add_draft_augmentations,
    add_hitter_supplemental_data,
    add_pitcher_supplemental_data,
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
        "--sort",
        type=str,
        default="atc",
        help="Sort results by specified column (default: atc)",
    )

    args = parser.parse_args()
    return args


def main():
    """Main entry point"""
    args = init_parser()
    print_startup_banner()

    print("args.league:", args.league)
    print("args.use_cache:", args.use_cache)

    try:
        # Get all projection data
        hitters_df, pitchers_df = get_or_fetch_fangraphs_data(
            use_cache=args.use_cache,
            use_ros_projections=False,
            league=args.league,
        )
        if args.league == "bush":
            hitters_df = filter_available_players(hitters_df)
            pitchers_df = filter_available_players(pitchers_df)

        hitters_df = add_hitter_supplemental_data(hitters_df, use_cache=args.use_cache)
        pitchers_df = add_pitcher_supplemental_data(
            pitchers_df, use_cache=args.use_cache
        )

        if args.draft:
            hitters_df = add_draft_augmentations(hitters_df)
            pitchers_df = add_draft_augmentations(pitchers_df)

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
            print(
                f"📤 Uploaded to Google Sheets tabs: {GOOGLE_SHEETS_HITTERS_TAB}, {GOOGLE_SHEETS_PITCHERS_TAB}"
            )
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
