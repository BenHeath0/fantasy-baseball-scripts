import csv


def read_csv(file_path):
    with open(file_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]


def find_matching_players(combined_data, fantrax_data):
    # Clean up fantrax data to be just names
    fantrax_names = {player["Player"] for player in fantrax_data}
    matching_players = []
    for name, ranking in combined_data.items():
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
        for player in data["arr"]:
            name = player["Name"]
            if name not in output:
                output[name] = {}

            output[name][source] = player["Rank"]

    return output


def main():
    fantrax_file = "Fantrax-Players-The Bush League.csv"
    fangraphs_file = "fangraphs_top_100.csv"
    baseball_prospectus_file = "baseball_prospectus_top_100.csv"

    fangraphs_data = read_csv(fangraphs_file)
    fantrax_data = read_csv(fantrax_file)
    baseball_prospectus_data = read_csv(baseball_prospectus_file)

    combined_data = combine_rankings(
        [
            {"source": "fangraphs", "arr": fangraphs_data},
            {"source": "baseball_prospectus", "arr": baseball_prospectus_data},
        ]
    )
    matching_players = find_matching_players(combined_data, fantrax_data)

    for player in matching_players:
        print(player)


if __name__ == "__main__":
    main()
