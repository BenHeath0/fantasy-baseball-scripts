import json
import os
import time
import webbrowser

import pandas as pd
import requests
from dotenv import load_dotenv
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

from player_evaluation.config import YAHOO_OAUTH_TOKEN_FILE
from player_evaluation.utils import get_required_env

load_dotenv()

YAHOO_AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
YAHOO_TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
YAHOO_REDIRECT_URI = "https://localhost"


def bootstrap_yahoo_token(token_path=YAHOO_OAUTH_TOKEN_FILE):
    # yahoo-oauth's built-in flow hardcodes redirect_uri=oob which yahoo deprecated;
    # we run the auth dance manually with https://localhost and write a token file
    # the library can refresh from going forward.
    client_id = get_required_env("YAHOO_CLIENT_ID")
    client_secret = get_required_env("YAHOO_CLIENT_SECRET")

    auth_url = (
        f"{YAHOO_AUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={YAHOO_REDIRECT_URI}"
        f"&response_type=code"
    )
    print("Opening Yahoo authorization URL in your browser:")
    print(auth_url)
    print()
    print("1. Click 'Agree'.")
    print(f"2. Your browser will be redirected to {YAHOO_REDIRECT_URI}/?code=XXXXX (the page will fail to load — that's fine).")
    print("3. Copy the value after 'code=' from the URL bar and paste it below.")
    print()
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    code = input("Paste the code value here: ").strip()
    if not code:
        raise RuntimeError("No code provided")

    resp = requests.post(
        YAHOO_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": YAHOO_REDIRECT_URI,
            "code": code,
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    payload = resp.json()

    token_data = {
        "access_token": payload["access_token"],
        "consumer_key": client_id,
        "consumer_secret": client_secret,
        "guid": payload.get("xoauth_yahoo_guid"),
        "refresh_token": payload["refresh_token"],
        "token_time": time.time(),
        "token_type": payload.get("token_type", "bearer"),
    }
    os.makedirs(os.path.dirname(token_path) or ".", exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)
    print(f"Wrote Yahoo OAuth token file: {token_path}")


def yahoo_oauth_login(token_path=YAHOO_OAUTH_TOKEN_FILE):
    if not os.path.exists(token_path):
        raise RuntimeError(
            f"Yahoo OAuth token file not found at {token_path}. "
            "Run bootstrap_yahoo_token() once to create it."
        )
    sc = OAuth2(None, None, from_file=token_path)
    if not sc.token_is_valid():
        sc.refresh_access_token()
    return sc


def fetch_yahoo_roster_csv(league_key, season, output_path):
    print(f"Fetching Yahoo roster for league {league_key} ({season})...")
    sc = yahoo_oauth_login()
    game = yfa.Game(sc, "mlb")
    league = game.to_league(league_key)

    rows = []
    for team_info in league.teams().values():
        team_key = team_info["team_key"]
        team_name = team_info.get("name", "")

        team = league.to_team(team_key)
        for player in team.roster():
            rows.append({
                "Player": player.get("name"),
                "Team": player.get("editorial_team_abbr", ""),
                "Position": player.get("eligible_positions", player.get("position_type", "")),
                "Status": team_name,
            })

    df = pd.DataFrame(rows, columns=["Player", "Team", "Position", "Status"])
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} Yahoo roster rows to {output_path}")
    return df
