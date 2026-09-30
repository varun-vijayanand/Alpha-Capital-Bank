"""
schema_checks.py

Validates data quality WITHIN each table: uniqueness of primary keys,
completeness of required fields, and temporal validity between
related date columns.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd


def check_uniqueness(df: pd.DataFrame, column: str, table_name: str) -> dict:
    """Confirms a column (usually the primary key) has no duplicate values."""
    duplicate_count = df[column].duplicated().sum()
    passed = duplicate_count == 0
    return {
        "check": f"{table_name}.{column} uniqueness",
        "passed": passed,
        "detail": f"{duplicate_count} duplicate values" if not passed else "",
    }


def check_completeness(df: pd.DataFrame, column: str, table_name: str) -> dict:
    """Confirms a required (non-nullable) column has no missing values."""
    null_count = df[column].isna().sum()
    passed = null_count == 0
    return {
        "check": f"{table_name}.{column} completeness",
        "passed": passed,
        "detail": f"{null_count} null values" if not passed else "",
    }


def check_temporal_order(df: pd.DataFrame, earlier_col: str, later_col: str,
                          table_name: str, allow_null_later: bool = True) -> dict:
    """
    Confirms later_col is always >= earlier_col, wherever later_col is populated.
    E.g. closing_date >= opening_date, verification_date >= onboarding_date.
    """
    subset = df[[earlier_col, later_col]].copy()

    if allow_null_later:
        subset = subset.dropna(subset=[later_col])

    violations = subset[subset[later_col] < subset[earlier_col]]
    passed = len(violations) == 0
    return {
        "check": f"{table_name}: {later_col} >= {earlier_col}",
        "passed": passed,
        "detail": f"{len(violations)} rows violate this order" if not passed else "",
    }


def run_all_schema_checks(data: dict) -> list:
    results = []

    # --- Uniqueness: every primary key should be unique ---
    results.append(check_uniqueness(data["customers"], "customer_id", "customers"))
    results.append(check_uniqueness(data["accounts"], "account_id", "accounts"))
    results.append(check_uniqueness(data["devices"], "device_id", "devices"))
    results.append(check_uniqueness(data["merchants"], "merchant_id", "merchants"))
    results.append(check_uniqueness(data["locations"], "location_id", "locations"))
    results.append(check_uniqueness(data["cards"], "card_id", "cards"))
    results.append(check_uniqueness(data["beneficiaries"], "beneficiary_id", "beneficiaries"))
    results.append(check_uniqueness(data["transactions"], "transaction_id", "transactions"))

    # --- Completeness: required fields should never be null ---
    results.append(check_completeness(data["customers"], "date_of_birth", "customers"))
    results.append(check_completeness(data["customers"], "occupation", "customers"))
    results.append(check_completeness(data["accounts"], "customer_id", "accounts"))
    results.append(check_completeness(data["accounts"], "account_type", "accounts"))
    results.append(check_completeness(data["transactions"], "amount", "transactions"))
    results.append(check_completeness(data["transactions"], "timestamp", "transactions"))
    results.append(check_completeness(data["transactions"], "status", "transactions"))

    # --- Temporal validity: chronological logic between related dates ---
    results.append(check_temporal_order(
        data["accounts"], "opening_date", "closing_date", "accounts"
    ))
    results.append(check_temporal_order(
        data["kyc"].merge(data["customers"][["customer_id", "onboarding_date"]], on="customer_id"),
        "onboarding_date", "verification_date", "kyc"
    ))
    results.append(check_temporal_order(
        data["devices"].merge(data["customers"][["customer_id", "onboarding_date"]], on="customer_id"),
        "onboarding_date", "first_seen", "devices", allow_null_later=False
    ))

    return results


def print_results(results: list):
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\n{'='*60}")
    print(f"SCHEMA / QUALITY CHECK RESULTS: {passed_count}/{len(results)} passed")
    print(f"{'='*60}\n")

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{status}  {r['check']}")
        if not r["passed"]:
            print(f"        {r['detail']}")


if __name__ == "__main__":
    from database.load_data import generate_all_data

    print("Generating data for validation...")
    data = generate_all_data()

    results = run_all_schema_checks(data)
    print_results(results)