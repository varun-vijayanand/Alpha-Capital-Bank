"""
customer_transaction_summary.py

Creates the customer_transaction_summary SQL view and previews it.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text

from config.config_loader import get_db_connection_string


SQL_PATH = Path(__file__).parent / "sql" / "customer_transaction_summary.sql"


def create_view(engine):
    with open(SQL_PATH, "r") as f:
        sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("View 'customer_transaction_summary' created.")


def preview(engine, limit=15):
    query = f"SELECT * FROM customer_transaction_summary ORDER BY monthly_transaction_value DESC LIMIT {limit};"
    df = pd.read_sql(query, engine)
    print(f"\nTop {limit} customer-months by transaction value:")
    print(df)

    total_rows_query = "SELECT COUNT(*) AS total_rows FROM customer_transaction_summary;"
    total = pd.read_sql(total_rows_query, engine)
    print(f"\nTotal rows in view: {total['total_rows'].iloc[0]:,}")


if __name__ == "__main__":
    engine = create_engine(get_db_connection_string())
    create_view(engine)
    preview(engine)