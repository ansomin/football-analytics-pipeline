USE football;

CREATE OR REPLACE VIEW view_fouls_per_league_season AS
SELECT l.name AS league, s.label AS season,
SUM(m.fouls) AS total_fouls,
SUM(m.games_played) / 2 AS num_matches,
SUM(m.fouls) / (SUM(m.games_played) / 2) AS fouls_per_match,
AVG(m.cards_yellow) AS avg_yellow_cards,
AVG(m.cards_red) AS avg_red_cards
FROM Metric m
JOIN League_Season ls ON m.ls_id = ls.ls_id
JOIN League l ON ls.league_id = l.league_id
JOIN Season s ON ls.season_id = s.season_id
GROUP BY l.name, s.label
ORDER BY l.name, s.label;