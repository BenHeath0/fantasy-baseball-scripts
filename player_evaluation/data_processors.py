"""Data processing functions for fantasy baseball player evaluation"""

from .config import (
    TEAM_ABBREV_TO_FANGRAPHS,
    INPUT_DATA_DIR,
    PROJECTION_SYSTEMS,
)
from .data_fetchers import (
    fetch_stuff_plus_data,
    fetch_statcast_batting_data,
)
from .utils import normalize_name_column, load_local_csv_data


def fix_team_abbreviations(avail_players):
    """Fix team abbreviations for Bush League format"""
    avail_players["team"] = avail_players["team"].apply(
        lambda x: TEAM_ABBREV_TO_FANGRAPHS.get(x, x)
    )
    return avail_players


def add_nfbc_data(df):
    """Add NFBC ADP data to the dataframe"""
    nfbc_df = load_local_csv_data("nfbc_adp.tsv")
    if nfbc_df is None:
        return df

    try:
        # Process NFBC data
        required_columns = ["Player", "Team", "Rank"]
        available_columns = [col for col in required_columns if col in nfbc_df.columns]

        if len(available_columns) != len(required_columns):
            print(f"Warning: NFBC data missing columns. Available: {available_columns}")
            return df

        nfbc_df = nfbc_df[required_columns].copy()
        nfbc_df.rename(
            columns={"Rank": "NFBC_ADP", "Player": "player_name", "Team": "team"},
            inplace=True,
        )
        nfbc_df = nfbc_df[["player_name", "team", "NFBC_ADP"]]
        nfbc_df["player_name"] = nfbc_df["player_name"].apply(
            lambda x: " ".join(x.split(", ")[::-1])
        )
        print(nfbc_df["player_name"].head(10))
        normalize_name_column(nfbc_df)

        nfbc_df = fix_team_abbreviations(nfbc_df)

        print(nfbc_df["player_name"].head(10))

        # Merge with main dataframe
        df = df.merge(nfbc_df, on=["player_name", "team"], how="left")
        # Reorder columns to put NFBC_ADP right after atc
        if "NFBC_ADP" in df.columns and "atc" in df.columns:
            cols = df.columns.tolist()
            cols.remove("NFBC_ADP")
            atc_idx = cols.index("atc")
            cols.insert(atc_idx + 1, "NFBC_ADP")
            df = df[cols]
        return df
    except Exception as e:
        print(f"Error processing NFBC data: {e}")
        return df


def add_eno_rankings(df):
    """Add Eno pitcher rankings"""
    eno_df = load_local_csv_data("eno_rankings.csv")
    if eno_df is None:
        return df

    eno_df.rename(columns={"Player": "player_name", "Rank": "eno"}, inplace=True)
    normalize_name_column(eno_df)
    eno_df = eno_df[["player_name", "eno"]]
    df = df.merge(eno_df, how="left", on="player_name")
    return df


def add_closermonkey_data(df):
    """Add CloserMonkey reliever rankings (saves, holds, and combined)"""
    files = {
        "closermonkey.tsv": "closermonkey rank",
        "closermonkey_solds.tsv": "closermonkey solds rank",
        "closermonkey_holds.tsv": "closermonkey holds rank",
    }
    for filename, col_name in files.items():
        cm_df = load_local_csv_data(filename)
        if cm_df is None:
            continue
        cm_df.rename(columns={"Rank": col_name}, inplace=True)
        normalize_name_column(cm_df)
        df = df.merge(cm_df, on="player_name", how="left")
    return df


def add_stuff_plus_data(df, use_cache=False, fetch_last_month=False):
    """Add Stuff+ data from Fangraphs"""
    filename = f"{'lastmonth_' if fetch_last_month else ''}stuffplus.csv"
    if not use_cache:
        print("Fetching fresh Stuff+ data from Fangraphs...")
        stuffplus_df = fetch_stuff_plus_data(fetch_last_month=fetch_last_month)
        if stuffplus_df is not None:
            # Save to local file for backup
            stuffplus_df.to_csv(f"{INPUT_DATA_DIR}/{filename}", index=False)
        else:
            # Fall back to local file
            stuffplus_df = load_local_csv_data(filename)
    else:
        stuffplus_df = load_local_csv_data(filename)

    if stuffplus_df is None:
        return df

    df = df.merge(stuffplus_df, on=["player_name", "team"], how="left")

    return df


def add_statcast_batting_data(df, use_cache=False):
    """Add Statcast batting data"""
    if not use_cache:
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


def add_fantasy_team(projection_df):
    """Add fantasy_team column showing which Bush League team owns each player"""
    bush_league = load_local_csv_data("rosters/bush_league_players.csv")
    if bush_league is None:
        print("Warning: Bush League players file not found")
        return projection_df

    bush_league = bush_league[["Player", "Team", "Status"]].copy()
    bush_league.rename(
        columns={"Player": "player_name", "Team": "team", "Status": "fantasy_team"},
        inplace=True,
    )
    bush_league = fix_team_abbreviations(bush_league)
    normalize_name_column(bush_league)

    df = projection_df.merge(bush_league, how="left", on=["player_name", "team"])

    # Place fantasy_team between position and the first projection column
    cols = df.columns.tolist()
    cols.remove("fantasy_team")
    pos_idx = cols.index("position") + 1
    cols.insert(pos_idx, "fantasy_team")
    df = df[cols]

    return df


def add_pitcher_supplemental_data(df, use_cache=False):
    """Add pitcher-specific data augmentations"""
    df = add_eno_rankings(df)
    df = add_closermonkey_data(df)
    df = add_stuff_plus_data(df, use_cache)
    df = add_stuff_plus_data(df, use_cache, fetch_last_month=True)
    return df


def add_hitter_supplemental_data(df, use_cache=False):
    """Add hitter-specific data augmentations"""
    df = add_statcast_batting_data(df, use_cache)
    return df
