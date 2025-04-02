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

### Notes for my future self

- Can i get FV data from everywhere?
- In 2025 i ended up not using composite when making decisions. I instead used the script to made a CSV of fangraphs + baseball prospectus rankings. Then I manually entered rankings for ESPN and The Athletic, and created my own avg of the 4. I did steal the MLB pipeline rankings from composite tho
- Then as draft went on i just used that sheet
- TBH i stopped using the output from the script, but still good to have
- Could change script to grab prospectus and fangraphs from composite... but good to keep as is incase composite cant find in future

## keeper-evaluation

Script that looks at players on my roster (and their cost to keep) and compares to value from fangraphs auction calculator. Script fetches fresh data from fangraphs API

## calc-auction-draft-money

I suck at excel, so i made a python script to track how much $$$ im spending during the draft on pitchers and hitters.

## player-master-list

In years past ive tracked draft stuff across the athletic cheat sheet, enos rankings, and other stuff. no more! all in one place.

Uses keeper-evaluation to have up to date fangraphs auction calculations... maybe move that API stuff to a helper.

Make sure auction calc and cheat sheet are set up for each specific league.

## find-common-players

Something often that happens is wanting to take a list of players from some article, and see who is available on waivers. Its literally like 4 lines of code but hey git is free
