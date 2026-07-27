"""Test NBA API through proxy on port 7892"""
import requests

PROXY = "http://127.0.0.1:7892"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Host": "stats.nba.com",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}

# Test 1: Basic proxy connectivity
print("=== Test 1: Proxy Connectivity ===")
try:
    r = requests.get("https://www.google.com", proxies={"http": PROXY, "https": PROXY}, timeout=10)
    print(f"Google via proxy: {r.status_code}")
except Exception as e:
    print(f"Google via proxy FAILED: {e}")

# Test 2: NBA Stats API through proxy
print("\n=== Test 2: NBA Stats API via Proxy ===")
session = requests.Session()
session.headers.update(HEADERS)

url = "https://stats.nba.com/stats/playercareerstats"
params = {"PerMode": "PerGame", "PlayerID": 2544}

try:
    r = session.get(url, params=params, proxies={"http": PROXY, "https": PROXY}, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type', '?')}")

    try:
        data = r.json()
        result_sets = data.get("resultSets", [])
        for rs in result_sets:
            print(f"  {rs['name']}: {len(rs['rowSet'])} rows x {len(rs['headers'])} cols")
        print("SUCCESS! Proxy works for NBA API!")
    except:
        print(f"NOT JSON: {r.text[:200]}...")
except Exception as e:
    print(f"ERROR: {e}")
