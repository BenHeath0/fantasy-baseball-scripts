import argparse
import pandas as pd
from data_loaders import (
    load_fantasypros_data,
    load_athletic_data,
    load_nffc_data,
    load_player_notes,
)


def print_startup_banner():
    """Print a nice startup banner"""
    print("=" * 60)
    print("🏆 Fantasy Football Draft Tool 🏆")
    print("=" * 60)


def create_output_file(league):
    """Create the output file for the given league"""

    # Start w/ fantasypros
    df = load_fantasypros_data(league=league)

    # Add top 10 fantasypros data
    top_10_df = load_fantasypros_data(league=league, is_top_10=True)
    df = df.merge(top_10_df, on="name", how="left")

    # Add athletic data
    # athletic_df = load_athletic_data(league)
    # df = df.merge(athletic_df, on="name", how="left")

    # Add nffc data
    nffc_df = load_nffc_data()
    df = df.merge(nffc_df, on="name", how="left")

    # Add player notes
    player_notes_df = load_player_notes()
    print(player_notes_df.head())
    df = df.merge(player_notes_df, on="name", how="left")

    # Add a "drafted" column
    df["drafted"] = ""

    # Reorder columns
    df = df[
        [
            "name",
            "drafted",
            "fantasypros_rk",
            "fantasypros_rk_top10",
            "nffc_adp",
            "primetime_adp",
            "fantasypros_tier",
            "fantasypros_pos_rank",
            "Note",
        ]
    ]
    print(df.head())

    df.to_csv(f"output_{league}.csv", index=False)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fantasy Football Draft Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--league",
        type=str,
        default="barterball",
        choices=["barterball", "fnf", "recharge"],
        help="Specify the league type (default: barterball)",
    )

    args = parser.parse_args()

    # Print startup banner
    print_startup_banner()

    create_output_file(args.league)


if __name__ == "__main__":
    main()
