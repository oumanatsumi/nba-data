"""Quick diagnostic for import issues"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from dotenv import load_dotenv; load_dotenv()
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'nba_data')}"
)
engine = create_engine(DB_URL)
session = Session(engine)

# Count players
total_active = session.execute(text(
    "SELECT COUNT(*) FROM players WHERE active = TRUE"
)).fetchone()[0]
print(f"Active players: {total_active}")

# Test first 3 players
from nba_api.stats.endpoints import playercareerstats

rows = session.execute(text(
    "SELECT player_id FROM players WHERE active = TRUE ORDER BY player_id LIMIT 3"
)).fetchall()
print(f"Testing first 3 players: {[r[0] for r in rows]}")

for (pid,) in rows:
    existing = session.execute(text(
        "SELECT COUNT(*) FROM player_season_stats WHERE player_id = :pid"
    ), {"pid": pid}).fetchone()[0]
    print(f"  Player {pid}: {existing} existing season rows")

    try:
        career = playercareerstats.PlayerCareerStats(player_id=pid)
        df = career.get_data_frames()[0]
        print(f"    API returned {len(df)} season rows")
        if len(df) > 0:
            cols = list(df.columns)[:8]
            print(f"    Columns: {cols}")
        time.sleep(0.7)
    except Exception as e:
        print(f"    ERROR: {e}")

session.close()
print("Done!")
