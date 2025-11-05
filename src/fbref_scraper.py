import requests
import sys
import pandas as pd
import time
import argparse
import re
import random
from bs4 import BeautifulSoup
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_raw"

class Country(Enum):
    ENGLAND = 9
    SPAIN = 12
    FRANCE = 13
    GERMANY = 20
    ITALY = 11

def create_url(year: int, country: str):
    base_url = "https://fbref.com/en/comps/"

    input_enum = Country[country.upper()]

    comp_num = input_enum.value
    if input_enum == Country.ENGLAND:
        comp = "Premier-League"
    elif input_enum == Country.SPAIN:
        comp = "La-Liga"
    elif input_enum == Country.FRANCE:
        comp = "Ligue-1"
    elif input_enum == Country.GERMANY:
        comp = "Bundesliga"
    elif input_enum == Country.ITALY:
        comp = "Serie-A"
    else:
        print("Country not supported")
        sys.exit(1)
    

    season = str(year) + "-" + str(year + 1)

    url = base_url + str(comp_num) + "/" + season + "/"
    
    suburl = season + "-" + comp + "-Stats"

    return url + suburl


def scrape_url(url: str):
    # retrieve url
    res = requests.get(url)

    # comments causing parsing failure for some urls
    comm = re.compile("<!--|-->")
    
    # create BeautifulSoup object
    soup = BeautifulSoup(comm.sub("",res.text),'lxml')
    # soup = BeautifulSoup(res.text, 'html.parser')

    # scrape standard stats table
    main_table = soup.find("table", {"id": "stats_squads_standard_for"})
    if main_table is None:
        print("Failed to find table id: stats_squads_standard_for")
        print(f"url: {url}")
        print(res.text)
        sys.exit(1)
    main_table_df = parse_table(main_table)

    # scrape miscellaneous stats stable
    misc_table = soup.find("table", {"id": "stats_squads_misc_for"})
    if misc_table is None:
        print("Failed to find table id: stats_squads_misc_for")
        print(f"url: {url}")
        sys.exit(1)
    misc_table_df = parse_table(misc_table)

    # combine the two tables
    full_table = pd.merge(main_table_df, misc_table_df, how='left', on='team')

    return full_table

def parse_table(table):
    # scrape column names
    thead_rows = table.find('thead').find_all('tr')

    # account for multi-level col names
    if len(thead_rows) > 1:
        col_names = thead_rows[1]
    else:
        col_names = thead_rows[0]
    col_list = []
    for col in col_names.find_all('th'):
        col_list.append(col.get('data-stat').strip())
    col_list

    # create df based on column names
    table_df = pd.DataFrame(columns=col_list)

    # scrape table values
    table_values = table.find('tbody').find_all('tr')
    for row in table_values:
        temp_row_list=[]
        for col in col_list:
            val = row.find(["th", "td"], {"data-stat": col})
            if val is None or val.text.strip() == '':
                temp_row_list.append(pd.NA)
            else:
                temp_row_list.append(val.text.strip())

        temp_df = pd.DataFrame([temp_row_list], columns=table_df.columns)
        table_df = pd.concat([table_df, temp_df])

    return table_df

def main():
    # python -m src.fbref_scraper -s 1999 -e 2025
    parser = argparse.ArgumentParser("Scrape fbref.com for team stats.")
    parser.add_argument("-s", "--start", type=int, required=True, help="Start year (ex. 1999)")
    parser.add_argument("-e", "--end",   type=int, required=True, help="End year (exclusive, ex. 2025)")
    parser.add_argument("-c", "--countries", nargs="+", default=None,
                        help="List of countries to scrape: england spain france germany italy (default: all)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_countries = [c.name.lower() for c in Country]
    if args.countries is None:
        countries = all_countries
    else:
        countries = []
        for c in args.countries:
            if c.lower() in set(all_countries):
                countries.append(c.lower())
            else:
                print(f"{c.lower()} not supported!")
                sys.exit(1)
        if len(countries) == 0:
            countries = all_countries
    
    start = args.start
    end = args.end

    urls = []
    for year in range(start, end): # inclusive-exclusive
        for country in countries:
            urls.append(create_url(year, country))

    print(f"Scraping {len(urls)} urls...")
    num_completed = 0
    for url in urls:
        try:
            table_df = scrape_url(url)
            file_name = url.split('/')[-1] + ".csv"
            out = DATA_DIR / file_name
            table_df.to_csv(out, index=False)
            # set timer for rate-limit
            time.sleep(4.5 + random.uniform(0.2, 0.8))
        except Exception as e:
            print(f"Failed to scrape: {url}")
            print(e)
            sys.exit(1)
        
        num_completed += 1
        print(f"{num_completed} out of {len(urls)} done")
    
    print(f"Done! Outputs saved to: {DATA_DIR}")

if __name__ == "__main__":
    main()