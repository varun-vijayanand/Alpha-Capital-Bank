"""
mule.py

Injects mule-account behaviour: money flows IN from multiple, often
unrelated senders (mix of other Alpha Capital accounts and external),
sits briefly, then flows back OUT to other, often unrelated receivers
(again a mix). Fast pass-through and fan-in/fan-out shape is the
detectable pattern — no transaction is individually flagged.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import date, timedelta, datetime

import pandas as pd

from config.config_loader import SETTINGS


TRANSFER_CHANNELS = ["NEFT", "IMPS", "UPI"]


def _pick_primary_account(cust_accounts: list):
    primary = next((a for a in cust_accounts if a["account_type"] == "Current"), None)
    if primary is None:
        primary = next((a for a in cust_accounts if a["account_type"] == "Savings"), None)
    if primary is None:
        primary = cust_accounts[0]
    return primary


def generate_mule_transactions(customers_df: pd.DataFrame,
                                 accounts_df: pd.DataFrame,
                                 devices_df: pd.DataFrame,
                                 scenario_df: pd.DataFrame) -> pd.DataFrame:
    seed = SETTINGS["random_seed"]
    random.seed(seed)

    sim_start = date.fromisoformat(SETTINGS["simulation"]["start_date"])
    num_months = SETTINGS["simulation"]["months"]

    accounts_by_customer = {}
    for _, acc in accounts_df.iterrows():
        accounts_by_customer.setdefault(acc["customer_id"], []).append(acc)

    devices_by_customer = {}
    for _, dev in devices_df.iterrows():
        devices_by_customer.setdefault(dev["customer_id"], []).append(dev["device_id"])

    all_account_ids = accounts_df["account_id"].tolist()

    mule_customers = scenario_df[scenario_df["scenario"] == "mule"]["customer_id"].tolist()

    records = []
    txn_counter = 1

    def next_txn_id():
        nonlocal txn_counter
        tid = f"TM{910000 + txn_counter}"
        txn_counter += 1
        return tid

    def add_transaction(sender, receiver, amount, currency, device_id, txn_date, txn_time_hour):
        records.append({
            "transaction_id": next_txn_id(),
            "timestamp": datetime.combine(txn_date, datetime.min.time())
                         + timedelta(hours=txn_time_hour, minutes=random.randint(0, 59)),
            "sender_account_id": sender,
            "receiver_account_id": receiver,
            "amount": round(amount, 2),
            "currency": currency,
            "transaction_type": "Transfer",   # ordinary-looking, no fraud tag
            "channel": random.choice(TRANSFER_CHANNELS),
            "merchant_id": None,
            "device_id": device_id,
            "location_id": None,
            "status": "Success",
        })

    for customer_id in mule_customers:
        cust_accounts = accounts_by_customer.get(customer_id, [])
        if not cust_accounts:
            continue
        cust_devices = devices_by_customer.get(customer_id, [])
        device_id = random.choice(cust_devices) if cust_devices else None

        mule_account = _pick_primary_account(cust_accounts)
        own_account_ids = {a["account_id"] for a in cust_accounts}
        currency = mule_account["currency"]

        # Accounts NOT belonging to this customer — pool for "internal" counterparties
        other_account_ids = [a for a in all_account_ids if a not in own_account_ids]

        # A mule account typically runs several in-out cycles across the simulation period
        num_cycles = random.randint(3, 8)

        for _ in range(num_cycles):
            # Pick a random day within the simulation period for this cycle's inflow
            cycle_day_offset = random.randint(0, num_months * 28 - 5)
            inflow_date = sim_start + timedelta(days=cycle_day_offset)

            # --- FAN-IN: 2-5 inbound transactions from unrelated senders ---
            num_senders = random.randint(2, 5)
            total_inflow = 0

            for _ in range(num_senders):
                is_internal = random.random() < 0.5
                sender_id = random.choice(other_account_ids) if is_internal else None

                amount = random.uniform(15000, 250000)
                total_inflow += amount

                # Senders trickle in over a short window (same day to 2 days)
                txn_date = inflow_date + timedelta(days=random.randint(0, 2))
                add_transaction(
                    sender=sender_id, receiver=mule_account["account_id"],
                    amount=amount, currency=currency, device_id=device_id,
                    txn_date=txn_date, txn_time_hour=random.randint(9, 20),
                )

            # --- FAST PASS-THROUGH: money leaves again shortly after ---
            # Weighted toward FAST (0-1 days most common, up to 3 days)
            pass_through_delay = random.choices([0, 1, 2, 3], weights=[40, 35, 15, 10], k=1)[0]
            outflow_date = inflow_date + timedelta(days=pass_through_delay + 2)  # after fan-in window

            # --- FAN-OUT: 1-3 outbound transactions, sending most of it back out ---
            num_receivers = random.randint(1, 3)
            # Keep a small residue (mule accounts don't always empty to zero)
            amount_to_move_out = total_inflow * random.uniform(0.90, 0.98)
            per_receiver = amount_to_move_out / num_receivers

            for _ in range(num_receivers):
                is_internal = random.random() < 0.5
                receiver_id = random.choice(other_account_ids) if is_internal else None

                txn_date = outflow_date + timedelta(days=random.randint(0, 1))
                add_transaction(
                    sender=mule_account["account_id"], receiver=receiver_id,
                    amount=per_receiver, currency=currency, device_id=device_id,
                    txn_date=txn_date, txn_time_hour=random.randint(9, 20),
                )

    return pd.DataFrame(records)


if __name__ == "__main__":
    from generators.customers import generate_customers
    from generators.accounts import generate_accounts
    from generators.devices import generate_devices
    from scenarios.assign_scenarios import assign_scenarios

    customers_df = generate_customers()
    accounts_df = generate_accounts(customers_df)
    devices_df = generate_devices(customers_df)
    scenario_df = assign_scenarios(customers_df)

    mule_txns = generate_mule_transactions(customers_df, accounts_df, devices_df, scenario_df)

    print(mule_txns.shape)
    print(mule_txns.head(10))

    print("\nInternal vs external counterparties:")
    print("Sender is internal (non-null):", mule_txns["sender_account_id"].notna().sum())
    print("Receiver is internal (non-null):", mule_txns["receiver_account_id"].notna().sum())

    # Inspect one mule account's full cycle
    example_customer_id = scenario_df[scenario_df["scenario"] == "mule"]["customer_id"].iloc[0]
    example_accounts = accounts_df[accounts_df["customer_id"] == example_customer_id]["account_id"].tolist()
    example = mule_txns[
        (mule_txns["sender_account_id"].isin(example_accounts)) |
        (mule_txns["receiver_account_id"].isin(example_accounts))
    ].sort_values("timestamp")
    print(f"\nExample mule account {example_accounts}, full transaction history:")
    print(example[["timestamp", "sender_account_id", "receiver_account_id", "amount"]])