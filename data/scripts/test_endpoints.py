"""Test various NBA API endpoints"""
import requests

PROXY = {"http": "http://127.0.0.1:7892", "https": "http://127.0.0.1:7892"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json",
}

endpoints = [
    ("CDN team list", "https://cdn.nba.com/static/json/staticData/teamList.json"),
    ("CDN scoreboard", "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"),
    ("Stats - team years", "https://stats.nba.com/stats/commonTeamYears"),
    ("Stats - LeBron career", "https://stats.nba.com/stats/playercareerstats?PerMode=PerGame&PlayerID=2544"),
]

for name, url in endpoints:
    try:
        r = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=15)
        ct = r.headers.get("Content-Type", "?")

        try:
            data = r.json()
            keys = list(data.keys())[:5] if isinstance(data, dict) else "list"
            print(f"[OK] {name}: JSON, keys={keys}")
        except:
            print(f"[NO] {name}: status={r.status_code}, type={ct}, preview={r.text[:80].strip()}")
    except Exception as e:
        print(f"[ERR] {name}: {e}")

print("\nDone!")
