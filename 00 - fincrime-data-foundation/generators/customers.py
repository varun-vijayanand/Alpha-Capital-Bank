"""
customers.py

Generates the Customer table: one row per synthetic customer,
with realistic demographic and onboarding fields.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from config.config_loader import SETTINGS


def generate_customers() -> pd.DataFrame:
    """Generate a DataFrame of synthetic customers based on settings.yaml."""

    seed = SETTINGS["random_seed"]
    num_customers = SETTINGS["population"]["num_customers"]
    sim_start = date.fromisoformat(SETTINGS["simulation"]["start_date"])

    random.seed(seed)
    fake = Faker("en_IN")
    Faker.seed(seed)

    occupations = [
    "Salaried - IT", "Salaried - Government", "Self-Employed",
    "Business Owner", "Student", "Retired", "Unemployed"
    ]

    # Weights control how LIKELY each occupation is to be picked.
    # Higher weight = more common. These don't need to sum to 100 or 1 —
    # random.choices() normalizes them internally.

    occupation_weights = [
        25,  # Salaried - IT
        20,  # Salaried - Government
        15,  # Self-Employed
        10,  # Business Owner
        12,  # Student
        13,  # Retired
        5,   # Unemployed — deliberately rare
    ]
    residencies = ["Resident", "Non-Resident"]
    customer_types = ["Individual", "Joint", "Corporate"]

    # Maps each occupation to a customer_id prefix segment
    occupation_prefix_map = {
        "Salaried - IT": "SAL",
        "Salaried - Government": "SAL",
        "Self-Employed": "BUS",
        "Business Owner": "BUS",
        "Student": "STU",
        "Retired": "RET",
        "Unemployed": "UEM",
    }

    # Realistic age ranges per occupation
    occupation_age_ranges = {
        "Salaried - IT": (22, 58),
        "Salaried - Government": (23, 60),
        "Self-Employed": (25, 65),
        "Business Owner": (28, 70),
        "Student": (18, 26),
        "Retired": (60, 85),
        "Unemployed": (20, 60),
    }
    # Tracks the next sequence number for EACH prefix independently
    prefix_counters = {prefix: 100000 for prefix in set(occupation_prefix_map.values())}

    records = []
    for i in range(num_customers):
        occupation = random.choices(occupations, weights=occupation_weights, k=1)[0]
        prefix = occupation_prefix_map[occupation]

        # Pull this prefix's current counter, then increment it for next time
        seq = prefix_counters[prefix]
        prefix_counters[prefix] += 1
        customer_id = f"{prefix}{seq}"

        min_age, max_age = occupation_age_ranges[occupation]
        dob = fake.date_of_birth(minimum_age=min_age, maximum_age=max_age)

        if occupation == "Business Owner":
            income = random.randint(80000, 500000)
        elif occupation.startswith("Salaried"):
            income = random.randint(25000, 150000)
        elif occupation == "Self-Employed":
            income = random.randint(20000, 200000)
        elif occupation == "Student":
            income = random.randint(0, 15000)
        elif occupation == "Unemployed":
            income = random.randint(2000, 12000)  # benefits / family support / dwindling savings
        else:  # Retired
            income = random.randint(10000, 60000)

        days_before_start = random.randint(0, 730)
        onboarding_date = sim_start - timedelta(days=days_before_start)

        records.append({
            "customer_id": customer_id,
            "date_of_birth": dob,
            "occupation": occupation,
            "income": income,
            "residency": random.choice(residencies),
            "customer_type": random.choice(customer_types),
            "onboarding_date": onboarding_date,
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    df = generate_customers()
    print(df.shape)
    print(df.head())
    print(df["occupation"].value_counts())