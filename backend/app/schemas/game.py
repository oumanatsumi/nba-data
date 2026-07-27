"""Pydantic schemas for Game API"""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class GameBase(BaseModel):
    game_id: int
    season_id: str
    game_date: date
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    game_type: str = "Regular Season"
    playoff_round: Optional[str] = None

    model_config = {"from_attributes": True}


class GameScore(BaseModel):
    game_id: int
    game_date: date
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    game_type: str
    playoff_round: Optional[str] = None


class BoxScorePlayer(BaseModel):
    player_id: int
    full_name: str
    minutes_played: Optional[float] = None
    points: Optional[int] = None
    rebounds_total: Optional[int] = None
    assists: Optional[int] = None
    steals: Optional[int] = None
    blocks: Optional[int] = None
    turnovers: Optional[int] = None
    field_goals_made: Optional[int] = None
    field_goals_attempted: Optional[int] = None
    three_pointers_made: Optional[int] = None
    three_pointers_attempted: Optional[int] = None
    free_throws_made: Optional[int] = None
    free_throws_attempted: Optional[int] = None
    plus_minus: Optional[int] = None


class BoxScoreResponse(BaseModel):
    game: GameScore
    home_team_players: list[BoxScorePlayer]
    away_team_players: list[BoxScorePlayer]
