"""Team API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()


@router.get("/teams", tags=["Teams"])
async def list_teams(
    active: bool = Query(None),
    db: Session = Depends(get_db),
):
    """List all teams"""
    where = "WHERE is_active = :active" if active is not None else ""
    rows = db.execute(text(f"""
        SELECT team_id, abbreviation, nickname, full_name, city, conference, division, is_active
        FROM teams {where} ORDER BY conference, division, full_name
    """), {"active": active} if active is not None else {}).fetchall()

    cols = ["team_id", "abbreviation", "nickname", "full_name", "city", "conference", "division", "is_active"]
    return [dict(zip(cols, r)) for r in rows]


@router.get("/teams/{team_id}", tags=["Teams"])
async def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get team details"""
    row = db.execute(text("""
        SELECT team_id, abbreviation, nickname, full_name, city, year_founded,
               arena, conference, division, is_active
        FROM teams WHERE team_id = :tid
    """), {"tid": team_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Team not found")

    cols = ["team_id", "abbreviation", "nickname", "full_name", "city",
            "year_founded", "arena", "conference", "division", "is_active"]
    return dict(zip(cols, row))


@router.get("/teams/{team_id}/stats", tags=["Teams"])
async def get_team_season_stats(
    team_id: int,
    db: Session = Depends(get_db),
):
    """Get team season statistics"""
    rows = db.execute(text("""
        SELECT season_id, wins, losses, win_pct, points_per_game,
               points_allowed_per_game, conference_rank, playoff_seed
        FROM team_season_stats
        WHERE team_id = :tid
        ORDER BY season_id
    """), {"tid": team_id}).fetchall()

    cols = ["season_id", "wins", "losses", "win_pct", "points_per_game",
            "points_allowed_per_game", "conference_rank", "playoff_seed"]
    return [dict(zip(cols, r)) for r in rows]


@router.get("/teams/{team_id}/roster", tags=["Teams"])
async def get_team_roster(
    team_id: int,
    season_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get team roster for a season"""
    params = {"tid": team_id}
    season_filter = ""
    if season_id:
        season_filter = "AND pss.season_id = :sid"
        params["sid"] = season_id

    rows = db.execute(text(f"""
        SELECT p.player_id, p.full_name, p.position,
               pss.points_per_game, pss.rebounds_per_game, pss.assists_per_game
        FROM player_season_stats pss
        JOIN players p ON pss.player_id = p.player_id
        WHERE pss.team_id = :tid {season_filter}
        ORDER BY pss.points_per_game DESC
    """), params).fetchall()

    return [
        {"player_id": r[0], "full_name": r[1], "position": r[2],
         "points_per_game": float(r[3]) if r[3] else None,
         "rebounds_per_game": float(r[4]) if r[4] else None,
         "assists_per_game": float(r[5]) if r[5] else None}
        for r in rows
    ]


@router.get("/teams/{team_id}/games", tags=["Teams"])
async def get_team_games(
    team_id: int,
    season_id: str = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Get team games"""
    params = {"tid": team_id, "limit": limit}
    season_filter = ""
    if season_id:
        season_filter = "AND g.season_id = :sid"
        params["sid"] = season_id

    rows = db.execute(text(f"""
        SELECT g.game_id, g.game_date, g.game_type,
               ht.abbreviation as home, g.home_score, g.away_score, at.abbreviation as away
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams at ON g.away_team_id = at.team_id
        WHERE (g.home_team_id = :tid OR g.away_team_id = :tid) {season_filter}
        ORDER BY g.game_date DESC
        LIMIT :limit
    """), params).fetchall()

    return [
        {"game_id": r[0], "game_date": str(r[1]), "game_type": r[2],
         "matchup": f"{r[3]} {r[4]}-{r[5]} {r[6]}"}
        for r in rows
    ]
