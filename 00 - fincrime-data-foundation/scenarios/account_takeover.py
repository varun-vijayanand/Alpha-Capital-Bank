"""
account_takeover.py

Injects account takeover (ATO) behaviour as a BEHAVIOURAL TRANSITION,
not a hard switch:

  Normal behaviour (already exists) → takeover event → behavioural
  transition (new device, new location, new beneficiary, unusual
  timing, velocity spike) → some normal activity continues alongside it

The customer's normal monthly transactions (generated separately by
transactions.py) keep running throughout — legitimate recurring
payments don't stop. This module ADDS the attacker's transactions on
top, plus a new device and new beneficiary the attacker introduces.
No transaction is individually tagged as fraud; the ground truth is
only in scenario_df.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import date, timedelta, datetime

import pandas as pd
from faker import Faker

from config.config_loader import SETTINGS


ATO_CHANNELS = ["Mobile Banking", "UPI", "IMPS"]
ATO_MOBILE_OS = ["Android", "iOS"]


def _pick_target_account(cust_accounts: list):
    """Attacker targets whichever account looks most liquid/active."""
    target = next((a for a in cust_accounts if a["account_type"] == "Current"), None)
    if target is None:
        target = next((a for a in cust_accounts if a["account_type"] == "Savings"), None)
    if target is None:
        target = cust_accounts[0]
    return target


def generate_account_takeover_data(customers_df: pd.DataFrame,
                                     accounts_df: pd.DataFrame,
                                     devices_df: pd.DataFrame,
                                     locations_df: pd.DataFrame,
                                     scenario_df: pd.DataFrame):
    """
    Returns a tuple of THREE DataFrames:
      - ato_transactions_df : the attacker's transactions
      - extra_devices_df    : new device(s) introduced at takeover
      - extra_beneficiaries_df : new beneficiary(ies) the attacker adds
    These get concatenated onto the main devices/beneficiaries/transactions
    tables when everything is loaded together.
    """
    seed = SETTINGS["random_seed"]
    random.seed(seed)
    fake = Faker("en_IN")
    Faker.seed(seed)

    sim_start = date.fromisoformat(SETTINGS["simulation"]["start_date"])
    num_months = SETTINGS["simulation"]["months"]

    accounts_by_customer = {}
    for _, acc in accounts_df.iterrows():
        accounts_by_customer.setdefault(acc["customer_id"], []).append(acc)

    all_account_ids = accounts_df["account_id"].tolist()

    # Prefer international locations for the "unusual location" signal —
    # maximally different from a domestic customer's normal home location
    international_location_ids = locations_df[~locations_df["is_domestic"]]["location_id"].tolist()
    domestic_location_ids = locations_df[locations_df["is_domestic"]]["location_id"].tolist()

    ato_customers = scenario_df[scenario_df["scenario"] == "account_takeover"]["customer_id"].tolist()

    txn_records = []
    device_records = []
    beneficiary_records = []

    txn_counter = 1
    device_counter = 1
    beneficiary_counter = 1

    def next_txn_id():
        nonlocal txn_counter
        tid = f"TA{920000 + txn_counter}"
        txn_counter += 1
        return tid

    def next_device_id():
        nonlocal device_counter
        did = f"D{390000 + device_counter}"
        device_counter += 1
        return did

    def next_beneficiary_id():
        nonlocal beneficiary_counter
        bid = f"B{890000 + beneficiary_counter}"
        beneficiary_counter += 1
        return bid

    for customer_id in ato_customers:
        cust = customers_df[customers_df["customer_id"] == customer_id].iloc[0]
        cust_accounts = accounts_by_customer.get(customer_id, [])
        if not cust_accounts:
            continue

        target_account = _pick_target_account(cust_accounts)
        currency = target_account["currency"]
        own_account_ids = {a["account_id"] for a in cust_accounts}
        other_account_ids = [a for a in all_account_ids if a not in own_account_ids]

        # --- Takeover event: pick a date, leaving room for a post-ATO tail ---
        latest_possible_offset = max((num_months - 2) * 28, 30)  # leave ~2 months of "after" runway
        takeover_offset_days = random.randint(30, latest_possible_offset)
        takeover_date = sim_start + timedelta(days=takeover_offset_days)

        # --- ATO indicator 1: a new device appears, first seen exactly at takeover ---
        new_device_id = next_device_id()
        device_records.append({
            "device_id": new_device_id,
            "customer_id": customer_id,
            "device_type": "Mobile",
            "operating_system": random.choice(ATO_MOBILE_OS),
            "ip_address": fake.ipv4_public(),
            "first_seen": takeover_date,
        })

        # --- ATO indicator 2: unusual location (mostly international, some far domestic) ---
        if random.random() < 0.7:
            unusual_location = random.choice(international_location_ids)
        else:
            unusual_location = random.choice(domestic_location_ids)

        # --- ATO indicator 3: a new beneficiary the attacker adds, to receive stolen funds ---
        is_internal_beneficiary = random.random() < 0.5
        beneficiary_account_id = random.choice(other_account_ids) if is_internal_beneficiary else None
        new_beneficiary_id = next_beneficiary_id()
        beneficiary_records.append({
            "beneficiary_id": new_beneficiary_id,
            "account_id": target_account["account_id"],
            "beneficiary_name": fake.name(),
            "beneficiary_type": "Internal" if is_internal_beneficiary else "External",
            "beneficiary_account_id": beneficiary_account_id,
            "beneficiary_bank": "Alpha Capital Bank" if is_internal_beneficiary else random.choice(
                ["HDFC Bank", "ICICI Bank", "Yes Bank", "Kotak Mahindra Bank"]
            ),
        })

        # --- Behavioural transition: a burst of transactions over 1-4 days ---
        burst_days = random.randint(1, 4)

        # Rough sense of "typical" transaction size for THIS customer, so the
        # spike is relative to them, not a flat number — a low earner's spike
        # looks different in absolute terms than a high earner's
        baseline_txn_size = max(cust["income"] * 0.15, 3000)

        # First move: one deliberately LARGE transaction (testing the account) —
        # matches the brief's "Large transaction" step
        large_amount = baseline_txn_size * random.uniform(4, 9)
        large_txn_date = takeover_date
        odd_hour = random.choice([1, 2, 3, 4, 23])  # unusual login time

        txn_records.append({
            "transaction_id": next_txn_id(),
            "timestamp": datetime.combine(large_txn_date, datetime.min.time())
                         + timedelta(hours=odd_hour, minutes=random.randint(0, 59)),
            "sender_account_id": target_account["account_id"],
            "receiver_account_id": beneficiary_account_id,  # None if external
            "amount": round(large_amount, 2),
            "currency": currency,
            "transaction_type": "Fund Transfer",
            "channel": random.choice(ATO_CHANNELS),
            "merchant_id": None,
            "device_id": new_device_id,
            "location_id": unusual_location,
            "status": "Success",
        })

        # Then: several smaller RAPID transfers over the burst window,
        # spreading money to a mix of the new beneficiary and other accounts —
        # matches "money may move through multiple accounts"
        num_rapid_transfers = random.randint(3, 6)
        for _ in range(num_rapid_transfers):
            rapid_amount = baseline_txn_size * random.uniform(1.5, 4)
            day_offset = random.randint(0, burst_days)
            txn_date = takeover_date + timedelta(days=day_offset)
            odd_hour = random.choice([0, 1, 2, 3, 4, 22, 23])

            receiver = random.choice(
                [beneficiary_account_id] + other_account_ids
            ) if random.random() < 0.9 else None  # occasionally external, no account id

            txn_records.append({
                "transaction_id": next_txn_id(),
                "timestamp": datetime.combine(txn_date, datetime.min.time())
                             + timedelta(hours=odd_hour, minutes=random.randint(0, 59)),
                "sender_account_id": target_account["account_id"],
                "receiver_account_id": receiver,
                "amount": round(rapid_amount, 2),
                "currency": currency,
                "transaction_type": "Fund Transfer",
                "channel": random.choice(ATO_CHANNELS),
                "merchant_id": None,
                "device_id": new_device_id,
                "location_id": unusual_location,
                "status": "Success",
            })

        # Note: we do NOT touch or stop this customer's normal monthly
        # transactions generated elsewhere — those keep running throughout,
        # which is exactly the "some normal transactions continue" behaviour.

    return (
        pd.DataFrame(txn_records),
        pd.DataFrame(device_records),
        pd.DataFrame(beneficiary_records),
    )


if __name__ == "__main__":
    from generators.customers import generate_customers
    from generators.accounts import generate_accounts
    from generators.devices import generate_devices
    from generators.locations import generate_locations
    from scenarios.assign_scenarios import assign_scenarios

    customers_df = generate_customers()
    accounts_df = generate_accounts(customers_df)
    devices_df = generate_devices(customers_df)
    locations_df = generate_locations()
    scenario_df = assign_scenarios(customers_df)

    ato_txns, extra_devices, extra_beneficiaries = generate_account_takeover_data(
        customers_df, accounts_df, devices_df, locations_df, scenario_df
    )

    print("ATO transactions:", ato_txns.shape)
    print("New devices introduced:", extra_devices.shape)
    print("New beneficiaries introduced:", extra_beneficiaries.shape)

    example_customer_id = scenario_df[scenario_df["scenario"] == "account_takeover"]["customer_id"].iloc[0]
    example_device = extra_devices[extra_devices["customer_id"] == example_customer_id]
    print(f"\nNew device for {example_customer_id}:")
    print(example_device)

    example_accounts = accounts_df[accounts_df["customer_id"] == example_customer_id]["account_id"].tolist()
    example_txns = ato_txns[ato_txns["sender_account_id"].isin(example_accounts)].sort_values("timestamp")
    print(f"\nATO burst transactions for {example_customer_id}:")
    print(example_txns[["timestamp", "amount", "receiver_account_id", "device_id", "location_id"]])