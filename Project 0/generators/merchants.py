"""
merchants.py

Generates the Merchants table: a pool of merchants transactions will
reference later. Includes everyday categories (common) and
AML/fraud-relevant higher-risk categories (rare).
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random

import pandas as pd
from faker import Faker

from config.config_loader import SETTINGS
from generators.locations import generate_locations


# Everyday categories: the bulk of merchants
EVERYDAY_CATEGORIES = [
    "Grocery", "Fuel", "Retail", "Restaurants",
    "E-commerce", "Utilities", "Pharmacy", "Electronics"
]

# Higher-risk categories: rare, but deliberately present —
# real-world AML monitoring treats these as elevated-risk merchant types
HIGH_RISK_CATEGORIES = [
    "Crypto Exchange", "Money Service Business", "Jewelry", "Casino/Gaming"
]

BUSINESS_TYPES = ["Sole Proprietor", "Partnership", "Private Limited", "Public Limited"]

def generate_merchants(locations_df: pd.DataFrame) -> pd.DataFrame:
    """Generate a pool of merchants. High-risk categories are deliberately rare."""

    seed = SETTINGS["random_seed"]
    num_merchants = SETTINGS["population"]["num_merchants"]

    random.seed(seed)
    fake = Faker("en_IN")
    Faker.seed(seed)

    # Merchants are mostly domestic, but a small fraction can be international
    # (e.g. an NRI-facing merchant, or a high-risk category more common abroad)
    domestic_locations = locations_df[locations_df["is_domestic"]]["location_id"].tolist()
    international_locations = locations_df[~locations_df["is_domestic"]]["location_id"].tolist()

    records = []
    for i in range(num_merchants):
        merchant_id = f"M{400000 + i}"

        is_high_risk = random.random() < 0.05

        if is_high_risk:
            merchant_category = random.choice(HIGH_RISK_CATEGORIES)
        else:
            merchant_category = random.choice(EVERYDAY_CATEGORIES)

        # ~90% of merchants are domestic, ~10% international
        if random.random() < 0.90:
            location_id = random.choice(domestic_locations)
        else:
            location_id = random.choice(international_locations)

        records.append({
            "merchant_id": merchant_id,
            "merchant_name": fake.company(),
            "merchant_category": merchant_category,
            "business_type": random.choice(BUSINESS_TYPES),
            "location_id": location_id,
            "is_high_risk_category": is_high_risk,
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    from generators.locations import generate_locations

    locations_df = generate_locations()
    df = generate_merchants(locations_df)
    print(df.shape)
    print(df.head(10))
    print("\nCategory distribution:")
    print(df["merchant_category"].value_counts())
    print("\nHigh-risk merchant count:")
    print(df["is_high_risk_category"].value_counts())
    print("\nDomestic vs international merchant locations:")
    print(df["location_id"].isin(locations_df[locations_df["is_domestic"]]["location_id"]).value_counts())