"""
beneficiaries.py

Generates the Beneficiaries table: registered payees an account can
send money to. Mix of internal (another Alpha Capital Bank customer's
account) and external (outside bank) beneficiaries.
Each account has 0-5 beneficiaries, skewed toward fewer.
Depends on the accounts DataFrame.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random

import pandas as pd
from faker import Faker

from config.config_loader import SETTINGS


EXTERNAL_BANKS = [
    "HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank",
    "Kotak Mahindra Bank", "Punjab National Bank", "Yes Bank", "IDFC First Bank"
]


def _num_beneficiaries_for_account() -> int:
    """0-5 beneficiaries per account, skewed toward fewer (0-2 most common)."""
    return random.choices([0, 1, 2, 3, 4, 5], weights=[25, 25, 20, 15, 10, 5], k=1)[0]


def generate_beneficiaries(accounts_df: pd.DataFrame) -> pd.DataFrame:
    seed = SETTINGS["random_seed"]
    random.seed(seed)
    fake = Faker("en_IN")
    Faker.seed(seed)

    # Pool of all account_ids, so "internal" beneficiaries can point to real accounts
    all_account_ids = accounts_df["account_id"].tolist()

    records = []
    beneficiary_counter = 1

    def next_beneficiary_id():
        nonlocal beneficiary_counter
        bid = f"B{800000 + beneficiary_counter}"
        beneficiary_counter += 1
        return bid

    for _, acc in accounts_df.iterrows():
        num_beneficiaries = _num_beneficiaries_for_account()

        for _ in range(num_beneficiaries):
            # ~40% internal (another Alpha Capital Bank account), ~60% external
            is_internal = random.random() < 0.40

            if is_internal:
                # Pick any other account as the beneficiary (not the account itself)
                candidate = random.choice(all_account_ids)
                # Avoid an account listing itself as its own beneficiary
                attempts = 0
                while candidate == acc["account_id"] and attempts < 5:
                    candidate = random.choice(all_account_ids)
                    attempts += 1

                records.append({
                    "beneficiary_id": next_beneficiary_id(),
                    "account_id": acc["account_id"],  # the account that ADDED this beneficiary
                    "beneficiary_name": fake.name(),
                    "beneficiary_type": "Internal",
                    "beneficiary_account_id": candidate,   # links to a real Alpha Capital account
                    "beneficiary_bank": "Alpha Capital Bank",
                })
            else:
                records.append({
                    "beneficiary_id": next_beneficiary_id(),
                    "account_id": acc["account_id"],
                    "beneficiary_name": fake.name(),
                    "beneficiary_type": "External",
                    "beneficiary_account_id": None,  # no link into our own account universe
                    "beneficiary_bank": random.choice(EXTERNAL_BANKS),
                })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    from generators.customers import generate_customers
    from generators.accounts import generate_accounts

    customers_df = generate_customers()
    accounts_df = generate_accounts(customers_df)
    beneficiaries_df = generate_beneficiaries(accounts_df)

    print(beneficiaries_df.shape)
    print(beneficiaries_df.head(10))
    print("\nBeneficiary type distribution:")
    print(beneficiaries_df["beneficiary_type"].value_counts())
    print("\nBeneficiaries per account:")
    print(beneficiaries_df.groupby("account_id").size().value_counts().sort_index())