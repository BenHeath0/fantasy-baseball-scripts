"""Build the HTML body of the daily fantasy report."""

import html

import pandas as pd

HITTER_DISPLAY_COLS = ["AB", "R", "H", "HR", "RBI", "SB"]
PITCHER_DISPLAY_COLS = ["IP", "H_p", "ER", "BB", "K", "W", "SV", "HLD"]
PITCHER_DISPLAY_LABELS = {"H_p": "H"}

TABLE_STYLE = (
    "border-collapse:collapse;font-family:-apple-system,Helvetica,Arial,sans-serif;"
    "font-size:13px;margin-bottom:18px;"
)
TH_STYLE = "border:1px solid #ddd;padding:4px 8px;background:#f4f4f4;text-align:left;"
TD_STYLE = "border:1px solid #ddd;padding:4px 8px;"
H2_STYLE = "font-family:-apple-system,Helvetica,Arial,sans-serif;margin:18px 0 6px 0;"
H3_STYLE = "font-family:-apple-system,Helvetica,Arial,sans-serif;margin:12px 0 4px 0;font-size:15px;"


def _esc(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return html.escape(str(value))


def _format_sp(name, owner):
    if not name:
        return "<em>TBD</em>"
    if owner:
        return f"<b>{_esc(name)}</b> <span style='color:#888;'>({_esc(owner)})</span>"
    return _esc(name)


def _games_table(games):
    rows = [
        "<tr>"
        + "".join(f"<th style='{TH_STYLE}'>{h}</th>" for h in ["Time", "Matchup", "Away SP", "Home SP"])
        + "</tr>"
    ]
    for game in games:
        matchup = f"{_esc(game['away_team'])} @ {_esc(game['home_team'])}"
        rows.append(
            "<tr>"
            f"<td style='{TD_STYLE}'>{_esc(game['game_time_local'])}</td>"
            f"<td style='{TD_STYLE}'>{matchup}</td>"
            f"<td style='{TD_STYLE}'>{_format_sp(game['away_sp_name'], game['away_sp_owned_by'])}</td>"
            f"<td style='{TD_STYLE}'>{_format_sp(game['home_sp_name'], game['home_sp_owned_by'])}</td>"
            "</tr>"
        )
    return f"<table style='{TABLE_STYLE}'>{''.join(rows)}</table>"


def _stats_table(df, display_cols, labels=None):
    labels = labels or {}
    headers = ["Player", "Team"] + [labels.get(c, c) for c in display_cols]
    head = "<tr>" + "".join(f"<th style='{TH_STYLE}'>{h}</th>" for h in headers) + "</tr>"
    body_rows = []
    for _, row in df.iterrows():
        cells = [_esc(row["player_name"]), _esc(row["team"])]
        for c in display_cols:
            cells.append(_esc(row.get(c)))
        body_rows.append(
            "<tr>" + "".join(f"<td style='{TD_STYLE}'>{c}</td>" for c in cells) + "</tr>"
        )
    return f"<table style='{TABLE_STYLE}'>{head}{''.join(body_rows)}</table>"


def _split_played(df, role_cols):
    """Split a roster frame into (played, did_not_play) based on whether stat cols are filled."""
    if df.empty:
        return df, df
    has_stats = df[role_cols].notna().any(axis=1)
    return df[has_stats], df[~has_stats]


def build_html_email(games, hitters_df, pitchers_df, today_str, yesterday_str):
    parts = [
        f"<h2 style='{H2_STYLE}'>Today's Games &mdash; {_esc(today_str)}</h2>",
        _games_table(games) if games else "<p>No games scheduled.</p>",
        f"<h2 style='{H2_STYLE}'>Yesterday's Stats &mdash; {_esc(yesterday_str)}</h2>",
    ]

    leagues = sorted(set(hitters_df["fantasy_league"]).union(pitchers_df["fantasy_league"]))
    for league in leagues:
        parts.append(f"<h3 style='{H3_STYLE}'>{_esc(league)} &mdash; Hitters</h3>")
        league_hitters = hitters_df[hitters_df["fantasy_league"] == league]
        played, dnp = _split_played(league_hitters, HITTER_DISPLAY_COLS)
        if not played.empty:
            parts.append(_stats_table(played, HITTER_DISPLAY_COLS))
        else:
            parts.append("<p><em>No hitters played.</em></p>")
        if not dnp.empty:
            names = ", ".join(_esc(n) for n in dnp["player_name"])
            parts.append(f"<p style='color:#888;font-size:12px;'>Did not play: {names}</p>")

        parts.append(f"<h3 style='{H3_STYLE}'>{_esc(league)} &mdash; Pitchers</h3>")
        league_pitchers = pitchers_df[pitchers_df["fantasy_league"] == league]
        played, dnp = _split_played(league_pitchers, PITCHER_DISPLAY_COLS)
        if not played.empty:
            parts.append(_stats_table(played, PITCHER_DISPLAY_COLS, PITCHER_DISPLAY_LABELS))
        else:
            parts.append("<p><em>No pitchers played.</em></p>")
        if not dnp.empty:
            names = ", ".join(_esc(n) for n in dnp["player_name"])
            parts.append(f"<p style='color:#888;font-size:12px;'>Did not play: {names}</p>")

    subject = f"Daily Baseball Report — {today_str}"
    body = "<html><body>" + "".join(parts) + "</body></html>"
    return subject, body
