"""Today's MLB schedule with rostered-SP flags."""

from api.mlb_stats import get_schedule
from player_evaluation.config import TEAM_ABBREV_TO_FANGRAPHS
from player_evaluation.utils import normalize_player_name


def _to_fangraphs_team(mlb_abbrev):
    return TEAM_ABBREV_TO_FANGRAPHS.get(mlb_abbrev, mlb_abbrev)


def _owner_for(rosters_df, sp_name, team_abbrev):
    """Return the fantasy_league label that owns this SP, or None."""
    if not sp_name:
        return None
    name = normalize_player_name(sp_name)
    team = _to_fangraphs_team(team_abbrev)
    match = rosters_df[
        (rosters_df["player_name"] == name) & (rosters_df["team"] == team)
    ]
    if match.empty:
        return None
    return match.iloc[0]["fantasy_league"]


def get_today_schedule_with_roster_flags(rosters_df, date):
    """Return today's games enriched with `away_sp_owned_by` / `home_sp_owned_by`."""
    games = get_schedule(date)
    for game in games:
        game["away_sp_owned_by"] = _owner_for(
            rosters_df, game["away_sp_name"], game["away_team"]
        )
        game["home_sp_owned_by"] = _owner_for(
            rosters_df, game["home_sp_name"], game["home_team"]
        )
    return games
