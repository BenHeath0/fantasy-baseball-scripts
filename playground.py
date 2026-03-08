#!/usr/bin/env python3
"""Playground for testing individual parts of the player_evaluation pipeline."""

from player_evaluation.data_fetchers import fetch_stuff_plus_data

print("Fetching Stuff+ leaderboard...")
df = fetch_stuff_plus_data()

if df is not None:
    print(f"\nRows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"\n{df.head(20).to_string(index=False)}")
else:
    print("No data returned.")
