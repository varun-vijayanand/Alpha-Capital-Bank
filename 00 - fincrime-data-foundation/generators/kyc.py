"""
kyc.py

Generates the KYC (Know Your Customer) table: one row per customer,
capturing compliance-relevant fields used for risk categorization.
Depends on the customers DataFrame (needs customer_id, occupation, income).
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import timedelta

import pandas as pd

from config.config_loader import SETTINGS
from generators.customers import generate_customers


def generate_kyc(customers_df: pd.DataFrame) -> pd.DataFrame:
    """Generate a KYC DataFrame linked to an existing customers DataFrame."""

    seed = SETTINGS["random_seed"]
    random.seed(seed)

    kyc_statuses = ["Verified", "Pending", "Rejected"]
    kyc_status_weights = [90, 7, 3]  # most customers pass KYC cleanly

    source_of_funds_options = [
        "Salary", "Business Income", "Investments",
        "Inheritance", "Rental Income", "Other"
    ]

    records = []
    for _, cust in customers_df.iterrows():
        kyc_status = random.choices(kyc_statuses, weights=kyc_status_weights, k=1)[0]

        # Verification happens shortly AFTER onboarding, not before
        days_after_onboarding = random.randint(1, 30)
        verification_date = cust["onboarding_date"] + timedelta(days=days_after_onboarding)

        # Risk category loosely tied to occupation + income,
        # so it's not disconnected from the customer's actual profile
        if cust["occupation"] in ("Business Owner", "Self-Employed"):
            risk_category = random.choices(
                ["Low", "Medium", "High"], weights=[40, 45, 15], k=1
            )[0]
        elif cust["occupation"] == "Unemployed":
            risk_category = random.choices(
                ["Low", "Medium", "High"], weights=[50, 35, 15], k=1
            )[0]
        else:
            risk_category = random.choices(
                ["Low", "Medium", "High"], weights=[70, 25, 5], k=1
            )[0]

        source_of_funds = random.choice(source_of_funds_options)

        # Expected monthly volume roughly scales with income,
        # with some random variation so it's not a pure formula
        expected_monthly_volume = round(
            cust["income"] * random.uniform(0.6, 1.4), 2
        )

        records.append({
            "customer_id": cust["customer_id"],
            "kyc_status": kyc_status,
            "verification_date": verification_date,
            "risk_category": risk_category,
            "occupation": cust["occupation"],
            "source_of_funds": source_of_funds,
            "expected_monthly_volume": expected_monthly_volume,
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    customers_df = generate_customers()
    kyc_df = generate_kyc(customers_df)
    print(kyc_df.shape)
    print(kyc_df.head())
    print(kyc_df["kyc_status"].value_counts())
    print(kyc_df["risk_category"].value_counts())