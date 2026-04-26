"""Configuration for the fantasy reports (daily + weekly)."""

import os

from player_evaluation.config import INPUT_DATA_DIR

ROSTER_SOURCES = [
    {
        "label": "NFBC",
        "path": f"{INPUT_DATA_DIR}/rosters/nfbc_roster.csv",
        "name_col": "PLAYER NAME",
        "team_col": "TEAM",
        "position_col": "POS",
        "filter": None,
    },
    {
        "label": "Bush League",
        "path": f"{INPUT_DATA_DIR}/rosters/bush_league_players.csv",
        "name_col": "Player",
        "team_col": "Team",
        "position_col": "Position",
        # User's manager code lives in BUSH_MANAGER_CODE env var.
        "filter": {"col": "Status", "env": "BUSH_MANAGER_CODE"},
    },
]

REPORT_RECIPIENT = "benjheath0@gmail.com"

# Gmail SMTP settings
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
GMAIL_USER_ENV = "GMAIL_USER"
GMAIL_APP_PASSWORD_ENV = "GMAIL_APP_PASSWORD"


def get_required_env(name):
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Required env var {name} is not set")
    return val
