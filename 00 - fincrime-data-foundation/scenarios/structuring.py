"""
structuring.py

Injects structuring behaviour: a customer moves a large sum of money
by deliberately splitting it into several transactions, each kept
under the real CTR (Cash Transaction Report) reporting threshold.

The "big sum" is scaled to the customer's own annual income, so it's
proportionate to who they are — not a flat number applied to everyone.
Transactions themselves carry NO fraud label; only scenario_df (built
separately) marks these customers as ground truth.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import date, timedelta, datetime

import pandas as pd

from config.config_loader import SETTINGS


CTR_THRESHOLD = 1_000_000  # ₹10,00,000 — the real Indian CTR reporting threshold
DEPOSIT_CHANNELS = ["Cash", "NEFT", "IMPS"]


def _split_into_chunks(total: float) -> list:
    """
    Splits `total` into chunks, each deliberately kept under CTR_THRESHOLD
    (specifically 65-95% of it). Avoids leaving a tiny leftover final
    chunk UNLESS folding it in would push the chunk over the threshold —
    in that case, the small leftover becomes its own final chunk instead.
    """
    chunks = []
    remaining = total

    while remaining > 0:
        cap = CTR_THRESHOLD * random.uniform(0.65, 0.95)
        chunk = min(remaining, cap)

        leftover_after = remaining - chunk
        # Only fold the leftover in if doing so STILL keeps the chunk
        # safely under the threshold — never fold if it would cross the line
        if 0 < leftover_after < CTR_THRESHOLD * 0.1 and (chunk + leftover_after) < CTR_THRESHOLD:
            chunk = remaining

        chunks.append(chunk)
        remaining -= chunk

    return chunks


def _pick_primary_account(cust_accounts: list):
    primary = next((a for a in cust_accounts if a["account_type"] == "Salary"), None)
    if primary is None:
        primary = next((a for a in cust_accounts if a["account_type"] == "Current"), None)
    if primary is None:
        primary = cust_accounts[0]
    return primary


def generate_structuring_transactions(customers_df: pd.DataFrame,
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

    structuring_customers = scenario_df[scenario_df["scenario"] == "structuring"]["customer_id"].tolist()

    records = []
    txn_counter = 1

    def next_txn_id():
        nonlocal txn_counter
        tid = f"TS{900000 + txn_counter}"
        txn_counter += 1
        return tid

    for customer_id in structuring_customers:
        cust = customers_df[customers_df["customer_id"] == customer_id].iloc[0]
        cust_accounts = accounts_by_customer.get(customer_id, [])
        if not cust_accounts:
            continue
        cust_devices = devices_by_customer.get(customer_id, [])

        primary = _pick_primary_account(cust_accounts)
        currency = primary["currency"]

        # The "big sum" — proportionate to THEIR annual income, but floored
        # so it's always large enough to actually require structuring.
        annual_income = cust["income"] * 12
        total_sum = max(
            annual_income * random.uniform(0.5, 1.5),
            CTR_THRESHOLD * 1.2
        )

        # Real-world mix: most structuring is a single windfall event;
        # a minority is an ongoing, repeated pattern across several months.
        is_recurring = random.random() < 0.35
        num_rounds = random.randint(2, 4) if is_recurring else 1
        sum_per_round = total_sum / num_rounds

        # Pick which months (within the simulation period) each round happens in
        available_months = list(range(num_months))
        round_months = random.sample(available_months, k=min(num_rounds, len(available_months)))

        for round_month in round_months:
            month_date = date(sim_start.year, sim_start.month, 1) + timedelta(days=30 * round_month)
            chunks = _split_into_chunks(sum_per_round)

            # Chunks land close together in time — within a 1-10 day window,
            # which is itself part of what makes the pattern detectable later
            window_start_day = random.randint(1, 20)
            for chunk_amount in chunks:
                day_offset = random.randint(0, 9)
                txn_day = min(window_start_day + day_offset, 28)  # stay within any month safely
                txn_date = date(month_date.year, month_date.month, txn_day)

                records.append({
                    "transaction_id": next_txn_id(),
                    "timestamp": datetime.combine(txn_date, datetime.min.time())
                                 + timedelta(hours=random.randint(9, 18), minutes=random.randint(0, 59)),
                    "sender_account_id": None,   # external inflow — looks like a normal large deposit
                    "receiver_account_id": primary["account_id"],
                    "amount": round(chunk_amount, 2),
                    "currency": currency,
                    "transaction_type": "Cash Deposit",   # ordinary-looking label — no fraud tag
                    "channel": random.choice(DEPOSIT_CHANNELS),
                    "merchant_id": None,
                    "device_id": random.choice(cust_devices) if cust_devices else None,
                    "location_id": None,
                    "status": "Success",
                })

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

    structuring_txns = generate_structuring_transactions(
        customers_df, accounts_df, devices_df, scenario_df
    )

    print(structuring_txns.shape)
    print(structuring_txns.head(10))

    print("\nAll amounts under CTR threshold?", (structuring_txns["amount"] < CTR_THRESHOLD).all())

    print("\nExample: one customer's structuring transactions, sorted by time")
    example_customer_accounts = accounts_df[
        accounts_df["customer_id"] == scenario_df[scenario_df["scenario"] == "structuring"]["customer_id"].iloc[0]
    ]["account_id"].tolist()
    example = structuring_txns[structuring_txns["receiver_account_id"].isin(example_customer_accounts)]
    print(example[["timestamp", "amount"]].sort_values("timestamp"))
    print("Total:", example["amount"].sum())