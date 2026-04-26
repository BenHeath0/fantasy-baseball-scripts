"""Daily fantasy baseball email report.

Lists today's MLB games (with rostered SPs flagged) and yesterday's box-score
lines for every player on the user's fantasy rosters.

Usage:
    python -m report.daily                  # send the email
    python -m report.daily --dry-run        # print HTML to stdout
    python -m report.daily --date 2026-04-26  # override "today"
"""

import argparse
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

from .config import REPORT_RECIPIENT
from .daily_stats import (
    HITTER_COLS,
    PITCHER_COLS,
    get_yesterday_stats_for_rosters,
)
from .email_sender import send_email
from .html import H2_STYLE, TABLE_STYLE, TD_STYLE, TH_STYLE, esc, render_league_section
from .rosters import load_all_rosters
from .schedule import get_today_schedule_with_roster_flags

PITCHER_LABELS = {"H_p": "H"}


def _format_sp(name, owner):
    if not name:
        return "<em>TBD</em>"
    if owner:
        return f"<b>{esc(name)}</b> <span style='color:#888;'>({esc(owner)})</span>"
    return esc(name)


def _games_table(games):
    rows = [
        "<tr>"
        + "".join(f"<th style='{TH_STYLE}'>{h}</th>" for h in ["Time", "Matchup", "Away SP", "Home SP"])
        + "</tr>"
    ]
    for game in games:
        matchup = f"{esc(game['away_team'])} @ {esc(game['home_team'])}"
        rows.append(
            "<tr>"
            f"<td style='{TD_STYLE}'>{esc(game['game_time_local'])}</td>"
            f"<td style='{TD_STYLE}'>{matchup}</td>"
            f"<td style='{TD_STYLE}'>{_format_sp(game['away_sp_name'], game['away_sp_owned_by'])}</td>"
            f"<td style='{TD_STYLE}'>{_format_sp(game['home_sp_name'], game['home_sp_owned_by'])}</td>"
            "</tr>"
        )
    return f"<table style='{TABLE_STYLE}'>{''.join(rows)}</table>"


def _build_html(games, hitters_df, pitchers_df, today_str, yesterday_str):
    parts = [
        f"<h2 style='{H2_STYLE}'>Today's Games &mdash; {esc(today_str)}</h2>",
        _games_table(games) if games else "<p>No games scheduled.</p>",
        f"<h2 style='{H2_STYLE}'>Yesterday's Stats &mdash; {esc(yesterday_str)}</h2>",
    ]
    leagues = sorted(set(hitters_df["fantasy_league"]).union(pitchers_df["fantasy_league"]))
    for league in leagues:
        render_league_section(
            parts, league, hitters_df, pitchers_df,
            HITTER_COLS, PITCHER_COLS, PITCHER_LABELS,
        )
    subject = f"Daily Baseball Report — {today_str}"
    body = "<html><body>" + "".join(parts) + "</body></html>"
    return subject, body


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Daily fantasy baseball email report")
    parser.add_argument("--date", default=None, help="Override 'today' (YYYY-MM-DD).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the HTML body to stdout instead of sending.")
    args = parser.parse_args()

    today = (
        datetime.strptime(args.date, "%Y-%m-%d").date()
        if args.date
        else datetime.now().date()
    )
    yesterday = today - timedelta(days=1)
    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()

    rosters = load_all_rosters()
    games = get_today_schedule_with_roster_flags(rosters, today_str)
    hitters, pitchers = get_yesterday_stats_for_rosters(rosters, yesterday_str)
    subject, html_body = _build_html(games, hitters, pitchers, today_str, yesterday_str)

    if args.dry_run:
        print(f"Subject: {subject}\n")
        print(html_body)
        return

    send_email(subject, html_body, REPORT_RECIPIENT)


if __name__ == "__main__":
    main()
