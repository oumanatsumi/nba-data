"""Answer Q1 and Q2 — handle season_id quirks"""
from sqlalchemy import create_engine, text
import pandas as pd

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL)

pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 150)
pd.set_option('display.max_colwidth', 30)

# ============================================================
# Q1: 2018 NBA Western Conference Finals
#     Season 2017-18, but stored under '2017-20' in DB
# ============================================================
print("=" * 70)
print("Q1: 2018 NBA Western Conference Finals — Game Scores")
print("    (GSW vs HOU, 2017-18 season, May 2018)")
print("=" * 70)

SQL_Q1 = """
SELECT
    g.game_date,
    ht.abbreviation as home_team,
    g.home_score,
    g.away_score,
    at.abbreviation as away_team,
    CASE WHEN g.home_score > g.away_score
         THEN ht.abbreviation || ' Win'
         ELSE at.abbreviation || ' Win'
    END as result
FROM games g
JOIN teams ht ON g.home_team_id = ht.team_id
JOIN teams at ON g.away_team_id = at.team_id
WHERE g.game_type = 'Playoffs'
  AND g.playoff_round = 'Conference Finals'
  AND g.season_id = '2017-20'
  AND ht.conference = 'West'
ORDER BY g.game_date
"""

with engine.connect() as conn:
    df = pd.read_sql(text(SQL_Q1), conn)
    if len(df) > 0:
        print(df.to_string(index=False))
        gsw_wins = sum(1 for _, r in df.iterrows()
                       if ('GSW' in r['result']))
        hou_wins = len(df) - gsw_wins
        print(f"\nSeries result: GSW {gsw_wins}-{hou_wins} HOU (GSW advances to NBA Finals)")
    else:
        print("(No data found)")

# ============================================================
# Q2: 2026 NBA Eastern Conference Finals — Top Scorer Per Game
#     Season 2025-26, May-June 2026
# ============================================================
print("\n" + "=" * 70)
print("Q2: 2026 NBA Eastern Conference Finals — Top Scorer Per Game")
print("    (2025-26 season)")
print("=" * 70)

SQL_Q2 = """
WITH east_games AS (
    SELECT DISTINCT g.game_id, g.game_date, g.home_team_id, g.away_team_id
    FROM games g
    WHERE g.game_type = 'Playoffs'
      AND g.playoff_round = 'Conference Finals'
      AND g.season_id = '2025-26'
),
top_scorers AS (
    SELECT
        eg.game_date,
        p.full_name,
        pgs.points,
        pgs.team_id,
        ROW_NUMBER() OVER (
            PARTITION BY eg.game_id ORDER BY pgs.points DESC
        ) as rn
    FROM east_games eg
    JOIN player_game_stats pgs ON eg.game_id = pgs.game_id
    JOIN players p ON pgs.player_id = p.player_id
    WHERE pgs.points IS NOT NULL
),
game_scores AS (
    SELECT g.game_date, ht.abbreviation as home, g.home_score,
           g.away_score, at.abbreviation as away
    FROM games g
    JOIN teams ht ON g.home_team_id = ht.team_id
    JOIN teams at ON g.away_team_id = at.team_id
    WHERE g.game_type = 'Playoffs'
      AND g.playoff_round = 'Conference Finals'
      AND g.season_id = '2025-26'
)
SELECT
    ts.game_date,
    ts.full_name as top_scorer,
    ts.points,
    gs.home || ' ' || gs.home_score || '-' || gs.away_score || ' ' || gs.away as score
FROM top_scorers ts
JOIN game_scores gs ON ts.game_date = gs.game_date
WHERE ts.rn = 1
ORDER BY ts.game_date
"""

with engine.connect() as conn:
    df = pd.read_sql(text(SQL_Q2), conn)
    if len(df) > 0:
        print(df.to_string(index=False))
    else:
        print("(No data found)")

# ============================================================
# Show SQL
# ============================================================
print("\n\n--- Q1 SQL ---")
print(SQL_Q1)
print("\n\n--- Q2 SQL ---")
print(SQL_Q2)
