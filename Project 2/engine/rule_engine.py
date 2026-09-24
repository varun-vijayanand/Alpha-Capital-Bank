"""
Rule Engine — Project 2 (Transaction Monitoring)

Runs a registered set of rule functions against the database and
collects their outputs into a single, uniformly-shaped triggers table.

Each rule function must have the signature:
    rule_fn(conn, config: dict) -> pd.DataFrame

...and must return a DataFrame with columns:
    rule_name, entity_type, entity_id, trigger_date, severity, reason, supporting_data
"""

import sys
from pathlib import Path

import pandas as pd
sys.path.append(str(Path(__file__).resolve().parents[2] / "Project 0" / "config"))
from config_loader import get_db_connection_string, load_settings

# --- Rule registry -----------------------------------------------------
# As each rule module gets built (rules/batch/structuring.py, etc.),
# we import its run() function here and add it to this list.

BATCH_RULES = [
    # (rule_name, rule_fn)
]

REALTIME_RULES = [
    # (rule_name, rule_fn)
]


# --- Required output schema for every rule ------------------------------

REQUIRED_COLUMNS = [
    "rule_name",
    "entity_type",
    "entity_id",
    "trigger_date",
    "severity",
    "reason",
    "supporting_data",
]


def _validate_rule_output(df: pd.DataFrame, rule_name: str) -> None:
    """
    Fail loudly and early if a rule doesn't conform to the contract.
    Cheaper to catch a schema mismatch here than debug it inside alert_merger.py later.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Rule '{rule_name}' output is missing required columns: {missing}"
        )


def run_batch_rules(conn, config: dict) -> pd.DataFrame:
    """
    Executes every registered batch rule and stacks their outputs
    into one long DataFrame of raw triggers (not yet merged into alerts).
    """
    results = []

    for rule_name, rule_fn in BATCH_RULES:
        print(f"Running batch rule: {rule_name}")
        df = rule_fn(conn, config)
        _validate_rule_output(df, rule_name)
        results.append(df)

    if not results:
        # No rules registered yet — return an empty but correctly-shaped DataFrame
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    return pd.concat(results, ignore_index=True)


def run_realtime_rules(conn, config: dict) -> pd.DataFrame:
    """
    Same pattern as run_batch_rules, but for the real-time-style rules.
    Kept as a separate function (not merged with batch here) because
    alert_merger.py needs to know which stream each trigger came from.
    """
    results = []

    for rule_name, rule_fn in REALTIME_RULES:
        print(f"Running real-time rule: {rule_name}")
        df = rule_fn(conn, config)
        _validate_rule_output(df, rule_name)
        results.append(df)

    if not results:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    return pd.concat(results, ignore_index=True)


def main():
    config = load_settings()  # reuses Project 0/1's config_loader
    conn = get_db_connection_string()

    batch_triggers = run_batch_rules(conn, config)
    realtime_triggers = run_realtime_rules(conn, config)

    print(f"Batch triggers: {len(batch_triggers)}")
    print(f"Real-time triggers: {len(realtime_triggers)}")

    return batch_triggers, realtime_triggers


if __name__ == "__main__":
    main()