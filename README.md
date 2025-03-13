# fantasy-baseball-scripts

For all scripts, make sure you create a venv, install packages, and run the script from its given dir

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## rookie-draft

Script that parses top100 prospect lists and the Fantrax players pool, to see what top prospects are available to draft

make sure you are in `/rookie-draft` dir to run script

```
python rookie_draft_help.py
```

### Notes for my future self

- Will need to find a new composite sheet
  - But tbh, i dont know how much i trust all the data sources
- In 2025 i ended up not using composite when making decisions. I instead used the script to made a CSV of fangraphs + baseball prospectus rankings. Then I manually entered rankings for ESPN and The Athletic, and created my own avg of the 4.
- Then as draft went on i just used that sheet
- TBH i stopped using the output from the script, but still good to have

## keeper-evaluation

Two different scripts for helping with keeper evaluation

### combine_auction_values.py

Fangraphs auction calculator splits between Hitters and Pitchers. This script combines them into one CSV

```
python combine_auction_values.py
```

### calc_keeper_recommendations

Script that looks at players on my roster (and their cost to keep) and compares to value from fangraphs auction calculator

```
python calc_keeper_recommendations
```
