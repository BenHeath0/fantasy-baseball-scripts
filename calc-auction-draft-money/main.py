import pandas as pd

# Read the CSV file
df = pd.read_csv("draft.csv")

# Calculate the sum of costs for hitters and pitchers
hitters_cost = df[df["Type"] == "Hitters"]["Cost"].sum()
pitchers_cost = df[df["Type"] == "Pitchers"]["Cost"].sum()

num_keepers_hitters = 8
num_keepers_pitchers = 3

num_hitters_drafted = len(df[df["Type"] == "Hitters"]) - 1
num_pitchers_drafted = len(df[df["Type"] == "Pitchers"]) - 1

# Calculate the total cost of all players
total_cost = df["Cost"].sum()

# Output the total cost
print(f"Total Cost for All Players: {total_cost}\n")

# Output the results
print(f"Total Cost for Hitters: {hitters_cost} (Goal: between 150 and 180)")
print(f"Total number of Hitters: {num_hitters_drafted + num_keepers_hitters} / 14\n")


print(f"Total Cost for Pitchers: {pitchers_cost} (Goal: between 120 and 150)")
print(f"Total number of Pitchers: {num_pitchers_drafted + num_keepers_pitchers} / 11")
