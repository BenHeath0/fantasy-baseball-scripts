"""Load and unify fantasy rosters across leagues."""

import os

import pandas as pd

from player_evaluation.config import TEAM_ABBREV_TO_FANGRAPHS
from player_evaluation.utils import normalize_name_column

from .config import ROSTER_SOURCES


def _load_one(source):
    df = pd.read_csv(source["path"])
    if source["filter"]:
        f = source["filter"]
        if "env" in f:
            value = os.environ.get(f["env"])
            if not value:
                raise RuntimeError(
                    f"Roster '{source['label']}' requires env var {f['env']}"
                )
        else:
            value = f["value"]
        df = df[df[f["col"]] == value].copy()

    keep = [source["name_col"], source["team_col"]]
    if source.get("position_col") and source["position_col"] in df.columns:
        keep.append(source["position_col"])
    df = df[keep].copy()

    rename_map = {source["name_col"]: "player_name", source["team_col"]: "team"}
    if source.get("position_col") and source["position_col"] in df.columns:
        rename_map[source["position_col"]] = "position"
    df.rename(columns=rename_map, inplace=True)

    if "position" not in df.columns:
        df["position"] = ""

    df["team"] = df["team"].replace(TEAM_ABBREV_TO_FANGRAPHS)
    df["fantasy_league"] = source["label"]
    normalize_name_column(df)
    return df[["fantasy_league", "player_name", "team", "position"]]


def load_all_rosters():
    """Return a unified DataFrame of every player on every fantasy roster."""
    frames = [_load_one(src) for src in ROSTER_SOURCES]
    return pd.concat(frames, ignore_index=True)
