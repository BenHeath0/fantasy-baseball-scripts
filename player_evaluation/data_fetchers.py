"""Data fetching functions for fantasy baseball player evaluation"""

import pandas as pd
import requests
from .config import (
    ROS_PROJECTION_SYSTEMS,
    FANGRAPHS_LEADERBOARD_STATS_MAPPING,
    PROJECTION_SYSTEMS,
    LEAGUE_SETTINGS,
)
from .utils import normalize_name_column
from api.fangraphs import (
    get_fangraphs_leaderboard,
    get_auction_values,
    get_player_rater_values,
    get_fangraphs_projections,
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
    response = get_fangraphs_leaderboard(
        stats_type="pit",
        leaderboard_type="stuff+",
        fetch_last_month=fetch_last_month,
    )

    return format_fangraphs_leaderboard_data(response, "stuff+", fetch_last_month)


def fetch_statcast_batting_data(fetch_last_month=False):
    """Fetch Statcast batting data from Fangraphs"""
    response = get_fangraphs_leaderboard(
        stats_type="bat",
        leaderboard_type="statcast_batters",
        fetch_last_month=fetch_last_month,
    )

    return format_fangraphs_leaderboard_data(
        response, "statcast_batters", fetch_last_month
    )


def fetch_fangraphs_projections(projection_system, stats_type, stats=None):
    """Fetch Fangraphs projections from Fangraphs.

    Args:
        projection_system: Projection system name (e.g., "atc")
        stats_type: "bat" or "pit"
        stats: List of stat columns to keep. If None, returns all columns.
    """
    response = get_fangraphs_projections(projection_system, stats_type)
    df = pd.DataFrame(response)
    df.rename(columns={"PlayerName": "player_name", "Team": "team"}, inplace=True)
    normalize_name_column(df)
    if stats is not None:
        df = df[["player_name", "team"] + stats]
    return df


def get_auction_values_df(projection_system, league_settings):
    """Get auction values dataframes for a projection system.

    Returns (batters_df, pitchers_df) tuple.
    """
    batters = get_auction_values(projection_system, "bat", league_settings)
    pitchers = get_auction_values(projection_system, "pit", league_settings)

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

    batters_df = pd.DataFrame(batters_data)
    pitchers_df = pd.DataFrame(pitchers_data)
    normalize_name_column(batters_df)
    normalize_name_column(pitchers_df)

    return batters_df, pitchers_df


def get_player_rater_df(projection_system):
    """Get player rater dataframe for a projection system"""
    response = get_player_rater_values(projection_system)
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


# ATC projection stats to keep from projections API
ATC_HITTER_PROJECTION_STATS = ["PA", "HR", "R", "RBI", "SB", "AVG", "OBP", "SLG"]
ATC_PITCHER_PROJECTION_STATS = ["IP", "W", "SV", "SO", "ERA", "WHIP"]


def get_or_fetch_fangraphs_data(
    fetch_fresh=True, use_ros_projections=False, league="bush"
):
    """Get Fangraphs data from cache or fetch if needed.

    Returns (hitters_df, pitchers_df) tuple.
    """
    from .config import HITTERS_CACHE_FILE, PITCHERS_CACHE_FILE

    league_settings = LEAGUE_SETTINGS[league]
    hitters_cache = HITTERS_CACHE_FILE.format(league=league)
    pitchers_cache = PITCHERS_CACHE_FILE.format(league=league)

    # Check if we need to fetch new data
    fetch_needed = fetch_fresh

    if not fetch_needed:
        try:
            hitters_df = pd.read_csv(hitters_cache)
            pitchers_df = pd.read_csv(pitchers_cache)
            print("Using cached projection data")
            return hitters_df, pitchers_df
        except FileNotFoundError:
            print("Cache file not found, fetching new data")
            fetch_needed = True

    if fetch_needed:
        print("Fetching new projection data...")
        merged_hitters = None
        merged_pitchers = None

        projection_systems = (
            ROS_PROJECTION_SYSTEMS if use_ros_projections else PROJECTION_SYSTEMS
        )

        # 1. Auction values
        for system in projection_systems:
            batters_df, pitchers_df = get_auction_values_df(system, league_settings)
            if merged_hitters is None:
                merged_hitters = batters_df
                merged_pitchers = pitchers_df
            else:
                merged_hitters = merged_hitters.merge(
                    batters_df, how="left", on=["player_name", "team", "position"]
                )
                merged_pitchers = merged_pitchers.merge(
                    pitchers_df, how="left", on=["player_name", "team", "position"]
                )

        # use player rater to get last30 data (may not be available in offseason)
        try:
            # 2. Player rater
            last30_df = get_player_rater_df("last30")
            merged_hitters = merged_hitters.merge(
                last30_df, how="left", on=["player_name", "team", "position"]
            )
            merged_pitchers = merged_pitchers.merge(
                last30_df, how="left", on=["player_name", "team", "position"]
            )
        except requests.exceptions.HTTPError as e:
            print(f"Warning: Could not fetch last30 data (likely offseason): {e}")

        # 3. ATC Projections
        atc_hitters_df = fetch_fangraphs_projections(
            "atc", "bat", ATC_HITTER_PROJECTION_STATS
        )
        merged_hitters = merged_hitters.merge(
            atc_hitters_df, how="left", on=["player_name", "team"]
        )

        atc_pitchers_df = fetch_fangraphs_projections(
            "atc", "pit", ATC_PITCHER_PROJECTION_STATS
        )
        merged_pitchers = merged_pitchers.merge(
            atc_pitchers_df, how="left", on=["player_name", "team"]
        )

        # Save to cache
        merged_hitters.to_csv(hitters_cache, index=False)
        merged_pitchers.to_csv(pitchers_cache, index=False)

        return merged_hitters, merged_pitchers
