"""
accounts.py

Generates the Accounts table: each customer has 1-3 accounts.
account_type is influenced by customer_type and occupation.
Depends on the customers DataFrame (needs customer_id, occupation, customer_type, onboarding_date).
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import timedelta

import pandas as pd

from config.config_loader import SETTINGS
from generators.customers import generate_customers


ACCOUNT_TYPES = ["Savings", "Current", "Salary", "Fixed Deposit"]
BRANCHES = [f"BR{100 + i}" for i in range(20)]  # 20 branches: BR100-BR119
CURRENCIES = ["INR", "USD", "EUR"]
CURRENCY_WEIGHTS = [92, 5, 3]  # mostly domestic currency


def _num_accounts_for_customer() -> int:
    """Most customers get 1 account, fewer get 2, rare few get 3."""
    return random.choices([1, 2, 3], weights=[70, 25, 5], k=1)[0]


def _pick_account_type(occupation: str, customer_type: str) -> str:
    """Account type is influenced by customer segment, not fully random."""

    if customer_type == "Corporate":
        return random.choices(
            ["Current", "Fixed Deposit"], weights=[85, 15], k=1
        )[0]

    if occupation.startswith("Salaried"):
        return random.choices(
            ACCOUNT_TYPES, weights=[35, 10, 45, 10], k=1
        )[0]

    if occupation in ("Business Owner", "Self-Employed"):
        return random.choices(
            ACCOUNT_TYPES, weights=[25, 55, 5, 15], k=1
        )[0]

    if occupation == "Student":
        return random.choices(
            ACCOUNT_TYPES, weights=[80, 5, 0, 15], k=1
        )[0]

    if occupation == "Retired":
        return random.choices(
            ACCOUNT_TYPES, weights=[50, 5, 0, 45], k=1
        )[0]

    # Unemployed and any fallback
    return random.choices(
        ACCOUNT_TYPES, weights=[75, 10, 0, 15], k=1
    )[0]


def generate_accounts(customers_df: pd.DataFrame) -> pd.DataFrame:
    """Generate an Accounts DataFrame, 1-3 rows per customer."""

    seed = SETTINGS["random_seed"]
    random.seed(seed)

    records = []
    account_counter = 1  # global sequential counter across ALL accounts

    for _, cust in customers_df.iterrows():
        num_accounts = _num_accounts_for_customer()

        for _ in range(num_accounts):
            account_id = f"A{200000 + account_counter}"
            account_counter += 1

            account_type = _pick_account_type(cust["occupation"], cust["customer_type"])

            # Account opens on or shortly after customer onboarding
            days_after_onboarding = random.randint(0, 15)
            opening_date = cust["onboarding_date"] + timedelta(days=days_after_onboarding)

            # Most accounts stay open (status = Active); a small fraction closed
            status = random.choices(["Active", "Closed", "Dormant"], weights=[85, 8, 7], k=1)[0]
            closing_date = None
            if status == "Closed":
                # Closed sometime after opening, before "today" (assume sim covers recent history)
                days_open = random.randint(30, 700)
                closing_date = opening_date + timedelta(days=days_open)

            records.append({
                "account_id": account_id,
                "customer_id": cust["customer_id"],
                "account_type": account_type,
                "opening_date": opening_date,
                "closing_date": closing_date,
                "branch_id": random.choice(BRANCHES),
                "currency": random.choices(CURRENCIES, weights=CURRENCY_WEIGHTS, k=1)[0],
                "status": status,
            })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    customers_df = generate_customers()
    accounts_df = generate_accounts(customers_df)
    print(accounts_df.shape)
    print(accounts_df.head(10))
    print("\nAccounts per customer:")
    print(accounts_df.groupby("customer_id").size().value_counts())
    print("\nAccount type distribution:")
    print(accounts_df["account_type"].value_counts())
    print("\nStatus distribution:")
    print(accounts_df["status"].value_counts())