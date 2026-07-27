"""
Import player-level stats from second Kaggle dataset
======================================================
Source: eoinamoore/historical-nba-data-and-player-box-scores
Target tables: player_game_stats, player_season_stats
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import pandas as pd
import numpy as np
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
engine = create_engine(DB_URL, echo=False)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'archive-player')


def _safe_int(val):
    """Convert value to int, return None if invalid"""
    try:
        return int(float(val)) if pd.notna(val) else None
    except:
        return None


def _safe_float(val):
    """Convert value to float, return None if invalid"""
    try:
        return float(val) if pd.notna(val) else None
    except:
        return None


def import_player_game_stats():
    """Import player single-game stats from PlayerStatistics.csv"""
    print("=== Importing Player Single-Game Stats ===")
    print("  Reading CSV (371MB)...")
    t0 = time.time()

    df = pd.read_csv(os.path.join(DATA_DIR, 'PlayerStatistics.csv'))
    rows = len(df)
    print(f"  Loaded {rows:,} rows in {time.time()-t0:.1f}s")

    session = Session(engine)
    count = 0
    batch = 0
    batch_size = 500

    for _, row in df.iterrows():
        game_id = _safe_int(row.get('gameId'))
        player_id = _safe_int(row.get('personId'))
        team_id = _safe_int(row.get('playerteamId'))

        if not all([game_id, player_id, team_id]):
            continue

        # Check existing
        existing = session.execute(text(
            "SELECT 1 FROM player_game_stats WHERE game_id = :gid AND player_id = :pid"
        ), {"gid": game_id, "pid": player_id}).fetchone()
        if existing:
            count += 1
            continue

        is_starter = False
        pos = row.get('startingPosition', '')
        if pd.notna(pos) and pos != '':
            is_starter = True

        session.execute(text("""
            INSERT INTO player_game_stats (
                game_id, player_id, team_id, is_starter,
                minutes_played, points, rebounds_total, rebounds_offensive,
                rebounds_defensive, assists, steals, blocks, turnovers,
                personal_fouls, field_goals_made, field_goals_attempted,
                three_pointers_made, three_pointers_attempted,
                free_throws_made, free_throws_attempted, plus_minus
            ) VALUES (
                :gid, :pid, :tid, :starter,
                :min, :pts, :reb, :oreb, :dreb,
                :ast, :stl, :blk, :tov, :pf,
                :fgm, :fga, :fg3m, :fg3a, :ftm, :fta, :pm
            )
            ON CONFLICT (game_id, player_id) DO NOTHING
        """), {
            "gid": game_id, "pid": player_id, "tid": team_id,
            "starter": is_starter,
            "min": _safe_float(row.get('numMinutes')),
            "pts": _safe_int(row.get('points')),
            "reb": _safe_int(row.get('reboundsTotal')),
            "oreb": _safe_int(row.get('reboundsOffensive')),
            "dreb": _safe_int(row.get('reboundsDefensive')),
            "ast": _safe_int(row.get('assists')),
            "stl": _safe_int(row.get('steals')),
            "blk": _safe_int(row.get('blocks')),
            "tov": _safe_int(row.get('turnovers')),
            "pf": _safe_int(row.get('foulsPersonal')),
            "fgm": _safe_int(row.get('fieldGoalsMade')),
            "fga": _safe_int(row.get('fieldGoalsAttempted')),
            "fg3m": _safe_int(row.get('threePointersMade')),
            "fg3a": _safe_int(row.get('threePointersAttempted')),
            "ftm": _safe_int(row.get('freeThrowsMade')),
            "fta": _safe_int(row.get('freeThrowsAttempted')),
            "pm": _safe_int(row.get('plusMinusPoints')),
        })

        batch += 1
        if batch >= batch_size:
            session.commit()
            count += batch
            elapsed = time.time() - t0
            pct = count / rows * 100
            rate = count / elapsed
            eta = (rows - count) / rate / 60 if rate > 0 else 0
            print(f"  [{count:>8,}/{rows:,}] {pct:.1f}% | {rate:.0f} rows/s | ETA {eta:.1f}min")
            batch = 0

    session.commit()
    count += batch
    session.close()

    print(f"  Done: {count:,} player game stats ({time.time()-t0:.0f}s)")


def enrich_advanced_stats():
    """Add advanced stats from PlayerStatisticsExtended.csv"""
    print("\n=== Enriching with Advanced Stats ===")
    print("  Reading CSV (432MB)...")
    t0 = time.time()

    df = pd.read_csv(os.path.join(DATA_DIR, 'PlayerStatisticsExtended.csv'))
    print(f"  Loaded {len(df):,} rows in {time.time()-t0:.1f}s")

    session = Session(engine)
    count = 0

    for _, row in df.iterrows():
        game_id = _safe_int(row.get('gameId'))
        player_id = _safe_int(row.get('personId'))

        if not all([game_id, player_id]):
            continue

        # Update efficiency rating (use PIE as efficiency_rating proxy)
        pie = _safe_float(row.get('playerImpactEstimate'))

        session.execute(text("""
            UPDATE player_game_stats
            SET efficiency_rating = :pie
            WHERE game_id = :gid AND player_id = :pid AND efficiency_rating IS NULL
        """), {"gid": game_id, "pid": player_id, "pie": pie})

        count += 1
        if count % 5000 == 0:
            session.commit()
            elapsed = time.time() - t0
            print(f"  [{count:>8,}/{len(df):,}] {count/len(df)*100:.1f}%")

    session.commit()
    session.close()
    print(f"  Done: {count:,} rows enriched")


def aggregate_player_season_stats():
    """Aggregate player season stats from game stats"""
    print("\n=== Aggregating Player Season Stats ===")
    session = Session(engine)

    result = session.execute(text("""
        INSERT INTO player_season_stats (
            season_id, player_id, team_id,
            games_played, games_started, minutes_per_game,
            points_per_game, rebounds_per_game, assists_per_game,
            steals_per_game, blocks_per_game, turnovers_per_game,
            field_goal_pct, three_point_pct, free_throw_pct,
            player_efficiency_rating
        )
        SELECT
            g.season_id,
            pgs.player_id,
            pgs.team_id,
            COUNT(*) as games_played,
            SUM(CASE WHEN pgs.is_starter THEN 1 ELSE 0 END) as games_started,
            AVG(pgs.minutes_played) as minutes_per_game,
            AVG(pgs.points) as points_per_game,
            AVG(pgs.rebounds_total) as rebounds_per_game,
            AVG(pgs.assists) as assists_per_game,
            AVG(pgs.steals) as steals_per_game,
            AVG(pgs.blocks) as blocks_per_game,
            AVG(pgs.turnovers) as turnovers_per_game,
            CASE WHEN SUM(pgs.field_goals_attempted) > 0
                THEN SUM(pgs.field_goals_made)::numeric / SUM(pgs.field_goals_attempted)::numeric
                ELSE NULL END as field_goal_pct,
            CASE WHEN SUM(pgs.three_pointers_attempted) > 0
                THEN SUM(pgs.three_pointers_made)::numeric / SUM(pgs.three_pointers_attempted)::numeric
                ELSE NULL END as three_point_pct,
            CASE WHEN SUM(pgs.free_throws_attempted) > 0
                THEN SUM(pgs.free_throws_made)::numeric / SUM(pgs.free_throws_attempted)::numeric
                ELSE NULL END as free_throw_pct,
            AVG(pgs.efficiency_rating) as player_efficiency_rating
        FROM player_game_stats pgs
        JOIN games g ON pgs.game_id = g.game_id
        WHERE g.game_type = 'Regular Season'
        GROUP BY g.season_id, pgs.player_id, pgs.team_id
        ON CONFLICT (season_id, player_id, team_id) DO UPDATE
        SET games_played = EXCLUDED.games_played,
            points_per_game = EXCLUDED.points_per_game,
            rebounds_per_game = EXCLUDED.rebounds_per_game,
            assists_per_game = EXCLUDED.assists_per_game
    """))

    print(f"  Aggregated: {result.rowcount} player-season combinations")

    session.commit()
    session.close()


def summarize():
    """Print final summary"""
    session = Session(engine)
    tables = [
        "players", "teams", "seasons", "games",
        "player_season_stats", "team_season_stats",
        "player_game_stats", "playoff_series"
    ]
    print("\n" + "=" * 50)
    print("FINAL DATABASE SUMMARY")
    print("=" * 50)
    for t in tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        status = "🫧" if count > 0 else "🙵"
        print(f"  {status} {t:30s}: {count:>10,}")
    session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("NBA Player Stats Importer")
    print("=" * 60)
    print(f"  Source: {DATA_DIR}")

    import_player_game_stats()
    enrich_advanced_stats()
    aggregate_player_season_stats()
    summarize()
