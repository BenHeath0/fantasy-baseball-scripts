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
    python main.py --fresh-data                 # Force fetch fresh data from APIs
"""

import argparse
import sys
from datetime import datetime

from config import OUTPUT_DIR, PROJECTION_SYSTEMS
from utils import ensure_directory_exists, get_current_date_string
from data_fetchers import get_or_fetch_fangraphs_data
from data_processors import (
    filter_available_players,
    calculate_projection_metrics,
    add_draft_augmentations,
    add_data_augmentations,
)
from analysis import (
    determine_keepers,
    calculate_total_keeper_cost,
    get_top_available_players,
)


def print_startup_banner():
    """Print a nice startup banner"""
    print("=" * 60)
    print("🏆 Fantasy Baseball Player Evaluation Tool 🏆")
    print("=" * 60)
    print(f"Using projection systems: {', '.join(PROJECTION_SYSTEMS)}")
    total_cost = calculate_total_keeper_cost()
    print(f"Current keeper cost: ${total_cost}")
    print("-" * 60)


def run_keeper_analysis(args):
    """Run keeper analysis workflow"""
    print("\n📊 Running Keeper Analysis...")

    # Get projection data
    projection_df = get_or_fetch_fangraphs_data(fetch_fresh=args.fresh_data)

    # Run keeper analysis
    recommended_keepers = determine_keepers(projection_df)

    return recommended_keepers


def run_draft_analysis(args):
    """Run draft preparation workflow"""
    print(f"\n🏈 Preparing draft analysis for {args.league} league...")

    # Get projection data
    projection_df = get_or_fetch_fangraphs_data(fetch_fresh=args.fresh_data)

    # Filter to available players
    df = filter_available_players(projection_df, args.league)

    # Calculate projection metrics
    df = calculate_projection_metrics(df)

    # Add data augmentations
    df = add_data_augmentations(df, args.league, fetch_fresh=args.fresh_data)

    # Add draft-specific augmentations
    if args.draft:
        df = add_draft_augmentations(df)

    # Sort by best projection
    df = df.sort_values(by="best_projection", ascending=False)

    # Save to CSV
    ensure_directory_exists(OUTPUT_DIR)
    current_date = get_current_date_string()
    output_file = f"{OUTPUT_DIR}/{current_date}_players_avail.csv"
    df.to_csv(output_file, index=False)

    print(f"\n✅ Results saved to: {output_file}")
    print(f"📊 Total players analyzed: {len(df)}")

    # Show top players
    top_players = get_top_available_players(df, n=20)
    print(f"\n🏆 Top 20 Available Players:")
    print("-" * 50)

    display_cols = [
        "player_name",
        "team",
        "position",
        "best_projection",
        "avg_projection",
    ]
    available_display_cols = [col for col in display_cols if col in top_players.columns]

    print(top_players[available_display_cols].to_string(index=False))

    return df


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fantasy Baseball Player Evaluation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Analysis mode arguments
    parser.add_argument(
        "--keepers",
        action="store_true",
        help="Run keeper analysis to determine which players to keep",
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
        "--fresh-data",
        action="store_true",
        default=True,
        help="Force fetch fresh data from APIs instead of using cache",
    )

    parser.add_argument(
        "--sort",
        type=str,
        default="best_projection",
        help="Sort results by specified column (default: best_projection)",
    )

    args = parser.parse_args()

    # Print startup banner
    print_startup_banner()

    try:
        # Determine which analysis to run
        if args.keepers:
            run_keeper_analysis(args)
        else:
            # Default: run draft analysis
            run_draft_analysis(args)

        print(f"\n✅ Analysis completed successfully!")

    except KeyboardInterrupt:
        print(f"\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    # except Exception as e:
    #     print(f"\n❌ Error during analysis: {e}")
    #     sys.exit(1)


if __name__ == "__main__":
    main()
