import pandas as pd
import requests
from datetime import datetime

projection_systems = ["steamer", "thebatx", "zips", "zipsdc", "oopsy"]


roster = [
    # Hitters
    {"player_name": "Kyle Higashioka", "keeper_cost": 5},
    {"player_name": "Bo Naylor", "keeper_cost": 8},
    {"player_name": "Ryan O'Hearn", "keeper_cost": 1},
    {"player_name": "Nico Hoerner", "keeper_cost": 14},
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


def fetch_auction_values(projection_system, player_type):
    print("fetching...")
    url = "https://www.fangraphs.com/api/fantasy/auction-calculator/data"
    params = {
        "teams": 19,
        "lg": "MLB",
        "dollars": 300,
        "mb": 1,
        "mp": 20,
        "msp": 5,
        "mrp": 5,
        "type": player_type,
        "players": "",
        "proj": projection_system,
        "split": "",
        "points": "c|1,2,3,4,5,6|0,1,10,2,3,6",
        "rep": 0,
        "drp": 0,
        "pp": "C,SS,2B,3B,OF,1B",
        "pos": "2,1,1,1,4,1,1,1,0,2,5,4,2,0,0",
        "sort": "",
        "view": 0,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_auction_values_df(projection_system):
    batters = fetch_auction_values(projection_system, "bat")
    pitchers = fetch_auction_values(projection_system, "pit")

    batters_data = [
        {"PlayerName": player["PlayerName"], "Dollars": player["Dollars"]}
        for player in batters["data"]
    ]

    pitchers_data = [
        {"PlayerName": player["PlayerName"], "Dollars": player["Dollars"]}
        for player in pitchers["data"]
    ]

    # Create DataFrame
    batters_df = pd.DataFrame(batters_data)
    pitchers_df = pd.DataFrame(pitchers_data)

    combined_df = pd.concat([batters_df, pitchers_df], ignore_index=True)
    combined_df.rename(
        columns={
            "PlayerName": "player_name",
            "Dollars": projection_system,
        },
        inplace=True,
    )

    return combined_df


def determine_keepers(roster_with_projections_df):
    keep_threshold = -5.0
    print(f"Threshold: {keep_threshold}\n\n")
    for idx, row in roster_with_projections_df.iterrows():
        keeper_cost = row["keeper_cost"]
        player_name = row["player_name"]

        if any(
            row[system] - keeper_cost >= keep_threshold for system in projection_systems
        ):
            print(f"---{player_name}, Keeper Cost: {keeper_cost}---")
            for system in projection_systems:
                profit = row[system] - keeper_cost
                profit = row[system] - keeper_cost
                print(f"  {system}: {profit:.1f} {'✅' if profit >= 0 else ''}")
            print()


def determine_fetch_needed():
    # Check when we last ran this
    last_fetched_file = "last_fetched.txt"

    try:
        with open(last_fetched_file, "r") as file:
            last_fetched_str = file.read().strip()
            if not last_fetched_str:
                return True
            last_fetched = datetime.strptime(last_fetched_str, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - last_fetched).days >= 1:
                return True
    except FileNotFoundError:
        return True

    return False


def get_projections_df():
    # If we dont need to fetch, just read from file
    fetch_needed = determine_fetch_needed()
    if not fetch_needed:
        df = pd.read_csv("auction_values_combined.csv")
        return df

    # If need to, fetch and combine
    merged_df = None
    for system in projection_systems:
        df = get_auction_values_df(system)
        if merged_df is None:
            merged_df = df
        else:
            merged_df = merged_df.merge(df, how="left", on="player_name")

    merged_df.to_csv("auction_values_combined.csv", index=False)
    with open("last_fetched.txt", "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return merged_df


def main():
    projection_df = get_projections_df()
    roster_with_projections_df = pd.merge(
        roster_df, projection_df, how="left", on="player_name"
    )
    determine_keepers(roster_with_projections_df)


if __name__ == "__main__":
    main()
