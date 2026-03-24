# Fantasy Baseball Player Evaluation Tool

A tool for evaluating fantasy baseball players using projection data from Fangraphs and other sources.

## Project Structure

```
player_evaluation/
├── main.py              # Main entry point
├── config.py            # Configuration constants and settings
├── utils.py             # Utility functions (name normalization, etc.)
├── data_fetchers.py     # Data fetching from Fangraphs APIs and files
├── data_processors.py   # Data cleaning and augmentation
├── input_data/          # Local CSV files (NFBC ADP, CloserMonkey, etc.)
├── output/              # Generated CSV files and Google Sheets token
└── README.md            # This file
```

## Usage

Run from the project root via `main.py` or as a module:

```bash
# Generate player rankings for Bush League
python -m player_evaluation.main --draft --league bush

# Generate rankings for NFBC league using cached data
python -m player_evaluation.main --draft --league nfbc --use-cache

# Sort by a specific projection system
python -m player_evaluation.main --sort steamer

# Skip Google Sheets upload
python -m player_evaluation.main --no-google
```

### CLI Flags

| Flag          | Description                                       | Default |
| ------------- | ------------------------------------------------- | ------- |
| `--draft`     | Add additional data sources for draft preparation | off     |
| `--league`    | League type: `bush`, `nfbc`, `yahoo`, `espn`      | `bush`  |
| `--use-cache` | Use cached data instead of fetching from APIs     | off     |
| `--sort`      | Column to sort results by                         | `atc`   |
| `--no-google` | Skip uploading to Google Sheets                   | off     |

## Data Sources

### Fetched from Fangraphs APIs

- **Auction Values**: From multiple projection systems (steamer, thebatx, oopsy, atc)
- **Stuff+ Data**: Pitcher performance metrics
- **Statcast Data**: Advanced batting metrics (EV, Barrel%, HardHit%, xwOBA, etc.)

### Local CSV Files

- **NFBC ADP** (`nfbc_adp.tsv`): Average draft position data
- **CloserMonkey** (`closermonkey.csv`): Reliever rankings
- **Eno Rankings** (`eno_rankings.csv`): Pitcher-specific rankings
  - Most up-to-date version: https://docs.google.com/spreadsheets/d/1daR9RNic3GcfDb6FLsm2OZRBS8VkqucOqHSnIS7ru5c/edit?gid=543684644#gid=543684644
- **Statcast Batters** (`statcast_batters.csv`): Fallback Statcast data
- **Stuff+** (`stuffplus.csv`, `lastmonth_stuffplus.csv`): Fallback Stuff+ data
- **Bush League Roster/Available** (`bush_league_roster.csv`, `bush_league_players.csv`)

## Configuration

Edit `config.py` to customize:

- Projection systems (`PROJECTION_SYSTEMS`)
- League settings (teams, budget, positions)
- Fangraphs API endpoints and leaderboard mappings
- File paths for input/output
- Google Sheets spreadsheet IDs and tab names

## Output

Results are saved to `output/` as dated CSV files (e.g., `2026-03-05_hitters.csv`, `2026-03-05_pitchers.csv`) and optionally uploaded to Google Sheets.
