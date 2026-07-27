"""One-shot fix all season_id formats"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL, echo=False)
conn = engine.connect()

# ----- Disable FK checks temporarily to clean up -----
conn.execute(text("SET session_replication_role = 'replica'"))

# Fix games that have malformed season_id like "1973-"
conn.execute(text("""
    UPDATE games
    SET season_id = SUBSTRING(season_id, 1, 4) || '-'
        || CASE WHEN LENGTH(SUBSTRING(season_id, 6)) = 0
            THEN LPAD((CAST(SUBSTRING(season_id, 1, 4) AS INT) + 1)::TEXT, 2, '0')
            ELSE SUBSTRING(season_id, 6)
        END
    WHERE season_id LIKE '____-%' AND LENGTH(season_id) < 7
"""))

# Also fix any that look like just 4 digits
conn.execute(text("""
    UPDATE games SET season_id = season_id || '-'
        || LPAD((CAST(season_id AS INT) + 1)::TEXT, 2, '0')
    WHERE season_id ~ '^[0-9]{4}$'
"""))

conn.commit()

# Clean up seasons: delete all, rebuild from actual games
conn.execute(text("DELETE FROM seasons"))
conn.execute(text("""
    INSERT INTO seasons (season_id, start_year, end_year, regular_season_games)
    SELECT DISTINCT
        g.season_id,
        CAST(LEFT(g.season_id, 4) AS INT),
        CAST(LEFT(g.season_id, 4) AS INT) + 1,
        82
    FROM games g
    WHERE g.season_id LIKE '____-__'
    ORDER BY g.season_id
"""))
conn.commit()

# Re-enable FK checks
conn.execute(text("SET session_replication_role = 'origin'"))

# Verify
row = conn.execute(text("SELECT MIN(season_id), MAX(season_id), COUNT(*) FROM seasons")).fetchone()
print(f"Seasons: {row[0]} -> {row[1]} ({row[2]} total)")

# Check for any remaining bad formats
bad_games = conn.execute(text(
    "SELECT season_id, COUNT(*) FROM games WHERE season_id NOT LIKE '____-__' GROUP BY season_id LIMIT 5"
)).fetchall()
bad_seasons = conn.execute(text(
    "SELECT season_id, COUNT(*) FROM seasons WHERE season_id NOT LIKE '____-__' GROUP BY season_id LIMIT 5"
)).fetchall()
print(f"Bad game season_ids: {bad_games if bad_games else 'NONE! All clean.'}")
print(f"Bad season season_ids: {bad_seasons if bad_seasons else 'NONE! All clean.'}")

conn.close()
print("Done!")
