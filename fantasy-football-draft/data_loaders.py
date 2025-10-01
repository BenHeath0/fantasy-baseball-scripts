import pandas as pd


# Clean player names by removing suffixes like Jr., Sr., III, etc.
def transform_nffc_name(name):
    """Transform name from 'Last, First' to 'First Last' format."""
    if pd.isna(name):
        return name

    if "," in name:
        last, first = name.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    return name


def clean_player_name(name):
    """Remove common name suffixes like Jr., Sr., III, etc."""
    if pd.isna(name):
        return name

    # Common suffixes to remove
    suffixes = [" Jr.", " Sr.", " III", " II", " IV", " V"]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)]

    return name.strip()


def load_fantasypros_data(league, is_top_10=False):
    """Load the fantasypros data for the given league"""
    filename = None

    if league == "fnf":
        filename = f"input_data/fantasypros_ppr{'_top10' if is_top_10 else ''}.csv"
    else:
        filename = f"input_data/fantasypros_{league}{'_top10' if is_top_10 else ''}.csv"

    df = pd.read_csv(filename)
    df = df[["PLAYER NAME", "POS", "TIERS", "RK"]]
    df = df.rename(
        columns={
            "RK": f"fantasypros_rk{'_top10' if is_top_10 else ''}",
            "TIERS": f"fantasypros_tier{'_top10' if is_top_10 else ''}",
            "PLAYER NAME": "name",
            "POS": f"fantasypros_pos_rank{'_top10' if is_top_10 else ''}",
        }
    )

    # Apply name cleaning to the dataframe
    df["name"] = df["name"].apply(clean_player_name)
    # Convert name column to lowercase
    df["name"] = df["name"].str.lower()

    return df


def load_athletic_data(league):
    df = pd.read_csv(f"input_data/athletic_{league}.tsv", sep="\t")
    df = df[["RK", "OVERALL PLAYER", "POS RK", "VORP"]]
    df = df.rename(
        columns={
            "RK": "athletic_rk",
            "OVERALL PLAYER": "name",
            "POS RK": "athletic_pos_rank",
        }
    )
    # Convert name column to lowercase
    df["name"] = df["name"].str.lower()

    return df


def load_nffc_data():
    df = pd.read_csv("input_data/nffc_adp.tsv", sep="\t")
    df = df[["Player", "ADP"]]
    # Transform player names from "Last, First" to "First Last"
    df["Player"] = df["Player"].apply(transform_nffc_name)
    df = df.rename(
        columns={
            "Player": "name",
            "ADP": "nffc_adp",
        }
    )
    # Convert name column to lowercase
    df["name"] = df["name"].str.lower()

    # also grab primetime adp
    primetime_df = pd.read_csv("input_data/nffc_primetime_adp.tsv", sep="\t")
    primetime_df = primetime_df[["Player", "ADP"]]
    primetime_df["Player"] = primetime_df["Player"].apply(transform_nffc_name)
    primetime_df = primetime_df.rename(
        columns={
            "Player": "name",
            "ADP": "primetime_adp",
        }
    )
    primetime_df["name"] = primetime_df["name"].str.lower()
    df = df.merge(primetime_df, on="name", how="left")

    return df


def load_player_notes():
    df = pd.read_csv("input_data/player_notes.csv")
    df = df.dropna(subset=["Note"])
    # Convert name column to lowercase
    df["name"] = df["name"].str.lower()
    return df
