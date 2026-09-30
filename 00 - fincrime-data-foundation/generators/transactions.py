"""
transactions.py

Generates the Transactions table — the "normal behaviour" baseline.
For each customer, builds a connected monthly story across all of
their own accounts: income credit, rent, bills, groceries,
discretionary spending, and internal transfers between their own
accounts. This is the data later fraud/AML scenarios will deviate from.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
import calendar
from datetime import date, datetime, timedelta

import pandas as pd

from config.config_loader import SETTINGS


CHANNELS = ["UPI", "NEFT", "IMPS", "Card", "Cash"]

EMPLOYED_OCCUPATIONS = {
    "Salaried - IT", "Salaried - Government", "Self-Employed", "Business Owner"
}

# category -> transaction_type label
CATEGORY_TO_TXN_TYPE = {
    "Grocery": "Grocery Purchase",
    "Utilities": "Bill Payment",
    "Fuel": "Fuel Purchase",
    "Restaurants": "Restaurant Purchase",
    "Retail": "Retail Purchase",
    "E-commerce": "E-commerce Purchase",
    "Pharmacy": "Pharmacy Purchase",
    "Electronics": "Electronics Purchase",
}

# category -> (min_amount, max_amount) per single transaction, in INR
CATEGORY_AMOUNT_RANGES = {
    "Grocery": (300, 3000),
    "Utilities": (500, 3500),
    "Fuel": (500, 3000),
    "Restaurants": (300, 2500),
    "Retail": (500, 6000),
    "E-commerce": (400, 8000),
    "Pharmacy": (200, 2000),
    "Electronics": (1000, 25000),
}

def _income_tier(income: float) -> str:
    """Classify income into a tier used to scale spending amount and frequency."""
    if income < 8000:
        return "very_low"
    elif income < 20000:
        return "low"
    elif income < 60000:
        return "medium"
    elif income < 150000:
        return "high"
    else:
        return "very_high"


# Multiplies category spending amounts based on income tier
SPENDING_MULTIPLIER = {
    "very_low": 0.25,
    "low": 0.5,
    "medium": 1.0,
    "high": 1.3,
    "very_high": 1.6,
}

# (min, max) count of grocery transactions per month, by income tier
GROCERY_COUNT_RANGE = {
    "very_low": (1, 2),
    "low": (2, 3),
    "medium": (3, 6),
    "high": (3, 6),
    "very_high": (4, 7),
}

# (min, max) count of discretionary transactions per month, by income tier
DISCRETIONARY_COUNT_RANGE = {
    "very_low": (0, 1),
    "low": (1, 2),
    "medium": (2, 5),
    "high": (2, 5),
    "very_high": (3, 6),
}

def _cap_to_income(amount: float, income: float, max_fraction: float = 0.5) -> float:
    """
    Caps a single purchase so it can never exceed max_fraction of the
    customer's monthly income — prevents one expensive category (e.g.
    Electronics) from producing an implausible one-off spend for a
    low-income customer, regardless of the category's normal amount range.
    """
    income_floor = max(income, 2000)  # avoid an unreasonably tiny cap for zero/near-zero income
    cap = income_floor * max_fraction
    return min(amount, cap)

def _month_start(base: date, offset: int) -> date:
    """Return the 1st of the month, `offset` months after `base`."""
    month_index = base.month - 1 + offset
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _random_day_in_month(month_date: date) -> date:
    """Pick a random valid day within the given month."""
    days_in_month = calendar.monthrange(month_date.year, month_date.month)[1]
    day = random.randint(1, days_in_month)
    return date(month_date.year, month_date.month, day)


def _account_active_in_month(account, month_date: date) -> bool:
    """An account can only have transactions while it's open."""
    if account["status"] == "Closed" and pd.notna(account["closing_date"]):
        if account["closing_date"] < month_date:
            return False
    if account["opening_date"] > month_date:
        return False
    return True


def generate_transactions(customers_df, accounts_df, merchants_df, devices_df, locations_df) -> pd.DataFrame:
    seed = SETTINGS["random_seed"]
    random.seed(seed)

    sim_start = date.fromisoformat(SETTINGS["simulation"]["start_date"])
    num_months = SETTINGS["simulation"]["months"]

    # --- Pre-compute lookups so we're not filtering DataFrames inside loops ---

    # customer_id -> list of their account rows (as dicts)
    accounts_by_customer = {}
    for _, acc in accounts_df.iterrows():
        accounts_by_customer.setdefault(acc["customer_id"], []).append(acc)

    # customer_id -> list of their device_ids
    devices_by_customer = {}
    for _, dev in devices_df.iterrows():
        devices_by_customer.setdefault(dev["customer_id"], []).append(dev["device_id"])

    # everyday merchant category -> list of merchant_ids in that category
    # (normal customers only visit everyday merchants, not high-risk ones)
    everyday_merchants = merchants_df[~merchants_df["is_high_risk_category"]]
    merchants_by_category = {}
    for _, m in everyday_merchants.iterrows():
        merchants_by_category.setdefault(m["merchant_category"], []).append(m["merchant_id"])

    # merchant_id -> location_id, for stamping transaction location from the merchant
    merchant_location = dict(zip(merchants_df["merchant_id"], merchants_df["location_id"]))

    # Each customer gets a consistent "home" location (domestic only) —
    # this becomes the baseline that account-takeover scenarios will later violate
    domestic_location_ids = locations_df[locations_df["is_domestic"]]["location_id"].tolist()
    # (fallback: just reuse merchant locations pool; a cleaner source is locations_df directly if passed in)
    home_location_by_customer = {}

    records = []
    txn_counter = 1

    def next_txn_id():
        nonlocal txn_counter
        tid = f"T{600000 + txn_counter}"
        txn_counter += 1
        return tid

    def add_transaction(sender, receiver, amount, currency, txn_type, channel,
                         merchant_id, device_id, location_id, txn_date, status="Success"):
        records.append({
            "transaction_id": next_txn_id(),
            "timestamp": datetime.combine(txn_date, datetime.min.time())
                         + timedelta(hours=random.randint(6, 22), minutes=random.randint(0, 59)),
            "sender_account_id": sender,
            "receiver_account_id": receiver,
            "amount": round(amount, 2),
            "currency": currency,
            "transaction_type": txn_type,
            "channel": channel,
            "merchant_id": merchant_id,
            "device_id": device_id,
            "location_id": location_id,
            "status": status,
        })

    for _, cust in customers_df.iterrows():
        cust_accounts = accounts_by_customer.get(cust["customer_id"], [])
        if not cust_accounts:
            continue  # shouldn't happen, but guard anyway

        cust_devices = devices_by_customer.get(cust["customer_id"], [])

        # Pick a stable home location for this customer, once
        home_location_by_customer[cust["customer_id"]] = random.choice(domestic_location_ids)
        home_location = home_location_by_customer[cust["customer_id"]]

        # Choose primary account: prefer Salary, then Current, else first account
        primary = next((a for a in cust_accounts if a["account_type"] == "Salary"), None)
        if primary is None:
            primary = next((a for a in cust_accounts if a["account_type"] == "Current"), None)
        if primary is None:
            primary = cust_accounts[0]

        # Secondary account: any other account, for internal transfers
        secondary_candidates = [a for a in cust_accounts if a["account_id"] != primary["account_id"]]
        secondary = secondary_candidates[0] if secondary_candidates else None

        is_employed = cust["occupation"] in EMPLOYED_OCCUPATIONS
        tier = _income_tier(cust["income"])
        spending_multiplier = SPENDING_MULTIPLIER[tier]
        grocery_min, grocery_max = GROCERY_COUNT_RANGE[tier]
        discretionary_min, discretionary_max = DISCRETIONARY_COUNT_RANGE[tier]
        pays_rent = random.random() < 0.45  # fixed per customer, decided once

        for month_offset in range(num_months):
            month_date = _month_start(sim_start, month_offset)

            if not _account_active_in_month(primary, month_date):
                continue

            currency = primary["currency"]

            # 1. Income credit (payday, early in the month)
            if is_employed:
                income_variation = random.uniform(0.95, 1.05)
                income_amount = cust["income"] * income_variation
                txn_type = "Business Income" if cust["occupation"] in ("Business Owner", "Self-Employed") else "Salary Credit"
                payday = date(month_date.year, month_date.month, random.randint(1, 5))
                add_transaction(
                    sender=None, receiver=primary["account_id"],
                    amount=income_amount, currency=currency,
                    txn_type=txn_type, channel="NEFT",
                    merchant_id=None, device_id=random.choice(cust_devices) if cust_devices else None,
                    location_id=home_location, txn_date=payday,
                )

            # 2. Rent (mid-month, if applicable)
            if pays_rent and cust["income"] > 0:
                rent_amount = cust["income"] * random.uniform(0.2, 0.35)
                rent_day = _random_day_in_month(month_date)
                add_transaction(
                    sender=primary["account_id"], receiver=None,
                    amount=rent_amount, currency=currency,
                    txn_type="Rent Payment", channel="NEFT",
                    merchant_id=None, device_id=random.choice(cust_devices) if cust_devices else None,
                    location_id=home_location, txn_date=rent_day,
                )

            # 3. Utilities (1 per month)
            if "Utilities" in merchants_by_category:
                merchant_id = random.choice(merchants_by_category["Utilities"])
                low, high = CATEGORY_AMOUNT_RANGES["Utilities"]
                amount = _cap_to_income(random.uniform(low, high) * spending_multiplier, cust["income"])
                add_transaction(
                    sender=primary["account_id"], receiver=None,
                    amount=amount, currency=currency,
                    txn_type=CATEGORY_TO_TXN_TYPE["Utilities"], channel=random.choice(CHANNELS),
                    merchant_id=merchant_id, device_id=random.choice(cust_devices) if cust_devices else None,
                    location_id=merchant_location.get(merchant_id, home_location),
                    txn_date=_random_day_in_month(month_date),
                )

            # 4. Groceries (3-6 per month)
            if "Grocery" in merchants_by_category:
                for _ in range(random.randint(grocery_min, grocery_max)):
                    merchant_id = random.choice(merchants_by_category["Grocery"])
                    low, high = CATEGORY_AMOUNT_RANGES["Grocery"]
                    amount = _cap_to_income(random.uniform(low, high) * spending_multiplier, cust["income"])
                    add_transaction(
                        sender=primary["account_id"], receiver=None,
                        amount=amount, currency=currency,
                        txn_type=CATEGORY_TO_TXN_TYPE["Grocery"], channel=random.choice(CHANNELS),
                        merchant_id=merchant_id, device_id=random.choice(cust_devices) if cust_devices else None,
                        location_id=merchant_location.get(merchant_id, home_location),
                        txn_date=_random_day_in_month(month_date),
                    )

            # 5. Discretionary spending (2-5 per month, mixed categories)
            discretionary_categories = ["Fuel", "Restaurants", "Retail", "E-commerce", "Pharmacy", "Electronics"]
            available_categories = [c for c in discretionary_categories if c in merchants_by_category]
            for _ in range(random.randint(discretionary_min, discretionary_max)):
                if not available_categories:
                    break
                category = random.choice(available_categories)
                merchant_id = random.choice(merchants_by_category[category])
                low, high = CATEGORY_AMOUNT_RANGES[category]
                amount = _cap_to_income(random.uniform(low, high) * spending_multiplier, cust["income"])
                add_transaction(
                    sender=primary["account_id"], receiver=None,
                    amount=amount, currency=currency,
                    txn_type=CATEGORY_TO_TXN_TYPE[category], channel=random.choice(CHANNELS),
                    merchant_id=merchant_id, device_id=random.choice(cust_devices) if cust_devices else None,
                    location_id=merchant_location.get(merchant_id, home_location),
                    txn_date=_random_day_in_month(month_date),
                )

            # 6. Internal transfer to secondary account (if one exists)
            if secondary is not None and _account_active_in_month(secondary, month_date) and is_employed:
                transfer_amount = cust["income"] * random.uniform(0.1, 0.3)
                add_transaction(
                    sender=primary["account_id"], receiver=secondary["account_id"],
                    amount=transfer_amount, currency=currency,
                    txn_type="Internal Transfer", channel="IMPS",
                    merchant_id=None, device_id=random.choice(cust_devices) if cust_devices else None,
                    location_id=home_location,
                    txn_date=_random_day_in_month(month_date),
                )

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    from generators.customers import generate_customers
    from generators.kyc import generate_kyc
    from generators.accounts import generate_accounts
    from generators.devices import generate_devices
    from generators.merchants import generate_merchants
    from generators.locations import generate_locations

    customers_df = generate_customers()
    locations_df = generate_locations()
    accounts_df = generate_accounts(customers_df)
    devices_df = generate_devices(customers_df)
    merchants_df = generate_merchants(locations_df)

    transactions_df = generate_transactions(customers_df, accounts_df, merchants_df, devices_df, locations_df)

    print(transactions_df.shape)
    print(transactions_df.head(10))
    print("\nTransaction type distribution:")
    print(transactions_df["transaction_type"].value_counts())
    print("\nAvg transactions per customer:")
    print(len(transactions_df) / len(customers_df))