"""Diagnose Q2 conference filtering issue"""
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@localhost:5432/nba_data")
conn = engine.connect()

# Check conference data
print("=== Teams in 2025-26 Conference Finals ===")
rows = conn.execute(text("""
    SELECT DISTINCT ht.team_id, ht.full_name, ht.conference,
           at.team_id, at.full_name, at.conference
    FROM games g
    JOIN teams ht ON g.home_team_id = ht.team_id
    JOIN teams at ON g.away_team_id = at.team_id
    WHERE g.season_id = '2025-26'
      AND g.playoff_round = 'Conference Finals'
""")).fetchall()
for r in rows:
    print(f"  {r[1]} (conf={r[2]}) vs {r[4]} (conf={r[5]})")

# Check: are conferences NULL?
print("\n=== Teams with NULL conference ===")
rows = conn.execute(text("""
    SELECT team_id, full_name, conference, is_active
    FROM teams
    WHERE conference IS NULL AND team_id IN (
        SELECT DISTINCT home_team_id FROM games
        WHERE season_id = '2025-26' AND playoff_round = 'Conference Finals'
        UNION
        SELECT DISTINCT away_team_id FROM games
        WHERE season_id = '2025-26' AND playoff_round = 'Conference Finals'
    )
""")).fetchall()
for r in rows:
    print(f"  {r}")

print("\n=== All teams in 2025-26 Finals with conference info ===")
rows = conn.execute(text("""
    SELECT g.game_date, ht.abbreviation || ' vs ' || at.abbreviation as matchup,
           ht.conference as home_conf, at.conference as away_conf
    FROM games g
    JOIN teams ht ON g.home_team_id = ht.team_id
    JOIN teams at ON g.away_team_id = at.team_id
    WHERE g.season_id = '2025-26'
      AND g.playoff_round = 'Conference Finals'
    ORDER BY g.game_date
""")).fetchall()
for r in rows:
    print(f"  {r[0]} | {r[1]:25s} | home_conf={r[2]} | away_conf={r[3]}")

conn.close()
