"""
Fill playoff_series table from Games.csv gameLabel data
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL, echo=False)
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'archive-player')


def _season_id_from_date(dt):
    """Derive season_id from date"""
    from datetime import datetime
    try:
        d = datetime.strptime(str(dt)[:10], '%Y-%m-%d')
        year = d.year
        month = d.month
        if month >= 10:
            return f"{year}-{str(year+1)[-2:]}"
        else:
            return f"{year-1}-{str(year)[-2:]}"
    except:
        return None


def main():
    print("Loading Games.csv...")
    gf = pd.read_csv(os.path.join(DATA_DIR, 'Games.csv'), low_memory=False)
    po = gf[gf['gameType'] == 'Playoffs'].copy()
    print(f"  Playoff games: {len(po):,}")

    # Map round labels to standardized names
    label_to_round = {}
    for lbl in po['gameLabel'].dropna().unique():
        lbl_clean = str(lbl).replace(' - ', ' ').strip()
        if 'First Round' in lbl_clean:
            label_to_round[lbl] = 'First Round'
        elif 'Semifinals' in lbl_clean or 'Semis' in lbl_clean:
            label_to_round[lbl] = 'Conference Semifinals'
        elif 'Finals' in lbl_clean and ('Conf' in lbl_clean or 'East' in lbl_clean or 'West' in lbl_clean):
            label_to_round[lbl] = 'Conference Finals'
        elif 'NBA Finals' in lbl_clean or ('Finals' in lbl_clean and 'Conf' not in lbl_clean):
            label_to_round[lbl] = 'NBA Finals'
        elif 'Play-In' in lbl_clean:
            label_to_round[lbl] = 'Play-In'
        else:
            label_to_round[lbl] = lbl_clean

    # Build series groups: (season, round, matchup) -> [(game_id, score)]
    session = Session(engine)

    # First, update playoff_round in games table
    print("  Updating playoff_round in games...")
    updated = 0
    for _, row in po.iterrows():
        gid = int(row['gameId'])
        round_name = label_to_round.get(row.get('gameLabel'), None)
        if round_name:
            r = session.execute(text(
                "UPDATE games SET playoff_round = :pr WHERE game_id = :gid"
            ), {"pr": round_name, "gid": gid})
            updated += r.rowcount
    print(f"    Updated {updated:,} games with round info")

    session.commit()

    # Now derive series from games
    print("  Deriving playoff series...")
    result = session.execute(text("""
        INSERT INTO playoff_series (
            season_id, round, series_number, home_team_id, away_team_id,
            home_team_wins, away_team_wins, winner_team_id
        )
        WITH series_games AS (
            SELECT
                season_id,
                playoff_round,
                home_team_id,
                away_team_id,
                SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) as home_wins,
                SUM(CASE WHEN away_score > home_score THEN 1 ELSE 0 END) as away_wins,
                ROW_NUMBER() OVER (
                    PARTITION BY season_id, playoff_round
                    ORDER BY home_team_id
                ) as s_num,
                CASE
                    WHEN SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) >
                         SUM(CASE WHEN away_score > home_score THEN 1 ELSE 0 END)
                    THEN home_team_id
                    ELSE away_team_id
                END as winner
            FROM games
            WHERE game_type = 'Playoffs'
              AND playoff_round IS NOT NULL
            GROUP BY season_id, playoff_round, home_team_id, away_team_id
        )
        SELECT
            season_id,
            playoff_round,
            s_num,
            home_team_id,
            away_team_id,
            home_wins,
            away_wins,
            winner
        FROM series_games
        ON CONFLICT DO NOTHING
    """))
    print(f"    Created {result.rowcount:,} playoff series")

    session.commit()
    session.close()

    # Show summary
    session2 = Session(engine)
    r = session2.execute(text(
        "SELECT round, COUNT(*) FROM playoff_series GROUP BY round ORDER BY COUNT(*) DESC"
    )).fetchall()
    print("\n  Playoff series by round:")
    for round_name, cnt in r:
        print(f"    {round_name or 'Unknown':30s}: {cnt:>5}")
    session2.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
