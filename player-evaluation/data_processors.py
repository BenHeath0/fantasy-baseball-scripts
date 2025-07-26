"""Data processing functions for fantasy baseball player evaluation"""

import pandas as pd
from config import FANTRAX_TO_FANGRAPHS_TEAMS, ROS_PROJECTION_SYSTEMS, INPUT_DATA_DIR
from data_fetchers import (
    load_local_csv_data,
    fetch_stuff_plus_data,
    fetch_statcast_batting_data,
)
from utils import cleanup_juniors


def fix_bush_league_players(avail_players):
    """Fix team abbreviations and player names for Bush League format"""
    # Fix team abbreviations
    avail_players["team"] = avail_players["team"].apply(
        lambda x: FANTRAX_TO_FANGRAPHS_TEAMS.get(x, x)
    )

    # Fix specific player names
    avail_players.loc[avail_players["player_name"] == "Luis Ortiz", "player_name"] = (
        "Luis L. Ortiz"
    )

    return avail_players


def add_nfbc_data(df):
    """Add NFBC ADP data to the dataframe"""
    nfbc_df = load_local_csv_data("nfbc_adp.csv")
    if nfbc_df is None:
        return df

    try:
        # Process NFBC data
        required_columns = ["Player", "Position(s)", "Rank", "Team"]
        available_columns = [col for col in required_columns if col in nfbc_df.columns]

        if len(available_columns) != len(required_columns):
            print(f"Warning: NFBC data missing columns. Available: {available_columns}")
            return df

        nfbc_df = nfbc_df[required_columns].copy()
        nfbc_df.rename(
            columns={"Rank": "NFBC_ADP", "Player": "player_name", "Team": "team"},
            inplace=True,
        )
        nfbc_df = nfbc_df[["player_name", "Position(s)", "team", "NFBC_ADP"]]
        nfbc_df["player_name"] = nfbc_df["player_name"].apply(
            lambda x: " ".join(x.split(", ")[::-1])
        )
        nfbc_df = cleanup_juniors(nfbc_df, "player_name")

        # Merge with main dataframe
        df = df.merge(nfbc_df, on=["player_name", "team"], how="left")
        return df
    except Exception as e:
        print(f"Error processing NFBC data: {e}")
        return df


def add_baseball_prospectus_data(df):
    """Add Baseball Prospectus expert rankings data"""
    bp_df = load_local_csv_data("baseball_prospectus_model_portfolio.csv")
    if bp_df is None:
        return df

    bp_df = bp_df[["Player"]].copy()
    bp_df.rename(columns={"Player": "player_name"}, inplace=True)
    bp_df["bp_expert_count"] = bp_df.groupby("player_name")["player_name"].transform(
        "count"
    )
    bp_df = bp_df.drop_duplicates(subset=["player_name"])
    bp_df = bp_df.sort_values(by="bp_expert_count", ascending=False)

    df = df.merge(bp_df, on="player_name", how="left")
    return df


def add_athletic_rankings(df, league):
    """Add Athletic rankings for ESPN and Yahoo leagues"""
    if league not in ("yahoo", "espn"):
        return df

    athletic_df = load_local_csv_data(f"athletic-{league}.csv")
    if athletic_df is None:
        return df

    athletic_df = athletic_df[["Player", "Rank"]].copy()
    athletic_df.rename(
        columns={"Rank": "athletic", "Player": "player_name"}, inplace=True
    )

    df = df.merge(athletic_df, on="player_name", how="left")
    return df


def add_eno_rankings(df):
    """Add Eno pitcher rankings"""
    eno_df = load_local_csv_data("eno_rankings.csv")
    if eno_df is None:
        return df

    eno_df.rename(columns={"Player": "player_name", "Rank": "eno"}, inplace=True)
    df = df.merge(eno_df, how="left", on="player_name")
    return df


def add_closermonkey_data(df):
    """Add CloserMonkey reliever rankings"""
    closermonkey_df = load_local_csv_data("closermonkey.csv")
    if closermonkey_df is None:
        return df

    closermonkey_df.rename(
        columns={"Tier": "closermonkey tier", "Rank": "closermonkey rank"}, inplace=True
    )
    df = df.merge(closermonkey_df, on="player_name", how="left")
    return df


def add_stuff_plus_data(df, fetch_fresh=True, fetch_last_month=False):
    """Add Stuff+ data from Fangraphs"""
    if fetch_fresh:
        print("Fetching fresh Stuff+ data from Fangraphs...")
        stuffplus_df = fetch_stuff_plus_data(fetch_last_month=fetch_last_month)
        if stuffplus_df is not None:
            # Save to local file for backup
            stuffplus_df.to_csv(
                f"{INPUT_DATA_DIR}/{'lastmonth_' if fetch_last_month else ''}stuffplus.csv",
                index=False,
            )
        else:
            # Fall back to local file
            stuffplus_df = load_local_csv_data("stuffplus.csv")
    else:
        stuffplus_df = load_local_csv_data("stuffplus.csv")

    if stuffplus_df is None:
        return df

    df = df.merge(stuffplus_df, on=["player_name", "team"], how="left")

    return df


def add_statcast_batting_data(df, fetch_fresh=True):
    """Add Statcast batting data"""
    if fetch_fresh:
        print("Fetching fresh Statcast batting data from Fangraphs...")
        batting_statcast_df = fetch_statcast_batting_data()
        if batting_statcast_df is not None:
            batting_statcast_df.to_csv(
                f"{INPUT_DATA_DIR}/statcast_batters.csv", index=False
            )
        else:
            batting_statcast_df = load_local_csv_data("statcast_batters.csv")
    else:
        batting_statcast_df = load_local_csv_data("statcast_batters.csv")

    if batting_statcast_df is None:
        return df

    df = df.merge(batting_statcast_df, on=["player_name", "team"], how="left")

    return df


def filter_available_players(projection_df, league):
    """Filter players based on league availability"""
    if league == "bush":
        # Load Bush League available players
        avail_players = load_local_csv_data("bush_league_avail_players.csv")
        if avail_players is None:
            print("Warning: Bush League available players file not found")
            return projection_df

        avail_players = avail_players[["Player", "Team", "Status"]].copy()
        avail_players.rename(
            columns={"Player": "player_name", "Team": "team"}, inplace=True
        )
        avail_players = fix_bush_league_players(avail_players)

        # Filter to only available players
        df = projection_df.merge(avail_players, how="inner", on=["player_name", "team"])
    else:
        # For other leagues, start with all players
        df = projection_df.copy()

    return df


def calculate_projection_metrics(df):
    """Add projection metrics like best and average projections"""
    df["best_projection"] = df[ROS_PROJECTION_SYSTEMS].max(axis=1)
    df["avg_projection"] = df[ROS_PROJECTION_SYSTEMS].mean(axis=1)
    return df


def add_data_augmentations(df, league, fetch_fresh=True):
    """Add all data augmentations"""
    df = add_athletic_rankings(df, league)
    df = add_eno_rankings(df)
    df = add_closermonkey_data(df)
    df = add_stuff_plus_data(df, fetch_fresh)
    df = add_stuff_plus_data(df, fetch_fresh, fetch_last_month=True)
    df = add_statcast_batting_data(df, fetch_fresh)
    return df


def add_draft_augmentations(df):
    """Add all draft-specific data augmentations"""
    print("Adding draft-specific data...")
    # Add a column for manual tracking
    df.insert(df.columns.get_loc("player_name") + 1, "is_drafted", "")
    df = add_nfbc_data(df)
    df = add_baseball_prospectus_data(df)
    return df
