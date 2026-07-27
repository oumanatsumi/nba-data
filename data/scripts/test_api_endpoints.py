"""Quick API test"""
import requests, json
base = "http://localhost:8000"

# Test health
r = requests.get(f"{base}/health")
print("Health:", r.json())

# Test players search
r = requests.get(f"{base}/api/v1/players", params={"search": "LeBron", "limit": 2})
d = r.json()
print(f"\nPlayers search: {d['total']} matches")
for p in d["players"]:
    print(f"  {p['full_name']} (ID: {p['player_id']})")

# Test player stats
pid = d["players"][0]["player_id"]
r = requests.get(f"{base}/api/v1/players/{pid}/stats", params={"season_id": "2023-24"})
stats = r.json()
if stats:
    s = stats[0]
    print(f"\nLeBron 2023-24: {s['points_per_game']} PPG, {s['assists_per_game']} APG, PER={s['player_efficiency_rating']}")

# Test teams
r = requests.get(f"{base}/api/v1/teams")
teams = r.json()
print(f"\nTeams: {len(teams)} total")
for t in teams[:3]:
    print(f"  {t['full_name']} ({t['abbreviation']})")

# Test games
r = requests.get(f"{base}/api/v1/games", params={"game_type": "Playoffs", "season_id": "2025-26", "limit": 3})
games = r.json()
print(f"\nPlayoff games 2025-26: {games['total']} total")
for g in games["games"][:3]:
    print(f"  {g['game_date']} | {g['home_team']} {g['home_score']}-{g['away_score']} {g['away_team']} | {g.get('playoff_round','')}")

# Test boxscore
if games["games"]:
    gid = games["games"][0]["game_id"]
    r = requests.get(f"{base}/api/v1/games/{gid}/boxscore")
    box = r.json()
    top = box["home_players"][:3] if box.get("home_players") else []
    print(f"\nBoxscore game {gid}:")
    for p in top:
        print(f"  {p['full_name']}: {p['points']} PTS, {p['rebounds_total']} REB, {p['assists']} AST")

# Test stats leaders
r = requests.get(f"{base}/api/v1/stats/leaders", params={"season_id": "2023-24", "stat": "player_efficiency_rating", "limit": 5})
leaders = r.json()
print(f"\nPER Leaders 2023-24:")
for l in leaders:
    print(f"  {l['player']}: {l['value']}")

# Test playoff bracket
r = requests.get(f"{base}/api/v1/playoffs/bracket", params={"season_id": "2025-26"})
bracket = r.json()
print(f"\nPlayoff bracket 2025-26:")
for round_name, series_list in bracket.get("bracket", {}).items():
    print(f"  {round_name}:")
    for s in series_list:
        print(f"    {s['home_team']['abbreviation']} vs {s['away_team']['abbreviation']} — {s['score']} Winner: {s['winner']}")

# Test player comparison
r = requests.get(f"{base}/api/v1/stats/compare", params={"player_ids": "2544,203999", "season_id": "2023-24"})
comp = r.json()
print(f"\nPlayer comparison ({comp['season']}):")
for p in comp["players"]:
    print(f"  {p['name']}: {p['points_per_game']} PPG, PER={p['player_efficiency_rating']}, WS={p['win_shares']}")

# Test playoff matchups
r = requests.get(f"{base}/api/v1/playoffs/matchups", params={"team1": "GSW", "team2": "HOU"})
mu = r.json()
print(f"\nGSW vs HOU historical matchups: {mu['total_matchups']} total")

print("\n✅ API fully operational!")
