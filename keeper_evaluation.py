import argparse
import os

import pandas as pd

from player_evaluation.config import PROJECTION_SYSTEMS
from player_evaluation.data_fetchers import get_or_fetch_fangraphs_data
from player_evaluation.utils import normalize_name_column


def get_roster_data():
    """Get the current roster with keeper costs and status"""
    roster_path = os.path.join(
        os.path.dirname(__file__),
        "player_evaluation",
        "input_data",
        "bush_league_roster.csv",
    )

    # Read hitting section (skip first row, use row 2 as header)
    hitting_df = pd.read_csv(roster_path, skiprows=1, nrows=19)

    # Read pitching section (skip to row 24, use it as header)
    pitching_df = pd.read_csv(roster_path, skiprows=23)

    # Combine both sections and extract Player and Salary columns
    roster_df = pd.concat([hitting_df, pitching_df], ignore_index=True)

    roster_df = roster_df[["Player", "Salary"]].dropna()
    roster_df = roster_df.rename(
        columns={"Player": "player_name", "Salary": "keeper_cost"}
    )
    roster_df["keeper_cost"] = roster_df["keeper_cost"].astype(int)
    normalize_name_column(roster_df)

    return roster_df


def determine_keepers(projection_df, roster_df):
    """Print each rostered player's keeper cost vs projected auction values."""
    normalize_name_column(projection_df)
    merged_df = pd.merge(roster_df, projection_df, how="left", on="player_name")
    merged_df = merged_df.sort_values("keeper_cost", ascending=False)

    print(merged_df.to_string())
    merged_df.to_csv("keeper_analysis.csv", index=False)


def print_startup_banner(total_cost):
    """Print a nice startup banner"""
    print("=" * 60)
    print("🏆 Fantasy Baseball Player Evaluation Tool 🏆")
    print("=" * 60)
    print(f"Using projection systems: {', '.join(PROJECTION_SYSTEMS)}")
    print(f"Current keeper cost: ${total_cost}")
    print("-" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fantasy Baseball Player Evaluation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached data instead of fetching fresh",
    )
    args = parser.parse_args()

    roster_df = get_roster_data()
    total_keeper_cost = roster_df["keeper_cost"].sum()

    print_startup_banner(total_keeper_cost)
    projection_df = get_or_fetch_fangraphs_data(
        use_cache=args.use_cache, use_ros_projections=False
    )
    determine_keepers(projection_df, roster_df)


if __name__ == "__main__":
    main()
