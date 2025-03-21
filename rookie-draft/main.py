import csv
import argparse
import pandas as pd


# https://docs.google.com/spreadsheets/d/1vNB0IZe_PZwaNF6MA5LRsYzHMvlySQ1sK6_mHBAVAJM/edit?gid=0#gid=0
def clean_composite_csv(input_file, output_file):
    with open(input_file, mode="r") as infile, open(
        output_file, mode="w", newline=""
    ) as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ["Name", "Rank", "AVG", "mlb_pipeline"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        row_count = 0
        for row in reader:
            last_first = row["PlayerName"]
            first_last = " ".join(last_first.split(", ")[::-1])
            writer.writerow(
                {
                    "Name": first_last,
                    "Rank": row["RANK"],
                    "AVG": row["AVG"],
                    "mlb_pipeline": row["MLB Pipeline"],
                }
            )
            row_count += 1
            if row_count == 150:
                break


just_drafted_players = [
    "Roki Sasaki",
    "Jac Caglianone",
    "Kristian Campbell",
    "Travis Bazzana",
    "JJ Wetherholt",
    "Jesus Made",
    "Christian Moore",
    "Chandler Simpson",
    "Chase Burns",
    "Charlie Condon",
    "Nick Kurtz",
    "Kevin McGonigle",
    "Drake Baldwin",
    "Cam Smith",
    "Hagen Smith",
    "Jarlin Susana",
    "Braden Montgomery",
    "Luke Keaschall",
]


def main():
    parser = argparse.ArgumentParser(
        description="Compares top 100 prospect rankings with available players in Fantrax league."
    )
    parser.add_argument(
        "--sort", type=str, default="composite", help="Sort by specified ranking source"
    )
    args = parser.parse_args()

    fangraphs_file = "fangraphs_top_100.csv"
    baseball_prospectus_file = "baseball_prospectus_top_100.csv"
    composite_file = "composite_cleaned.csv"

    fangraphs_data = pd.read_csv(fangraphs_file)
    baseball_prospectus_data = pd.read_csv(baseball_prospectus_file)
    composite_data = pd.read_csv(composite_file)

    # Merge all three DataFrames by "Name"
    merged_df = composite_data[["Name", "AVG", "mlb_pipeline"]].rename(
        columns={"AVG": "composite"}
    )

    merged_df = merged_df.merge(
        baseball_prospectus_data[["Name", "Rank"]].rename(
            columns={"Rank": "baseball_prospectus"}
        ),
        on="Name",
        how="left",
    )

    merged_df = merged_df.merge(
        fangraphs_data[["Name", "Rank", "Team", "ETA"]].rename(
            columns={"Rank": "fangraphs"}
        ),
        on="Name",
        how="left",
    )

    merged_df = merged_df.sort_values(by=args.sort)

    fantrax_file = "Fantrax-Players-The Bush League.csv"
    fantrax_data = pd.read_csv(fantrax_file)

    # Filter out rows from merged_df if the player name is in fantrax_data
    fantrax_player_names = set(fantrax_data["Player"])
    merged_df = merged_df[merged_df["Name"].isin(fantrax_player_names)]

    # Filter out rows from merged_df if the player name is in just_drafted_players
    merged_df = merged_df[~merged_df["Name"].isin(just_drafted_players)]
    print(merged_df)

    merged_df.to_csv("top_available_players.csv", index=False)


if __name__ == "__main__":
    main()
    # input_file = (
    #     "/Users/benheath/Developer/fantasy-baseball-scripts/rookie-draft/composite.csv"
    # )
    # output_file = "/Users/benheath/Developer/fantasy-baseball-scripts/rookie-draft/composite_cleaned.csv"

    # clean_composite_csv(input_file, output_file)
