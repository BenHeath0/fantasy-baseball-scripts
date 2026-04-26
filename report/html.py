"""Shared HTML helpers for daily and weekly reports."""

import html as _html

import pandas as pd

TABLE_STYLE = (
    "border-collapse:collapse;font-family:-apple-system,Helvetica,Arial,sans-serif;"
    "font-size:13px;margin-bottom:18px;"
)
TH_STYLE = "border:1px solid #ddd;padding:4px 8px;background:#f4f4f4;text-align:left;"
TD_STYLE = "border:1px solid #ddd;padding:4px 8px;"
H2_STYLE = "font-family:-apple-system,Helvetica,Arial,sans-serif;margin:18px 0 6px 0;"
H3_STYLE = "font-family:-apple-system,Helvetica,Arial,sans-serif;margin:12px 0 4px 0;font-size:15px;"


def esc(value):
    """Escape a cell value, collapsing whole-number floats (3.0 → 3)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return _html.escape(str(value))


def stats_table(df, display_cols, labels=None):
    labels = labels or {}
    headers = ["Player", "Team"] + [labels.get(c, c) for c in display_cols]
    head = "<tr>" + "".join(f"<th style='{TH_STYLE}'>{h}</th>" for h in headers) + "</tr>"
    body_rows = []
    for _, row in df.iterrows():
        cells = [esc(row["player_name"]), esc(row["team"])]
        for c in display_cols:
            cells.append(esc(row.get(c)))
        body_rows.append(
            "<tr>" + "".join(f"<td style='{TD_STYLE}'>{c}</td>" for c in cells) + "</tr>"
        )
    return f"<table style='{TABLE_STYLE}'>{head}{''.join(body_rows)}</table>"


def split_played(df, role_cols):
    """Split a roster frame into (played, did_not_play) based on whether stat cols are filled."""
    if df.empty:
        return df, df
    has_stats = df[role_cols].notna().any(axis=1)
    return df[has_stats], df[~has_stats]


def render_league_section(parts, league, hitters_df, pitchers_df,
                         hitter_cols, pitcher_cols, pitcher_labels=None):
    """Append the per-league hitter + pitcher tables (and DNP footers) to `parts`."""
    parts.append(f"<h3 style='{H3_STYLE}'>{esc(league)} &mdash; Hitters</h3>")
    league_hitters = hitters_df[hitters_df["fantasy_league"] == league]
    played, dnp = split_played(league_hitters, hitter_cols)
    if not played.empty:
        parts.append(stats_table(played, hitter_cols))
    else:
        parts.append("<p><em>No hitters played.</em></p>")
    if not dnp.empty:
        names = ", ".join(esc(n) for n in dnp["player_name"])
        parts.append(f"<p style='color:#888;font-size:12px;'>Did not play: {names}</p>")

    parts.append(f"<h3 style='{H3_STYLE}'>{esc(league)} &mdash; Pitchers</h3>")
    league_pitchers = pitchers_df[pitchers_df["fantasy_league"] == league]
    played, dnp = split_played(league_pitchers, pitcher_cols)
    if not played.empty:
        parts.append(stats_table(played, pitcher_cols, pitcher_labels))
    else:
        parts.append("<p><em>No pitchers played.</em></p>")
    if not dnp.empty:
        names = ", ".join(esc(n) for n in dnp["player_name"])
        parts.append(f"<p style='color:#888;font-size:12px;'>Did not play: {names}</p>")
