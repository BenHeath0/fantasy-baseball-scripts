from player_evaluation.analysis import get_roster_data, determine_keepers
from player_evaluation.data_fetchers import get_or_fetch_fangraphs_data
from player_evaluation.config import PROJECTION_SYSTEMS
import argparse


def calculate_total_keeper_cost():
    """Calculate the total cost of currently designated keepers"""
    roster_df = get_roster_data()
    total_keeper_cost = roster_df[roster_df.get("keeping", False) == True][
        "keeper_cost"
    ].sum()
    return total_keeper_cost


def print_startup_banner():
    """Print a nice startup banner"""
    print("=" * 60)
    print("🏆 Fantasy Baseball Player Evaluation Tool 🏆")
    print("=" * 60)
    print(f"Using projection systems: {', '.join(PROJECTION_SYSTEMS)}")
    total_cost = calculate_total_keeper_cost()
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
    print_startup_banner()
    projection_df = get_or_fetch_fangraphs_data(
        fetch_fresh=not args.use_cache, use_ros_projections=False
    )
    determine_keepers(projection_df)


if __name__ == "__main__":
    main()
