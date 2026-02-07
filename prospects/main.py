import argparse
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from player_evaluation.utils import normalize_player_name

CURRENT_SEASON = 2026
INPUT_DATA_DIR = "input_data"
RANKING_COLUMNS = [
    "Baseball Prospectus",
    "ESPN",
    "MLB Pipeline",
    "The Athletic",
    "TJStats",
]


def get_prospect_ratings(year: int = CURRENT_SEASON):
    composite_cols = [
        "Name",
        "Team",
        "Pos",
        "Age",
        "Draft",
        "Highest Level",
    ] + RANKING_COLUMNS
    # https://docs.google.com/spreadsheets/d/1NbEynvII4J0fKwBd6AX1-nMvfp-QxB46OkTaRxQDlQQ/edit?gid=0#gid=0
    df = pd.read_csv(f"{INPUT_DATA_DIR}/{year}/composite.csv")[composite_cols]

    # Convert "Last, First" to "First Last"
    df["Name"] = df["Name"].apply(
        lambda n: (
            f"{n.split(',')[1].strip()} {n.split(',')[0].strip()}"
            if isinstance(n, str) and "," in n
            else n
        )
    )
    df["Name"] = df["Name"].apply(normalize_player_name)

    # Replace 150 values with None (150 indicates unranked/missing data)
    df = df.replace(150, None)

    fantrax_data = pd.read_csv(f"{INPUT_DATA_DIR}/{year}/bush_league_taken_players.csv")
    fantrax_data["Player"] = fantrax_data["Player"].apply(normalize_player_name)

    # Note if player is taken
    fantrax_player_names = set(fantrax_data["Player"])
    df["taken"] = df["Name"].apply(
        lambda name: "X" if name in fantrax_player_names else None
    )

    return df


def cleanup_data(df):
    info_cols = ["Name", "taken", "Team", "Pos", "Age", "Draft", "Highest Level"]
    # Reorder columns to move "taken" next to "Name"
    df = df[info_cols + [col for col in df.columns if col not in info_cols]].copy()

    # Calculate 'avg' column as the average of specified rankings
    df["avg"] = df[RANKING_COLUMNS].apply(
        lambda row: row.dropna().mean() if not row.dropna().empty else None, axis=1
    )

    # Calculate 'top_projection' column as the minimum value out of ranking columns
    df["top_projection"] = df[RANKING_COLUMNS].apply(
        lambda row: row.min() if not row.dropna().empty else None, axis=1
    )

    # Calculate 'num_places_ranked' column as the number of non-null values in ranking columns
    df["num_places_ranked"] = df[RANKING_COLUMNS].count(axis=1)
    # Drop rows where 'num_places_ranked' is 0
    df = df[df["num_places_ranked"] > 0]

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Merges prospect rankings from various sources and outputs a CSV. Filter out players that are already taken."
    )
    parser.add_argument(
        "--sort", type=str, default="avg", help="Sort by specified ranking source"
    )
    args = parser.parse_args()

    df = get_prospect_ratings()
    df = cleanup_data(df)

    df = df.sort_values(by=args.sort)
    print(df.head(30))

    df.to_csv("prospects.csv", index=False)


if __name__ == "__main__":
    main()
