-- Football Transfer Analysis - SQL Queries

-- 1. Number of players per club
SELECT c.club_name, COUNT(p.player_id) AS player_count
FROM clubs c
JOIN players p ON c.club_id = p.current_club_id
GROUP BY c.club_name
ORDER BY player_count DESC
LIMIT 10;

-- 2. Top 10 goal scorers
SELECT p.full_name, c.club_name, s.goals
FROM players p, stats s, clubs c
WHERE p.player_id = s.player_id AND p.current_club_id = c.club_id
ORDER BY s.goals DESC
LIMIT 10;

-- 3. Average pass accuracy by position
SELECT
    SPLIT_PART(p.position, ',', 1) AS primary_position,
    ROUND(AVG(s.pass_accuracy), 2) AS avg_pass_accuracy,
    COUNT(*) AS player_count
FROM players p
JOIN stats s ON p.player_id = s.player_id
WHERE s.pass_accuracy IS NOT NULL
AND s.appearances >= 10
GROUP BY SPLIT_PART(p.position, ',', 1)
ORDER BY avg_pass_accuracy DESC;

-- 4. Average goals per league
SELECT l.league_name, ROUND(AVG(s.goals), 2) AS avg_goals
FROM leagues l, players p, stats s, clubs c
WHERE l.league_id = c.league_id
AND c.club_id = p.current_club_id
AND p.player_id = s.player_id
GROUP BY l.league_name
ORDER BY avg_goals DESC;

-- 5. Top 10 most expensive transfers
SELECT
    p.full_name,
    c1.club_name AS from_club,
    c2.club_name AS to_club,
    t.transfer_fee,
    t.transfer_type
FROM transfers t
JOIN players p ON t.player_id = p.player