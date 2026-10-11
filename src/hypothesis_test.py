import pandas as pd
import os
import sys
import argparse
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from scipy.stats import t as student_t
import statsmodels.formula.api as smf
from statsmodels.stats.weightstats import DescrStatsW, CompareMeans


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

def conduct_weighted_ols(df):
    df = df.copy()

    # find midpoint year to set the reference for the intercept (for intercept interpretability)
    # center_year = (df["start_year"].min() + df["start_year"].max()) / 2
    center_year = df["start_year"].mean()
    df["year_centered"] = df["start_year"] - center_year

    # fouls_per_match varies year_centered and league
    # seasons with more matches get more influence
    model = smf.wls("fouls_per_match ~ year_centered + C(league)", data=df, weights=df["num_matches"])
    result = model.fit(cov_type="HC3")

    # retrieve estimated slope
    beta = result.params.get("year_centered", np.nan)
    # retrieve standard error
    se = result.bse.get("year_centered", np.nan)
    # compute t-statistic for the trend(beta and standard error)
    if se and np.isfinite(se):
        tval = beta / se
    else:
        tval = np.nan

    # compute the one-sided p-value for hypothesis H1, which states beta < 0
    # for t distribution, CDF(t) is exactly P(T <= t), which is the left-tail p-val
    p_one_sided = student_t.cdf(tval, df=result.df_resid)

    # get 97.5th percentile of the t-distribution
    # build the 95% confidence interval for the slope
    tcrit = student_t.ppf(0.975, df=result.df_resid)
    ci_low = beta - tcrit * se
    ci_high = beta + tcrit * se

    return {
        "beta_year": beta,
        "se": se,
        "t": tval,
        "p_one_sided_beta_lt_0": p_one_sided,
        "ci95": (ci_low, ci_high),
        "center_year": center_year,
        "cov_type": "HC3",
        "n_rows": int(result.nobs),
        # "summary": result.summary().as_text()
    }

def conduct_welch_ttest(df, weighted=True):
    midpoint = (df["start_year"].min() + df["start_year"].max()) // 2
    early = df[df["start_year"] < midpoint]
    late  = df[df["start_year"] >= midpoint]

    if len(early) < 3 or len(late) < 3:
        return {"ok": False, "reason": "Not enough data in early/late windows."}

    if weighted:
        e = DescrStatsW(early["fouls_per_match"], weights=early["num_matches"], ddof=1)
        l = DescrStatsW(late["fouls_per_match"],  weights=late["num_matches"],  ddof=1)
    else:
        # unweighted fallback
        e = DescrStatsW(early["fouls_per_match"], ddof=1)
        l = DescrStatsW(late["fouls_per_match"],  ddof=1)

    cm = CompareMeans(e, l)

    # Welch t-test two-sided; we convert to one-sided (H1: early > late)
    tstat, p_two, dof = cm.ttest_ind(alternative="two-sided", usevar="unequal")
    # For one-sided early>late, halve if tstat > 0; otherwise 1 - halved
    if tstat > 0:
        p_one = p_two / 2.0
    else:
        p_one = 1.0 - (p_two / 2.0)

    return {
        "ok": True,
        "tstat": tstat,
        "p_one_sided_early_gt_late": float(p_one),
        "early_mean": float(early["fouls_per_match"].mean()),
        "late_mean": float(late["fouls_per_match"].mean()),
        "early_n": int(len(early)),
        "late_n": int(len(late)),
        "weighted": weighted,
        "windows": {
            "early": [df["start_year"].min(), midpoint - 1],
            "late": [midpoint, df["start_year"].max()]
        }
    }

def main():
    engine = db_engine()

    path = ROOT / "sql" / "analysis.sql"

    with engine.begin() as conn:
        sql = path.read_text(encoding="utf-8")

        command = [s.strip() for s in sql.split(';') if s.strip()][0]

        df = pd.read_sql(text(command), conn)

    # drop null rows
    df = df.dropna(subset=["fouls_per_match","num_matches","start_year"])
    # drop rows without any matches
    df = df[df["num_matches"] > 0]

    print("Conducting Weighted Least Squares")
    print(conduct_weighted_ols(df))
    print()

    print("Conducting Welch's t-test")
    print(conduct_welch_ttest(df))



if __name__ == "__main__":
    main()