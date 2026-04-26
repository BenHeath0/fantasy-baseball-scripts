"""Yesterday's box-score lines, filtered to rostered players."""

import pandas as pd

from api.mlb_stats import get_boxscores_for_date
from player_evaluation.config import TEAM_ABBREV_TO_FANGRAPHS
from player_evaluation.utils import normalize_name_column

HITTER_COLS = ["AB", "R", "H", "HR", "RBI", "SB", "AVG"]
PITCHER_COLS = ["IP", "H_p", "ER", "BB", "K", "W", "SV", "HLD", "ERA", "WHIP"]


def _normalize_box(df):
    df = df.copy()
    df["team"] = df["team"].replace(TEAM_ABBREV_TO_FANGRAPHS)
    normalize_name_column(df)
    return df


def get_yesterday_stats_for_rosters(rosters_df, date):
    """Return (hitter_df, pitcher_df) of yesterday's stat lines for rostered players."""
    box = get_boxscores_for_date(date)
    if box.empty:
        return pd.DataFrame(), pd.DataFrame()

    box = _normalize_box(box)
    merged = rosters_df.merge(box, on=["player_name", "team"], how="left")

    hitters = _filter_role(merged, rosters_df, role="hitter")
    pitchers = _filter_role(merged, rosters_df, role="pitcher")
    return hitters, pitchers


def _filter_role(merged, rosters_df, role):
    """Split merged frame into hitter / pitcher rows.

    A roster slot is a pitcher if its position contains 'SP' or 'RP'; otherwise hitter.
    Players with no row in the box score still appear (with NaN stat columns) so we
    can show 'did not play' below.
    """
    pos = merged["position"].fillna("").str.upper()
    is_pitcher = pos.str.contains("SP") | pos.str.contains("RP") | (pos == "P")

    if role == "pitcher":
        df = merged[is_pitcher].copy()
        keep = ["fantasy_league", "player_name", "team", "position"] + PITCHER_COLS
    else:
        df = merged[~is_pitcher].copy()
        keep = ["fantasy_league", "player_name", "team", "position"] + HITTER_COLS
    return df[[c for c in keep if c in df.columns]]
