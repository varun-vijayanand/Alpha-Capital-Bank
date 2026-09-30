"""
customer_profiling.py

Runs sql/customer_profiling.sql against the Alpha Capital Bank DB
and prints a quick sanity-check of how customers are distributed
across the derived segments.
"""

import sys
from pathlib import Path

# make Project 0/config importable
sys.path.append(str(Path(__file__).resolve().parents[2] / "Project 0" / "config"))
from config_loader import get_db_connection_string

from sqlalchemy import create_engine, text
import pandas as pd

pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)

SQL_PATH = Path(__file__).resolve().parents[1] / "sql" / "customer_profiling.sql"


def run_customer_profiling() -> pd.DataFrame:
    engine = create_engine(get_db_connection_string())
    query = SQL_PATH.read_text()
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df


def sanity_check(df: pd.DataFrame) -> None:
    print(f"\nTotal customers profiled: {len(df)}\n")

    for col in [
        "occupation",
        "customer_type",
        "residency",
        "risk_category",
        "income_tier_fixed",
        "income_tier_percentile",
    ]:
        print(f"--- {col} ---")
        print(df[col].value_counts(dropna=False))
        print()

    print("--- income (describe) ---")
    print(df["income"].describe())
    print()

    print("--- age (describe) ---")
    print(df["age"].describe())
    print()

    print("--- account_count (describe) ---")
    print(df["account_count"].describe())


if __name__ == "__main__":
    df = run_customer_profiling()
    sanity_check(df)