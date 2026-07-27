"""Step 3 only: Aggregate player season stats"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv; load_dotenv()

DB_URL = "postgresql://postgres:postgres@localhost:5432/nba_data"
engine = create_engine(DB_URL)
session = Session(engine)

print("Aggregating player season stats...")
r = session.execute(text('''
    INSERT INTO player_season_stats (
        season_id, player_id, team_id, games_played, games_started,
        minutes_per_game, points_per_game, rebounds_per_game,
        assists_per_game, steals_per_game, blocks_per_game,
        turnovers_per_game, field_goal_pct, three_point_pct, free_throw_pct
    )
    SELECT
        g.season_id, pgs.player_id, pgs.team_id,
        COUNT(DISTINCT pgs.game_id),
        SUM(CASE WHEN pgs.is_starter THEN 1 ELSE 0 END),
        AVG(pgs.minutes_played), AVG(pgs.points), AVG(pgs.rebounds_total),
        AVG(pgs.assists), AVG(pgs.steals), AVG(pgs.blocks),
        AVG(pgs.turnovers),
        CASE WHEN SUM(pgs.field_goals_attempted) > 0
            THEN SUM(pgs.field_goals_made)::numeric / NULLIF(SUM(pgs.field_goals_attempted), 0)
            ELSE NULL END,
        CASE WHEN SUM(pgs.three_pointers_attempted) > 0
            THEN SUM(pgs.three_pointers_made)::numeric / NULLIF(SUM(pgs.three_pointers_attempted), 0)
            ELSE NULL END,
        CASE WHEN SUM(pgs.free_throws_attempted) > 0
            THEN SUM(pgs.free_throws_made)::numeric / NULLIF(SUM(pgs.free_throws_attempted), 0)
            ELSE NULL END
    FROM player_game_stats pgs
    JOIN games g ON pgs.game_id = g.game_id
    WHERE g.game_type = 'Regular Season'
    GROUP BY g.season_id, pgs.player_id, pgs.team_id
    ON CONFLICT (season_id, player_id, team_id) DO NOTHING
'''))
print(f"Aggregated: {r.rowcount} rows")

session.commit()

# Show summary
for t in ['players','teams','seasons','games','player_game_stats','player_season_stats','team_season_stats']:
    c = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
    print(f"  {t}: {c:,}")

session.close()
print("Done!")
