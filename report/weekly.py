"""Weekly fantasy baseball email report.

Aggregates the previous week's stats (Mon-Sun) for every player on the user's
fantasy rosters. Intended to run Monday mornings.

Usage:
    python -m report.weekly                  # send the email
    python -m report.weekly --dry-run        # print HTML to stdout
    python -m report.weekly --end 2026-04-26 # override the week's end date (Sunday)
"""

import argparse
from datetime import date, datetime, timedelta

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

from .config import REPORT_RECIPIENT
from .email_sender import send_email
from .html import H2_STYLE, esc, render_league_section
from .rosters import load_all_rosters
from .weekly_stats import get_week_stats_for_rosters

HITTER_DISPLAY_COLS = ["AB", "R", "H", "HR", "RBI", "SB", "AVG", "OBP", "SLG"]
PITCHER_DISPLAY_COLS = ["IP", "H_p", "ER", "BB", "K", "W", "SV", "HLD", "ERA", "WHIP"]
PITCHER_LABELS = {"H_p": "H"}


def _previous_sunday(today):
    """Return the Sunday of the most recently completed Mon-Sun week."""
    # weekday(): Mon=0..Sun=6. Days back to the prior Sunday: weekday+1.
    return today - timedelta(days=today.weekday() + 1)


def _build_html(hitters_df, pitchers_df, start_str, end_str):
    parts = [
        f"<h2 style='{H2_STYLE}'>Weekly Stats &mdash; {esc(start_str)} to {esc(end_str)}</h2>",
    ]
    leagues = sorted(set(hitters_df["fantasy_league"]).union(pitchers_df["fantasy_league"]))
    for league in leagues:
        render_league_section(
            parts, league, hitters_df, pitchers_df,
            HITTER_DISPLAY_COLS, PITCHER_DISPLAY_COLS, PITCHER_LABELS,
        )
    subject = f"Weekly Baseball Report — {start_str} to {end_str}"
    body = "<html><body>" + "".join(parts) + "</body></html>"
    return subject, body


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Weekly fantasy baseball email report")
    parser.add_argument(
        "--end",
        default=None,
        help="End date of the week to report on, YYYY-MM-DD (inclusive). "
        "Defaults to the most recently completed Sunday.",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the HTML body to stdout instead of sending.")
    args = parser.parse_args()

    end = (
        datetime.strptime(args.end, "%Y-%m-%d").date()
        if args.end
        else _previous_sunday(date.today())
    )
    start = end - timedelta(days=6)
    start_str = start.isoformat()
    end_str = end.isoformat()

    rosters = load_all_rosters()
    hitters, pitchers = get_week_stats_for_rosters(rosters, end_str)
    subject, html_body = _build_html(hitters, pitchers, start_str, end_str)

    if args.dry_run:
        print(f"Subject: {subject}\n")
        print(html_body)
        return

    send_email(subject, html_body, REPORT_RECIPIENT)


if __name__ == "__main__":
    main()
