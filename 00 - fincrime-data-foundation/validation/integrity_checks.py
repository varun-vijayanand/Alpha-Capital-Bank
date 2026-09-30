"""
integrity_checks.py

Validates referential integrity across the generated DataFrames —
catches orphaned foreign keys BEFORE they ever reach PostgreSQL.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd


def check_foreign_key(child_df: pd.DataFrame, child_col: str,
                       parent_df: pd.DataFrame, parent_col: str,
                       relationship_name: str, allow_null: bool = False) -> dict:
    """
    Confirms every non-null value in child_df[child_col] exists in parent_df[parent_col].
    Returns a result dict instead of raising, so we can run every check and report all failures at once.
    """
    child_values = child_df[child_col]

    if allow_null:
        child_values = child_values.dropna()

    valid_parent_values = set(parent_df[parent_col])
    orphaned = child_values[~child_values.isin(valid_parent_values)]

    passed = len(orphaned) == 0
    return {
        "check": relationship_name,
        "passed": passed,
        "orphaned_count": len(orphaned),
        "sample_orphans": orphaned.unique()[:5].tolist() if not passed else [],
    }


def run_all_integrity_checks(data: dict) -> list:
    """
    data: dict of {table_name: DataFrame}, same shape as generate_all_data() output.
    Returns a list of result dicts, one per relationship checked.
    """
    results = []

    results.append(check_foreign_key(
        data["kyc"], "customer_id", data["customers"], "customer_id",
        "kyc.customer_id -> customers.customer_id"
    ))
    results.append(check_foreign_key(
        data["accounts"], "customer_id", data["customers"], "customer_id",
        "accounts.customer_id -> customers.customer_id"
    ))
    results.append(check_foreign_key(
        data["devices"], "customer_id", data["customers"], "customer_id",
        "devices.customer_id -> customers.customer_id"
    ))
    results.append(check_foreign_key(
        data["merchants"], "location_id", data["locations"], "location_id",
        "merchants.location_id -> locations.location_id"
    ))
    results.append(check_foreign_key(
        data["cards"], "customer_id", data["customers"], "customer_id",
        "cards.customer_id -> customers.customer_id"
    ))
    results.append(check_foreign_key(
        data["cards"], "account_id", data["accounts"], "account_id",
        "cards.account_id -> accounts.account_id", allow_null=True
    ))
    results.append(check_foreign_key(
        data["beneficiaries"], "account_id", data["accounts"], "account_id",
        "beneficiaries.account_id -> accounts.account_id"
    ))
    results.append(check_foreign_key(
        data["beneficiaries"], "beneficiary_account_id", data["accounts"], "account_id",
        "beneficiaries.beneficiary_account_id -> accounts.account_id", allow_null=True
    ))
    results.append(check_foreign_key(
        data["transactions"], "sender_account_id", data["accounts"], "account_id",
        "transactions.sender_account_id -> accounts.account_id", allow_null=True
    ))
    results.append(check_foreign_key(
        data["transactions"], "receiver_account_id", data["accounts"], "account_id",
        "transactions.receiver_account_id -> accounts.account_id", allow_null=True
    ))
    results.append(check_foreign_key(
        data["transactions"], "merchant_id", data["merchants"], "merchant_id",
        "transactions.merchant_id -> merchants.merchant_id", allow_null=True
    ))
    results.append(check_foreign_key(
        data["transactions"], "device_id", data["devices"], "device_id",
        "transactions.device_id -> devices.device_id", allow_null=True
    ))
    results.append(check_foreign_key(
        data["transactions"], "location_id", data["locations"], "location_id",
        "transactions.location_id -> locations.location_id", allow_null=True
    ))

    return results


def print_results(results: list):
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\n{'='*60}")
    print(f"INTEGRITY CHECK RESULTS: {passed_count}/{len(results)} passed")
    print(f"{'='*60}\n")

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{status}  {r['check']}")
        if not r["passed"]:
            print(f"        {r['orphaned_count']} orphaned values, e.g. {r['sample_orphans']}")


if __name__ == "__main__":
    from database.load_data import generate_all_data

    print("Generating data for validation...")
    data = generate_all_data()

    results = run_all_integrity_checks(data)
    print_results(results)