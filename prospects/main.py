import csv
import argparse
import pandas as pd


# https://docs.google.com/spreadsheets/d/1vNB0IZe_PZwaNF6MA5LRsYzHMvlySQ1sK6_mHBAVAJM/edit?gid=0#gid=0
def clean_composite_csv(input_file, output_file):
    with open(input_file, mode="r") as infile, open(
        output_file, mode="w", newline=""
    ) as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ["Name", "Team", "Pos"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        row_count = 0
        for row in reader:
            last_first = row["PlayerName"]
            first_last = " ".join(last_first.split(", ")[::-1])
            writer.writerow(
                {
                    "Name": first_last,
                    "Team": row["Team"],
                    "Pos": row["Pos"],
                }
            )
            row_count += 1
            if row_count == 200:
                break


def get_prospect_ratings(year: int = 2025):
    # Init df with composite data
    df = pd.read_csv(f"input_data/{year}/composite_cleaned.csv")

    filenames = [
        {"filename": f"input_data/{year}/mlb_pipeline.csv", "extra_fields": []},
        {"filename": f"input_data/{year}/baseball_prospectus.csv", "extra_fields": []},
        {"filename": f"input_data/{year}/fangraphs.csv", "extra_fields": ["ETA"]},
        {"filename": f"input_data/{year}/athletic.csv", "extra_fields": []},
        {"filename": f"input_data/{year}/espn.csv", "extra_fields": []},
        {"filename": f"input_data/{year}/just_baseball.csv", "extra_fields": []},
    ]

    for filename in filenames:
        source = filename["filename"].split("/")[-1].split(".")[0]
        cols = ["Name", "Rank"] + filename["extra_fields"]
        prospect_data = pd.read_csv(filename["filename"])[cols].rename(
            columns={"Rank": source}
        )
        df = df.merge(
            prospect_data,
            on="Name",
            how="left",
        )
    fantrax_data = pd.read_csv(f"input_data/{year}/bush_league_taken_players.csv")

    # Note if player is taken
    fantrax_player_names = set(fantrax_data["Player"])
    df["taken"] = df["Name"].apply(
        lambda name: "X"
        if name in fantrax_player_names or name in just_drafted_players
        else None
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
    ]

    # Calculate 'my_avg' column as the average of specified rankings
    ranking_columns = [
        "baseball_prospectus",
        "espn",
        "athletic",
        "fangraphs",
        "mlb_pipeline",
        "just_baseball",
    ]

    df["my_avg"] = df[ranking_columns].apply(
        lambda row: row.dropna().mean() if not row.dropna().empty else None, axis=1
    )

    # Calculate 'top_projection' column as the minimum value out of ranking_columns
    df["top_projection"] = df[ranking_columns].apply(
        lambda row: row.min() if not row.dropna().empty else None, axis=1
    )

    # Calculate 'num_places_ranked' column as the number of non-null values in ranking_columns
    df["num_places_ranked"] = df[ranking_columns].count(axis=1)
    # Drop rows where 'num_places_ranked' is 0
    df = df[df["num_places_ranked"] > 0]

    # Convert ETA from float to int
    df["ETA"] = df["ETA"].fillna(0).astype(int)
    return df


just_drafted_players = []


def main():
    parser = argparse.ArgumentParser(
        description="Merges prospect rankings from various sources and outputs a CSV. Filter out players that are already taken."
    )
    parser.add_argument(
        "--sort", type=str, default="fangraphs", help="Sort by specified ranking source"
    )
    args = parser.parse_args()

    df = get_prospect_ratings()
    df = cleanup_data(df)

    df = df.sort_values(by=args.sort)
    print(df.head(30))

    df.to_csv("prospects.csv", index=False)


if __name__ == "__main__":
    main()
