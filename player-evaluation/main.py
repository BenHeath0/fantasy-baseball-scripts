import pandas as pd
import requests
import argparse
from datetime import datetime

"""
NOTES:
- Fangraphs is source of truth on all naming conventions... like team abbreviations and positions
"""


# TODO: we need to do alot more data cleanup. repeated players we dont handle rn
def cleanup_juniors(df, key):
    df[key] = df[key].str.replace("Jr.", "", regex=False).str.strip()
    return df


# projection_systems = ["steamer", "thebatx", "zips", "zipsdc", "oopsy"]
projection_systems = ["steamer", "thebatx", "oopsy"]
player_rater_systems = ["steamerr", "rthebatx", "roopsydc", "season"]

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
roster_df = pd.DataFrame(roster)

total_keeper_cost = roster_df[roster_df["keeping"] == True]["keeper_cost"].sum()
print(f"Total Keeper Cost: {total_keeper_cost}")


def fetch_auction_values(projection_system, player_type):
    print("fetching auction vals...")
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


"""
TODO: when we get players from projection systems, its just projectons.
if we change timeframe, it gives us the value that guys have actually produced. Maybe thats better?
"""


def fetch_player_rater_values(projection_system):
    print("fetching player rater vals...")
    url = "https://www.fangraphs.com/api/fantasy/player-rater/data"
    params = {
        "timeframetype": projection_system,
        "leaguetype": 3,
        "pos": None,
        "postype": None,
        "season": 2025,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_player_rater_df(projection_system):
    response = fetch_player_rater_values(projection_system)
    player_data = [
        # TODO: instead of projection system, map the value to more user friendly, so same as auction calc
        {
            "player_name": player["playerName"],
            "team": player["auction"]["AbbName"],
            "position": player["auction"]["Position"],
            projection_system: player["auction"]["Dollars"],
        }
        for player in response["data"]
    ]

    player_rater_df = pd.DataFrame(player_data)
    return player_rater_df


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


def determine_keepers(projection_df):
    roster_with_projections_df = pd.merge(
        roster_df, projection_df, how="left", on="player_name"
    )
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
                print(
                    f"  {system}: {profit:.1f} {'✅' if profit >= 0 else '' if profit >= keep_threshold else '❌'}"
                )
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
    for system in player_rater_systems:
        # df = get_auction_values_df(system)
        df = get_player_rater_df(system)
        if merged_df is None:
            merged_df = df
        else:
            merged_df = merged_df.merge(
                df, how="left", on=["player_name", "team", "position"]
            )

    merged_df.to_csv("auction_values_combined.csv", index=False)
    with open("last_fetched.txt", "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return merged_df


def draft_specific_augmentations(df, league):
    #######################
    # Read in NFBC ADP data
    # https://nfc.shgn.com/adp/baseball
    #######################
    nfbc_df = pd.read_csv(
        "data/nfbc_adp.csv", usecols=["Player", "Position(s)", "Rank", "Team"]
    )
    nfbc_df.rename(columns={"Rank": "NFBC_ADP", "Player": "player_name"}, inplace=True)
    nfbc_df = nfbc_df[["player_name", "Position(s)", "Team", "NFBC_ADP"]]
    nfbc_df["player_name"] = nfbc_df["player_name"].apply(
        lambda x: " ".join(x.split(", ")[::-1])
    )
    nfbc_df = cleanup_juniors(nfbc_df, "player_name")
    df = df.merge(nfbc_df, on=["player_name", "team"], how="left")

    #############################
    # Read in baseball prospectus
    #############################
    bp_df = pd.read_csv("data/baseball_prospectus_model_portfolio.csv")[
        ["Player"]
    ].rename(columns={"Player": "player_name"}, inplace=True)
    bp_df["bp_expert_count"] = bp_df.groupby("player_name")["player_name"].transform(
        "count"
    )
    bp_df = bp_df.drop_duplicates(subset=["player_name"])
    bp_df = bp_df.sort_values(by="bp_expert_count", ascending=False)
    df = df.merge(bp_df, on="player_name", how="left")

    ###################################
    # Read in athletic (ESPN and Yahoo)
    # (bush doesnt need)
    #################################
    if league in ("yahoo", "espn"):
        athletic_df = pd.read_csv(f"data/athletic-{league}.csv")[
            ["Player", "Rank"]
        ].rename(columns={"Rank": "athletic", "Player": "player_name"}, inplace=True)
        df = df.merge(athletic_df, on="player_name", how="left")

    # Add col for filtering out
    df.insert(df.columns.get_loc("player_name") + 1, "is_drafted", "")

    return df


def fix_bush_league_players(avail_players):
    # fix team abbreviations
    fantrax_to_fangraphs = {
        "SF": "SFG",
        "TB": "TBR",
        "WSH": "WSN",
        "SD": "SDP",
        "KC": "KCR",
    }
    avail_players["team"] = avail_players["team"].apply(
        lambda x: fantrax_to_fangraphs[x] if x in fantrax_to_fangraphs else x
    )

    # Fix player names
    # Fix specific player names
    avail_players.loc[avail_players["player_name"] == "Luis Ortiz", "player_name"] = (
        "Luis L. Ortiz"
    )

    return avail_players


def determine_best_avail_players(projection_df, league):
    df = None
    # If bush league, start with the available players
    if league == "bush":
        avail_players = pd.read_csv("input_data/bush_league_avail_players.csv")[
            ["Player", "Team", "Status"]
        ]
        avail_players.rename(
            columns={"Player": "player_name", "Team": "team"}, inplace=True
        )
        avail_players = fix_bush_league_players(avail_players)

        df = projection_df.merge(avail_players, how="inner", on=["player_name", "team"])
    else:
        # For other leagues, start with all players
        df = projection_df

    df["best_projection"] = df[player_rater_systems].max(axis=1)
    df["avg_projection"] = df[player_rater_systems].mean(axis=1)
    df.sort_values(by="best_projection", ascending=False, inplace=True)

    # bring in eno rankings for pitchers
    # TODO: add team name
    eno_df = pd.read_csv("input_data/eno_rankings.csv")
    eno_df.rename(columns={"Player": "player_name", "Rank": "eno"}, inplace=True)
    df = df.merge(eno_df, how="left", on="player_name")

    # TODO: add team name
    closermonkey_df = pd.read_csv("input_data/closermonkey.csv")
    closermonkey_df.rename(
        columns={"Tier": "closermonkey tier", "Rank": "closermonkey rank"}, inplace=True
    )
    df = df.merge(closermonkey_df, on="player_name", how="left")

    # stuff+
    # https://www.fangraphs.com/leaders/major-league?pos=all&stats=pit&lg=all&type=36&season=2025&month=0&season1=2025&ind=0&pageitems=2000000000&qual=0
    stuffplus_df = pd.read_csv("input_data/stuffplus.csv")[
        ["Name", "Team", "Stuff+", "Location+", "Pitching+"]
    ]
    stuffplus_df.rename(columns={"Name": "player_name", "Team": "team"}, inplace=True)
    df = df.merge(stuffplus_df, on=["player_name", "team"], how="left")

    # last month stuff plus
    # https://www.fangraphs.com/leaders/major-league?pos=all&stats=pit&lg=all&type=36&season=2025&month=1000&season1=2025&ind=0&pageitems=2000000000&qual=0&startdate=2025-05-11&enddate=2025-11-01&team=0
    lastmonth_stuffplus_df = pd.read_csv("input_data/lastmonth_stuffplus.csv")[
        [
            "Name",
            "Team",
            "Stuff+",
            "Location+",
            "Pitching+",
        ]
    ]
    lastmonth_stuffplus_df.rename(
        columns={
            "Name": "player_name",
            "Team": "team",
            "Stuff+": "lastmonth_stuff+",
            "Location+": "lastmonth_location+",
            "Pitching+": "lastmonth_pitching+",
        },
        inplace=True,
    )
    df = df.merge(lastmonth_stuffplus_df, on=["player_name", "team"], how="left")

    # batting statcast stats
    # https://www.fangraphs.com/leaders/major-league?pos=all&stats=bat&lg=all&type=24&season=2025&season1=2025&ind=0&pageitems=2000000000&qual=0&month=0
    batting_statcast_df = pd.read_csv("input_data/statcast_batters.csv")[
        [
            "Name",
            "Team",
            "Events",
            "EV",
            "maxEV",
            "Barrel%",
            "HardHit%",
            "wOBA",
            "xwOBA",
        ]
    ]
    batting_statcast_df.rename(
        columns={"Name": "player_name", "Team": "team"}, inplace=True
    )
    df = df.merge(batting_statcast_df, on=["player_name", "team"], how="left")

    return df


"""
Things to update each week

- stuff+
- closermonkey
- bush_league available + roster

# TODO
- player_rater should be scoped to not full season once we get further
"""


def main():
    parser = argparse.ArgumentParser(
        description="Multi-purpose script that fetches player projections and helps evaluate keepers and free agent options"
    )
    parser.add_argument(
        "--sort", type=str, default="fangraphs", help="Sort by specified ranking source"
    )
    parser.add_argument(
        "--keepers",
        action="store_true",
        help="run determine_keepers()",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="add additional data to output CSV to help with drafting",
    )
    parser.add_argument(
        "--league",
        type=str,
        default="bush",
        help="Specify the league (default: bush)",
    )
    args = parser.parse_args()

    projection_df = get_projections_df()

    if args.keepers:
        determine_keepers(projection_df)
        return

    df = determine_best_avail_players(projection_df, args.league)

    if args.draft:
        df = draft_specific_augmentations(df, args.league)

    print("Best Available Players\n", df.head(50))
    current_date = datetime.now().strftime("%Y-%m-%d")
    df.to_csv(f"output/{current_date}_players_avail.csv", index=False)


if __name__ == "__main__":
    main()
