"""
Enrich player_season_stats with BBR Advanced Stats
=====================================================
Source: sumitrodatta/nba-aba-baa-stats (Advanced.csv)
Adds: PER, TS%, USG%, WS, WS/48, OBPM, DBPM, BPM, VORP
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL, echo=False)
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'archive-stats')


def build_name_index():
    """Build mapping: lower_name -> db_player_id"""
    session = Session(engine)
    rows = session.execute(text(
        "SELECT player_id, first_name, last_name FROM players"
    )).fetchall()
    session.close()

    # Multiple lookup strategies
    index = {}  # "{first} {last}" -> [player_ids]
    for pid, first, last in rows:
        fn = (first or '').lower().strip()
        ln = (last or '').lower().strip()
        key = f"{fn} {ln}"
        if key not in index:
            index[key] = []
        index[key].append(pid)
    return index


def enrich():
    print("=" * 60)
    print("Enriching with BBR Advanced Stats")
    print("=" * 60)

    # Build name index
    print("\n[1/3] Building name index...")
    name_index = build_name_index()
    print(f"  {len(name_index):,} unique name keys")

    # Load BBR data
    print("\n[2/3] Loading Advanced.csv...")
    adv = pd.read_csv(os.path.join(DATA_DIR, 'Advanced.csv'))
    print(f"  {len(adv):,} rows, {adv['player_id'].nunique():,} unique players")
    print(f"  Seasons: {adv['season'].min()} - {adv['season'].max()}")

    # Build BBR name -> db_id mapping
    bbr_names = adv[['player_id', 'player']].drop_duplicates()
    bbr_to_db = {}  # bbr_player_id -> db_player_id
    match_count = 0

    for _, row in bbr_names.iterrows():
        bbr_name = row['player'].lower().strip()
        if bbr_name in name_index:
            # Take first match (most common case has only 1)
            bbr_to_db[row['player_id']] = name_index[bbr_name][0]
            match_count += 1

    print(f"\n  BBR players matched to DB: {match_count}/{len(bbr_names)} ({match_count/len(bbr_names)*100:.1f}%)")

    # Map season format: BBR uses year (e.g., 1947 -> "1946-47")
    # BBR 'season' is the ending year
    def bbr_season_to_std(s):
        try:
            y = int(s)
            return f"{y-1}-{str(y)[-2:]}"
        except:
            return str(s)

    adv['std_season'] = adv['season'].apply(bbr_season_to_std)

    # Convert team abbreviation to team_id lookup
    # First, get team abbreviation -> team_id from our DB
    session = Session(engine)
    team_abbr_map = {}
    for tid, abbr in session.execute(text("SELECT team_id, abbreviation FROM teams")).fetchall():
        team_abbr_map[abbr.upper()] = tid

    # Update player_season_stats with advanced metrics
    print("\n[3/3] Updating player_season_stats with advanced metrics...")
    updated = 0
    not_found = 0
    batch = 0

    for _, row in adv.iterrows():
        bbr_pid = row['player_id']
        db_pid = bbr_to_db.get(bbr_pid)
        if not db_pid:
            continue

        std_season = row['std_season']
        team = str(row.get('team', '')).upper().strip()
        db_tid = team_abbr_map.get(team)

        # Find the matching row in player_season_stats
        if db_tid:
            result = session.execute(text("""
                UPDATE player_season_stats
                SET player_efficiency_rating = :per,
                    true_shooting_pct = :ts,
                    usage_rate = :usg,
                    win_shares = :ws,
                    offensive_rating = :ortg,
                    defensive_rating = :drtg,
                    box_plus_minus = :bpm,
                    value_over_replacement_player = :vorp
                WHERE player_id = :pid
                  AND season_id = :sid
                  AND team_id = :tid
            """), {
                "pid": db_pid,
                "sid": std_season,
                "tid": db_tid,
                "per": float(row['per']) if pd.notna(row['per']) else None,
                "ts": float(row['ts_percent']) if pd.notna(row['ts_percent']) else None,
                "usg": float(row['usg_percent']) if pd.notna(row['usg_percent']) else None,
                "ws": float(row['ws']) if pd.notna(row['ws']) else None,
                "ortg": float(row['obpm']) if pd.notna(row['obpm']) else None,
                "drtg": float(row['dbpm']) if pd.notna(row['dbpm']) else None,
                "bpm": float(row['bpm']) if pd.notna(row['bpm']) else None,
                "vorp": float(row['vorp']) if pd.notna(row['vorp']) else None,
            })
        else:
            # Try without team_id
            result = session.execute(text("""
                UPDATE player_season_stats
                SET player_efficiency_rating = COALESCE(player_efficiency_rating, :per),
                    true_shooting_pct = COALESCE(true_shooting_pct, :ts),
                    usage_rate = COALESCE(usage_rate, :usg),
                    win_shares = COALESCE(win_shares, :ws),
                    offensive_rating = COALESCE(offensive_rating, :ortg),
                    defensive_rating = COALESCE(defensive_rating, :drtg),
                    box_plus_minus = COALESCE(box_plus_minus, :bpm),
                    value_over_replacement_player = COALESCE(value_over_replacement_player, :vorp)
                WHERE player_id = :pid
                  AND season_id = :sid
            """), {
                "pid": db_pid,
                "sid": std_season,
                "per": float(row['per']) if pd.notna(row['per']) else None,
                "ts": float(row['ts_percent']) if pd.notna(row['ts_percent']) else None,
                "usg": float(row['usg_percent']) if pd.notna(row['usg_percent']) else None,
                "ws": float(row['ws']) if pd.notna(row['ws']) else None,
                "ortg": float(row['obpm']) if pd.notna(row['obpm']) else None,
                "drtg": float(row['dbpm']) if pd.notna(row['dbpm']) else None,
                "bpm": float(row['bpm']) if pd.notna(row['bpm']) else None,
                "vorp": float(row['vorp']) if pd.notna(row['vorp']) else None,
            })

        if result.rowcount > 0:
            updated += 1
        else:
            not_found += 1

        batch += 1
        if batch % 5000 == 0:
            session.commit()
            print(f"  [{batch:>6,}/{len(adv):,}] Updated: {updated:,}, Not found: {not_found:,}")

    session.commit()
    print(f"\n  Done! Updated: {updated:,}, Not found: {not_found:,}")

    # Show summary
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(player_efficiency_rating) as with_per,
            COUNT(true_shooting_pct) as with_ts,
            COUNT(win_shares) as with_ws,
            COUNT(box_plus_minus) as with_bpm,
            COUNT(value_over_replacement_player) as with_vorp
        FROM player_season_stats
    """)).fetchone()
    print(f"\n  player_season_stats with advanced metrics:")
    print(f"    Total rows: {result[0]:,}")
    print(f"    With PER:   {result[1]:,}")
    print(f"    With TS%:   {result[2]:,}")
    print(f"    With WS:    {result[3]:,}")
    print(f"    With BPM:   {result[4]:,}")
    print(f"    With VORP:  {result[5]:,}")

    session.close()


if __name__ == "__main__":
    enrich()
    print("\n✅ BBR Advanced Stats enrichment complete!")
