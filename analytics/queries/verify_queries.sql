-- ================================================================
-- Q1: 2018年西部决赛每场比赛的比分
-- ================================================================
-- Conference Finals, 2017-18 season (season_id = 2017-18)
-- Series: Golden State Warriors (1610612744) vs Houston Rockets (1610612745)

SELECT
    game_date,
    CONCAT(h.abbreviation, ' ', ROW_NUMBER() OVER (PARTITION BY game_date ORDER BY game_date)) as home_team,
    home_score,
    away_score,
    CONCAT(a.abbreviation, ' ', ROW_NUMBER() OVER (PARTITION BY game_date ORDER BY game_date DESC)) as away_team,
    CASE WHEN home_score > away_score THEN h.abbreviation ELSE a.abbreviation END as winner
FROM games g
JOIN teams h ON g.home_team_id = h.team_id
JOIN teams a ON g.away_team_id = a.team_id
WHERE g.game_type = 'Playoffs'
  AND g.playoff_round = 'Conference Finals'
  AND g.season_id = '2017-18'
  AND (h.abbreviation = 'GSW' OR h.abbreviation = 'HOU')
  AND (a.abbreviation = 'GSW' OR a.abbreviation = 'HOU')
ORDER BY g.game_date;


-- ================================================================
-- Q2: 2026年东部决赛每场比赛最高得分球员
-- ================================================================
-- Conference Finals, 2025-26 season (season_id = 2025-26)
-- Eastern Conference

WITH east_conf_games AS (
    SELECT g.game_id, g.game_date
    FROM games g
    JOIN teams ht ON g.home_team_id = ht.team_id
    WHERE g.game_type = 'Playoffs'
      AND g.playoff_round = 'Conference Finals'
      AND g.season_id = '2025-26'
      AND ht.conference = 'East'
),
top_scorer AS (
    SELECT
        e.game_id,
        e.game_date,
        pgs.player_id,
        p.full_name,
        pgs.points,
        ROW_NUMBER() OVER (PARTITION BY e.game_id ORDER BY pgs.points DESC, pgs.minutes_played DESC) as rn
    FROM east_conf_games e
    JOIN player_game_stats pgs ON e.game_id = pgs.game_id
    JOIN players p ON pgs.player_id = p.player_id
    WHERE pgs.points IS NOT NULL
)
SELECT
    game_date,
    full_name as top_scorer,
    points
FROM top_scorer
WHERE rn = 1
ORDER BY game_date;
