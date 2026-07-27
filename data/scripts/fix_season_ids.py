"""Fix season_id format across all tables"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL, echo=False)
conn = engine.connect()

# Step 1: Fix player_season_stats
r1 = conn.execute(text("""
    UPDATE player_season_stats
    SET season_id = SUBSTRING(season_id, 2, 4) || '-' || SUBSTRING(season_id, 6, 2)
    WHERE season_id ~ '^[0-9]{5}$'
"""))
conn.commit()
print(f"player_season_stats: {r1.rowcount} rows fixed")

# Step 2: Fix team_season_stats
r2 = conn.execute(text("""
    UPDATE team_season_stats
    SET season_id = SUBSTRING(season_id, 2, 4) || '-' || SUBSTRING(season_id, 6, 2)
    WHERE season_id ~ '^[0-9]{5}$'
"""))
conn.commit()
print(f"team_season_stats: {r2.rowcount} rows fixed")

# Step 3: Fix playoff_series
r3 = conn.execute(text("""
    UPDATE playoff_series
    SET season_id = SUBSTRING(season_id, 2, 4) || '-' || SUBSTRING(season_id, 6, 2)
    WHERE season_id ~ '^[0-9]{5}$'
"""))
conn.commit()
print(f"playoff_series: {r3.rowcount} rows fixed")

# Step 4: Remove malformed season ids (orphaned 5-digit)
conn.execute(text("""
    DELETE FROM seasons WHERE season_id ~ '^[0-9]{5}$'
"""))
conn.commit()
print("Removed orphaned 5-digit season rows")

# Step 5: Verify
row = conn.execute(text("""
    SELECT MIN(season_id), MAX(season_id), COUNT(*) FROM seasons
""")).fetchone()
print(f"\nSeasons: {row[0]} to {row[1]} ({row[2]} total)")

# Check remaining bad formats
bad = conn.execute(text(
    "SELECT season_id FROM seasons WHERE season_id NOT LIKE '____-__' LIMIT 10"
)).fetchall()
if bad:
    print(f"Still malformed: {[b[0] for b in bad]}")
else:
    print("All season_ids are clean YYYY-YY format!")

conn.close()
print("Done!")
