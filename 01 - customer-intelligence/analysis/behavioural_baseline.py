"""
behavioural_baseline.py

Runs sql/behavioural_summary.sql and sql/category_mix.sql against the
Alpha Capital Bank DB and prints a sanity-check of the resulting
per-customer, per-month behavioural data.
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

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
SUMMARY_SQL_PATH = SQL_DIR / "behavioural_summary.sql"
CATEGORY_SQL_PATH = SQL_DIR / "category_mix.sql"


def run_query(sql_path: Path) -> pd.DataFrame:
    engine = create_engine(get_db_connection_string())
    query = sql_path.read_text()
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df


def sanity_check_summary(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("BEHAVIOURAL SUMMARY — sanity check")
    print("=" * 60)

    print(f"\nTotal customer-month rows: {len(df)}")
    print(f"Distinct customers: {df['customer_id'].nunique()}")
    print(f"Distinct months: {df['txn_month'].nunique()}")

    numeric_cols = [
        "spend_txn_count",
        "total_spend",
        "avg_txn_amount",
        "stddev_txn_amount",
        "max_txn_amount",
        "odd_hour_txn_count",
        "channel_diversity",
        "location_diversity",
        "international_txn_count",
        "credit_txn_count",
        "total_credit",
    ]

    for col in numeric_cols:
        print(f"\n--- {col} (describe) ---")
        print(df[col].describe())

    print("\n--- weekday_txn_count (describe) ---")
    print(df["weekday_txn_count"].describe())

    print("\n--- weekend_txn_count (describe) ---")
    print(df["weekend_txn_count"].describe())

    print("\n--- most_common_hour (value_counts, top 10) ---")
    print(df["most_common_hour"].value_counts(dropna=False).head(10))

    print("\n--- rows with zero spend_txn_count (should be 0 - sender join guarantees activity) ---")
    print((df["spend_txn_count"] == 0).sum())

    print("\n--- rows with null avg_txn_amount (unexpected if spend_txn_count > 0) ---")
    print(df["avg_txn_amount"].isna().sum())


def sanity_check_category(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("CATEGORY MIX — sanity check")
    print("=" * 60)

    print(f"\nTotal customer-month-category rows: {len(df)}")
    print(f"Distinct customers: {df['customer_id'].nunique()}")
    print(f"Distinct categories: {df['merchant_category'].nunique()}")

    print("\n--- merchant_category (value_counts, by row count) ---")
    print(df["merchant_category"].value_counts())

    print("\n--- category_spend by category (sum) ---")
    print(df.groupby("merchant_category")["category_spend"].sum().sort_values(ascending=False))

    print("\n--- category_txn_count (describe) ---")
    print(df["category_txn_count"].describe())

    print("\n--- category_spend (describe) ---")
    print(df["category_spend"].describe())


if __name__ == "__main__":
    summary_df = run_query(SUMMARY_SQL_PATH)
    category_df = run_query(CATEGORY_SQL_PATH)

    sanity_check_summary(summary_df)
    sanity_check_category(category_df)