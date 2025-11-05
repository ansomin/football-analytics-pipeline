import pandas as pd
import re
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data_raw"
CLEAN_DIR = ROOT / "data_clean"

def combine_csvs(csv_list):
    pattern = re.compile(r"^(\d{4}-\d{4})-(.+?)-Stats\.csv$")

    dfs_list = []
    for csv in csv_list:
        path = RAW_DIR / csv
        reg_match = pattern.match(csv)
        if reg_match is None:
            print(f"Skipping unexpected file: {csv}")
            continue
            
        season = reg_match.group(1)
        league = reg_match.group(2)
        cur_df = pd.read_csv(path)
        cur_df['season'] = season
        cur_df['league'] = league
        dfs_list.append(cur_df)

    if len(dfs_list) == 0:
        return pd.DataFrame()

    return pd.concat(dfs_list, ignore_index=True)

def convert_integer(val):
    if pd.isnull(val):
        return pd.NA
    val = val.replace(',', "")
    return int(val)

def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    # holds a list of csv names
    csv_list = os.listdir(RAW_DIR)

    # merge all csvs into one df
    combined_df = combine_csvs(csv_list)

    # clean column names with spaces
    combined_df.columns = combined_df.columns.str.strip().str.replace(" ", "_", regex=False).str.lower()

    # convert minutes column from object to int
    combined_df['minutes'] = combined_df['minutes'].apply(convert_integer)

    # rename columns that may be ambiguous
    cols_to_rename = {
        'games': 'games_played',
        'pens_att': 'pens_attempted',
    }
    combined_df = combined_df.rename(mapper=cols_to_rename, axis=1)

    # find list of columns that ends with '_y' and drop those columns
    cols_to_drop = [col for col in combined_df.columns if col.endswith('_y')]
    combined_df = combined_df.drop(columns=cols_to_drop, errors='ignore')

    # remove '_x' from column names
    combined_df.columns = combined_df.columns.str.replace(r'_x$', '', regex=True)

    # save dataframe into csv
    combined_df.to_csv(CLEAN_DIR / "fbref_stats_full.csv", index=False)

    # drop columns ending with per90 as we can compute those values
    cols_90s = [col for col in combined_df.columns if col.endswith('_per90')]
    combined_df = combined_df.drop(columns=cols_90s, errors='ignore')

    # drop redundant or computable columns
    # check notebooks/code_tester.ipynb for more details
    columns_to_drop = [
        'games_starts', 'minutes', 'minutes_90s',
        'goals_assists', 'goals_pens', 'cards_yellow_red',
        'npxg_xg_assist', 'aerials_won_pct'
    ]
    combined_df = combined_df.drop(columns=columns_to_drop, errors='ignore')

    # save cleaned dataframe into csv
    combined_df.to_csv(CLEAN_DIR / "fbref_stats_cleaned.csv", index=False)
    combined_df.to_parquet(CLEAN_DIR / "fbref_stats_cleaned.parquet", index=False)

    print(f"Done! Outputs saved to: {CLEAN_DIR}")




if __name__ == "__main__":
    main()