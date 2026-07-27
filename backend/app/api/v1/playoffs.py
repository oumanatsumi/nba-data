"""Playoffs API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()


@router.get("/playoffs/bracket", tags=["Playoffs"])
async def get_playoff_bracket(
    season_id: str = Query(..., description="Season (e.g., 2023-24)"),
    db: Session = Depends(get_db),
):
    """Get playoff bracket for a season"""
    series_data = db.execute(text("""
        SELECT ps.round, ps.series_number, ps.home_team_wins, ps.away_team_wins,
               ht.abbreviation as home_abbr, ht.full_name as home_team,
               at.abbreviation as away_abbr, at.full_name as away_team,
               wt.abbreviation as winner_abbr
        FROM playoff_series ps
        JOIN teams ht ON ps.home_team_id = ht.team_id
        JOIN teams at ON ps.away_team_id = at.team_id
        LEFT JOIN teams wt ON ps.winner_team_id = wt.team_id
        WHERE ps.season_id = :sid
        ORDER BY
            CASE ps.round
                WHEN 'First Round' THEN 1
                WHEN 'Conference Semifinals' THEN 2
                WHEN 'Conference Finals' THEN 3
                WHEN 'NBA Finals' THEN 4
                ELSE 5
            END,
            ps.series_number
    """), {"sid": season_id}).fetchall()

    if not series_data:
        raise HTTPException(status_code=404, detail=f"No playoff data for season {season_id}")

    bracket = {}
    for r in series_data:
        round_name = r[0]
        if round_name not in bracket:
            bracket[round_name] = []
        bracket[round_name].append({
            "home_team": {"abbreviation": r[4], "name": r[5]},
            "away_team": {"abbreviation": r[6], "name": r[7]},
            "score": f"{r[2]}-{r[3]}",
            "winner": r[8],
        })

    return {"season": season_id, "bracket": bracket}


@router.get("/playoffs/series", tags=["Playoffs"])
async def get_playoff_series(
    season_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """List all playoff series"""
    params = {}
    season_filter = ""
    if season_id:
        season_filter = "WHERE ps.season_id = :sid"
        params["sid"] = season_id

    rows = db.execute(text(f"""
        SELECT ps.season_id, ps.round, ht.abbreviation, at.abbreviation,
               ps.home_team_wins, ps.away_team_wins,
               COALESCE(wt.abbreviation, ht.abbreviation) as winner
        FROM playoff_series ps
        JOIN teams ht ON ps.home_team_id = ht.team_id
        JOIN teams at ON ps.away_team_id = at.team_id
        LEFT JOIN teams wt ON ps.winner_team_id = wt.team_id
        {season_filter}
        ORDER BY ps.season_id DESC, ps.round, ps.series_number
        LIMIT 200
    """), params).fetchall()

    return [
        {"season": r[0], "round": r[1],
         "home": r[2], "away": r[3],
         "score": f"{r[4]}-{r[5]}", "winner": r[6]}
        for r in rows
    ]


@router.get("/playoffs/matchups", tags=["Playoffs"])
async def get_playoff_matchups(
    team1: str = Query(..., description="First team abbreviation"),
    team2: str = Query(..., description="Second team abbreviation"),
    db: Session = Depends(get_db),
):
    """Get historical playoff matchups between two teams"""
    rows = db.execute(text("""
        SELECT ps.season_id, ps.round, ht.abbreviation, at.abbreviation,
               ps.home_team_wins, ps.away_team_wins,
               COALESCE(wt.abbreviation, ht.abbreviation) as winner
        FROM playoff_series ps
        JOIN teams ht ON ps.home_team_id = ht.team_id
        JOIN teams at ON ps.away_team_id = at.team_id
        LEFT JOIN teams wt ON ps.winner_team_id = wt.team_id
        WHERE (ht.abbreviation IN (:t1, :t2) AND at.abbreviation IN (:t1, :t2))
        ORDER BY ps.season_id DESC
    """), {"t1": team1.upper(), "t2": team2.upper()}).fetchall()

    return {
        "teams": f"{team1.upper()} vs {team2.upper()}",
        "total_matchups": len(rows),
        "series": [
            {"season": r[0], "round": r[1], "home": r[2], "away": r[3],
             "score": f"{r[4]}-{r[5]}", "winner": r[6]}
            for r in rows
        ],
    }
