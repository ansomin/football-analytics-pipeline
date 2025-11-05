import pandas as pd
import os
import sys
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
SQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
SQL_USER = os.getenv("MYSQL_USER", "root")
SQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
SQL_DB = os.getenv("MYSQL_DB", "football")

def db_engine():
    # future=True necessary for SQLAlchemy 2.0 or later
    # pool_pre_ping=True checks if connection is working, and reconnects if disconnected
    return create_engine(
        f"mysql+pymysql://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DB}",
        future=True,
        pool_pre_ping=True
    )

def run_sql_file(conn, path):
    sql = path.read_text(encoding="utf-8")

    print(f"Executing: {path}...")

    commands = [s.strip() for s in sql.split(';') if s.strip()]

    for command in commands:
        conn.execute(text(command))

    print("Done")

def main():
    parser = argparse.ArgumentParser("Run any sql file in sql directory.")
    parser.add_argument("-f", "--file", required=True, help="SQL file to execute.")
    args = parser.parse_args()

    fname = args.file
    fpath = ROOT / "sql" / fname

    if fpath.exists():
        engine = db_engine()

        with engine.begin() as conn:
            run_sql_file(conn, fpath)
    else:
        print(f"The file '{fname}' does not exist inside the sql directory!")

if __name__ == "__main__":
    main()