"""Game + Playoffs API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()


@router.get("/games", tags=["Games"])
async def list_games(
    season_id: str = Query(None),
    game_type: str = Query(None, description="Regular Season / Playoffs / All-Star"),
    date_from: str = Query(None),
    date_to: str = Query(None),
    team_id: int = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """List games with filters"""
    conditions = ["1=1"]
    params = {"limit": limit, "offset": offset}

    if season_id:
        conditions.append("g.season_id = :sid")
        params["sid"] = season_id
    if game_type:
        conditions.append("g.game_type = :gt")
        params["gt"] = game_type
    if date_from:
        conditions.append("g.game_date >= :df::date")
        params["df"] = date_from
    if date_to:
        conditions.append("g.game_date <= :dt::date")
        params["dt"] = date_to
    if team_id:
        conditions.append("(g.home_team_id = :tid OR g.away_team_id = :tid)")
        params["tid"] = team_id

    where = " AND ".join(conditions)

    total = db.execute(text(f"SELECT COUNT(*) FROM games g WHERE {where}"), params).scalar()
    rows = db.execute(text(f"""
        SELECT g.game_id, g.season_id, g.game_date, g.game_type, g.playoff_round,
               ht.abbreviation, g.home_score, g.away_score, at.abbreviation
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams at ON g.away_team_id = at.team_id
        WHERE {where}
        ORDER BY g.game_date DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    return {
        "total": total,
        "games": [
            {"game_id": r[0], "season_id": r[1], "game_date": str(r[2]),
             "game_type": r[3], "playoff_round": r[4],
             "home_team": r[5], "home_score": r[6], "away_score": r[7], "away_team": r[8]}
            for r in rows
        ],
    }


@router.get("/games/{game_id}/boxscore", tags=["Games"])
async def get_boxscore(game_id: int, db: Session = Depends(get_db)):
    """Get box score for a specific game"""
    game = db.execute(text("""
        SELECT g.game_id, g.game_date, g.game_type, g.playoff_round,
               ht.abbreviation, g.home_score, g.away_score, at.abbreviation
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams at ON g.away_team_id = at.team_id
        WHERE g.game_id = :gid
    """), {"gid": game_id}).fetchone()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    players = db.execute(text("""
        SELECT pgs.player_id, p.full_name, pgs.minutes_played, pgs.points,
               pgs.rebounds_total, pgs.assists, pgs.steals, pgs.blocks,
               pgs.turnovers, pgs.field_goals_made, pgs.field_goals_attempted,
               pgs.three_pointers_made, pgs.three_pointers_attempted,
               pgs.free_throws_made, pgs.free_throws_attempted, pgs.plus_minus,
               pgs.team_id
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        WHERE pgs.game_id = :gid
        ORDER BY pgs.points DESC
    """), {"gid": game_id}).fetchall()

    cols = ["player_id", "full_name", "minutes_played", "points", "rebounds_total",
            "assists", "steals", "blocks", "turnovers", "field_goals_made",
            "field_goals_attempted", "three_pointers_made", "three_pointers_attempted",
            "free_throws_made", "free_throws_attempted", "plus_minus"]

    # Separate home/away players
    home_tid = db.execute(text("SELECT home_team_id FROM games WHERE game_id = :gid"), {"gid": game_id}).scalar()

    return {
        "game": {
            "game_id": game[0], "game_date": str(game[1]), "game_type": game[2],
            "playoff_round": game[3], "home_team": game[4], "home_score": game[5],
            "away_score": game[6], "away_team": game[7],
        },
        "home_players": [
            {k: (float(v) if v is not None else None) for k, v in zip(cols, p) if k != "team_id"}
            for p in players if p[-1] == home_tid
        ],
        "away_players": [
            {k: (float(v) if v is not None else None) for k, v in zip(cols, p) if k != "team_id"}
            for p in players if p[-1] != home_tid
        ],
    }


@router.get("/analytics/trends", tags=["Analytics"])
async def get_trends(
    stat: str = Query("points_per_game"),
    player_ids: str = Query(None, description="Comma-separated player IDs"),
    season_from: str = Query("2000-01"),
    season_to: str = Query("2025-26"),
    db: Session = Depends(get_db),
):
    """Get trend data over time for analysis"""
    valid = {"points_per_game", "rebounds_per_game", "assists_per_game",
             "player_efficiency_rating", "true_shooting_pct", "win_shares", "value_over_replacement_player"}
    if stat not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid stat: {stat}")

    params = {"from": season_from, "to": season_to, "limit": 100}
    id_filter = ""
    if player_ids:
        ids = [int(x.strip()) for x in player_ids.split(",") if x.strip().isdigit()]
        if ids:
            id_filter = "AND pss.player_id IN :pids"
            params["pids"] = tuple(ids)

    rows = db.execute(text(f"""
        SELECT p.full_name, pss.season_id, pss.{stat} as val, pss.games_played
        FROM player_season_stats pss
        JOIN players p ON pss.player_id = p.player_id
        WHERE pss.season_id BETWEEN :from AND :to
          AND pss.{stat} IS NOT NULL
          {id_filter}
        ORDER BY pss.{stat} DESC
        LIMIT :limit
    """), params).fetchall()

    return [
        {"player": r[0], "season": r[1], "value": float(r[2]) if r[2] else None, "games": r[3]}
        for r in rows
    ]
