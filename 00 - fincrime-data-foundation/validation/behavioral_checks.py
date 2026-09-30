"""
behavioural_checks.py

Validates that customer financial behaviour is plausible relative to
their declared profile — e.g. a customer's actual monthly transaction
volume shouldn't wildly exceed their declared income/expected volume,
unless that mismatch is intentional (a fraud scenario).

Right now, on pure "normal" data, these should all pass. This same
logic becomes the detection tool once scenarios are injected later.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd


def check_income_vs_transaction_volume(customers_df: pd.DataFrame,
                                         transactions_df: pd.DataFrame,
                                         accounts_df: pd.DataFrame,
                                         num_months: int,
                                         multiplier: float = 5.0) -> dict:
    """
    Flags customers whose average MONTHLY outgoing transaction volume
    is more than `multiplier` times their declared income.
    A normal customer's spending should roughly track their income,
    not dwarf it by 5x+.
    """
    # Map every account back to its owning customer
    account_to_customer = dict(zip(accounts_df["account_id"], accounts_df["customer_id"]))

    # Only count OUTGOING money (sender_account_id present) as "spending volume"
    outgoing = transactions_df.dropna(subset=["sender_account_id"]).copy()
    outgoing["customer_id"] = outgoing["sender_account_id"].map(account_to_customer)

    monthly_volume_by_customer = (
        outgoing.groupby("customer_id")["amount"].sum() / num_months
    )

    merged = customers_df.set_index("customer_id").join(
        monthly_volume_by_customer.rename("avg_monthly_outgoing")
    )
    merged["avg_monthly_outgoing"] = merged["avg_monthly_outgoing"].fillna(0)

    # Avoid dividing by zero for Unemployed/zero-income customers —
    # use a small floor so we don't get infinite ratios
    income_floor = merged["income"].clip(lower=1000)
    merged["volume_to_income_ratio"] = merged["avg_monthly_outgoing"] / income_floor

    violations = merged[merged["volume_to_income_ratio"] > multiplier]
    passed = len(violations) == 0

    return {
        "check": f"avg monthly spending <= {multiplier}x declared income",
        "passed": passed,
        "detail": f"{len(violations)} customers exceed this ratio" if not passed else "",
        "violations_sample": violations.head(5)[["income", "avg_monthly_outgoing", "volume_to_income_ratio"]] if not passed else None,
    }


def check_expected_vs_actual_kyc_volume(kyc_df: pd.DataFrame,
                                          transactions_df: pd.DataFrame,
                                          accounts_df: pd.DataFrame,
                                          num_months: int,
                                          multiplier: float = 3.0) -> dict:
    """
    Flags customers whose actual monthly volume exceeds what they
    DECLARED to the bank at KYC time (expected_monthly_volume) by
    more than `multiplier`x. This is closer to a real bank's KYC
    breach check than the income comparison above.
    """
    account_to_customer = dict(zip(accounts_df["account_id"], accounts_df["customer_id"]))

    outgoing = transactions_df.dropna(subset=["sender_account_id"]).copy()
    outgoing["customer_id"] = outgoing["sender_account_id"].map(account_to_customer)

    monthly_volume_by_customer = (
        outgoing.groupby("customer_id")["amount"].sum() / num_months
    )

    merged = kyc_df.set_index("customer_id").join(
        monthly_volume_by_customer.rename("avg_monthly_outgoing")
    )
    merged["avg_monthly_outgoing"] = merged["avg_monthly_outgoing"].fillna(0)

    expected_floor = merged["expected_monthly_volume"].clip(lower=1000)
    merged["actual_to_expected_ratio"] = merged["avg_monthly_outgoing"] / expected_floor

    violations = merged[merged["actual_to_expected_ratio"] > multiplier]
    passed = len(violations) == 0

    return {
        "check": f"avg monthly spending <= {multiplier}x KYC-declared expected volume",
        "passed": passed,
        "detail": f"{len(violations)} customers exceed this ratio" if not passed else "",
        "violations_sample": violations.head(5)[["expected_monthly_volume", "avg_monthly_outgoing", "actual_to_expected_ratio"]] if not passed else None,
    }


def run_all_behavioural_checks(data: dict, num_months: int) -> list:
    results = []
    results.append(check_income_vs_transaction_volume(
        data["customers"], data["transactions"], data["accounts"], num_months
    ))
    results.append(check_expected_vs_actual_kyc_volume(
        data["kyc"], data["transactions"], data["accounts"], num_months
    ))
    return results


def print_results(results: list):
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\n{'='*60}")
    print(f"BEHAVIOURAL VALIDITY CHECK RESULTS: {passed_count}/{len(results)} passed")
    print(f"{'='*60}\n")

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{status}  {r['check']}")
        if not r["passed"]:
            print(f"        {r['detail']}")
            print(r["violations_sample"])


if __name__ == "__main__":
    from database.load_data import generate_all_data
    from config.config_loader import SETTINGS

    print("Generating data for validation...")
    data = generate_all_data()

    num_months = SETTINGS["simulation"]["months"]
    results = run_all_behavioural_checks(data, num_months)
    print_results(results)