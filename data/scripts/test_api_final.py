"""Test all API endpoints"""
import requests, json
base = "http://localhost:8000"

tests = [
    ("Health", "/health", None),
    ("Players search", "/api/v1/players", {"search": "LeBron", "limit": 2}),
    ("Teams", "/api/v1/teams", None),
    ("Games", "/api/v1/games", {"game_type": "Playoffs", "season_id": "2025-26", "limit": 2}),
    ("Stats leaders", "/api/v1/stats/leaders", {"season_id": "2023-24", "stat": "points_per_game", "limit": 3}),
    ("Playoff bracket", "/api/v1/playoffs/bracket", {"season_id": "2025-26"}),
    ("Player stats", "/api/v1/players/2544/stats", {"season_id": "2023-24"}),
    ("Team roster", "/api/v1/teams/1610612744/roster", {"season_id": "2023-24"}),
]

for name, path, params in tests:
    try:
        r = requests.get(base + path, params=params, timeout=10)
        if r.status_code == 200:
            j = r.json()
            if isinstance(j, dict) and "total" in j:
                print(f"✅ {name:15s} — {j['total']} results")
            elif isinstance(j, list):
                print(f"✅ {name:15s} — {len(j)} items")
            elif isinstance(j, dict) and "bracket" in j:
                cnt = sum(len(v) for v in j["bracket"].values())
                print(f"✅ {name:15s} — {cnt} series in bracket")
            else:
                print(f"✅ {name:15s} — {json.dumps(j)[:80]}")
        else:
            print(f"❌ {name:15s} — HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"❌ {name:15s} — {e}")

print("\nDone! Open http://localhost:8000/docs for Swagger UI")
