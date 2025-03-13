import os
import pandas as pd
import glob
from utils import load_auction_projections


# Consolidates all auction values into one CSV
def create_all_values_csv():
    # Make sure everything is combined
    for system in ["steamer", "batx", "zips", "steamer-experimental"]:
        load_auction_projections(system)

    directory = "combined_auction_values"
    all_values_df = pd.DataFrame()

    for file_path in glob.glob(os.path.join(directory, "*.csv")):
        system_name = os.path.splitext(os.path.basename(file_path))[0]
        df = pd.read_csv(file_path, usecols=["player_name", "auction_value"])
        df = df.rename(columns={"auction_value": f"{system_name}_auction_value"})
        if all_values_df.empty:
            all_values_df = df
        else:
            all_values_df = pd.merge(all_values_df, df, on="player_name", how="outer")

    # Sort by steamer_auction_value
    if "steamer_auction_value" in all_values_df.columns:
        all_values_df = all_values_df.sort_values(
            by="steamer_auction_value", ascending=False
        )

    # Check for duplicated player names
    duplicated_players = all_values_df[
        all_values_df.duplicated(subset="player_name", keep=False)
    ]
    if not duplicated_players.empty:
        print("Duplicated player names found:")
        print(duplicated_players)
    else:
        print("No duplicated player names found.")

    all_values_df.to_csv("all_values.csv", index=False)


def main():
    create_all_values_csv()


if __name__ == "__main__":
    main()
