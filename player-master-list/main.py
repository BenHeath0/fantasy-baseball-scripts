import pandas as pd
import argparse


def cleanup_juniors(df, key):
    df[key] = df[key].str.replace("Jr.", "", regex=False).str.strip()
    return df


def reorder_df_cols(df):
    """
    Put cols in correct order
    """

    cols = ["Player", "Position(s)", "Team", "athletic", "NFBC_ADP", "Eno"] + [
        col
        for col in df.columns
        if col not in ["Player", "Position(s)", "Team", "athletic", "NFBC_ADP", "Eno"]
    ]

    return df[cols]


def main(league):
    ########################
    # init w/ auction values
    #########################
    # TODO: remove dupes from auction calcs
    # TODO: instead of reading bush league values, need to fetch custom for each league
    df = pd.read_csv("../keeper-evaluation/auction_values_combined.csv")
    df = cleanup_juniors(df, "player_name")
    df.rename(columns={"player_name": "Player"}, inplace=True)

    #######################
    # Read in NFBC ADP data
    # https://nfc.shgn.com/adp/baseball
    #######################
    nfbc_df = pd.read_csv(
        "data/nfbc_adp.csv", usecols=["Player", "Position(s)", "Rank", "Team"]
    )
    nfbc_df.rename(columns={"Rank": "NFBC_ADP"}, inplace=True)
    nfbc_df = nfbc_df[["Player", "Position(s)", "Team", "NFBC_ADP"]]
    nfbc_df["Player"] = nfbc_df["Player"].apply(lambda x: " ".join(x.split(", ")[::-1]))
    nfbc_df = cleanup_juniors(nfbc_df, "Player")
    df = df.merge(nfbc_df, on="Player", how="left")

    #######################
    # Read in Eno rankings
    #######################
    eno_df = pd.read_csv("data/eno_rankings.csv")
    eno_df.rename(columns={"Rank": "Eno"}, inplace=True)
    df = df.merge(eno_df, on="Player", how="left")

    #######################
    # Read in closermonkey
    #######################
    # ESPN uses SOLDs. Rest use SAVES
    closermonkey_df = (
        pd.read_csv("data/closermonkey_solds.csv")
        if league == "espn"
        else pd.read_csv("data/closermonkey_saves.csv")
    )

    closermonkey_df.rename(
        columns={"Tier": "closermonkey tier", "Rank": "closermonkey rank"}, inplace=True
    )
    df = df.merge(closermonkey_df, on="Player", how="left")

    #######################
    # Read in baseball prospectus
    #######################
    bp_df = pd.read_csv("data/baseball_prospectus_model_portfolio.csv")[["Player"]]
    bp_df["bp_expert_count"] = bp_df.groupby("Player")["Player"].transform("count")
    bp_df = bp_df.drop_duplicates(subset=["Player"])
    bp_df = bp_df.sort_values(by="bp_expert_count", ascending=False)
    df = df.merge(bp_df, on="Player", how="left")

    ###################################
    # Read in athletic (ESPN and Yahoo)
    # (bush doesnt need)
    #################################
    if league in ("yahoo", "espn"):
        athletic_df = pd.read_csv(f"data/athletic-{league}.csv")
        athletic_df = athletic_df[["Player", "Rank"]]
        athletic_df.rename(columns={"Rank": "athletic"}, inplace=True)
        df = df.merge(athletic_df, on="Player", how="left")

    # Reorder columns
    df = reorder_df_cols(df)

    # Add col for filtering out
    df.insert(df.columns.get_loc("Player") + 1, "is_drafted", "")

    # Output results
    df.to_csv(f"rankings_{league}.csv", index=False)
    print(f"wrote to rankings_{league}.csv")
    print(df.head(30))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process fantasy baseball data.")
    parser.add_argument(
        "--league",
        type=str,
        default="yahoo",
        help="Specify the league (default: yahoo)",
    )
    args = parser.parse_args()

    main(args.league)
