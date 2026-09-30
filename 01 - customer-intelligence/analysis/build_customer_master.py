"""
build_customer_master.py

Joins customer_profiling, behavioural_summary (aggregated to per-customer),
and category_mix (pivoted wide) into a single per-customer analytical table.
This is the master dataset the rest of Project 1's EDA and correlation
analysis will run against.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "Project 0" / "config"))
from config_loader import get_db_connection_string

from sqlalchemy import create_engine, text
import pandas as pd

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_query(sql_path: Path) -> pd.DataFrame:
    engine = create_engine(get_db_connection_string())
    query = sql_path.read_text()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def aggregate_behavioural_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse 12 monthly rows per customer into one row of
    per-customer averages/totals across the year."""
    agg = df.groupby("customer_id").agg(
        avg_spend_txn_count=("spend_txn_count", "mean"),
        avg_total_spend=("total_spend", "mean"),
        avg_txn_amount=("avg_txn_amount", "mean"),
        max_txn_amount_seen=("max_txn_amount", "max"),
        total_odd_hour_txns=("odd_hour_txn_count", "sum"),
        avg_channel_diversity=("channel_diversity", "mean"),
        avg_location_diversity=("location_diversity", "mean"),
        total_international_txns=("international_txn_count", "sum"),
        avg_weekday_txn_count=("weekday_txn_count", "mean"),
        avg_weekend_txn_count=("weekend_txn_count", "mean"),
        active_months=("txn_month", "count"),
    ).reset_index()
    return agg


def pivot_category_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse category_mix into one row per customer, with total
    spend per category as columns, plus each category's % of total spend."""
    totals = df.groupby(["customer_id", "merchant_category"])["category_spend"].sum().reset_index()
    wide = totals.pivot(index="customer_id", columns="merchant_category", values="category_spend").fillna(0)
    wide.columns = [f"spend_{c.lower()}" for c in wide.columns]

    wide["total_category_spend"] = wide.sum(axis=1)
    spend_cols = [c for c in wide.columns if c != "total_category_spend"]
    for c in spend_cols:
        wide[f"pct_{c}"] = wide[c] / wide["total_category_spend"].replace(0, pd.NA)

    return wide.reset_index()


def build_master() -> pd.DataFrame:
    profiling = run_query(SQL_DIR / "customer_profiling.sql")
    behavioural = run_query(SQL_DIR / "behavioural_summary.sql")
    category = run_query(SQL_DIR / "category_mix.sql")

    behavioural_agg = aggregate_behavioural_summary(behavioural)
    category_wide = pivot_category_mix(category)

    master = profiling.merge(behavioural_agg, on="customer_id", how="left")
    master = master.merge(category_wide, on="customer_id", how="left")

    return master


def sanity_check(df: pd.DataFrame) -> None:
    print(f"\nCustomer master table: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Distinct customers: {df['customer_id'].nunique()}")

    print("\n--- customers with no behavioural data (never appeared as sender) ---")
    print(df["avg_spend_txn_count"].isna().sum())

    print("\n--- customers with no category spend ---")
    print(df["total_category_spend"].isna().sum())

    print("\n--- column list ---")
    print(list(df.columns))


if __name__ == "__main__":
    master = build_master()
    sanity_check(master)

    out_path = OUTPUT_DIR / "customer_master.csv"
    master.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")
