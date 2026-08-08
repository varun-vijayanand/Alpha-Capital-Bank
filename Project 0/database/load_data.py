"""
load_data.py

Runs schema.sql to (re)create all tables, then loads freshly generated
DataFrames into PostgreSQL in dependency order.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

from config.config_loader import get_db_connection_string
from generators.customers import generate_customers
from generators.kyc import generate_kyc
from generators.locations import generate_locations
from generators.accounts import generate_accounts
from generators.devices import generate_devices
from generators.merchants import generate_merchants
from generators.cards import generate_cards
from generators.beneficiaries import generate_beneficiaries
from generators.transactions import generate_transactions


SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def run_schema(engine):
    """Execute schema.sql to drop and recreate all tables fresh."""
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    with engine.connect() as conn:
        # schema.sql has multiple statements separated by ';' —
        # split and run them one at a time inside a transaction
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()

    print("Schema created.")


def generate_all_data() -> dict:
    """Run every generator in dependency order, return a dict of DataFrames."""
    print("Generating customers...")
    customers_df = generate_customers()

    print("Generating locations...")
    locations_df = generate_locations()

    print("Generating KYC...")
    kyc_df = generate_kyc(customers_df)

    print("Generating accounts...")
    accounts_df = generate_accounts(customers_df)

    print("Generating devices...")
    devices_df = generate_devices(customers_df)

    print("Generating merchants...")
    merchants_df = generate_merchants(locations_df)

    print("Generating cards...")
    cards_df = generate_cards(accounts_df)

    print("Generating beneficiaries...")
    beneficiaries_df = generate_beneficiaries(accounts_df)

    print("Generating transactions (this takes a moment)...")
    transactions_df = generate_transactions(
        customers_df, accounts_df, merchants_df, devices_df, locations_df
    )

    return {
        "customers": customers_df,
        "locations": locations_df,
        "kyc": kyc_df,
        "accounts": accounts_df,
        "devices": devices_df,
        "merchants": merchants_df,
        "cards": cards_df,
        "beneficiaries": beneficiaries_df,
        "transactions": transactions_df,
    }


def load_all(engine, data: dict):
    """Load each DataFrame into its matching table, in dependency order."""
    # Same order as table creation — parents before children
    load_order = [
        "customers", "locations", "kyc", "accounts",
        "devices", "merchants", "cards", "beneficiaries", "transactions"
    ]

    for table_name in load_order:
        df = data[table_name]
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Loaded {len(df):,} rows into '{table_name}'")


def main():
    engine = create_engine(get_db_connection_string())

    run_schema(engine)
    data = generate_all_data()
    load_all(engine, data)

    print("\nAll tables created and loaded successfully.")


if __name__ == "__main__":
    main()