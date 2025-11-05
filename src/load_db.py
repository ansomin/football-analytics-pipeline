import pandas as pd
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = ROOT / "sql" / "schema.sql"
INPUT_DATA = ROOT / "data_clean" / "fbref_stats_cleaned.csv"

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
SQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
SQL_USER = os.getenv("MYSQL_USER", "root")
SQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
SQL_DB = os.getenv("MYSQL_DB", "football")

def db_engine_no_db():
    # future=True necessary for SQLAlchemy 2.0 or later
    # pool_pre_ping=True checks if connection is working, and reconnects if disconnected
    return create_engine(
        f"mysql+pymysql://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}",
        future=True,
        pool_pre_ping=True
    )

def db_engine():
    # future=True necessary for SQLAlchemy 2.0 or later
    # pool_pre_ping=True checks if connection is working, and reconnects if disconnected
    return create_engine(
        f"mysql+pymysql://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DB}",
        future=True,
        pool_pre_ping=True
    )

def db_init(e):
    with e.begin() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS {SQL_DB}"
            )
        )

def run_sql_file(conn, path):
    sql = path.read_text(encoding="utf-8")

    print(f"Executing: {path}...")

    commands = [s.strip() for s in sql.split(';') if s.strip()]

    for command in commands:
        conn.execute(text(command))

    print("Done")

def apply_schema(e):
    with e.begin() as conn:
        run_sql_file(conn, SCHEMA_SQL)

def insert_basic_data(e, df):
    with e.begin() as conn:
        # League
        league_names = sorted(df["league"].dropna().unique())
        for name in league_names:
            t = text("""INSERT INTO League (name)
                     VALUES (:name) AS new
                     ON DUPLICATE KEY UPDATE name = new.name""")
            conn.execute(t, {"name": name})

        # Season
        seasons = sorted(df["season"].dropna().unique())
        for season in seasons:
            t = text("""
                     INSERT INTO Season (label, start_year, end_year)
                     VALUES (:season, :start, :end) AS new
                     ON DUPLICATE KEY UPDATE start_year = new.start_year, end_year = new.end_year
                     """)
            conn.execute(t, {"season": season,
                             "start": int(season.split("-")[0]),
                             "end": int(season.split("-")[1])})
            
        # Team
        teams = sorted(df["team"].dropna().unique())
        for team in teams:
            t = text("""INSERT INTO Team (name)
                     VALUES (:name) AS new
                     ON DUPLICATE KEY UPDATE name = new.name
                     """)
            conn.execute(t, {"name": team})

def insert_bridge_data(e, df):
    with e.begin() as conn:
        league_season = df[["league", "season"]].drop_duplicates()
        for idx, row in league_season.iterrows():
            t = text("""
                     INSERT IGNORE INTO League_Season (league_id, season_id)
                     SELECT L.league_id, S.season_id
                     FROM League L JOIN Season S ON S.label=:season
                     WHERE L.name=:league
                     """)
            conn.execute(t, {"league": row["league"], "season": row["season"]})

def insert_metrics_data(e, df):
    metric_cols = [
        'games_played', 'players_used', 'avg_age', 'possession', 
        'goals', 'assists', 'pens_made', 'pens_attempted', 'cards_yellow',
        'cards_red', 'fouls', 'fouled', 'offsides', 'crosses', 'interceptions',
        'tackles_won', 'pens_won', 'pens_conceded', 'own_goals',
        'xg', 'npxg', 'xg_assist', 'progressive_passes',
        'progressive_carries', 'ball_recoveries', 'aerials_won', 'aerials_lost'
    ]

    # if column is missing, create column
    for col in metric_cols:
        if col not in df.columns:
            df[col] = pd.NA

    with e.begin() as conn:
        for idx, row in df.iterrows():
            t = text(f"""
                     INSERT INTO Metric (ls_id, team_id, {", ".join(metric_cols)})
                     SELECT LS.ls_id, T.team_id, {", ".join([f":{col}" for col in metric_cols])}
                     FROM League_Season LS
                     JOIN League L ON LS.league_id = L.league_id
                     JOIN Season S ON LS.season_id = S.season_id
                     JOIN Team T ON T.name = :team
                     WHERE L.name = :league AND S.label = :season
                     ON DUPLICATE KEY UPDATE {", ".join([f"{col} = VALUES({col})" for col in metric_cols])}
                     """)
            
            params = {
                "league": row["league"], "season": row["season"], "team": row["team"],
                **{col: (None if pd.isnull(row[col]) else row[col]) for col in metric_cols}
            }
            conn.execute(t, params)


def main():
    try:
        df = pd.read_csv(INPUT_DATA)
        engine = db_engine_no_db()
    except Exception as e:
        print(e)
        sys.exit(1)

    # create db if it doesn't exist
    db_init(engine)

    # create engine with Football db
    engine = db_engine()

    # apply schema.sql
    apply_schema(engine)

    # insert data into db, apply in correct order
    print("Inserting data into League, Season, Team")
    insert_basic_data(engine, df)
    print("Inserting data into League_Season")
    insert_bridge_data(engine, df)
    print("Inserting data into Metric")
    insert_metrics_data(engine, df)

    print("Insert Complete")

if __name__ == "__main__":
    # decision between sqlalchemy vs mysql-connector
    # sqlalchemy provides portability for different sql dbs
    # we could use mysql-connector, but that means I'll be using raw SQL commands
    #   -> need to alter code if we decide to change from MySQL to Postgres
    # we can still use literal SQL using text() function in sqlalchemy

    main()