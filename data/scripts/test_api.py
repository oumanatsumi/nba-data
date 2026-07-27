"""Quick fix: test with proper headers and timeout"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from nba_api.stats.endpoints import playercareerstats

# Set custom headers that work with stats.nba.com
from nba_api.stats.static import players as p_static
all_players = p_static.get_players()
print(f"Static data works: {len(all_players)} players")

# Test with specific player
pid = 2544  # LeBron
for attempt in range(3):
    try:
        print(f"Attempt {attempt+1}...")
        career = playercareerstats.PlayerCareerStats(
            player_id=pid,
            timeout=60  # longer timeout
        )
        df = career.get_data_frames()[0]
        print(f"SUCCESS: {len(df)} seasons")
        print(df.head(2))
        break
    except Exception as e:
        print(f"  Failed: {e}")
        time.sleep(5)
