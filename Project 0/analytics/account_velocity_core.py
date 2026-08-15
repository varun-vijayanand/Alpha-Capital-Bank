"""
account_velocity_core.py

Creates the account_velocity_core SQL view and previews it.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text

from config.config_loader import get_db_connection_string


SQL_PATH = Path(__file__).parent / "sql" / "account_velocity_core.sql"


def create_view(engine):
    with open(SQL_PATH, "r") as f:
        sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("View 'account_velocity_core' created.")


def preview(engine):
    # Highest single-transaction 24h velocity spikes — a good first look
    # at whether our scenario-injected bursts actually show up
    query = """
        SELECT account_id, direction, timestamp, amount, txn_count_24h, amount_sum_24h
        FROM account_velocity_core
        ORDER BY txn_count_24h DESC
        LIMIT 15;
    """
    df = pd.read_sql(query, engine)
    print("\nTop 15 rows by 24h transaction count (biggest velocity spikes):")
    print(df)

    total = pd.read_sql("SELECT COUNT(*) AS total_rows FROM account_velocity_core;", engine)
    print(f"\nTotal rows in view: {total['total_rows'].iloc[0]:,}")


if __name__ == "__main__":
    engine = create_engine(get_db_connection_string())
    create_view(engine)
    preview(engine)