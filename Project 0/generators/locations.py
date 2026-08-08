"""
locations.py

Generates the Locations table: a shared pool of physical locations
referenced by both Merchants and Transactions.
Indian locations are grouped by state, with multiple major cities
per state. Plus a small pool of international cities for
NRI/international activity.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random

import pandas as pd

from config.config_loader import SETTINGS


# Grouped by state -> list of major cities in that state
INDIAN_LOCATIONS_BY_STATE = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Delhi": ["New Delhi"],
    "Karnataka": ["Bengaluru", "Mysuru"],
    "Telangana": ["Hyderabad", "Warangal"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Tamil Nadu": ["Chennai", "Coimbatore"],
    "West Bengal": ["Kolkata", "Howrah"],
    "Rajasthan": ["Jaipur", "Udaipur"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Noida"],
    "Kerala": ["Kochi", "Thiruvananthapuram"],
    "Punjab": ["Chandigarh", "Amritsar"],
    "Madhya Pradesh": ["Indore", "Bhopal"],
    "Haryana": ["Gurugram", "Faridabad"],
    "Bihar": ["Patna"],
    "Odisha": ["Bhubaneswar"],
}

INTERNATIONAL_LOCATIONS = [
    ("Dubai", "Dubai", "UAE"),
    ("Singapore", "Singapore", "Singapore"),
    ("London", "England", "UK"),
    ("New York", "New York", "USA"),
    ("Toronto", "Ontario", "Canada"),
]


def generate_locations() -> pd.DataFrame:
    """Generate a pool of locations: multiple major cities per Indian state, plus international."""

    seed = SETTINGS["random_seed"]
    random.seed(seed)

    # Flatten the state->cities dict into a flat list of (city, state, country) tuples
    indian_locations = [
        (city, state, "India")
        for state, cities in INDIAN_LOCATIONS_BY_STATE.items()
        for city in cities
    ]

    all_locations = indian_locations + INTERNATIONAL_LOCATIONS

    records = []
    for i, (city, region, country) in enumerate(all_locations):
        location_id = f"L{500000 + i}"
        records.append({
            "location_id": location_id,
            "city": city,
            "region": region,
            "country": country,
            "is_domestic": country == "India",
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    df = generate_locations()
    print(df.shape)
    print(df.to_string())
    print("\nCities per state:")
    print(df[df["is_domestic"]].groupby("region").size())
    print("\nDomestic vs international:")
    print(df["is_domestic"].value_counts())