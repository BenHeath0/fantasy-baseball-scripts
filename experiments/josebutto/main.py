import pandas as pd

# Read the CSV file into a Pandas DataFrame
file_path = "butto_stuffplus.csv"
df = pd.read_csv(file_path)

# Ensure numeric columns are properly handled
numeric_columns = df.columns[3:]  # Assuming first 4 columns are non-numeric
df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")

# Split the DataFrame by GS and calculate the average values
gs_1_avg = df[df["GS"] == 1].mean(numeric_only=True)
gs_0_avg = df[df["GS"] == 0].mean(numeric_only=True)

# # Print the results
# print("Average values for GS = 1:")
# print(gs_1_avg)
# print("\nAverage values for GS = 0:")
# print(gs_0_avg)
averages_df = pd.DataFrame([gs_1_avg, gs_0_avg], index=["GS=1", "GS=0"])

# Print the new DataFrame
print("Average values split by GS:")
print(averages_df)

# Log the counts of different values for GS
gs_counts = df["GS"].value_counts()
print("\nCounts of different values for GS:")
print(gs_counts)
