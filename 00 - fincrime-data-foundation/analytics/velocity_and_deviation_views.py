"""
velocity_and_deviation_views.py

Creates counterparty_velocity, flow_velocity, and behavioural_deviation
views, then previews each with a scenario-aware check.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text

from config.config_loader import get_db_connection_string


SQL_DIR = Path(__file__).parent / "sql"
VIEWS = ["counterparty_velocity", "flow_velocity", "behavioural_deviation"]


def create_view(engine, view_name):
    sql_path = SQL_DIR / f"{view_name}.sql"
    with open(sql_path, "r") as f:
        sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print(f"View '{view_name}' created.")


def preview_counterparty_velocity(engine):
    query = """
        SELECT a.customer_id, sl.scenario, v.activity_day,
               v.transaction_count, v.unique_counterparties
        FROM counterparty_velocity v
        JOIN accounts a ON v.account_id = a.account_id
        JOIN scenario_labels sl ON a.customer_id = sl.customer_id
        WHERE sl.scenario != 'normal'
        ORDER BY v.unique_counterparties DESC
        LIMIT 15;
    """
    print("\n--- Top scenario accounts by unique counterparties in a single day ---")
    print(pd.read_sql(query, engine))


def preview_flow_velocity(engine):
    query = """
        SELECT a.customer_id, sl.scenario, f.activity_day,
               f.total_inflow, f.total_outflow, f.same_day_outflow_ratio
        FROM flow_velocity f
        JOIN accounts a ON f.account_id = a.account_id
        JOIN scenario_labels sl ON a.customer_id = sl.customer_id
        WHERE sl.scenario != 'normal' AND f.same_day_outflow_ratio IS NOT NULL
        ORDER BY f.same_day_outflow_ratio DESC
        LIMIT 15;
    """
    print("\n--- Top scenario accounts by same-day outflow ratio ---")
    print(pd.read_sql(query, engine))


def preview_behavioural_deviation(engine):
    query = """
        SELECT a.customer_id, sl.scenario, d.timestamp,
               d.current_transaction_value, d.historical_average, d.deviation_from_average
        FROM behavioural_deviation d
        JOIN accounts a ON d.account_id = a.account_id
        JOIN scenario_labels sl ON a.customer_id = sl.customer_id
        WHERE sl.scenario != 'normal' AND d.deviation_from_average IS NOT NULL
        ORDER BY d.deviation_from_average DESC
        LIMIT 15;
    """
    print("\n--- Top scenario transactions by deviation from account's own average ---")
    print(pd.read_sql(query, engine))


if __name__ == "__main__":
    engine = create_engine(get_db_connection_string())

    for view in VIEWS:
        create_view(engine, view)

    preview_counterparty_velocity(engine)
    preview_flow_velocity(engine)
    preview_behavioural_deviation(engine)