"""Daily fantasy baseball email report.

Lists today's MLB games (with rostered SPs flagged) and yesterday's box-score
lines for every player on the user's fantasy rosters.

Usage:
    python -m daily_report.main                  # send the email
    python -m daily_report.main --dry-run        # print HTML to stdout
    python -m daily_report.main --date 2026-04-26  # override "today"
"""

import argparse
import os
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
except ImportError:  # graceful fallback if python-dotenv is missing
    def load_dotenv(*_args, **_kwargs):
        return False

from .config import REPORT_RECIPIENT
from .email_builder import build_html_email
from .email_sender import send_email
from .rosters import load_all_rosters
from .schedule import get_today_schedule_with_roster_flags
from .yesterday_stats import get_yesterday_stats_for_rosters


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Daily fantasy baseball email report")
    parser.add_argument(
        "--date",
        default=None,
        help="Override 'today' (YYYY-MM-DD). Yesterday is computed from this.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the HTML body to stdout instead of sending the email.",
    )
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
    subject, html_body = build_html_email(
        games, hitters, pitchers, today_str, yesterday_str
    )

    if args.dry_run:
        print(f"Subject: {subject}\n")
        print(html_body)
        return

    send_email(subject, html_body, REPORT_RECIPIENT)


if __name__ == "__main__":
    main()
