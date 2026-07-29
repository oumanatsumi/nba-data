"""Player API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.player import PlayerBase, PlayerDetail, PlayerSeasonStats, PlayerCareerResponse, PlayerListResponse

router = APIRouter()


@router.get("/players", response_model=PlayerListResponse, tags=["Players"])
async def list_players(
    search: str = Query(None, description="Search by name"),
    active: bool = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List players with optional search and filters"""
    conditions = []
    params = {}

    if search:
        conditions.append("full_name ILIKE :search")
        params["search"] = f"%{search}%"
    if active is not None:
        conditions.append("active = :active")
        params["active"] = active

    where = " AND ".join(conditions) if conditions else "1=1"

    total = db.execute(
        text(f"SELECT COUNT(*) FROM players WHERE {where}"), params
    ).scalar()

    rows = db.execute(text(f"""
        SELECT player_id, first_name, last_name, full_name
        FROM players WHERE {where}
        ORDER BY full_name LIMIT :limit OFFSET :offset
    """), {**params, "limit": limit, "offset": offset}).fetchall()

    return {
        "total": total,
        "players": [{"player_id": r[0], "first_name": r[1], "last_name": r[2], "full_name": r[3]} for r in rows],
    }


@router.get("/players/{player_id}", response_model=PlayerDetail, tags=["Players"])
async def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get player details"""
    row = db.execute(text("""
        SELECT player_id, first_name, last_name, full_name, birth_date,
               height_cm, weight_kg, position, country, draft_year,
               draft_round, draft_number, nba_years, active
        FROM players WHERE player_id = :pid
    """), {"pid": player_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Player not found")

    return {k: row[i] for i, k in enumerate([
        "player_id", "first_name", "last_name", "full_name", "birth_date",
        "height_cm", "weight_kg", "position", "country", "draft_year",
        "draft_round", "draft_number", "nba_years", "active",
    ])}


@router.get("/players/{player_id}/stats", response_model=list[PlayerSeasonStats], tags=["Players"])
async def get_player_season_stats(
    player_id: int,
    season_id: str = Query(None, description="Filter by season (e.g., 2023-24)"),
    db: Session = Depends(get_db),
):
    """Get player season statistics, including advanced stats"""
    params = {"pid": player_id}
    season_filter = ""
    if season_id:
        season_filter = "AND pss.season_id = :sid"
        params["sid"] = season_id

    rows = db.execute(text(f"""
        SELECT pss.season_id, pss.team_id, t.abbreviation as team_abbreviation,
               pss.games_played, pss.minutes_per_game,
               pss.points_per_game, pss.rebounds_per_game, pss.assists_per_game,
               pss.steals_per_game, pss.blocks_per_game, pss.field_goal_pct,
               pss.three_point_pct, pss.free_throw_pct,
               pss.player_efficiency_rating, pss.true_shooting_pct,
               pss.usage_rate, pss.win_shares, pss.box_plus_minus,
               pss.value_over_replacement_player
        FROM player_season_stats pss
        LEFT JOIN teams t ON pss.team_id = t.team_id
        WHERE pss.player_id = :pid {season_filter}
        ORDER BY pss.season_id
    """), params).fetchall()

    cols = ["season_id", "team_id", "team_abbreviation",
            "games_played", "minutes_per_game",
            "points_per_game", "rebounds_per_game", "assists_per_game",
            "steals_per_game", "blocks_per_game", "field_goal_pct",
            "three_point_pct", "free_throw_pct",
            "player_efficiency_rating", "true_shooting_pct",
            "usage_rate", "win_shares", "box_plus_minus",
            "value_over_replacement_player"]

    return [{k: (v) for k, v in zip(cols, row)} for row in rows]


@router.get("/players/{player_id}/career", response_model=PlayerCareerResponse, tags=["Players"])
async def get_player_career(player_id: int, db: Session = Depends(get_db)):
    """Get player details + all season stats"""
    player = await get_player(player_id, db)
    stats = await get_player_season_stats(player_id, None, db)
    return {"player": player, "seasons": stats}


@router.get("/stats/leaders", tags=["Stats"])
async def get_stat_leaders(
    season_id: str = Query(None, description="Season filter"),
    stat: str = Query("points_per_game", description="Statistic to rank by"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
):
    """Get statistical leaders for a given stat"""
    valid_stats = {
        "points_per_game", "rebounds_per_game", "assists_per_game",
        "steals_per_game", "blocks_per_game", "player_efficiency_rating",
        "true_shooting_pct", "win_shares", "box_plus_minus", "value_over_replacement_player",
    }
    if stat not in valid_stats:
        raise HTTPException(status_code=400, detail=f"Invalid stat: {stat}. Choose from {list(valid_stats)}")

    params = {"limit": limit}
    season_filter = "WHERE 1=1"
    if season_id:
        season_filter = "WHERE pss.season_id = :sid"
        params["sid"] = season_id

    rows = db.execute(text(f"""
        SELECT p.full_name, pss.season_id, pss.{stat} as stat_value, pss.games_played
        FROM player_season_stats pss
        JOIN players p ON pss.player_id = p.player_id
        {season_filter}
          AND pss.{stat} IS NOT NULL
        ORDER BY pss.{stat} DESC
        LIMIT :limit
    """), params).fetchall()

    return [
        {"player": r[0], "season": r[1], "value": float(r[2]) if r[2] else None, "games_played": r[3]}
        for r in rows
    ]


@router.get("/stats/compare", tags=["Stats"])
async def compare_players(
    player_ids: str = Query(..., description="Comma-separated player IDs"),
    season_id: str = Query(..., description="Season to compare"),
    db: Session = Depends(get_db),
):
    """Compare multiple players for a given season"""
    ids = [int(x.strip()) for x in player_ids.split(",") if x.strip().isdigit()]
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 player IDs")
    if len(ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 players")

    results = []
    for pid in ids:
        row = db.execute(text("""
            SELECT p.full_name, pss.*
            FROM player_season_stats pss
            JOIN players p ON pss.player_id = p.player_id
            WHERE pss.player_id = :pid AND pss.season_id = :sid
        """), {"pid": pid, "sid": season_id}).fetchone()
        if row:
            results.append({
                "player_id": pid,
                "name": row[0],
                "points_per_game": float(row[5]) if row[5] else None,
                "rebounds_per_game": float(row[6]) if row[6] else None,
                "assists_per_game": float(row[7]) if row[7] else None,
                "player_efficiency_rating": float(row[12]) if row[12] else None,
                "true_shooting_pct": float(row[13]) if row[13] else None,
                "win_shares": float(row[15]) if row[15] else None,
            })

    return {"season": season_id, "players": results}
