"""Data validation + answer 2 questions"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from sqlalchemy import create_engine, text
import pandas as pd

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL, echo=False)

pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 120)
pd.set_option('display.max_colwidth', 30)

print("=" * 70)
print("DATA VALIDATION")
print("=" * 70)

# Quick checks
checks = [
    ("Total seasons", "SELECT COUNT(*) FROM seasons"),
    ("Season range", "SELECT MIN(season_id), MAX(season_id) FROM seasons"),
    ("Total players", "SELECT COUNT(*) FROM players"),
    ("Total teams", "SELECT COUNT(*) FROM teams"),
    ("Total games", "SELECT COUNT(*) FROM games"),
    ("Regular Season", "SELECT COUNT(*) FROM games WHERE game_type='Regular Season'"),
    ("Playoffs", "SELECT COUNT(*) FROM games WHERE game_type='Playoffs'"),
    ("All-Star", "SELECT COUNT(*) FROM games WHERE game_type='All-Star'"),
    ("Game stats", "SELECT COUNT(*) FROM player_game_stats"),
    ("Season stats", "SELECT COUNT(*) FROM player_season_stats"),
    ("With PER", "SELECT COUNT(*) FROM player_season_stats WHERE player_efficiency_rating IS NOT NULL"),
    ("With TS%", "SELECT COUNT(*) FROM player_season_stats WHERE true_shooting_pct IS NOT NULL"),
    ("With WS", "SELECT COUNT(*) FROM player_season_stats WHERE win_shares IS NOT NULL"),
    ("With BPM/VORP", "SELECT COUNT(*) FROM player_season_stats WHERE box_plus_minus IS NOT NULL"),
    ("Playoff series", "SELECT COUNT(*) FROM playoff_series"),
    ("Games w/ round label", "SELECT COUNT(*) FROM games WHERE playoff_round IS NOT NULL"),
]

for name, sql in checks:
    with engine.connect() as conn:
        row = conn.execute(text(sql)).fetchone()
        print(f"  {name:25s}: {row[0] if len(row)==1 else row}")

# ============================================================
# Q1: 2018 Western Conference Finals (2017-18 season)
# ============================================================
print("\n" + "=" * 70)
print("Q1: 2018 NBA Western Conference Finals Scores")
print("=" * 70)

sql1 = """
SELECT
    g.game_date,
    ht.abbreviation as home_team,
    g.home_score,
    g.away_score,
    at.abbreviation as away_team,
    CASE WHEN g.home_score > g.away_score THEN ht.abbreviation ELSE at.abbreviation END as winner
FROM games g
JOIN teams ht ON g.home_team_id = ht.team_id
JOIN teams at ON g.away_team_id = at.team_id
WHERE g.game_type = 'Playoffs'
  AND g.playoff_round = 'Conference Finals'
  AND g.season_id = '2017-18'
  AND ht.conference = 'West'
ORDER BY g.game_date
"""

with engine.connect() as conn:
    df = pd.read_sql(text(sql1), conn)
    print(df.to_string(index=False))

# ============================================================
# Q2: 2026 Eastern Conference Finals Top Scorer Per Game
# ============================================================
print("\n" + "=" * 70)
print("Q2: 2026 NBA Eastern Conference Finals - Top Scorer Per Game")
print("=" * 70)

sql2 = """
WITH east_games AS (
    SELECT DISTINCT g.game_id, g.game_date
    FROM games g
    JOIN teams ht ON g.home_team_id = ht.team_id
    WHERE g.game_type = 'Playoffs'
      AND g.playoff_round = 'Conference Finals'
      AND g.season_id = '2025-26'
      AND ht.conference = 'East'
),
top_scorers AS (
    SELECT
        eg.game_date,
        p.full_name,
        pgs.points,
        ROW_NUMBER() OVER (PARTITION BY eg.game_id ORDER BY pgs.points DESC) as rn
    FROM east_games eg
    JOIN player_game_stats pgs ON eg.game_id = pgs.game_id
    JOIN players p ON pgs.player_id = p.player_id
    WHERE pgs.points IS NOT NULL
)
SELECT game_date, full_name, points
FROM top_scorers
WHERE rn = 1
ORDER BY game_date
"""

with engine.connect() as conn:
    df = pd.read_sql(text(sql2), conn)
    print(df.to_string(index=False))

print("\n" + "=" * 70)
print("Validation complete!")
print("=" * 70)

# Also show the SQL
print("\n\n--- SQL for Q1 ---")
print(sql1)
print("\n\n--- SQL for Q2 ---")
print(sql2)
