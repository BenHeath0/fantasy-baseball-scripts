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
    GOOGLE_SHEETS_SPREADSHEET_ID,
    GOOGLE_SHEETS_TAB_NAME,
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    GOOGLE_SHEETS_TOKEN_FILE,
)
from .data_fetchers import get_or_fetch_fangraphs_data
from .data_processors import (
    filter_available_players,
    add_draft_augmentations,
    add_supplemental_data,
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
        choices=["bush", "yahoo", "espn"],
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

    try:
        # Get all projection data
        df = get_or_fetch_fangraphs_data(
            fetch_fresh=not args.use_cache, use_ros_projections=False
        )
        if args.league == "bush":
            df = filter_available_players(df)

        df = add_supplemental_data(df, fetch_fresh=not args.use_cache)
        if args.draft:
            df = add_draft_augmentations(df)

        df = df.sort_values(by=args.sort, ascending=False)
        current_date = datetime.now().strftime("%Y-%m-%d")
        output_file = f"{OUTPUT_DIR}/{current_date}_players_avail.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✅ Results saved to: {output_file}")
        print(f"📊 Total players analyzed: {len(df)}")

        # Upload to Google Sheets
        try:
            from api.google_sheets import upload_to_google_sheets

            upload_to_google_sheets(
                df,
                GOOGLE_SHEETS_SPREADSHEET_ID,
                GOOGLE_SHEETS_TAB_NAME,
                GOOGLE_SHEETS_CREDENTIALS_FILE,
                GOOGLE_SHEETS_TOKEN_FILE,
            )
            print(f"📤 Uploaded to Google Sheets tab: {GOOGLE_SHEETS_TAB_NAME}")
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
            print("CSV was saved successfully.")

        # Show top players
        top_players = df.head(20)
        print(f"\n🏆 Top 20 Available Players:")
        print("-" * 50)

        display_cols = ["player_name", "team", "position"] + PROJECTION_SYSTEMS
        available_display_cols = [
            col for col in display_cols if col in top_players.columns
        ]

        print(top_players[available_display_cols].to_string(index=False))

    except KeyboardInterrupt:
        print(f"\n⚠️  Analysis interrupted by user")
        sys.exit(1)

    print(f"\n✅ Analysis completed successfully!")


if __name__ == "__main__":
    main()
