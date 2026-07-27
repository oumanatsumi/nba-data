"""Test basketball-reference scraper with proxy"""
from basketball_reference_web_scraper import client
import pandas as pd

# Test 1: Get player season totals for LeBron
print("=== Test 1: Player Season Totals ===")
try:
    # Try basic function
    stats = client.players_season_totals(season_end_year=2024)
    if stats is not None:
        print(f"  Got data: {type(stats)}")
        if hasattr(stats, 'head'):
            print(f"  Shape: {stats.shape}")
            print(f"  Columns: {list(stats.columns)[:8]}")
            print(stats.head(2))
        else:
            print(f"  Value: {str(stats)[:200]}")
    else:
        print("  Returned None - may need proxy")
except Exception as e:
    print(f"  Error: {e}")
    print("  BBR scraper needs proxy. Trying with requests+proxy...")

print("\n=== Test 2: Direct web access to basketball-reference.com ===")
import requests
PROXY = {"http": "http://127.0.0.1:7892", "https": "http://127.0.0.1:7892"}

url = "https://www.basketball-reference.com/leagues/NBA_2024_totals.html"
try:
    r = requests.get(url, proxies=PROXY, timeout=15)
    print(f"  Status: {r.status_code}")
    print(f"  Content length: {len(r.text)}")
    if "LeBron" in r.text:
        print("  Contains player data : OK")
    else:
        print("  Warning: may be blocked")
except Exception as e:
    print(f"  Failed: {e}")
