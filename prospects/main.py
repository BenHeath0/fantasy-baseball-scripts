import argparse
import pandas as pd
import os

CURRENT_SEASON = 2026
INPUT_DATA_DIR = "input_data"
RANKING_SOURCES = [
    "mlb_pipeline",
    "fangraphs",
    "baseball_prospectus",
    "athletic",
    "espn",
    "just_baseball",
]
RANKING_COLUMNS_FOR_AVG = [
    "baseball_prospectus",
    "espn",
    "athletic",
    "mlb_pipeline",
]


def get_prospect_ratings(year: int = CURRENT_SEASON):
    # Init df with mlb_pipeline as base
    df = pd.read_csv(f"{INPUT_DATA_DIR}/{year}/mlb_pipeline.csv")[
        ["Name", "Pos", "ETA", "Team"]
    ]

    for source in RANKING_SOURCES:
        filepath = f"{INPUT_DATA_DIR}/{year}/{source}.csv"
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            continue
        prospect_data = pd.read_csv(filepath)[["Name", "Rank"]].rename(
            columns={"Rank": source}
        )
        df = df.merge(
            prospect_data,
            on="Name",
            how="left",
        )
    fantrax_data = pd.read_csv(f"{INPUT_DATA_DIR}/{year}/bush_league_taken_players.csv")

    # Note if player is taken
    fantrax_player_names = set(fantrax_data["Player"])
    df["taken"] = df["Name"].apply(
        lambda name: "X" if name in fantrax_player_names else None
    )

    return df


def cleanup_data(df):
    # Reorder columns to move "taken" next to "Name"
    df = df[
        ["Name", "taken", "Team", "Pos", "ETA"]
        + [
            col
            for col in df.columns
            if col not in ["Name", "taken", "Team", "Pos", "ETA"]
        ]
    ].copy()

    # Calculate 'avg' column as the average of specified rankings
    df["avg"] = df[RANKING_COLUMNS_FOR_AVG].apply(
        lambda row: row.dropna().mean() if not row.dropna().empty else None, axis=1
    )

    # Calculate 'top_projection' column as the minimum value out of ranking columns
    df["top_projection"] = df[RANKING_COLUMNS_FOR_AVG].apply(
        lambda row: row.min() if not row.dropna().empty else None, axis=1
    )

    # Calculate 'num_places_ranked' column as the number of non-null values in ranking columns
    df["num_places_ranked"] = df[RANKING_COLUMNS_FOR_AVG].count(axis=1)
    # Drop rows where 'num_places_ranked' is 0
    df = df[df["num_places_ranked"] > 0]

    # Convert ETA from float to int
    df["ETA"] = df["ETA"].fillna(0).astype(int)
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
