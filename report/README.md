# report

Daily and weekly fantasy baseball email reports. Pulls box scores from the MLB Stats API, joins them against your fantasy rosters, and sends an HTML email via Gmail SMTP.

Both reports run automatically via GitHub Actions (`.github/workflows/daily-report.yml`, `weekly-report.yml`), April through September.

## Reports

- **`report.daily`** — today's MLB schedule (with rostered SPs flagged) and yesterday's box-score lines for every rostered player. Counting stats only (per-game ratio stats are unreliable from the MLB API).
- **`report.weekly`** — aggregated stats for the previous Mon–Sun week, including AVG/OBP/SLG/ERA/WHIP. Intended to run Monday mornings.

## Roster sources

Configured in `report/config.py`:

- **NFBC** — `input_data/rosters/nfbc_roster.csv`
- **Bush League** — `input_data/rosters/bush_league_players.csv`, filtered by the `BUSH_MANAGER_CODE` env var (your manager code in the `Status` column)

## Required env vars

| Var | Purpose |
|---|---|
| `GMAIL_USER` | Gmail address used to send the report |
| `GMAIL_APP_PASSWORD` | Gmail [app password](https://support.google.com/accounts/answer/185833) (not your normal password) |
| `BUSH_MANAGER_CODE` | Your manager code in the Bush League roster CSV (e.g. `TWN`) |

For local runs, put these in a `.env` file at the project root — both scripts call `load_dotenv()`.

## Running locally

From the project root, with the venv active:

```bash
# dry run — print HTML to stdout, do not send
python -m report.daily --dry-run
python -m report.weekly --dry-run

# send the email for real
python -m report.daily
python -m report.weekly

# override the date
python -m report.daily --date 2026-04-26      # treat this as "today"
python -m report.weekly --end 2026-04-26      # week's end date (Sunday, inclusive)
```

The recipient is hardcoded to `REPORT_RECIPIENT` in `report/config.py`.

## GitHub Actions

The workflows pass `GMAIL_USER`, `GMAIL_APP_PASSWORD`, and `BUSH_MANAGER_CODE` from repository secrets. Schedules:

- **daily** — `0 10 * 4-9 *` (6 AM EDT, daily, April–September)
- **weekly** — `0 10 * 4-9 1` (6 AM EDT, Mondays, April–September)

Both can also be triggered manually from the Actions tab via `workflow_dispatch`.
