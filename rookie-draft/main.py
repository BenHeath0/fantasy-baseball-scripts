import csv
import argparse


def read_csv(file_path):
    def convert_value(value):
        try:
            return float(value)
        except ValueError:
            return value

    with open(file_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return [{k: convert_value(v) for k, v in row.items()} for row in reader]


def find_matching_players(combined_data, fantrax_data):
    # Clean up fantrax data to be just names
    fantrax_names = {player["Player"] for player in fantrax_data}
    matching_players = []
    for name, ranking in combined_data:
        if name in fantrax_names:
            matching_players.append(f"{name} - {ranking}")

    return matching_players


def combine_rankings(data_arr):
    """
    data_arr: [
        {
            "source": "fangraphs",
            "arr": [
                {"Name": "Francisco Lindor", "Rank": 1},
                ...
            ]
        }
    ]
    """

    output = {}
    for data in data_arr:
        source = data["source"]
        rank_key = "Rank" if not "key" in data else data["key"]
        for player in data["arr"]:
            name = player["Name"]
            if name not in output:
                output[name] = {}

            output[name][source] = player[rank_key]

    return output


# https://docs.google.com/spreadsheets/d/1vNB0IZe_PZwaNF6MA5LRsYzHMvlySQ1sK6_mHBAVAJM/edit?gid=0#gid=0
def clean_composite_csv(input_file, output_file):
    with open(input_file, mode="r") as infile, open(
        output_file, mode="w", newline=""
    ) as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ["Name", "Rank", "AVG"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        row_count = 0
        for row in reader:
            last_first = row["PlayerName"]
            first_last = " ".join(last_first.split(", ")[::-1])
            writer.writerow(
                {"Name": first_last, "Rank": row["RANK"], "AVG": row["AVG"]}
            )
            row_count += 1
            if row_count == 150:
                break


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

    fangraphs_data = read_csv(fangraphs_file)
    baseball_prospectus_data = read_csv(baseball_prospectus_file)
    composite_data = read_csv(composite_file)

    combined_data = combine_rankings(
        [
            {"source": "fangraphs", "arr": fangraphs_data},
            {"source": "baseball_prospectus", "arr": baseball_prospectus_data},
            {"source": "composite", "arr": composite_data, "key": "AVG"},
        ]
    )

    combined_data = sorted(
        combined_data.items(), key=lambda x: x[1].get(args.sort, float("inf"))
    )

    fantrax_file = "Fantrax-Players-The Bush League.csv"
    fantrax_data = read_csv(fantrax_file)

    matching_players = find_matching_players(combined_data, fantrax_data)

    for player in matching_players:
        print(player)


if __name__ == "__main__":
    main()
    # input_file = (
    #     "/Users/benheath/Developer/fantasy-baseball-scripts/rookie-draft/composite.csv"
    # )
    # output_file = "/Users/benheath/Developer/fantasy-baseball-scripts/rookie-draft/composite_cleaned.csv"

    # clean_composite_csv(input_file, output_file)
