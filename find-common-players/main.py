import pandas as pd

# Read avail players
df = pd.read_csv("bush_league_avail_players.csv")[["Player"]]

closermonkey_df = pd.read_csv("closermonkey.csv").rename(
    columns={"Relievers": "Player"}
)

# Find intersection between the two DataFrames
common_players = pd.merge(df, closermonkey_df, on="Player")

print(common_players)
