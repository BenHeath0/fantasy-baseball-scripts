"""Analysis functions for fantasy baseball player evaluation"""

import pandas as pd
from config import PROJECTION_SYSTEMS, KEEPER_THRESHOLD


def get_roster_data():
    """Get the current roster with keeper costs and status"""
    roster = [
        # Hitters
        {"player_name": "Kyle Higashioka", "keeper_cost": 5, "keeping": True},
        {"player_name": "Bo Naylor", "keeper_cost": 8, "keeping": True},
        {"player_name": "Ryan O'Hearn", "keeper_cost": 1, "keeping": True},
        {"player_name": "Nico Hoerner", "keeper_cost": 14, "keeping": True},
        {"player_name": "Matt Chapman", "keeper_cost": 23, "keeping": True},
        {"player_name": "Trevor Story", "keeper_cost": 6, "keeping": True},
        {"player_name": "Alex Bregman", "keeper_cost": 38},
        {"player_name": "Michael Massey", "keeper_cost": 8, "keeping": True},
        {"player_name": "Ceddanne Rafaela", "keeper_cost": 22},
        {"player_name": "Jacob Young", "keeper_cost": 12},
        {"player_name": "Jorge Soler", "keeper_cost": 3, "keeping": True},
        {"player_name": "Miguel Vargas", "keeper_cost": 8, "keeping": True},
        {"player_name": "Daulton Varsho", "keeper_cost": 20},
        {"player_name": "Juan Yepez", "keeper_cost": 5},
        {"player_name": "Thayron Liranzo", "keeper_cost": 8},
        {"player_name": "Roman Anthony", "keeper_cost": 10},
        {"player_name": "Luis Matos", "keeper_cost": 10},
        # Pitchers
        {"player_name": "Yu Darvish", "keeper_cost": 33},
        {"player_name": "Bailey Falter", "keeper_cost": 11},
        {"player_name": "Shota Imanaga", "keeper_cost": 31},
        {"player_name": "Lance Lynn", "keeper_cost": 12},
        {"player_name": "Joe Musgrove", "keeper_cost": 28},
        {"player_name": "Jhony Brito", "keeper_cost": 1},
        {"player_name": "Gavin Stone", "keeper_cost": 8},
        {"player_name": "Hayden Wesneski", "keeper_cost": 8, "keeping": True},
        {"player_name": "Matt Strahm", "keeper_cost": 1, "keeping": True},
        {"player_name": "Austin Gomber", "keeper_cost": 5},
        {"player_name": "Taijuan Walker", "keeper_cost": 1},
        {"player_name": "Mike Clevinger", "keeper_cost": 1, "keeping": True},
        {"player_name": "J.P. France", "keeper_cost": 1, "keeping": True},
        {"player_name": "Robert Stephenson", "keeper_cost": 5},
        {"player_name": "Daniel Espino", "keeper_cost": 10},
        {"player_name": "Ricky Tiedemann", "keeper_cost": 10},
        {"player_name": "Zack Thompson", "keeper_cost": 5},
    ]
    return pd.DataFrame(roster)


def calculate_total_keeper_cost():
    """Calculate the total cost of currently designated keepers"""
    roster_df = get_roster_data()
    total_keeper_cost = roster_df[roster_df.get("keeping", False) == True][
        "keeper_cost"
    ].sum()
    return total_keeper_cost


def determine_keepers(projection_df, threshold=None):
    """
    Analyze roster and determine which players to keep based on projections

    Args:
        projection_df: DataFrame with player projections
        threshold: Profit threshold for keeping players (defaults to config value)
    """
    if threshold is None:
        threshold = KEEPER_THRESHOLD

    roster_df = get_roster_data()

    # Merge roster with projections
    roster_with_projections_df = pd.merge(
        roster_df, projection_df, how="left", on="player_name"
    )

    print(f"Keeper Analysis (Threshold: {threshold})")
    print("=" * 50)

    recommended_keepers = []

    for idx, row in roster_with_projections_df.iterrows():
        keeper_cost = row["keeper_cost"]
        player_name = row["player_name"]
        current_keeper_status = row.get("keeping", False)

        # Calculate profits for each projection system
        profits = {}
        max_profit = float("-inf")

        for system in PROJECTION_SYSTEMS:
            if system in row and pd.notna(row[system]):
                profit = row[system] - keeper_cost
                profits[system] = profit
                max_profit = max(max_profit, profit)
            else:
                profits[system] = None

        # Determine if player should be kept
        should_keep = max_profit >= threshold

        if should_keep or current_keeper_status:
            print(f"\n{player_name} (Cost: ${keeper_cost})")
            print(
                f"  Current Status: {'KEEPING' if current_keeper_status else 'Available'}"
            )
            print(f"  Recommendation: {'KEEP' if should_keep else 'DROP'}")

            for system, profit in profits.items():
                if profit is not None:
                    status_icon = (
                        "✅" if profit >= 0 else ("⚠️" if profit >= threshold else "❌")
                    )
                    print(f"    {system}: ${profit:.1f} {status_icon}")
                else:
                    print(f"    {system}: No data")

            if should_keep:
                recommended_keepers.append(
                    {
                        "player_name": player_name,
                        "keeper_cost": keeper_cost,
                        "max_profit": max_profit,
                        "current_keeper": current_keeper_status,
                    }
                )

    print(f"\n{'='*50}")
    print(f"SUMMARY:")
    print(f"Total recommended keepers: {len(recommended_keepers)}")

    current_keepers = roster_df[roster_df.get("keeping", False) == True]
    current_total = (
        current_keepers["keeper_cost"].sum() if len(current_keepers) > 0 else 0
    )

    recommended_total = sum(k["keeper_cost"] for k in recommended_keepers)

    print(f"Current keeper cost: ${current_total}")
    print(f"Recommended keeper cost: ${recommended_total}")
    print(f"Difference: ${recommended_total - current_total}")

    return recommended_keepers


def get_top_available_players(df, n=50):
    """Get top N available players sorted by best projection"""
    if "best_projection" not in df.columns:
        print("Warning: best_projection column not found. Computing now...")
        from data_processors import calculate_projection_metrics

        df = calculate_projection_metrics(df)

    top_players = df.nlargest(n, "best_projection")
    return top_players
