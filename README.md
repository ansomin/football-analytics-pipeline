# Football Data Analysis: Fouls per Match Over Time

### Central Question
Have football matches actually become less physical over time?

### Data Source
- Scraped from [fbref.com](https://fbref.com/en/) for top 5 European leagues (1999–2024)
- Includes standard and miscellaneous team statistics

### Data Pipeline
1. Web scrape data using `fbref_scraper.py`
    * `python fbref_scraper.py -s 1999 -e 2024`
2. Clean and normalize with `clean_data.py`
    * `python clean_data.py`
3. Load into MySQL (RDS) using `load_db.py` (normalized schema)
    * `python load_db.py`
4. Create aggregated view `v_league_season_fouls`
    * `python apply_sql.py -f sql_file`
5. Visualize in Tableau via RDS connection

### Key Metric
Average **fouls per match** =  
`SUM(fouls) / (SUM(games_played) / 2)`

### Findings
- Across all leagues, fouls per match show a **downward trend** since early 2000s.
- The **Serie A** has seen the sharpest decline.
- Yellow and red card averages per match have remained relatively stable.
