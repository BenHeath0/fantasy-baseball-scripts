import pandas as pd


def load_auction_projections(projection_system):
    """
    Combines ZiPS hitter and pitcher projections into one DataFrame with Name and Dollars.

    Args:
        hitters_path (str): Path to zips-hitters.csv
        pitchers_path (str): Path to zips-pitchers.csv

    Returns:
        pandas.DataFrame: Combined projections sorted by Dollars descending
    """
    """
    TODO
    - Try and fetch the data dynamically
    """

    # Read CSVs
    hitters_df = pd.read_csv(
        f"original_auction_values/{projection_system}-hitters.csv"
    )[["Name", "Dollars"]]
    pitchers_df = pd.read_csv(
        f"original_auction_values/{projection_system}-pitchers.csv"
    )[["Name", "Dollars"]]

    # Concatenate vertically
    combined_df = pd.concat([hitters_df, pitchers_df], ignore_index=True)
    combined_df.rename(
        columns={
            "Name": "player_name",
            "Dollars": "auction_value",  # example columns
        },
        inplace=True,
    )

    # Write the combined DataFrame to a CSV file
    combined_df.to_csv(f"combined_auction_values/{projection_system}.csv", index=False)

    return combined_df
