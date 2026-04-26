"""Aggregate the previous week's box-score lines for rostered players."""

from datetime import date, timedelta

import pandas as pd

from api.mlb_stats import get_boxscores_for_date
from player_evaluation.config import TEAM_ABBREV_TO_FANGRAPHS
from player_evaluation.utils import normalize_name_column

HITTER_SUM_COLS = ["AB", "R", "H", "HR", "RBI", "SB"]
PITCHER_SUM_COLS = ["H_p", "ER", "BB", "K", "W", "SV", "HLD"]


def _ip_to_outs(ip):
    """Convert MLB IP notation (e.g. '5.2' = 5 2/3) to total outs."""
    if ip is None or (isinstance(ip, float) and pd.isna(ip)):
        return 0
    s = str(ip)
    if "." in s:
        whole, frac = s.split(".", 1)
        return int(whole) * 3 + int(frac)
    return int(s) * 3


def _outs_to_ip(outs):
    """Convert outs back to MLB IP notation as a float (5.2 == 5 2/3)."""
    whole, frac = divmod(int(outs), 3)
    return float(f"{whole}.{frac}")


def _normalize_box(df):
    df = df.copy()
    df["team"] = df["team"].replace(TEAM_ABBREV_TO_FANGRAPHS)
    normalize_name_column(df)
    return df


def _fetch_week(end_date_str):
    """Fetch and concat boxscores for the 7 days ending on `end_date_str` (inclusive)."""
    end = date.fromisoformat(end_date_str)
    frames = []
    for i in range(7):
        d = (end - timedelta(days=6 - i)).isoformat()
        df = get_boxscores_for_date(d)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _aggregate_hitters(box):
    cols = [c for c in HITTER_SUM_COLS if c in box.columns]
    if not cols:
        return pd.DataFrame()
    df = box[["player_name", "team"] + cols].copy()
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    agg = df.groupby(["player_name", "team"], as_index=False)[cols].sum(min_count=1)
    if {"H", "AB"}.issubset(agg.columns):
        avg = (agg["H"] / agg["AB"]).where(agg["AB"] > 0)
        agg["AVG"] = avg.map(lambda v: f"{v:.3f}" if pd.notna(v) else None)
    return agg


def _aggregate_pitchers(box):
    df = box[["player_name", "team", "IP"] + [c for c in PITCHER_SUM_COLS if c in box.columns]].copy()
    df["outs"] = df["IP"].apply(_ip_to_outs)
    sum_cols = [c for c in PITCHER_SUM_COLS if c in df.columns]
    for c in sum_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    agg = df.groupby(["player_name", "team"], as_index=False).agg(
        {**{c: "sum" for c in sum_cols}, "outs": "sum"}
    )
    # Drop pitchers who never recorded an out (pure hitter rows ride along otherwise).
    agg = agg[agg["outs"] > 0].copy()
    agg["IP"] = agg["outs"].apply(lambda o: f"{_outs_to_ip(o):.1f}")
    innings = agg["outs"] / 3.0
    agg["ERA"] = (agg["ER"] * 9.0 / innings).map(lambda v: f"{v:.2f}" if pd.notna(v) else None)
    agg["WHIP"] = ((agg["BB"] + agg["H_p"]) / innings).map(lambda v: f"{v:.2f}" if pd.notna(v) else None)
    return agg.drop(columns=["outs"])


def _filter_role(merged, role):
    pos = merged["position"].fillna("").str.upper()
    is_pitcher = pos.str.contains("SP") | pos.str.contains("RP") | (pos == "P")
    return merged[is_pitcher].copy() if role == "pitcher" else merged[~is_pitcher].copy()


def get_week_stats_for_rosters(rosters_df, end_date_str):
    """Return (hitter_df, pitcher_df) of weekly totals for rostered players.

    Week = the 7 days ending on `end_date_str` (inclusive).
    """
    box = _fetch_week(end_date_str)
    if box.empty:
        return pd.DataFrame(), pd.DataFrame()

    box = _normalize_box(box)

    hitters_box = _aggregate_hitters(box)
    pitchers_box = _aggregate_pitchers(box)

    hitter_rosters = _filter_role(rosters_df, role="hitter")
    pitcher_rosters = _filter_role(rosters_df, role="pitcher")

    hitters = hitter_rosters.merge(hitters_box, on=["player_name", "team"], how="left")
    pitchers = pitcher_rosters.merge(pitchers_box, on=["player_name", "team"], how="left")
    return hitters, pitchers
