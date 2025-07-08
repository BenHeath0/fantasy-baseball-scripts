"""Data fetching functions for fantasy baseball player evaluation"""

from datetime import datetime, timedelta
import pandas as pd
import requests
from config import (
    FANGRAPHS_URLS,
    LEAGUE_SETTINGS,
    PLAYER_RATER_SYSTEMS,
    INPUT_DATA_DIR,
    FANGRAPHS_LEADERBOARD_TYPE_MAPPING,
    FANGRAPHS_LEADERBOARD_STATS_MAPPING,
)
from utils import determine_fetch_needed, update_last_fetched


def fetch_auction_values(projection_system, player_type):
    """Fetch auction values from Fangraphs API"""
    print(f"Fetching auction values for {projection_system} {player_type}...")

    params = {
        **LEAGUE_SETTINGS,
        "lg": "MLB",
        "type": player_type,
        "players": "",
        "proj": projection_system,
        "split": "",
        "sort": "",
        "view": 0,
    }

    response = requests.get(FANGRAPHS_URLS["auction_calculator"], params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def fetch_player_rater_values(projection_system):
    """Fetch player rater values from Fangraphs API"""
    print(f"Fetching player rater values for {projection_system}...")

    params = {
        "timeframetype": projection_system,
        "leaguetype": 3,
        "pos": None,
        "postype": None,
        "season": 2025,
    }

    response = requests.get(FANGRAPHS_URLS["player_rater"], params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def fetch_fangraphs_leaderboard(
    stats_type,
    season=2025,
    additional_params=None,
    leaderboard_type="stuff+",
    fetch_last_month=False,
):
    """
    Fetch data from Fangraphs leaderboard

    Args:
        stats_type: Type of stats (e.g., 'pit' for pitching, 'bat' for batting)
        season: Season year
        month: Month filter (0 for full season, 1000 for custom date range)
        additional_params: Dictionary of additional parameters
    """
    params = {
        "pos": "all",
        "stats": stats_type,
        "lg": "all",
        "season": season,
        "season1": season,
        "ind": 0,
        "qual": 0,
        "month": 1000 if fetch_last_month else 0,
        "team": 0,
        "type": FANGRAPHS_LEADERBOARD_TYPE_MAPPING[
            leaderboard_type
        ],  # Standard stats by default
        "pageitems": 2000000000,  # Large number to get all results
        "startdate": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if fetch_last_month
        else None,
        "enddate": datetime.now().strftime("%Y-%m-%d") if fetch_last_month else None,
    }

    if additional_params:
        params.update(additional_params)

    # Build the URL with export parameter to get CSV
    params["type"] = "csv"

    response = requests.get(FANGRAPHS_URLS["leaders"], params=params)
    if response.status_code == 200:
        json = response.json()["data"]
        df = pd.DataFrame(json)
        df = df[
            ["PlayerName", "TeamName"]
            + FANGRAPHS_LEADERBOARD_STATS_MAPPING[leaderboard_type]
        ]

        print("data_fetchers.py:109", df.head(), df.columns)

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
        return df
    else:
        response.raise_for_status()


def fetch_stuff_plus_data(fetch_last_month=False):
    """Fetch Stuff+ data from Fangraphs"""
    return fetch_fangraphs_leaderboard(
        stats_type="pit",
        leaderboard_type="stuff+",
        fetch_last_month=fetch_last_month,
    )


def fetch_statcast_batting_data(fetch_last_month=False):
    """Fetch Statcast batting data from Fangraphs"""
    return fetch_fangraphs_leaderboard(
        stats_type="bat",
        leaderboard_type="statcast_batters",
        fetch_last_month=fetch_last_month,
    )


def get_auction_values_df(projection_system):
    """Get auction values dataframe for a projection system"""
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
    return player_rater_df


def load_local_csv_data(filename):
    """Load CSV data from input_data directory with error handling"""
    filepath = f"{INPUT_DATA_DIR}/{filename}"
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. This data will be skipped.")
        return None
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def get_or_fetch_fangraphs_data():
    """Get Fangraphs data from cache or fetch if needed"""
    from config import CACHE_FILE

    # Check if we need to fetch new data
    fetch_needed = determine_fetch_needed()

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

        for system in PLAYER_RATER_SYSTEMS:
            df = get_player_rater_df(system)
            if merged_df is None:
                merged_df = df
            else:
                merged_df = merged_df.merge(
                    df, how="left", on=["player_name", "team", "position"]
                )

        # Save to cache
        merged_df.to_csv(CACHE_FILE, index=False)
        update_last_fetched()

        return merged_df
