"""Test NBA API with proper anti-bot headers"""
import time
import requests

# These headers simulate a real browser visiting nba.com
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Host": "stats.nba.com",
    "Origin": "https://www.nba.com",
    "Pragma": "no-cache",
    "Referer": "https://www.nba.com/",
    "Sec-Ch-Ua": '"Not?A_Brand";v="99", "Chromium";v="130"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}

session = requests.Session()
session.headers.update(HEADERS)

# Try LeBron career stats
url = "https://stats.nba.com/stats/playercareerstats"
params = {"PerMode": "PerGame", "PlayerID": 2544}

for attempt in range(3):
    print(f"Attempt {attempt + 1}...")
    try:
        r = session.get(url, params=params, timeout=30)
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('Content-Type', '?')}")

        try:
            data = r.json()
            result_sets = data.get("resultSets", [])
            for rs in result_sets:
                print(f"  ResultSet '{rs['name']}': {len(rs['rowSet'])} rows x {len(rs['headers'])} cols")
            print("SUCCESS!")
            break
        except:
            print(f"  Response is not JSON: {r.text[:150]}...")
    except Exception as e:
        print(f"  Error: {e}")

    time.sleep(3)
