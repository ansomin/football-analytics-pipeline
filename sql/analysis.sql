USE football;

SELECT l.name AS league, s.label AS season,
SUM(m.fouls) / (SUM(m.games_played) / 2) AS fouls_per_match
FROM Metric m
JOIN League_Season ls ON m.ls_id = ls.ls_id
JOIN League l ON ls.league_id = l.league_id
JOIN Season s ON ls.season_id = s.season_id
GROUP BY l.name, s.label
ORDER BY l.name, MIN(s.start_year);
