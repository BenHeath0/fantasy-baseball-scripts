import pandas as pd
from utils import load_auction_projections


def determine_keepers(roster_df, fangraphs_df):
    """
    Combine your roster info with Fangraphs Auction Values and apply
    your logic for deciding keepers.

    In this example, we assume your `roster_df` has columns:
      - 'player_name'
      - 'keeper_cost' (the cost to keep a player for your league)

    And `fangraphs_df` has columns:
      - 'player_name'
      - 'auction_value'

    We'll do a simple merge on player_name.
    """
    merged = pd.merge(
        roster_df,
        fangraphs_df,
        how="left",  # some players might not appear in the Fangraphs data
        left_on="player_name",
        right_on="player_name",
    )

    # Evaluate keeper or not
    # A simple approach: if auction_value > keeper_cost by some threshold
    # you keep them. You can refine this logic as needed.
    keep_threshold = -5.0
    recommendations = []
    for idx, row in merged.iterrows():
        cost = row.get("keeper_cost", 0)
        val = row.get("auction_value", 0)
        player = row.get("player_name")

        if pd.isna(val):
            # If the player's not found in Fangraphs data, assume we can't accurately project.
            recommendation = "No Value Data"
        else:
            profit = val - cost
            if profit >= keep_threshold:
                recommendation = (
                    f"KEEP (auction_val=${val:.1f}, cost=${cost}, profit=${profit:.1f})"
                )
                recommendations.append((player, recommendation))
            else:
                recommendation = (
                    f"DROP (auction_val=${val:.1f}, cost=${cost}, profit=${profit:.1f})"
                )

    recommendations.sort(key=lambda x: "KEEP" not in x[1])
    return recommendations


def calc_keeper_recommendations():
    roster = [
        # Hitters
        {"player_name": "Kyle Higashioka", "keeper_cost": 5},
        {"player_name": "Bo Naylor", "keeper_cost": 8},
        {"player_name": "Ryan O'Hearn", "keeper_cost": 1},
        {"player_name": "Nico Hoerner", "keeper_cost": 9},
        {"player_name": "Matt Chapman", "keeper_cost": 23},
        {"player_name": "Trevor Story", "keeper_cost": 6},
        {"player_name": "Alex Bregman", "keeper_cost": 38},
        {"player_name": "Michael Massey", "keeper_cost": 8},
        {"player_name": "Ceddanne Rafaela", "keeper_cost": 22},
        {"player_name": "Jacob Young", "keeper_cost": 12},
        {"player_name": "Jorge Soler", "keeper_cost": 3},
        {"player_name": "Miguel Vargas", "keeper_cost": 8},
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
        {"player_name": "Hayden Wesneski", "keeper_cost": 8},
        {"player_name": "Matt Strahm", "keeper_cost": 1},
        {"player_name": "Austin Gomber", "keeper_cost": 5},
        {"player_name": "Taijuan Walker", "keeper_cost": 1},
        {"player_name": "Mike Clevinger", "keeper_cost": 1},
        {"player_name": "J.P. France", "keeper_cost": 1},
        {"player_name": "Robert Stephenson", "keeper_cost": 5},
        {"player_name": "Daniel Espino", "keeper_cost": 10},
        {"player_name": "Ricky Tiedemann", "keeper_cost": 10},
        {"player_name": "Zack Thompson", "keeper_cost": 5},
    ]
    roster_df = pd.DataFrame(roster)

    projection_systems = ["steamer", "batx", "zips", "steamer-experimental"]

    keeper_recommendations = {}
    for system in projection_systems:
        # print(f"-----{system}-----")
        fangraphs_df = load_auction_projections(system)
        recommendations = determine_keepers(roster_df, fangraphs_df)

        for player, recommendation in recommendations:
            if player not in keeper_recommendations:
                keeper_recommendations[player] = {}
            keeper_recommendations[player][system] = recommendation

    for player, recs in keeper_recommendations.items():
        print(f"---{player}---")
        for system, rec in recs.items():
            print(f"{system}: {rec}")
        print()


def main():
    calc_keeper_recommendations()


if __name__ == "__main__":
    main()
