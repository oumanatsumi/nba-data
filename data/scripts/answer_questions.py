"""Answer Q1 and Q2 directly"""
from sqlalchemy import create_engine, text
import pandas as pd

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL)

pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 150)
pd.set_option('display.max_colwidth', 30)

# ============================================================
# Q1: 2018 West Finals
# ============================================================
print("=" * 70)
print("Q1: 2018 NBA Western Conference Finals — Game Scores")
print("=" * 70)

# First, what data do we actually have for 2017-18 playoffs?
with engine.connect() as conn:
    r = conn.execute(text(
        "SELECT playoff_round, COUNT(*) FROM games "
        "WHERE season_id = '2017-18' AND game_type = 'Playoffs' "
        "GROUP BY playoff_round"
    )).fetchall()
    print("2017-18 playoff rounds:", r)

    r2 = conn.execute(text(
        "SELECT COUNT(*) FROM games "
        "WHERE season_id = '2017-18' AND game_type = 'Playoffs'"
    )).fetchone()
    print(f"Total 2017-18 playoff games: {r2[0]}")

    # Try different season IDs
    print("\nTrying adjacent seasons:")
    for sid in ['2017-18', '2017-20', '2018-19']:
        cnt = conn.execute(text(
            "SELECT COUNT(*) FROM games WHERE season_id = :s AND game_type = 'Playoffs'"
        ), {"s": sid}).fetchone()[0]
        print(f"  {sid}: {cnt} playoff games")

# Check which season 2018 WCF would be in
print("\nSearching for GSW-HOU playoff games around 2018:")
with engine.connect() as conn:
    r = conn.execute(text("""
        SELECT g.season_id, g.game_date, ht.abbreviation as home, g.home_score,
               g.away_score, at.abbreviation as away, g.playoff_round
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams at ON g.away_team_id = at.team_id
        WHERE g.game_type = 'Playoffs'
          AND g.playoff_round LIKE '%Conf%'
          AND (ht.abbreviation = 'GSW' OR at.abbreviation = 'GSW')
          AND (ht.abbreviation = 'HOU' OR at.abbreviation = 'HOU')
        ORDER BY g.game_date
    """)).fetchall()
    if r:
        for row in r:
            print(f"  {row[0]} | {row[1]} | {row[2]} {row[3]}-{row[4]} {row[5]} | {row[6]}")
    else:
        print("  No results found! Let me find any GSW-HOU playoff games...")
        r2 = conn.execute(text("""
            SELECT g.season_id, g.game_date, ht.abbreviation, at.abbreviation, g.playoff_round, g.game_type
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams at ON g.away_team_id = at.team_id
            WHERE g.game_type = 'Playoffs'
              AND (ht.abbreviation = 'HOU' AND at.abbreviation = 'GSW')
            ORDER BY g.game_date
            LIMIT 20
        """)).fetchall()
        for row in r2:
            print(f"  {row[0]} | {row[1]} | {row[2]}-{row[3]} | round={row[4]} | {row[5]}")
