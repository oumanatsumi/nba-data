"""
Complete import of second Kaggle NBA dataset
===============================================
Source: eoinamoore/historical-nba-data-and-player-box-scores
Includes: games, player single-game stats, player season aggregation
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"localhost:5432/"
    f"{os.getenv('POSTGRES_DB', 'nba_data')}"
)
engine = create_engine(DB_URL, echo=False)
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'archive-player')


def _safe(v, dtype=int):
    try:
        if pd.isna(v):
            return None
        return dtype(v)
    except:
        return None


def _season_id_from_date(dt):
    """Derive season_id from date (e.g., 2025-11-15 -> 2025-26, 2025-05-15 -> 2024-25)"""
    if pd.isna(dt):
        return None
    try:
        if isinstance(dt, str):
            dt = datetime.strptime(dt[:10], '%Y-%m-%d')
        elif hasattr(dt, 'strftime'):
            dt = dt
        else:
            dt = datetime.strptime(str(dt)[:10], '%Y-%m-%d')
    except:
        return None

    year = dt.year
    month = dt.month
    # NBA season spans two years: starts in Oct, playoffs run through Jun
    if month >= 10:
        return f"{year}-{str(year+1)[-2:]}"
    else:
        return f"{year-1}-{str(year)[-2:]}"


def step0_import_players():
    """Import missing players from Players.csv"""
    print("=" * 60)
    print("STEP 0: Import Missing Players")
    print("=" * 60)

    pdf = pd.read_csv(os.path.join(DATA_DIR, 'Players.csv'))
    session = Session(engine)
    count = 0

    for _, row in pdf.iterrows():
        pid = _safe(row.get('personId'))
        if not pid:
            continue
        existing = session.execute(text(
            "SELECT 1 FROM players WHERE player_id = :pid"
        ), {"pid": pid}).fetchone()
        if existing:
            continue

        h = _safe(row.get('heightInches'))
        w_lbs = _safe(row.get('bodyWeightLbs'))
        w = int(w_lbs * 0.453592) if w_lbs else None

        pos = ''
        positions = []
        if row.get('guard'): positions.append('G')
        if row.get('forward'): positions.append('F')
        if row.get('center'): positions.append('C')
        pos = '-'.join(positions) if positions else None

        session.execute(text("""
            INSERT INTO players (player_id, first_name, last_name, full_name, birth_date, height_cm, weight_kg, position, country)
            VALUES (:pid, :fn, :ln, :full, :bd, :h, :w, :pos, :country)
        """), {
            "pid": pid,
            "fn": row.get('firstName', ''),
            "ln": row.get('lastName', ''),
            "full": f"{row.get('firstName', '')} {row.get('lastName', '')}",
            "bd": row.get('birthDate', None) if pd.notna(row.get('birthDate')) else None,
            "h": h,
            "w": w,
            "pos": pos,
            "country": row.get('country', None) if pd.notna(row.get('country')) else None,
        })
        count += 1

    session.commit()
    session.close()
    print(f"  Imported {count} missing players")
    return count


def step1_import_games():
    """Import games from second dataset's Games.csv"""
    print("=" * 60)
    print("STEP 1: Import Games from second dataset")
    print("=" * 60)

    print("  Reading Games.csv...")
    t0 = time.time()
    df = pd.read_csv(os.path.join(DATA_DIR, 'Games.csv'), low_memory=False)
    print(f"  Loaded {len(df):,} games in {time.time()-t0:.1f}s")

    session = Session(engine)

    # First, find and create missing teams
    all_home = set(df['hometeamId'].dropna().apply(int).unique())
    all_away = set(df['awayteamId'].dropna().apply(int).unique())
    all_teams = all_home | all_away
    existing = set(row[0] for row in session.execute(text("SELECT team_id FROM teams")).fetchall())
    missing = all_teams - existing

    if missing:
        # Derive team names from data
        for tid in missing:
            home_rows = df[df['hometeamId'].apply(lambda x: _safe(x) == tid if pd.notna(x) else False)]
            if len(home_rows) > 0:
                name = str(home_rows.iloc[0].get('hometeamName', f'Team {tid}'))
                city = str(home_rows.iloc[0].get('hometeamCity', ''))
                full = f"{city} {name}"
            else:
                away_rows = df[df['awayteamId'].apply(lambda x: _safe(x) == tid if pd.notna(x) else False)]
                if len(away_rows) > 0:
                    name = str(away_rows.iloc[0].get('awayteamName', f'Team {tid}'))
                    city = str(away_rows.iloc[0].get('awayteamCity', ''))
                    full = f"{city} {name}"
                else:
                    full = f'Team {tid}'

            abbr = full[:10]
            # Ensure unique abbreviation
            base = abbr
            suffix = 1
            while session.execute(text("SELECT 1 FROM teams WHERE abbreviation = :a"), {"a": abbr}).fetchone():
                abbr = f"{base[:8]}_{suffix}"
                suffix += 1

            session.execute(text(
                "INSERT INTO teams (team_id, abbreviation, nickname, full_name, is_active) VALUES (:tid, :a, :n, :f, FALSE)"
            ), {"tid": int(tid), "a": abbr, "n": full, "f": full})
        session.commit()
        print(f"  Created {len(missing)} missing teams")

    # Now import games
    count = 0
    skipped = 0

    for _, row in df.iterrows():
        gid = _safe(row.get('gameId'))
        if not gid:
            continue

        # Skip duplicates
        existing = session.execute(text(
            "SELECT 1 FROM games WHERE game_id = :gid"
        ), {"gid": gid}).fetchone()
        if existing:
            skipped += 1
            continue

        # Parse date
        game_date = None
        try:
            game_date = datetime.strptime(str(row['gameDateTimeEst'])[:10], '%Y-%m-%d').date()
        except:
            pass

        sid = _season_id_from_date(row.get('gameDateTimeEst'))

        # Map game type
        gt = str(row.get('gameType', 'Regular Season'))
        if 'Playoffs' in gt or 'Play-off' in gt:
            game_type = 'Playoffs'
        elif 'All-Star' in gt:
            game_type = 'All-Star'
        elif 'Regular' in gt:
            game_type = 'Regular Season'
        else:
            game_type = 'Regular Season'  # default

        session.execute(text("""
            INSERT INTO games (
                game_id, season_id, game_date,
                home_team_id, away_team_id,
                home_score, away_score, game_type
            ) VALUES (:gid, :sid, :gd, :ht, :at, :hs, :aws, :gt)
        """), {
            "gid": gid,
            "sid": sid,
            "gd": game_date,
            "ht": _safe(row.get('hometeamId')),
            "at": _safe(row.get('awayteamId')),
            "hs": _safe(row.get('homeScore')),
            "aws": _safe(row.get('awayScore')),
            "gt": game_type,
        })
        count += 1

        if count % 5000 == 0:
            session.commit()
            elapsed = time.time() - t0
            print(f"  [{count:>8,}/{len(df):,}] {count/len(df)*100:.1f}% | {count/elapsed:.0f} rows/s")

    session.commit()
    session.close()
    print(f"  Done: {count:,} imported, {skipped:,} skipped ({time.time()-t0:.0f}s)")
    return count


def step2_import_player_stats():
    """Import player single-game stats from PlayerStatistics.csv"""
    print("\n" + "=" * 60)
    print("STEP 2: Import Player Single-Game Stats")
    print("=" * 60)

    print("  Reading CSV (371MB)...")
    t0 = time.time()
    # Use chunks for memory efficiency
    chunk_size = 50000

    session = Session(engine)

    # Pre-load valid game and player IDs to skip rows with missing FK references
    print("  Pre-loading valid IDs...")
    valid_game_ids = set(row[0] for row in session.execute(text("SELECT game_id FROM games")).fetchall())
    valid_player_ids = set(row[0] for row in session.execute(text("SELECT player_id FROM players")).fetchall())
    print(f"  Valid games: {len(valid_game_ids)}, valid players: {len(valid_player_ids)}")

    total = 0
    skipped_fk = 0

    for chunk_idx, chunk in enumerate(pd.read_csv(
        os.path.join(DATA_DIR, 'PlayerStatistics.csv'), chunksize=chunk_size
    )):
        batch = 0
        for _, row in chunk.iterrows():
            gid = _safe(row.get('gameId'))
            pid = _safe(row.get('personId'))
            tid = _safe(row.get('playerteamId'))

            if not all([gid, pid, tid]):
                continue

            # Fast FK validation in Python
            if gid not in valid_game_ids or pid not in valid_player_ids:
                skipped_fk += 1
                continue

            pos = row.get('startingPosition', '')
            is_starter = pd.notna(pos) and pos != ''

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
                "gid": gid, "pid": pid, "tid": tid,
                "starter": is_starter,
                "min": _safe(row.get('numMinutes'), float),
                "pts": _safe(row.get('points')),
                "reb": _safe(row.get('reboundsTotal')),
                "oreb": _safe(row.get('reboundsOffensive')),
                "dreb": _safe(row.get('reboundsDefensive')),
                "ast": _safe(row.get('assists')),
                "stl": _safe(row.get('steals')),
                "blk": _safe(row.get('blocks')),
                "tov": _safe(row.get('turnovers')),
                "pf": _safe(row.get('foulsPersonal')),
                "fgm": _safe(row.get('fieldGoalsMade')),
                "fga": _safe(row.get('fieldGoalsAttempted')),
                "fg3m": _safe(row.get('threePointersMade')),
                "fg3a": _safe(row.get('threePointersAttempted')),
                "ftm": _safe(row.get('freeThrowsMade')),
                "fta": _safe(row.get('freeThrowsAttempted')),
                "pm": _safe(row.get('plusMinusPoints')),
            })

            batch += 1
            total += 1

        session.commit()
        elapsed = time.time() - t0
        print(f"  Chunk {chunk_idx+1}: {total:>10,} rows (+{skipped_fk:,} FK skipped) | {total/elapsed:.0f} rows/s | elapsed {elapsed:.0f}s")

    session.close()
    print(f"  Done: {total:,} imported, {skipped_fk:,} skipped (FK missing) ({time.time()-t0:.0f}s)")
    return total


def step3_aggregate_season_stats():
    """Aggregate player_season_stats from player_game_stats"""
    print("\n" + "=" * 60)
    print("STEP 3: Aggregate Player Season Stats")
    print("=" * 60)

    session = Session(engine)

    # Use regular season only for season-level stats
    result = session.execute(text("""
        INSERT INTO player_season_stats (
            season_id, player_id, team_id,
            games_played, games_started, minutes_per_game,
            points_per_game, rebounds_per_game, assists_per_game,
            steals_per_game, blocks_per_game, turnovers_per_game,
            field_goal_pct, three_point_pct, free_throw_pct
        )
        SELECT
            g.season_id,
            pgs.player_id,
            pgs.team_id,
            COUNT(DISTINCT pgs.game_id) as gp,
            SUM(CASE WHEN pgs.is_starter THEN 1 ELSE 0 END) as gs,
            AVG(pgs.minutes_played) as mpg,
            AVG(pgs.points) as ppg,
            AVG(pgs.rebounds_total) as rpg,
            AVG(pgs.assists) as apg,
            AVG(pgs.steals) as spg,
            AVG(pgs.blocks) as bpg,
            AVG(pgs.turnovers) as tpg,
            CASE WHEN SUM(pgs.field_goals_attempted) > 0
                THEN SUM(pgs.field_goals_made)::numeric / NULLIF(SUM(pgs.field_goals_attempted), 0)
                ELSE NULL END as fg_pct,
            CASE WHEN SUM(pgs.three_pointers_attempted) > 0
                THEN SUM(pgs.three_pointers_made)::numeric / NULLIF(SUM(pgs.three_pointers_attempted), 0)
                ELSE NULL END as fg3_pct,
            CASE WHEN SUM(pgs.free_throws_attempted) > 0
                THEN SUM(pgs.free_throws_made)::numeric / NULLIF(SUM(pgs.free_throws_attempted), 0)
                ELSE NULL END as ft_pct
        FROM player_game_stats pgs
        JOIN games g ON pgs.game_id = g.game_id
        WHERE g.game_type = 'Regular Season'
        GROUP BY g.season_id, pgs.player_id, pgs.team_id
        ON CONFLICT (season_id, player_id, team_id) DO UPDATE
        SET games_played = EXCLUDED.games_played,
            points_per_game = EXCLUDED.points_per_game,
            rebounds_per_game = EXCLUDED.rebounds_per_game,
            assists_per_game = EXCLUDED.assists_per_game,
            steals_per_game = EXCLUDED.steals_per_game,
            blocks_per_game = EXCLUDED.blocks_per_game,
            turnovers_per_game = EXCLUDED.turnovers_per_game,
            field_goal_pct = EXCLUDED.field_goal_pct,
            three_point_pct = EXCLUDED.three_point_pct,
            free_throw_pct = EXCLUDED.free_throw_pct
    """))
    print(f"  Aggregated: {result.rowcount} player-season records")

    session.commit()
    session.close()


def show_summary():
    session = Session(engine)
    tables = [
        "players", "teams", "seasons", "games",
        "player_season_stats", "team_season_stats",
        "player_game_stats"
    ]
    print("\n" + "=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)
    for t in tables:
        c = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        icon = "✅" if c > 0 else "❌"
        print(f"  {icon} {t:30s}: {c:>10,}")

    # Show game_type distribution
    print("\n  Game types:")
    for row in session.execute(text(
        "SELECT game_type, COUNT(*) FROM games GROUP BY game_type ORDER BY COUNT(*) DESC"
    )).fetchall():
        print(f"    {row[0]:20s}: {row[1]:>10,}")
    session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("NBA Player Stats Import (Second Dataset)")
    print("=" * 60)

    step0_import_players()
    step1_import_games()
    step2_import_player_stats()
    step3_aggregate_season_stats()
    show_summary()

    print("\n✅ All done!")
