import argparse
import os

import pandas as pd

from player_evaluation.config import PROJECTION_SYSTEMS
from player_evaluation.data_fetchers import get_or_fetch_fangraphs_data
from player_evaluation.utils import normalize_name_column


keeping = [
    ("Carlos Narvaez", "Hitter"),
    ("Miguel Vargas", "Hitter"),
    ("Edward Cabrera", "Pitcher"),
    ("Nolan McLean", "Pitcher"),
    ("Chris Sale", "Pitcher"),
    ("George Springer", "Hitter"),
    ("Michael Busch", "Hitter"),
    ("Drew Rasmussen", "Pitcher"),
    ("Chase Burns", "Pitcher"),
    ("Roman Anthony", "Hitter"),
    ("Marcell Ozuna", "Hitter"),
    ("Ryan OHearn", "Hitter"),
    ("Jorge Soler", "Hitter"),
    ("Brett Baty", "Hitter"),
    ("Colton Cowser", "Hitter"),
    ("Cody Bellinger", "Hitter"),
]


def get_roster_data():
    """Get the current roster with keeper costs and status"""
    players_path = os.path.join(
        os.path.dirname(__file__),
        "player_evaluation",
        "input_data",
        "rosters",
        "bush_league_players.csv",
    )

    players_df = pd.read_csv(players_path)
    roster_df = players_df[players_df["Status"] == "TWN"][["Player", "Salary"]].copy()

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


def calc_keeper_cost(roster_df):
    """Calculate and print keeper costs broken down by hitters and pitchers."""
    keeper_names = [name for name, _ in keeping]
    keeper_types = {name: ptype for name, ptype in keeping}

    keepers_df = roster_df[roster_df["player_name"].isin(keeper_names)].copy()

    print(keepers_df.to_string())

    unmatched = set(keeper_names) - set(keepers_df["player_name"])
    if unmatched:
        print(f"\nWARNING: Keepers not found in roster: {', '.join(sorted(unmatched))}")

    keepers_df["type"] = keepers_df["player_name"].map(keeper_types)

    total_cost = keepers_df["keeper_cost"].sum()
    hitter_cost = keepers_df.loc[keepers_df["type"] == "Hitter", "keeper_cost"].sum()
    pitcher_cost = keepers_df.loc[keepers_df["type"] == "Pitcher", "keeper_cost"].sum()
    num_hitters = (keepers_df["type"] == "Hitter").sum()
    num_pitchers = (keepers_df["type"] == "Pitcher").sum()

    print("\n" + "=" * 60)
    print("Keeper Cost Summary")
    print("=" * 60)
    print(f"  Hitters (Goal: 150-180):  ${hitter_cost}  ({num_hitters}/14)")
    print(f"  Pitchers (Goal: 120-150): ${pitcher_cost}  ({num_pitchers}/11)")
    print(f"  Total (Goal: 300):    ${total_cost}  ({num_hitters + num_pitchers}/25)")
    print("=" * 60)


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
    hitters_df, pitchers_df = get_or_fetch_fangraphs_data(
        use_cache=args.use_cache, use_ros_projections=False
    )
    keep_cols = [
        "player_name",
        "team",
        "position",
        "steamer",
        "thebatx",
        "oopsy",
        "atc",
    ]
    projection_df = pd.concat(
        [hitters_df[keep_cols], pitchers_df[keep_cols]], ignore_index=True
    )
    determine_keepers(projection_df, roster_df)
    calc_keeper_cost(roster_df)


if __name__ == "__main__":
    main()
