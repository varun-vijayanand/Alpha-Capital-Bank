"""
cards.py

Generates the Cards table: debit cards tied to Savings/Current/Salary
accounts (not Fixed Deposit), plus separate credit cards tied to the
customer directly (not any one account).
Depends on the accounts DataFrame (needs account_id, customer_id,
account_type, opening_date, status).
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import timedelta

import pandas as pd

from config.config_loader import SETTINGS


DEBIT_ELIGIBLE_ACCOUNT_TYPES = {"Savings", "Current", "Salary"}


def generate_cards(accounts_df: pd.DataFrame) -> pd.DataFrame:
    """Generate debit cards per eligible account, plus credit cards for some customers."""

    seed = SETTINGS["random_seed"]
    random.seed(seed)

    records = []
    card_counter = 1

    def next_card_id():
        nonlocal card_counter
        cid = f"CRD{700000 + card_counter}"
        card_counter += 1
        return cid

    # --- 1. Debit cards: one per eligible account (Savings/Current/Salary) ---
    eligible_accounts = accounts_df[accounts_df["account_type"].isin(DEBIT_ELIGIBLE_ACCOUNT_TYPES)]

    for _, acc in eligible_accounts.iterrows():
        # Not every eligible account has a card (some customers opt out / haven't collected it yet)
        if random.random() < 0.90:  # 90% of eligible accounts get a debit card
            issue_offset = random.randint(0, 10)
            issue_date = acc["opening_date"] + timedelta(days=issue_offset)

            # Card status mostly mirrors account status, but cards can also be
            # individually blocked (e.g. reported lost) even if account is Active
            if acc["status"] == "Closed":
                status = "Cancelled"
            else:
                status = random.choices(
                    ["Active", "Blocked", "Expired"], weights=[92, 5, 3], k=1
                )[0]

            records.append({
                "card_id": next_card_id(),
                "customer_id": acc["customer_id"],
                "account_id": acc["account_id"],
                "card_type": "Debit",
                "issue_date": issue_date,
                "status": status,
            })

    # --- 2. Credit cards: some customers get one, not tied to a specific account ---
    unique_customers = accounts_df["customer_id"].unique()

    for customer_id in unique_customers:
        if random.random() < 0.35:  # ~35% of customers have a credit card
            # Base issue date roughly around when their first account opened
            first_account_date = accounts_df[accounts_df["customer_id"] == customer_id]["opening_date"].min()
            issue_offset = random.randint(30, 200)  # credit cards usually come a bit after account opening
            issue_date = first_account_date + timedelta(days=issue_offset)

            status = random.choices(
                ["Active", "Blocked", "Expired"], weights=[90, 6, 4], k=1
            )[0]

            records.append({
                "card_id": next_card_id(),
                "customer_id": customer_id,
                "account_id": None,  # credit card isn't tied to one specific account
                "card_type": "Credit",
                "issue_date": issue_date,
                "status": status,
            })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    from generators.customers import generate_customers
    from generators.accounts import generate_accounts

    customers_df = generate_customers()
    accounts_df = generate_accounts(customers_df)
    cards_df = generate_cards(accounts_df)

    print(cards_df.shape)
    print(cards_df.head(10))
    print("\nCard type distribution:")
    print(cards_df["card_type"].value_counts())
    print("\nCard status distribution:")
    print(cards_df["status"].value_counts())
    print("\nDebit cards per eligible account type check (should exclude Fixed Deposit):")
    merged = cards_df.merge(accounts_df, on="account_id", how="left")
    print(merged[merged["card_type"] == "Debit"]["account_type"].value_counts())