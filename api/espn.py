import pandas as pd
from dotenv import load_dotenv
from espn_api.baseball import League

from player_evaluation.utils import get_required_env

load_dotenv()


def fetch_espn_roster_csv(league_id, season, output_path):
    swid = get_required_env("ESPN_SWID")
    espn_s2 = get_required_env("ESPN_S2")

    print(f"Fetching ESPN roster for league {league_id} ({season})...")
    league = League(league_id=league_id, year=season, espn_s2=espn_s2, swid=swid)

    rows = []
    for team in league.teams:
        for player in team.roster:
            rows.append({
                "Player": player.name,
                "Team": player.proTeam,
                "Position": player.position,
                "Status": team.team_name,
            })

    df = pd.DataFrame(rows, columns=["Player", "Team", "Position", "Status"])
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} ESPN roster rows to {output_path}")
    return df
