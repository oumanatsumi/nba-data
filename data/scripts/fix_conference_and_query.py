"""Populate team conferences and fix Q2"""
from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine("postgresql://postgres:postgres@localhost:5432/nba_data")
conn = engine.connect()

# Get team info from sumitrodatta's Team Abbrev data
import sys, os
CSV_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'archive-stats')

ta = pd.read_csv(os.path.join(CSV_DIR, 'Team Abbrev.csv'))
ts = pd.read_csv(os.path.join(CSV_DIR, 'Team Summaries.csv'))

# Team Summaries has team names + season data — use latest season for each team
latest = ts.sort_values('season', ascending=False)
# But this doesn't have conference either...

# Instead, get abbr -> team_id mapping from DB
abbr_map = {}
for row in conn.execute(text("SELECT team_id, abbreviation FROM teams")).fetchall():
    abbr_map[row[1].upper()] = row[0]

# NBA conference mapping (hardcoded, reliable)
EAST = {'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DET', 'IND', 'MIA', 'MIL',
        'NYK', 'ORL', 'PHI', 'TOR', 'WAS', 'NJN', 'CHH', 'WSB', 'BUF', 'SYR',
        'ROC', 'FTW', 'BLB', 'AND', 'INJ', 'PIT', 'PRO', 'TRI', 'WAT', 'WSC'}
WEST = {'GSW', 'LAL', 'LAC', 'SAC', 'PHX', 'DAL', 'HOU', 'MEM', 'NOP', 'SAS',
        'DEN', 'UTA', 'MIN', 'OKC', 'POR', 'NOH', 'NOK', 'SEA', 'VAN', 'KCK',
        'SDC', 'ANA', 'DNR', 'INO', 'BAL', 'CHS', 'STL', 'WAS', 'MIL', 'CIN'}

# Update teams
updated = 0
for abbr in EAST:
    tid = abbr_map.get(abbr)
    if tid:
        conn.execute(text("UPDATE teams SET conference = 'East' WHERE team_id = :tid"), {"tid": tid})
        updated += 1

for abbr in WEST:
    tid = abbr_map.get(abbr)
    if tid:
        conn.execute(text("UPDATE teams SET conference = 'West' WHERE team_id = :tid"), {"tid": tid})
        updated += 1

conn.commit()
print(f"Updated {updated} teams with conference info")

# Now populate divisions based on NBA divisions
divisions = {
    'ATL': 'Southeast', 'CHA': 'Southeast', 'MIA': 'Southeast', 'ORL': 'Southeast', 'WAS': 'Southeast',
    'BOS': 'Atlantic', 'BKN': 'Atlantic', 'NYK': 'Atlantic', 'PHI': 'Atlantic', 'TOR': 'Atlantic',
    'CHI': 'Central', 'CLE': 'Central', 'DET': 'Central', 'IND': 'Central', 'MIL': 'Central',
    'DEN': 'Northwest', 'MIN': 'Northwest', 'OKC': 'Northwest', 'POR': 'Northwest', 'UTA': 'Northwest',
    'GSW': 'Pacific', 'LAC': 'Pacific', 'LAL': 'Pacific', 'PHX': 'Pacific', 'SAC': 'Pacific',
    'DAL': 'Southwest', 'HOU': 'Southwest', 'MEM': 'Southwest', 'NOP': 'Southwest', 'SAS': 'Southwest',
}

for abbr, div in divisions.items():
    tid = abbr_map.get(abbr)
    if tid:
        conn.execute(text("UPDATE teams SET division = :div WHERE team_id = :tid"),
                     {"div": div, "tid": tid})

conn.commit()

# Verify
for row in conn.execute(text("SELECT conference, COUNT(*) FROM teams GROUP BY conference")).fetchall():
    print(f"  {row[0] if row[0] else '(empty)'}: {row[1]} teams")

# ============================================================
# Q2 (corrected): East only
# ============================================================
print("\n" + "=" * 70)
print("Q2 (corrected): 2026 Eastern Conference Finals — Top Scorer Per Game")
print("=" * 70)
print("Series: NYK vs CLE (7 games)")
print()

sql = """
WITH east_cf_games AS (
    -- Correctly identify East teams by looking at teams that are NOT in West
    SELECT g.game_id, g.game_date
    FROM games g
    JOIN teams ht ON g.home_team_id = ht.team_id
    WHERE g.game_type = 'Playoffs'
      AND g.playoff_round = 'Conference Finals'
      AND g.season_id = '2025-26'
      AND ht.conference = 'East'
),
top_scorer AS (
    SELECT eg.game_date, p.full_name, pgs.points,
           ROW_NUMBER() OVER (PARTITION BY eg.game_id ORDER BY pgs.points DESC) as rk
    FROM east_cf_games eg
    JOIN player_game_stats pgs ON eg.game_id = pgs.game_id
    JOIN players p ON pgs.player_id = p.player_id
    WHERE pgs.points IS NOT NULL
),
game_score AS (
    SELECT g.game_date, ht.abbreviation || ' ' || g.home_score || '-' || g.away_score || ' ' || at.abbreviation as match_score
    FROM games g
    JOIN teams ht ON g.home_team_id = ht.team_id
    JOIN teams at ON g.away_team_id = at.team_id
    WHERE g.game_type = 'Playoffs'
      AND g.playoff_round = 'Conference Finals'
      AND g.season_id = '2025-26'
      AND ht.conference = 'East'
)
SELECT ts.game_date, ts.full_name as player, ts.points, gs.match_score
FROM top_scorer ts
JOIN game_score gs ON ts.game_date = gs.game_date
WHERE ts.rk = 1
ORDER BY ts.game_date
"""

df = pd.read_sql(text(sql), conn)
print(df.to_string(index=False))

print("\n" + "=" * 70)
print("Q1 (fixed): 2018 Western Conference Finals Scores")
print("=" * 70)
print("Series: GSW vs HOU")
print()

sql_q1 = """
SELECT g.game_date,
       ht.abbreviation || ' ' || g.home_score || '-' || g.away_score || ' ' || at.abbreviation as score,
       CASE WHEN g.home_score > g.away_score THEN ht.abbreviation ELSE at.abbreviation END || ' Win' as result
FROM games g
JOIN teams ht ON g.home_team_id = ht.team_id
JOIN teams at ON g.away_team_id = at.team_id
WHERE g.game_type = 'Playoffs'
  AND g.playoff_round = 'Conference Finals'
  AND g.season_id = '2017-20'
  AND ht.conference = 'West'
ORDER BY g.game_date
"""

df_q1 = pd.read_sql(text(sql_q1), conn)
print(df_q1.to_string(index=False))

gsw_wins = sum(1 for _, r in df_q1.iterrows() if 'GSW' in r['score'] and 'GSW' in r['result'])
hou_wins = len(df_q1) - gsw_wins
print(f"\nSeries: GSW {gsw_wins}-{hou_wins} HOU")

print("\n--- Q2 SQL ---")
print(sql)
print("\n--- Q1 SQL ---")
print(sql_q1)

conn.close()
