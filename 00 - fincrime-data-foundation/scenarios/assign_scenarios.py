"""
assign_scenarios.py

Assigns exactly one behavioural scenario to each customer, based on
scenario_rates in settings.yaml. This becomes the GROUND TRUTH label —
kept separate from the main relational tables, used only for later
evaluation/benchmarking of detection models, not fed into them directly.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random

import pandas as pd

from config.config_loader import SETTINGS


def assign_scenarios(customers_df: pd.DataFrame) -> pd.DataFrame:
    """Returns a DataFrame: customer_id -> scenario (ground truth label)."""

    seed = SETTINGS["random_seed"]
    random.seed(seed)

    scenario_rates = SETTINGS["scenario_rates"]
    scenarios = list(scenario_rates.keys())
    weights = list(scenario_rates.values())

    records = []
    for customer_id in customers_df["customer_id"]:
        scenario = random.choices(scenarios, weights=weights, k=1)[0]
        records.append({"customer_id": customer_id, "scenario": scenario})

    return pd.DataFrame(records)


if __name__ == "__main__":
    from generators.customers import generate_customers

    customers_df = generate_customers()
    scenario_df = assign_scenarios(customers_df)

    print(scenario_df.shape)
    print(scenario_df.head(10))
    print("\nScenario distribution:")
    print(scenario_df["scenario"].value_counts())
    print("\nAs percentage:")
    print((scenario_df["scenario"].value_counts(normalize=True) * 100).round(2))