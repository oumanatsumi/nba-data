"""
NBA Data Importer - Multi-Phase Import Script
==============================================
Imports NBA historical data from nba_api into PostgreSQL.

Usage:
    python import_data.py              # Run all phases (interactive)
    python import_data.py --phase 1    # Run only Phase 1 (basics)
    python import_data.py --phase 2    # Run only Phase 2 (season stats)
    python import_data.py --phase 3    # Run only Phase 3 (games)

Phases:
    1. Basic data    (~2 min)    - Players, Teams, Seasons
    2. Season stats  (~60 min)   - Player/Team season stats, advanced metrics
    3. Games         (~4-6 hrs)  - Game records, playoff series
"""

import sys
import os
import time
import argparse
from datetime import datetime, date
from typing import Optional, Dict, Any

# Project path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/backend")

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# DB connection
DB_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'nba_data')}"
engine = create_engine(DB_URL, echo=False)

# nba_api imports
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playercareerstats,
    commonteamroster,
    teamyearbyyearstats,
    leaguegamefinder,
    leagueleaders,
    commonplayerinfo,
)

# ============================================================
# Rate Limiter
# ============================================================

class RateLimiter:
    """Respects NBA API rate limit: ~590 requests per 10 minutes"""
    def __init__(self, calls_per_window: int = 580, window_seconds: int = 600):
        self.calls_per_window = calls_per_window
        self.window_seconds = window_seconds
        self.call_times = []
        self.total_calls = 0

    def wait(self):
        """Wait if approaching rate limit"""
        now = time.time()
        cutoff = now - self.window_seconds
        self.call_times = [t for t in self.call_times if t > cutoff]
        if len(self.call_times) >= self.calls_per_window:
            sleep_time = self.call_times[0] - cutoff + 5
            print(f"  ⏳ Rate limit approaching, waiting {sleep_time:.0f}s...")
            time.sleep(sleep_time)
            self.call_times = [t for t in self.call_times if t > time.time() - self.window_seconds]
        self.call_times.append(now)
        self.total_calls += 1
        time.sleep(0.6)  # ~100 calls/minute, well under limit

limiter = RateLimiter()


# ============================================================
# Progress Display
# ============================================================

def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_step(step: int, total: int, text: str, status: str = "..."):
    pct = step / total * 100 if total else 0
    print(f"  [{step:4d}/{total}] {pct:5.1f}% | {status:6s} | {text}")

def print_summary(text: str):
    print(f"  ✓ {text}")


# ============================================================
# Phase 1: Basic Data
# ============================================================

def import_players(session: Session) -> int:
    """Import all NBA players"""
    print_header("Phase 1a: Importing Players")
    limiter.wait()
    all_players = players.get_players()
    count = 0
    skipped = 0

    for i, p in enumerate(all_players):
        pid = p['id']
        existing = session.execute(text("SELECT 1 FROM players WHERE player_id = :pid"), {"pid": pid}).fetchone()
        if existing:
            skipped += 1
            continue

        session.execute(text("""
            INSERT INTO players (player_id, first_name, last_name, full_name, position, active)
            VALUES (:pid, :fn, :ln, :full, :pos, :active)
        """), {
            "pid": pid,
            "fn": p.get('first_name', ''),
            "ln": p.get('last_name', ''),
            "full": p.get('full_name', ''),
            "pos": p.get('position', ''),
            "active": p.get('is_active', True),
        })

        if (i + 1) % 500 == 0:
            print_step(i + 1, len(all_players), f"Players processed", "OK")
            session.commit()

    session.commit()
    print_summary(f"Players: {len(all_players) - skipped} imported, {skipped} already existed (total {len(all_players)})")
    return len(all_players)


def import_teams(session: Session) -> int:
    """Import all NBA teams"""
    print_header("Phase 1b: Importing Teams")
    limiter.wait()
    all_teams = teams.get_teams()
    count = 0

    for t in all_teams:
        tid = t['id']
        existing = session.execute(text("SELECT 1 FROM teams WHERE team_id = :tid"), {"tid": tid}).fetchone()
        if existing:
            continue

        session.execute(text("""
            INSERT INTO teams (team_id, abbreviation, nickname, full_name, city, conference, division, is_active)
            VALUES (:tid, :abbr, :nick, :full, :city, :conf, :div, :active)
        """), {
            "tid": tid,
            "abbr": t.get('abbreviation', ''),
            "nick": t.get('nickname', ''),
            "full": t.get('full_name', ''),
            "city": t.get('city', ''),
            "conf": t.get('conference', ''),
            "div": t.get('division', ''),
            "active": t.get('is_active', True),
        })
        count += 1

    session.commit()
    print_summary(f"Teams: {count} imported (total {len(all_teams)})")
    return len(all_teams)


def create_seasons(session: Session) -> int:
    """Create season records (1946-47 through current)"""
    print_header("Phase 1c: Creating Seasons")
    count = 0
    for year in range(1946, 2026):
        season_id = f"{year}-{str(year + 1)[-2:]}"
        existing = session.execute(text("SELECT 1 FROM seasons WHERE season_id = :sid"), {"sid": season_id}).fetchone()
        if existing:
            continue

        games = 82
        if year in [1998, 2011]:  # Lockout seasons
            games = 50 if year == 1998 else 66
        elif year in [2019, 2020]:  # COVID seasons
            games = 72 if year == 2019 else 72
        elif year < 1967:
            games = 60

        session.execute(text("""
            INSERT INTO seasons (season_id, start_year, end_year, regular_season_games)
            VALUES (:sid, :sy, :ey, :g)
        """), {"sid": season_id, "sy": year, "ey": year + 1, "g": games})
        count += 1

    session.commit()
    print_summary(f"Seasons: {count} created (1946-47 through 2025-26)")
    return count


# ============================================================
# Phase 2: Season Statistics
# ============================================================

def _get_player_details(player_id: int) -> Optional[Dict]:
    """Get player details from commonplayerinfo (safe wrapper)"""
    try:
        limiter.wait()
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        df = info.get_data_frames()[0]
        return df.iloc[0].to_dict() if len(df) > 0 else None
    except Exception:
        return None


def import_player_season_stats(session: Session, seasons: list[str] = None) -> int:
    """Import player season stats for active players"""
    print_header("Phase 2a: Importing Player Season Stats")

    player_ids = [row[0] for row in session.execute(
        text("SELECT player_id FROM players WHERE active = TRUE ORDER BY player_id")
    ).fetchall()]

    if not player_ids:
        print("  No active players found!")
        return 0

    count = 0
    errors = 0
    total = len(player_ids)

    for i, pid in enumerate(player_ids):
        try:
            # Check if already imported
            existing = session.execute(text(
                "SELECT COUNT(*) FROM player_season_stats WHERE player_id = :pid"
            ), {"pid": pid}).fetchone()[0]
            if existing > 0:
                count += 1
                if (i + 1) % 200 == 0:
                    print_step(i + 1, total, f"Player #{pid} (skipped, already has {existing} seasons)", "SKIP")
                continue

            limiter.wait()
            career = playercareerstats.PlayerCareerStats(player_id=pid)
            career_df = career.get_data_frames()[0]

            if career_df.empty:
                continue

            for _, row in career_df.iterrows():
                sid = row.get('SEASON_ID', '')
                tid = row.get('TEAM_ID', 0)

                session.execute(text("""
                    INSERT INTO player_season_stats (
                        season_id, player_id, team_id,
                        games_played, games_started, minutes_per_game,
                        points_per_game, rebounds_per_game, assists_per_game,
                        steals_per_game, blocks_per_game, turnovers_per_game,
                        field_goal_pct, three_point_pct, free_throw_pct
                    ) VALUES (:sid, :pid, :tid, :gp, :gs, :mpg, :ppg, :rpg, :apg, :spg, :bpg, :tpg, :fgp, :tpp, :ftp)
                    ON CONFLICT (season_id, player_id, team_id) DO NOTHING
                """), {
                    "sid": sid, "pid": pid, "tid": tid,
                    "gp": row.get('GP', None), "gs": row.get('GS', None),
                    "mpg": row.get('MIN', None) if row.get('MIN') else None,
                    "ppg": row.get('PTS', None) if row.get('PTS') else None,
                    "rpg": row.get('REB', None) if row.get('REB') else None,
                    "apg": row.get('AST', None) if row.get('AST') else None,
                    "spg": row.get('STL', None) if row.get('STL') else None,
                    "bpg": row.get('BLK', None) if row.get('BLK') else None,
                    "tpg": row.get('TOV', None) if row.get('TOV') else None,
                    "fgp": row.get('FG_PCT', None) if row.get('FG_PCT') else None,
                    "tpp": row.get('FG3_PCT', None) if row.get('FG3_PCT') else None,
                    "ftp": row.get('FT_PCT', None) if row.get('FT_PCT') else None,
                })

            count += 1
            session.commit()

            if (i + 1) % 100 == 0:
                print_step(i + 1, total, f"Player #{pid}", "OK")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  ⚠ Player #{pid}: {str(e)[:80]}")
            session.rollback()
            continue

    session.commit()
    print_summary(f"Player season stats: {count} processed, {errors} errors")
    return count


def import_team_season_stats(session: Session) -> int:
    """Import team season stats for all teams"""
    print_header("Phase 2b: Importing Team Season Stats")

    team_ids = [row[0] for row in session.execute(
        text("SELECT team_id FROM teams WHERE is_active = TRUE ORDER BY team_id")
    ).fetchall()]

    count = 0
    for i, tid in enumerate(team_ids):
        try:
            existing = session.execute(text(
                "SELECT COUNT(*) FROM team_season_stats WHERE team_id = :tid"
            ), {"tid": tid}).fetchone()[0]
            if existing > 0:
                print(f"  [{i+1}/{len(team_ids)}] Team #{tid}: skipped (already has {existing} seasons)")
                continue

            limiter.wait()
            stats = teamyearbyyearstats.TeamYearByYearStats(team_id=tid)
            df = stats.get_data_frames()[0]

            if df.empty:
                continue

            for _, row in df.iterrows():
                session.execute(text("""
                    INSERT INTO team_season_stats (
                        season_id, team_id, wins, losses, win_pct,
                        points_per_game, points_allowed_per_game, rebounds_per_game,
                        assists_per_game, steals_per_game, blocks_per_game
                    ) VALUES (:sid, :tid, :w, :l, :wp, :ppg, :papg, :rpg, :apg, :spg, :bpg)
                    ON CONFLICT (season_id, team_id) DO NOTHING
                """), {
                    "sid": row.get('YEAR', ''),
                    "tid": tid,
                    "w": row.get('WINS', None),
                    "l": row.get('LOSSES', None),
                    "wp": row.get('WIN_PCT', None),
                    "ppg": row.get('PTS', None) if row.get('PTS') else None,
                    "papg": row.get('OPP_PTS', None) if row.get('OPP_PTS') else None,
                    "rpg": row.get('REB', None) if row.get('REB') else None,
                    "apg": row.get('AST', None) if row.get('AST') else None,
                    "spg": row.get('STL', None) if row.get('STL') else None,
                    "bpg": row.get('BLK', None) if row.get('BLK') else None,
                })

            session.commit()
            count += 1
            print(f"  [{i+1}/{len(team_ids)}] Team #{tid}: seasons imported ✓")

        except Exception as e:
            print(f"  ⚠ Team #{tid}: {str(e)[:80]}")
            session.rollback()
            continue

    session.commit()
    print_summary(f"Team season stats: {count} teams processed")
    return count


# ============================================================
# Phase 3: Games (long running!)
# ============================================================

def import_games(session: Session, start_season: str = "2015-16", end_season: str = "2025-26") -> int:
    """Import games for selected seasons. Skips seasons before start_season by default to save time."""
    print_header("Phase 3a: Importing Games")

    all_seasons = [
        row[0] for row in session.execute(
            text("SELECT season_id FROM seasons WHERE season_id >= :s ORDER BY season_id"),
            {"s": start_season}
        ).fetchall()
    ]

    total_games = 0
    for season_id in all_seasons:
        print(f"\n  --- Season {season_id} ---")
        try:
            # Check existing
            existing = session.execute(text(
                "SELECT COUNT(*) FROM games WHERE season_id = :sid"
            ), {"sid": season_id}).fetchone()[0]
            if existing > 0:
                print(f"  Season {season_id}: skipped ({existing} games already imported)")
                total_games += existing
                continue

            # Import regular season games
            limiter.wait()
            rs_finder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season_id,
                season_type_nullable='Regular Season'
            )
            rs_games = rs_finder.get_data_frames()[0]
            imported = _insert_games(session, rs_games, "Regular Season", None)

            # Import playoff games
            limiter.wait()
            po_finder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season_id,
                season_type_nullable='Playoffs'
            )
            po_games = po_finder.get_data_frames()[0]
            imported += _insert_games(session, po_games, "Playoffs", None)

            session.commit()
            total_games += imported
            print(f"  Season {season_id}: {imported} games imported ✓")

        except Exception as e:
            print(f"  ⚠ Season {season_id}: {str(e)[:120]}")
            session.rollback()
            continue

    print_summary(f"Games: {total_games} total imported")
    return total_games


def _insert_games(session: Session, df, game_type: str, playoff_round: Optional[str]) -> int:
    """Insert games from DataFrame"""
    count = 0
    for _, row in df.iterrows():
        gid = str(row.get('GAME_ID', ''))
        if not gid:
            continue

        existing = session.execute(text(
            "SELECT 1 FROM games WHERE game_id = :gid"
        ), {"gid": gid}).fetchone()
        if existing:
            continue

        try:
            game_date = datetime.strptime(str(row.get('GAME_DATE', ''))[:10], '%Y-%m-%d').date() if row.get('GAME_DATE') else None
        except Exception:
            game_date = None

        session.execute(text("""
            INSERT INTO games (game_id, season_id, game_date, home_team_id, away_team_id,
                               home_score, away_score, game_type, playoff_round)
            VALUES (:gid, :sid, :gd, :ht, :at, :hs, :as, :gt, :pr)
            ON CONFLICT (game_id) DO NOTHING
        """), {
            "gid": gid,
            "sid": row.get('SEASON_ID', ''),
            "gd": game_date,
            "ht": row.get('TEAM_ID', None),
            "at": row.get('MATCHUP', '').startswith('@') and row.get('TEAM_ID', None) or None,
            "hs": row.get('PTS', None),
            "as": row.get('PLUS_MINUS', None),
            "gt": game_type,
            "pr": playoff_round,
        })
        count += 1
    return count


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="NBA Data Importer")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], help="Run specific phase only")
    parser.add_argument("--skip-phase1", action="store_true", help="Skip phase 1 (already done)")
    args = parser.parse_args()

    session = Session(engine)

    try:
        print_header("NBA DATA IMPORTER")
        print(f"  API calls made: {limiter.total_calls}")
        print(f"  DB: {DB_URL.split('@')[1] if '@' in DB_URL else DB_URL}")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # ============================================================
        # PHASE 1: Basic Data (~2 minutes)
        # ============================================================
        if args.phase is None or args.phase == 1:
            if not args.skip_phase1:
                import_players(session)
                import_teams(session)
                create_seasons(session)
                print_summary("Phase 1 Complete! Players, Teams, Seasons ready.")

        # ============================================================
        # PHASE 2: Season Stats (~60 minutes)
        # ============================================================
        if args.phase is None or args.phase == 2:
            import_player_season_stats(session)
            import_team_season_stats(session)
            print_summary("Phase 2 Complete! Season stats imported.")

        # ============================================================
        # PHASE 3: Games (~4-6 hours for all seasons)
        # ============================================================
        if args.phase is None or args.phase == 3:
            print()
            print("  ╔══════════════════════════════════════════════╗")
            print("  ║  ⚠ PHASE 3: Games Import                    ║")
            print("  ║  Estimated time: several hours              ║")
            print("  ║  ~60,000+ games to import                   ║")
            print("  ╚══════════════════════════════════════════════╝")
            print()

            if args.phase is None:
                response = input("  Continue with Phase 3? (y/N): ").strip().lower()
                if response != 'y':
                    print("  Phase 3 skipped.")
                    print_summary("Import complete (Phases 1-2 done). Run with --phase 3 later.")
                    return

            import_games(session, start_season="2015-16")

        print_header("IMPORT COMPLETE")
        print(f"  Total API calls: {limiter.total_calls}")
        print(f"  Approximate data size: check PostgreSQL ('SELECT pg_size_pretty(pg_database_size('nba_data'));')")

    except KeyboardInterrupt:
        print("\n\n  ⚠ Import interrupted. Progress saved at last commit.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
