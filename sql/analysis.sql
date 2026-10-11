SELECT league, season,
CAST(SUBSTRING_INDEX(season, '-', 1) AS UNSIGNED) AS start_year,
fouls_per_match, num_matches
FROM view_fouls_per_league_season;
