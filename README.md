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
