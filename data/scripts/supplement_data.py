"""Supplement Kaggle data: team details, team season stats"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"localhost:5432/"
    f"{os.getenv('POSTGRES_DB', 'nba_data')}"
)
engine = create_engine(DB_URL)

CSV_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'archive', 'csv')


def update_team_details():
    """Update teams with arena, year founded, coach info"""
    print("=== Updating Team Details ===")
    df = pd.read_csv(os.path.join(CSV_DIR, 'team_details.csv'))
    session = Session(engine)
    updated = 0

    for _, row in df.iterrows():
        session.execute(text("""
            UPDATE teams
            SET arena = COALESCE(teams.arena, :arena),
                year_founded = COALESCE(teams.year_founded, :yf)
            WHERE team_id = :tid
        """), {
            "arena": row.get('arena', None) if pd.notna(row.get('arena')) else None,
            "yf": int(row['yearfounded']) if pd.notna(row.get('yearfounded')) else None,
            "tid": int(row['team_id']),
        })
        updated += 1

    session.commit()
    session.close()
    print(f"  Updated {updated} teams")


def derive_team_season_stats():
    """Derive team season stats from game data"""
    print("=== Deriving Team Season Stats from Games ===")
    session = Session(engine)

    # Aggregate from game data
    result = session.execute(text("""
        INSERT INTO team_season_stats (
            season_id, team_id, wins, losses
        )
        SELECT
            season_id,
            home_team_id as team_id,
            SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) as losses
        FROM games
        WHERE game_type = 'Regular Season' AND home_score IS NOT NULL AND away_score IS NOT NULL
        GROUP BY season_id, home_team_id
        ON CONFLICT (season_id, team_id) DO UPDATE
        SET wins = EXCLUDED.wins, losses = EXCLUDED.losses
    """))
    print(f"  Home team stats: {result.rowcount} rows")

    result2 = session.execute(text("""
        INSERT INTO team_season_stats (
            season_id, team_id, wins, losses
        )
        SELECT
            season_id,
            away_team_id as team_id,
            SUM(CASE WHEN away_score > home_score THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN away_score < home_score THEN 1 ELSE 0 END) as losses
        FROM games
        WHERE game_type = 'Regular Season' AND home_score IS NOT NULL AND away_score IS NOT NULL
        GROUP BY season_id, away_team_id
        ON CONFLICT (season_id, team_id) DO UPDATE
        SET wins = team_season_stats.wins + EXCLUDED.wins,
            losses = team_season_stats.losses + EXCLUDED.losses
    """))
    print(f"  Away team stats added: {result2.rowcount} rows")

    # Calculate win percentage
    session.execute(text("""
        UPDATE team_season_stats
        SET win_pct = CASE WHEN (wins + losses) > 0
            THEN wins::numeric / (wins + losses)::numeric
            ELSE NULL END
        WHERE win_pct IS NULL
    """))

    session.commit()

    # Summary
    total = session.execute(text("SELECT COUNT(*) FROM team_season_stats")).scalar()
    print(f"  Total team season stats records: {total}")

    session.close()


def summarize():
    """Print database summary"""
    session = Session(engine)
    tables = [
        "players", "teams", "seasons", "games",
        "player_season_stats", "team_season_stats",
        "player_game_stats", "playoff_series"
    ]
    print("\n" + "=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)
    for t in tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {t:30s}: {count:>8,}")
    session.close()


if __name__ == "__main__":
    update_team_details()
    derive_team_season_stats()
    summarize()
