"""
Import Kaggle NBA data into PostgreSQL
======================================
Imports data from the wyattowalsh/basketball Kaggle dataset

Usage:
    python import_kaggle_data.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Database connection
DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'nba_data')}"
)
engine = create_engine(DB_URL, echo=False)

# CSV directory
CSV_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'archive', 'csv')


def import_players():
    """Import players from player.csv + common_player_info.csv"""
    print("\n=== Importing Players ===")

    # Read basic player info
    player_df = pd.read_csv(os.path.join(CSV_DIR, 'player.csv'))
    print(f"Found {len(player_df)} players in player.csv")

    # Read detailed info
    detail_df = pd.read_csv(os.path.join(CSV_DIR, 'common_player_info.csv'))
    print(f"Found {len(detail_df)} players in common_player_info.csv")

    # Merge
    merged = player_df.merge(
        detail_df[['person_id', 'birthdate', 'school', 'country', 'height', 'weight',
                   'season_exp', 'position', 'draft_year', 'draft_round', 'draft_number']],
        left_on='id', right_on='person_id', how='left'
    )

    session = Session(engine)
    count = 0
    skipped = 0

    for _, row in merged.iterrows():
        # Check if exists
        existing = session.execute(text(
            "SELECT 1 FROM players WHERE player_id = :pid"
        ), {"pid": row['id']}).fetchone()

        if existing:
            skipped += 1
            continue

        # Parse birthdate
        birth_date = None
        if pd.notna(row.get('birthdate')):
            try:
                birth_date = datetime.strptime(str(row['birthdate'])[:10], '%Y-%m-%d').date()
            except:
                pass

        # Parse height/weight
        height = None
        if pd.notna(row.get('height')):
            try:
                h_str = str(row['height'])
                if '-' in h_str:  # Format: 6-6
                    parts = h_str.split('-')
                    height = int(parts[0]) * 30.48 + int(parts[1]) * 2.54  # Convert feet-inches to cm
                else:
                    height = int(float(h_str))
            except:
                pass

        weight = None
        if pd.notna(row.get('weight')):
            try:
                weight = int(float(row['weight']) * 0.453592)  # lbs to kg
            except:
                pass

        # Convert active to boolean
        is_active = bool(int(row['is_active'])) if pd.notna(row['is_active']) else False

        session.execute(text("""
            INSERT INTO players (
                player_id, first_name, last_name, full_name, birth_date,
                height_cm, weight_kg, position, country, draft_year,
                draft_round, draft_number, nba_years, active
            ) VALUES (:pid, :fn, :ln, :full, :bd, :h, :w, :pos, :country,
                      :dy, :dr, :dn, :ny, :active)
        """), {
            "pid": row['id'],
            "fn": row['first_name'],
            "ln": row['last_name'],
            "full": row['full_name'],
            "bd": birth_date,
            "h": height,
            "w": weight,
            "pos": row.get('position', None) if pd.notna(row.get('position')) else None,
            "country": row.get('country', None) if pd.notna(row.get('country')) else None,
            "dy": int(float(row.get('draft_year'))) if pd.notna(row.get('draft_year')) and str(row.get('draft_year')).replace('.','').isdigit() else None,
            "dr": int(float(row.get('draft_round'))) if pd.notna(row.get('draft_round')) and str(row.get('draft_round')).replace('.','').isdigit() else None,
            "dn": int(float(row.get('draft_number'))) if pd.notna(row.get('draft_number')) and str(row.get('draft_number')).replace('.','').isdigit() else None,
            "ny": int(float(row.get('season_exp'))) if pd.notna(row.get('season_exp')) else None,
            "active": is_active,
        })
        count += 1

    session.commit()
    session.close()
    print(f"✓ Imported {count} players, skipped {skipped} existing")
    return count


def import_teams():
    """Import teams from team.csv + create historical teams from games"""
    print("\n=== Importing Teams ===")

    # Import known teams
    team_df = pd.read_csv(os.path.join(CSV_DIR, 'team.csv'))
    print(f"Found {len(team_df)} teams in team.csv")

    session = Session(engine)
    count = 0

    for _, row in team_df.iterrows():
        existing = session.execute(text(
            "SELECT 1 FROM teams WHERE team_id = :tid"
        ), {"tid": row['id']}).fetchone()

        if existing:
            continue

        session.execute(text("""
            INSERT INTO teams (
                team_id, abbreviation, nickname, full_name, city, year_founded
            ) VALUES (:tid, :abbr, :nick, :full, :city, :yf)
        """), {
            "tid": row['id'],
            "abbr": row['abbreviation'],
            "nick": row['nickname'],
            "full": row['full_name'],
            "city": row['city'],
            "yf": row.get('year_founded', None),
        })
        count += 1

    # Create historical teams from game.csv
    print("Creating historical teams from games...")
    game_df = pd.read_csv(os.path.join(CSV_DIR, 'game.csv'))

    # Get all team IDs from games
    all_team_ids = set(game_df['team_id_home'].unique()) | set(game_df['team_id_away'].unique())

    # Get existing team IDs
    existing_ids = set(row[0] for row in session.execute(text("SELECT team_id FROM teams")).fetchall())

    # Find missing teams
    missing_ids = all_team_ids - existing_ids
    print(f"Found {len(missing_ids)} historical teams to create")

    for tid in missing_ids:
        # Try to get team name from game data
        home_rows = game_df[game_df['team_id_home'] == tid]
        away_rows = game_df[game_df['team_id_away'] == tid]

        team_name = None
        abbreviation = f"T{tid}"

        if len(home_rows) > 0:
            team_name = home_rows.iloc[0].get('team_name_home', f'Team {tid}')
            abbreviation = home_rows.iloc[0].get('team_abbreviation_home', f'T{tid}')
        elif len(away_rows) > 0:
            team_name = away_rows.iloc[0].get('team_name_away', f'Team {tid}')
            abbreviation = away_rows.iloc[0].get('team_abbreviation_away', f'T{tid}')

        if not team_name:
            team_name = f'Historical Team {tid}'

        # Make abbreviation unique
        base_abbr = str(abbreviation)[:10]
        final_abbr = base_abbr
        suffix = 1
        while True:
            existing_abbr = session.execute(text(
                "SELECT 1 FROM teams WHERE abbreviation = :abbr"
            ), {"abbr": final_abbr}).fetchone()
            if not existing_abbr:
                break
            final_abbr = f"{base_abbr[:8]}_{suffix}"
            suffix += 1

        session.execute(text("""
            INSERT INTO teams (team_id, abbreviation, nickname, full_name, is_active)
            VALUES (:tid, :abbr, :nick, :full, FALSE)
        """), {
            "tid": int(tid),
            "abbr": final_abbr,
            "nick": str(team_name),
            "full": str(team_name),
        })
        count += 1

    session.commit()
    session.close()
    print(f"✓ Imported {count} teams total")
    return count


def _convert_season_id(kaggle_sid):
    """Convert Kaggle season ID (e.g., 21946) to standard format (1946-47)"""
    s = str(int(kaggle_sid))
    if len(s) == 5 and s.startswith('2'):
        year = int(s[1:])
        return f"{year}-{str(year + 1)[-2:]}"
    return s


def _ensure_seasons_exist(session, season_ids):
    """Create any missing season records"""
    existing = set(row[0] for row in session.execute(text(
        "SELECT season_id FROM seasons"
    )).fetchall())

    missing = set(season_ids) - existing
    for sid in missing:
        try:
            year = int(sid.split('-')[0])
        except:
            continue
        games = 82
        if year in [1998, 2011]:
            games = 50 if year == 1998 else 66
        elif year in [2019, 2020]:
            games = 72
        elif year < 1967:
            games = 60
        session.execute(text("""
            INSERT INTO seasons (season_id, start_year, end_year, regular_season_games)
            VALUES (:sid, :sy, :ey, :g)
        """), {"sid": sid, "sy": year, "ey": year + 1, "g": games})

    if missing:
        session.commit()
        print(f"  Created {len(missing)} missing season records")


def import_games():
    """Import games from game.csv"""
    print("\n=== Importing Games ===")

    game_df = pd.read_csv(os.path.join(CSV_DIR, 'game.csv'))
    print(f"Found {len(game_df)} games")

    # Convert season IDs
    game_df['std_season_id'] = game_df['season_id'].apply(_convert_season_id)

    session = Session(engine)

    # Ensure all needed seasons exist
    all_seasons = set(game_df['std_season_id'].unique())
    _ensure_seasons_exist(session, all_seasons)

    count = 0
    skipped = 0

    for _, row in game_df.iterrows():
        # Parse game date
        game_date = None
        try:
            game_date = datetime.strptime(str(row['game_date'])[:10], '%Y-%m-%d').date()
        except:
            continue

        existing = session.execute(text(
            "SELECT 1 FROM games WHERE game_id = :gid"
        ), {"gid": row['game_id']}).fetchone()

        if existing:
            skipped += 1
            continue

        # Determine game type
        season_type = row.get('season_type', 'Regular Season')
        game_type = "Regular Season"
        if "Playoffs" in str(season_type) or "PO" in str(season_type):
            game_type = "Playoffs"
        elif "All-Star" in str(season_type):
            game_type = "All-Star"

        session.execute(text("""
            INSERT INTO games (
                game_id, season_id, game_date, home_team_id, away_team_id,
                home_score, away_score, game_type
            ) VALUES (:gid, :sid, :gd, :ht, :at, :hs, :aws, :gt)
        """), {
            "gid": row['game_id'],
            "sid": row['std_season_id'],
            "gd": game_date,
            "ht": int(row['team_id_home']),
            "at": int(row['team_id_away']),
            "hs": int(row['pts_home']) if pd.notna(row['pts_home']) else None,
            "aws": int(row['pts_away']) if pd.notna(row['pts_away']) else None,
            "gt": game_type,
        })
        count += 1

        if count % 10000 == 0:
            print(f"  Progress: {count}/{len(game_df)} games")
            session.commit()

    session.commit()
    session.close()
    print(f"✓ Imported {count} games, skipped {skipped} existing")
    return count


def import_line_scores():
    """Import quarter-by-quarter scores from line_score.csv"""
    print("\n=== Importing Line Scores (Quarter by Quarter) ===")

    ls_df = pd.read_csv(os.path.join(CSV_DIR, 'line_score.csv'))
    print(f"Found {len(ls_df)} line score records")

    # This could be used to enrich game data with quarter scores
    # For now, just count
    print(f"✓ {len(ls_df)} quarter-by-quarter scores available")
    return len(ls_df)


def import_draft_history():
    """Import draft history from draft_history.csv"""
    print("\n=== Importing Draft History ===")

    draft_df = pd.read_csv(os.path.join(CSV_DIR, 'draft_history.csv'))
    print(f"Found {len(draft_df)} draft picks")

    # Update players with draft info
    session = Session(engine)
    count = 0

    for _, row in draft_df.iterrows():
        player_id = row.get('person_id')
        if pd.isna(player_id):
            continue

        # Update player draft info
        session.execute(text("""
            UPDATE players
            SET draft_year = :dy, draft_round = :dr, draft_number = :dn
            WHERE player_id = :pid
        """), {
            "dy": int(float(row.get('year'))) if pd.notna(row.get('year')) else None,
            "dr": int(float(row.get('round_num'))) if pd.notna(row.get('round_num')) else None,
            "dn": int(float(row.get('overall_pick'))) if pd.notna(row.get('overall_pick')) else None,
            "pid": int(player_id),
        })
        count += 1

    session.commit()
    session.close()
    print(f"✓ Updated draft info for {count} players")
    return count


def main():
    print("=" * 60)
    print("NBA Kaggle Data Importer")
    print("=" * 60)

    try:
        import_players()
        import_teams()
        import_games()
        import_line_scores()
        import_draft_history()

        print("\n" + "=" * 60)
        print("Import Complete!")
        print("=" * 60)

        # Show summary
        session = Session(engine)
        players = session.execute(text("SELECT COUNT(*) FROM players")).scalar()
        teams = session.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        games = session.execute(text("SELECT COUNT(*) FROM games")).scalar()
        session.close()

        print(f"\nDatabase Summary:")
        print(f"  Players: {players}")
        print(f"  Teams: {teams}")
        print(f"  Games: {games}")

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
