"""Wrapper for the public MLB Stats API (statsapi.mlb.com)."""

from datetime import datetime

import pandas as pd
import requests

BASE_URL = "https://statsapi.mlb.com/api/v1"


def _format_local_time(iso_utc):
    """Convert an MLB ISO UTC timestamp to local-time HH:MM (e.g. '7:05 PM')."""
    dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00")).astimezone()
    return dt.strftime("%-I:%M %p")


def get_schedule(date):
    """Return a list of dicts with one entry per scheduled MLB game on `date`.

    Fields: game_pk, game_time_local, status, away_team, home_team,
    away_sp_id, away_sp_name, home_sp_id, home_sp_name.
    """
    print(f"Fetching MLB schedule for {date}...")
    params = {
        "sportId": 1,
        "date": date,
        "hydrate": "probablePitcher,team",
    }
    resp = requests.get(f"{BASE_URL}/schedule", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    games = []
    for date_block in data.get("dates", []):
        for game in date_block.get("games", []):
            away = game["teams"]["away"]
            home = game["teams"]["home"]
            games.append(
                {
                    "game_pk": game["gamePk"],
                    "game_time_local": _format_local_time(game["gameDate"]),
                    "status": game["status"]["detailedState"],
                    "away_team": away["team"]["abbreviation"],
                    "home_team": home["team"]["abbreviation"],
                    "away_sp_id": (away.get("probablePitcher") or {}).get("id"),
                    "away_sp_name": (away.get("probablePitcher") or {}).get("fullName"),
                    "home_sp_id": (home.get("probablePitcher") or {}).get("id"),
                    "home_sp_name": (home.get("probablePitcher") or {}).get("fullName"),
                }
            )
    return games


def _extract_player_rows(boxscore_team, team_abbrev):
    """Flatten one team's boxscore players into stat rows."""
    rows = []
    for player in boxscore_team.get("players", {}).values():
        person = player.get("person", {})
        stats = player.get("stats", {})
        batting = stats.get("batting") or {}
        pitching = stats.get("pitching") or {}
        if not batting and not pitching:
            continue
        row = {
            "player_name": person.get("fullName"),
            "team": team_abbrev,
            # hitter line
            "AB": batting.get("atBats"),
            "R": batting.get("runs"),
            "H": batting.get("hits"),
            "HR": batting.get("homeRuns"),
            "RBI": batting.get("rbi"),
            "SB": batting.get("stolenBases"),
            "AVG": batting.get("avg"),
            # pitcher line
            "IP": pitching.get("inningsPitched"),
            "H_p": pitching.get("hits"),
            "ER": pitching.get("earnedRuns"),
            "BB": pitching.get("baseOnBalls"),
            "K": pitching.get("strikeOuts"),
            "W": pitching.get("wins"),
            "SV": pitching.get("saves"),
            "HLD": pitching.get("holds"),
            "ERA": pitching.get("era"),
            "WHIP": pitching.get("whip"),
        }
        rows.append(row)
    return rows


def get_boxscores_for_date(date):
    """Return a DataFrame of per-game stat lines for every player who played on `date`.

    Columns: player_name, team (MLB abbrev), plus hitter and pitcher box-line stats.
    Hitter-only rows leave pitcher columns blank and vice versa.
    """
    print(f"Fetching MLB boxscores for {date}...")
    games = get_schedule(date)
    rows = []
    for game in games:
        if game["status"] in {"Scheduled", "Pre-Game", "Postponed", "Cancelled"}:
            continue
        resp = requests.get(
            f"{BASE_URL}/game/{game['game_pk']}/boxscore", timeout=30
        )
        resp.raise_for_status()
        box = resp.json()
        rows.extend(
            _extract_player_rows(box["teams"]["away"], game["away_team"])
        )
        rows.extend(
            _extract_player_rows(box["teams"]["home"], game["home_team"])
        )
    return pd.DataFrame(rows)
