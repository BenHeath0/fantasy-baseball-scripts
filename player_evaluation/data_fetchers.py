"""Data fetching functions for fantasy baseball player evaluation"""

import pandas as pd
import requests
from .config import (
    ROS_PROJECTION_SYSTEMS,
    FANGRAPHS_LEADERBOARD_STATS_MAPPING,
    PROJECTION_SYSTEMS,
)
from .utils import determine_fetch_needed, update_last_fetched, normalize_name_column
from api.fangraphs import (
    fetch_fangraphs_leaderboard,
    fetch_auction_values,
    fetch_player_rater_values,
)


def format_fangraphs_leaderboard_data(
    data: dict, leaderboard_type: str, fetch_last_month: bool = False
) -> pd.DataFrame:
    """Format Fangraphs leaderboard data"""
    # handle no data (unstable API)
    if not data:
        print(f"Warning: No {leaderboard_type} data available")
        return None

    df = pd.DataFrame(data["data"])
    required_cols = [
        "PlayerName",
        "TeamName",
    ] + FANGRAPHS_LEADERBOARD_STATS_MAPPING[leaderboard_type]

    missing_cols = [col for col in required_cols if col not in df.columns]
    # Sometimes we're missing data. log it.
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols} in {leaderboard_type} data")
        return None

    # keep only required columns
    df = df[required_cols]
    # Rename columns
    if leaderboard_type == "stuff+":
        df.rename(
            columns={
                "PlayerName": "player_name",
                "TeamName": "team",
                "sp_stuff": "lastmonth_stuff+" if fetch_last_month else "Stuff+",
                "sp_location": "lastmonth_location+"
                if fetch_last_month
                else "Location+",
                "sp_pitching": "lastmonth_pitching+"
                if fetch_last_month
                else "Pitching+",
            },
            inplace=True,
        )
    elif leaderboard_type == "statcast_batters":
        df.rename(
            columns={
                "PlayerName": "player_name",
                "TeamName": "team",
            },
            inplace=True,
        )
    normalize_name_column(df)
    return df


def fetch_stuff_plus_data(fetch_last_month=False):
    """Fetch Stuff+ data from Fangraphs"""
    response = fetch_fangraphs_leaderboard(
        stats_type="pit",
        leaderboard_type="stuff+",
        fetch_last_month=fetch_last_month,
    )

    return format_fangraphs_leaderboard_data(response, "stuff+", fetch_last_month)


def fetch_statcast_batting_data(fetch_last_month=False):
    """Fetch Statcast batting data from Fangraphs"""
    response = fetch_fangraphs_leaderboard(
        stats_type="bat",
        leaderboard_type="statcast_batters",
        fetch_last_month=fetch_last_month,
    )

    return format_fangraphs_leaderboard_data(
        response, "statcast_batters", fetch_last_month
    )


def get_auction_values_df(projection_system):
    """Get auction values dataframe for a projection system"""
    batters = fetch_auction_values(projection_system, "bat")
    pitchers = fetch_auction_values(projection_system, "pit")

    batters_data = [
        {
            "player_name": player["PlayerName"],
            "team": player["Team"],
            "position": player["POS"],
            projection_system: player["Dollars"],
        }
        for player in batters["data"]
    ]

    pitchers_data = [
        {
            "player_name": player["PlayerName"],
            "team": player["Team"],
            "position": player["POS"],
            projection_system: player["Dollars"],
        }
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
    normalize_name_column(combined_df)

    return combined_df


def get_player_rater_df(projection_system):
    """Get player rater dataframe for a projection system"""
    response = fetch_player_rater_values(projection_system)
    player_data = [
        {
            "player_name": player["playerName"],
            "team": player["auction"]["AbbName"],
            "position": player["auction"]["Position"],
            projection_system: player["auction"]["Dollars"],
        }
        for player in response["data"]
    ]

    player_rater_df = pd.DataFrame(player_data)
    normalize_name_column(player_rater_df)
    return player_rater_df


def get_or_fetch_fangraphs_data(fetch_fresh=False, use_ros_projections=False):
    """Get Fangraphs data from cache or fetch if needed"""
    from .config import CACHE_FILE

    # Check if we need to fetch new data
    fetch_needed = determine_fetch_needed() or fetch_fresh

    if not fetch_needed:
        try:
            df = pd.read_csv(CACHE_FILE)
            print("Using cached projection data")
            return df
        except FileNotFoundError:
            print("Cache file not found, fetching new data")
            fetch_needed = True

    if fetch_needed:
        print("Fetching new projection data...")
        merged_df = None

        projection_systems = (
            ROS_PROJECTION_SYSTEMS if use_ros_projections else PROJECTION_SYSTEMS
        )
        for system in projection_systems:
            df = get_auction_values_df(system)
            if merged_df is None:
                merged_df = df
            else:
                merged_df = merged_df.merge(
                    df, how="left", on=["player_name", "team", "position"]
                )
        # use player rater to get last30 data (may not be available in offseason)
        try:
            last30_df = get_player_rater_df("last30")
            merged_df = merged_df.merge(
                last30_df, how="left", on=["player_name", "team", "position"]
            )
        except requests.exceptions.HTTPError as e:
            print(f"Warning: Could not fetch last30 data (likely offseason): {e}")

        # Save to cache
        merged_df.to_csv(CACHE_FILE, index=False)
        update_last_fetched()

        return merged_df
