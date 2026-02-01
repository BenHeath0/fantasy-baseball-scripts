# fantasy-baseball-scripts

Collection of scripts for fantasy baseball analysis and draft preparation.

## Setup

For all scripts, make sure you create a venv, install packages, and run the script from its given dir

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Scripts

You can run any script from the root directory using `main.py`:

```bash
# List all available scripts
python3 main.py --list

# Run a script (from root directory)
python3 main.py <script_name> [script_args...]
python3 main.py player_evaluation --draft --league bush

```

## prospects

Script that parses top100 prospect lists and the Fantrax players pool and outputs CSV w/ composite of all rankings. Marks a column to denote if player is avail or not in bush league

### Notes for my future self

- Can i get FV data from everywhere?
- In 2025 i ended up not using composite when making decisions. I instead used the script to made a CSV of fangraphs + baseball prospectus rankings. Then I manually entered rankings for ESPN and The Athletic, and created my own avg of the 4. I did steal the MLB pipeline rankings from composite tho
- Then as draft went on i just used that sheet
- TBH i stopped using the output from the script, but still good to have
- Could change script to grab prospectus and fangraphs from composite... but good to keep as is incase composite cant find in future

## player_evaluation

Script that is used for all my player evaluation needs. Including...

- Who should I keep? (compare my roster with auction calculator projections)
- Who should I draft? (Produce one CSV of rankings for available players from auction calc, athletic rankings, eno rankings, closermonkey, etc)
- Who should I add midseason? (Look at available players and see who is most valuable by fangraphs player rater/auction calc, along with eno rankings etc.)

### Running

Run from the project root directory:

```bash
# Using the main.py runner
python3 main.py player_evaluation --draft --league bush

# Or run as a module directly
python -m player_evaluation.main --draft --league bush

# Keeper evaluation (separate script)
python keeper_evaluation.py --use-cache
```

### TODO

- cleanup the data. right now we dont handle guys w same names

### Files to update each week

- stuffplus.csv
- bush_league_avail_players.csv

## calc-auction-draft-money

I suck at excel, so i made a python script to track how much $$$ im spending during the draft on pitchers and hitters.
