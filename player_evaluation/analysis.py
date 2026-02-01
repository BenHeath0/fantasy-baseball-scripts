"""Analysis functions for fantasy baseball player evaluation"""

import pandas as pd
from .config import PROJECTION_SYSTEMS, KEEPER_THRESHOLD


def get_roster_data():
    """Get the current roster with keeper costs and status"""
    import os

    roster_path = os.path.join(os.path.dirname(__file__), "input_data", "roster.csv")

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
    roster_df["keeping"] = ""

    return roster_df


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

    print(f"\n{'=' * 50}")
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
        from .data_processors import calculate_projection_metrics

        df = calculate_projection_metrics(df)

    top_players = df.nlargest(n, "best_projection")
    return top_players
