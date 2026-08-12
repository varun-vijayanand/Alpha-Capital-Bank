"""
fraud.py

Injects card fraud behaviour: the customer's account itself is fine,
but their card gets compromised — unusual purchases appear in a short
burst, at a different location than usual, sized noticeably larger
than the customer's typical purchase. Everyday merchant categories,
same as normal spending — the anomaly is in AMOUNT, TIMING, and
LOCATION, not category. No new device/beneficiary (unlike ATO); the
customer's normal transactions continue untouched alongside this.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import date, timedelta, datetime

import pandas as pd

from config.config_loader import SETTINGS


EVERYDAY_CATEGORIES = [
    "Grocery", "Fuel", "Retail", "Restaurants",
    "E-commerce", "Utilities", "Pharmacy", "Electronics"
]

FRAUD_CHANNELS = ["Card"]  # card-present/card-not-present fraud specifically


def _pick_target_account(cust_accounts: list):
    target = next((a for a in cust_accounts if a["account_type"] in ("Current", "Salary")), None)
    if target is None:
        target = next((a for a in cust_accounts if a["account_type"] == "Savings"), None)
    if target is None:
        target = cust_accounts[0]
    return target


def generate_fraud_transactions(customers_df: pd.DataFrame,
                                  accounts_df: pd.DataFrame,
                                  devices_df: pd.DataFrame,
                                  merchants_df: pd.DataFrame,
                                  locations_df: pd.DataFrame,
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

    # Everyday merchants only — no need for the customer's OWN device,
    # card fraud doesn't require the attacker to be using the victim's phone
    everyday_merchants = merchants_df[merchants_df["merchant_category"].isin(EVERYDAY_CATEGORIES)]
    merchants_by_category = {}
    for _, m in everyday_merchants.iterrows():
        merchants_by_category.setdefault(m["merchant_category"], []).append(m["merchant_id"])
    merchant_location = dict(zip(merchants_df["merchant_id"], merchants_df["location_id"]))

    domestic_location_ids = locations_df[locations_df["is_domestic"]]["location_id"].tolist()

    fraud_customers = scenario_df[scenario_df["scenario"] == "fraud"]["customer_id"].tolist()

    records = []
    txn_counter = 1

    def next_txn_id():
        nonlocal txn_counter
        tid = f"TF{930000 + txn_counter}"
        txn_counter += 1
        return tid

    for customer_id in fraud_customers:
        cust = customers_df[customers_df["customer_id"] == customer_id].iloc[0]
        cust_accounts = accounts_by_customer.get(customer_id, [])
        if not cust_accounts:
            continue
        cust_devices = devices_by_customer.get(customer_id, [])

        target_account = _pick_target_account(cust_accounts)
        currency = target_account["currency"]

        # A "typical" purchase size for THIS customer, so the spike is relative
        baseline_purchase = max(cust["income"] * 0.05, 500)

        # A card fraud event usually shows up as ONE burst (card gets used
        # rapidly before it's blocked) — occasionally two separate incidents
        num_incidents = random.choices([1, 2], weights=[80, 20], k=1)[0]

        for _ in range(num_incidents):
            incident_offset = random.randint(0, num_months * 28 - 3)
            incident_date = sim_start + timedelta(days=incident_offset)

            # A different location than their usual — a nearby-but-different
            # domestic city works well for card fraud (unlike ATO, which
            # leaned international; a stolen physical card is more often
            # used somewhere domestic but unfamiliar to the customer)
            fraud_location = random.choice(domestic_location_ids)

            # 3-7 rapid purchases within a single day or two — cards get
            # used fast before the fraud is noticed / card gets blocked
            num_purchases = random.randint(3, 7)
            burst_day_span = random.randint(0, 1)

            for _ in range(num_purchases):
                category = random.choice(EVERYDAY_CATEGORIES)
                if category not in merchants_by_category:
                    continue
                merchant_id = random.choice(merchants_by_category[category])

                # Fraudulent purchases run noticeably larger than the
                # customer's normal baseline for that category
                amount = baseline_purchase * random.uniform(3, 8)

                day_offset = random.randint(0, burst_day_span)
                txn_date = incident_date + timedelta(days=day_offset)

                records.append({
                    "transaction_id": next_txn_id(),
                    "timestamp": datetime.combine(txn_date, datetime.min.time())
                                 + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59)),
                    "sender_account_id": target_account["account_id"],
                    "receiver_account_id": None,
                    "amount": round(amount, 2),
                    "currency": currency,
                    "transaction_type": f"{category} Purchase",  # looks exactly like a normal purchase type
                    "channel": "Card",
                    "merchant_id": merchant_id,
                    "device_id": None,  # card transaction — no device needed, unlike online/ATO fraud
                    "location_id": fraud_location,
                    "status": "Success",
                })

    return pd.DataFrame(records)


if __name__ == "__main__":
    from generators.customers import generate_customers
    from generators.accounts import generate_accounts
    from generators.devices import generate_devices
    from generators.merchants import generate_merchants
    from generators.locations import generate_locations
    from scenarios.assign_scenarios import assign_scenarios

    customers_df = generate_customers()
    accounts_df = generate_accounts(customers_df)
    devices_df = generate_devices(customers_df)
    locations_df = generate_locations()
    merchants_df = generate_merchants(locations_df)
    scenario_df = assign_scenarios(customers_df)

    fraud_txns = generate_fraud_transactions(
        customers_df, accounts_df, devices_df, merchants_df, locations_df, scenario_df
    )

    print(fraud_txns.shape)
    print(fraud_txns.head(10))

    example_customer_id = scenario_df[scenario_df["scenario"] == "fraud"]["customer_id"].iloc[0]
    example_accounts = accounts_df[accounts_df["customer_id"] == example_customer_id]["account_id"].tolist()
    example = fraud_txns[fraud_txns["sender_account_id"].isin(example_accounts)].sort_values("timestamp")
    print(f"\nFraud burst for {example_customer_id}:")
    print(example[["timestamp", "transaction_type", "amount", "location_id"]])