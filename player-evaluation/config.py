# Configuration constants for fantasy baseball player evaluation

# Projection systems for auction values
PROJECTION_SYSTEMS = ["steamer", "thebatx", "oopsy"]

# Player rater systems
ROS_PROJECTION_SYSTEMS = ["2025"]
# ROS_PROJECTION_SYSTEMS = ["steamerr", "rthebatx", "roopsydc", "2025"]

# League settings
LEAGUE_SETTINGS = {
    "teams": 19,
    "dollars": 300,
    "mb": 1,
    "mp": 20,
    "msp": 5,
    "mrp": 5,
    "points": "c|1,2,3,4,5,6|0,1,10,2,3,6",
    "rep": 0,
    "drp": 0,
    "pp": "C,SS,2B,3B,OF,1B",
    "pos": "2,1,1,1,4,1,1,1,0,2,5,4,2,0,0",
}

# Team abbreviation mappings
FANTRAX_TO_FANGRAPHS_TEAMS = {
    "SF": "SFG",
    "TB": "TBR",
    "WSH": "WSN",
    "WAS": "WSN",
    "SD": "SDP",
    "KC": "KCR",
    "CHW": "CWS",
}

# Fangraphs URLs and endpoints
FANGRAPHS_URLS = {
    "auction_calculator": "https://www.fangraphs.com/api/fantasy/auction-calculator/data",
    "player_rater": "https://www.fangraphs.com/api/fantasy/player-rater/data",
    "leaders": "https://www.fangraphs.com/api/leaders/major-league/data",
}

FANGRAPHS_LEADERBOARD_TYPE_MAPPING = {
    "stuff+": 36,
    "statcast_batters": 24,
}

FANGRAPHS_LEADERBOARD_STATS_MAPPING = {
    "stuff+": ["sp_stuff", "sp_location", "sp_pitching"],
    "statcast_batters": [
        "Events",
        "EV",
        "maxEV",
        "Barrel%",
        "HardHit%",
        "wOBA",
        "xwOBA",
    ],
}

# Data refresh settings
DATA_REFRESH_DAYS = 1

# File paths
INPUT_DATA_DIR = "input_data"
OUTPUT_DIR = "output"
CACHE_FILE = "auction_values_combined.csv"
LAST_FETCHED_FILE = "last_fetched.txt"

# Keep threshold for determining keepers
KEEPER_THRESHOLD = -5.0
