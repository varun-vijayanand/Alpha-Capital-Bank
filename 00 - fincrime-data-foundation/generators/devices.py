"""
devices.py

Generates the Devices table: each customer has 1-2 devices.
Younger customers mostly have 1 (mobile-first); older customers
more often have 2 (mobile + laptop).
Depends on the customers DataFrame (needs customer_id, date_of_birth).
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from config.config_loader import SETTINGS


DEVICE_TYPES_MOBILE = ["Mobile"]
DEVICE_TYPES_ALL = ["Mobile", "Laptop"]

MOBILE_OS = ["iOS", "Android"]
LAPTOP_OS = ["Windows", "macOS", "Linux"]

TODAY = date(2026, 8, 8)  # reference point for computing age


def _customer_age(dob: date) -> int:
    return TODAY.year - dob.year - ((TODAY.month, TODAY.day) < (dob.month, dob.day))


def _num_devices_for_customer(age: int) -> int:
    """Younger customers mostly get 1 device; older customers more often get 2."""
    if age < 40:
        return random.choices([1, 2], weights=[85, 15], k=1)[0]
    elif age < 60:
        return random.choices([1, 2], weights=[60, 40], k=1)[0]
    else:
        return random.choices([1, 2], weights=[45, 55], k=1)[0]


def generate_devices(customers_df: pd.DataFrame) -> pd.DataFrame:
    """Generate a Devices DataFrame, 1-2 rows per customer."""

    seed = SETTINGS["random_seed"]
    random.seed(seed)
    fake = Faker("en_IN")
    Faker.seed(seed)

    sim_start = date.fromisoformat(SETTINGS["simulation"]["start_date"])

    records = []
    device_counter = 1

    for _, cust in customers_df.iterrows():
        age = _customer_age(cust["date_of_birth"])
        num_devices = _num_devices_for_customer(age)

        # First device is always Mobile (mobile-first assumption).
        # Second device, if any, is a Laptop.
        device_types_for_customer = ["Mobile"] if num_devices == 1 else ["Mobile", "Laptop"]

        for device_type in device_types_for_customer:
            device_id = f"D{300000 + device_counter}"
            device_counter += 1

            operating_system = (
                random.choice(MOBILE_OS) if device_type == "Mobile"
                else random.choice(LAPTOP_OS)
            )

            # first_seen: sometime around onboarding (device already in use, or bought shortly after)
            days_offset = random.randint(0, 30)
            first_seen = cust["onboarding_date"] + timedelta(days=days_offset)
            # Don't let first_seen be in the "future" relative to simulation start
            if first_seen > sim_start:
                first_seen = sim_start

            records.append({
                "device_id": device_id,
                "customer_id": cust["customer_id"],
                "device_type": device_type,
                "operating_system": operating_system,
                "ip_address": fake.ipv4_public(),
                "first_seen": first_seen,
            })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    from generators.customers import generate_customers

    customers_df = generate_customers()
    devices_df = generate_devices(customers_df)
    print(devices_df.shape)
    print(devices_df.head(10))
    print("\nDevices per customer:")
    print(devices_df.groupby("customer_id").size().value_counts())
    print("\nDevice type distribution:")
    print(devices_df["device_type"].value_counts())