"""Test NBA API with curl_cffi (TLS fingerprint spoofing)"""
from curl_cffi import requests as curl_requests

PROXY = "http://127.0.0.1:7892"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# Test with chrome fingerprint impersonation
url = "https://stats.nba.com/stats/playercareerstats"
params = {"PerMode": "PerGame", "PlayerID": 2544}

for attempt in range(3):
    print(f"Attempt {attempt + 1}...")
    try:
        r = curl_requests.get(
            url,
            params=params,
            headers=HEADERS,
            proxy=PROXY,
            timeout=30,
            impersonate="chrome131"  # This is the key: mimic Chrome's TLS fingerprint
        )
        print(f"  Status: {r.status_code}")
        ct = r.headers.get("Content-Type", "?")
        print(f"  Content-Type: {ct}")

        if "json" in ct or r.text.strip().startswith("{"):
            data = r.json()
            print("  JSON! SUCCESS!")
            for rs in data.get("resultSets", []):
                print(f"    {rs['name']}: {len(rs['rowSet'])} rows")
            break
        else:
            print(f"  Still HTML: {r.text[:100].strip()}")
    except Exception as e:
        print(f"  Error: {e}")
