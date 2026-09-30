"""
rules/batch/structuring.py

Batch Rule 5.1 — Structuring Detection

Flags customers with multiple cash deposits, each individually under
the CTR reporting threshold, clustering together in time and summing
to an amount that would have crossed the CTR threshold had it been
one transaction — the classic "smurfing" pattern.

Mirrors Project 0's scenarios/structuring.py generator in reverse:
that script SPLITS a large sum into sub-threshold chunks landing
within a ~10-day window. This rule tries to DETECT that shape from
raw transaction data alone, with no knowledge of which customers were
actually seeded as "structuring" scenario customers.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[3] / "Project 0" / "config"))
from typing import cast
import pandas as pd


def _extract_candidate_deposits(conn, ctr_threshold: float) -> pd.DataFrame:
    """
    Pulls every sub-CTR-threshold cash deposit, joined through accounts
    to the customer who received it. SQL's job here is filtering and
    joining only — the time-clustering logic happens in Python below,
    where sliding-window comparisons are far more natural to express.
    """
    query = """
        SELECT
            a.customer_id,
            t.receiver_account_id AS account_id,
            t.transaction_id,
            t.timestamp,
            t.amount
        FROM transactions t
        JOIN accounts a ON a.account_id = t.receiver_account_id
        WHERE t.transaction_type = 'Cash Deposit'
          AND t.status = 'Success'
          AND t.amount < %(ctr_threshold)s
        ORDER BY a.customer_id, t.timestamp
    """
    df = pd.read_sql(query, conn, params={"ctr_threshold": ctr_threshold})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def _find_best_cluster(cust_df: pd.DataFrame, window_days: int, min_total: float, min_count: int):
    """
    Slides a window_days-wide window across one customer's deposits
    (already sorted by time) and checks each window against the
    min_count / min_total thresholds.

    Overlapping windows can describe the same underlying burst of
    activity, so we keep only the single highest-total window per
    customer rather than raising multiple alerts for one event.
    """
    cust_df = cust_df.sort_values("timestamp").reset_index(drop=True)
    clusters = []

    for i in range(len(cust_df)):
        window_start = cast(pd.Timestamp, cust_df.loc[i, "timestamp"])
        window_end = window_start + pd.Timedelta(days=window_days)

        window_df = cust_df[
            (cust_df["timestamp"] >= window_start) &
            (cust_df["timestamp"] < window_end)
        ]

        if len(window_df) >= min_count and window_df["amount"].sum() >= min_total:
            clusters.append({
                "window_start": window_start,
                "window_end": pd.Timestamp(window_df["timestamp"].max()),
                "deposit_count": len(window_df),
                "total_amount": window_df["amount"].sum(),
                "transaction_ids": window_df["transaction_id"].tolist(),
            })

    if not clusters:
        return None

    return max(clusters, key=lambda c: c["total_amount"])


def run(conn, config: dict) -> pd.DataFrame:
    cfg = config["structuring"]
    ctr_threshold = cfg["ctr_threshold"]
    window_days = cfg["clustering_window_days"]
    min_total = ctr_threshold * cfg["min_cluster_total_ratio"]
    min_count = cfg["min_deposit_count"]

    deposits = _extract_candidate_deposits(conn, ctr_threshold)

    rows = []
    for customer_id, cust_df in deposits.groupby("customer_id"):
        cluster = _find_best_cluster(cust_df, window_days, min_total, min_count)
        if cluster is None:
            continue

        rows.append({
            "rule_name": "structuring_detection",
            "entity_type": "customer",
            "entity_id": customer_id,
            "trigger_date": cluster["window_end"].date(),
            "severity": round(cluster["total_amount"] / ctr_threshold, 2),
            "reason": (
                f"{cluster['deposit_count']} cash deposits totalling "
                f"₹{cluster['total_amount']:,.0f} within {window_days} days, "
                f"each individually under the ₹{ctr_threshold:,.0f} CTR threshold"
            ),
            "supporting_data": {
                "window_start": str(cluster["window_start"]),
                "window_end": str(cluster["window_end"]),
                "deposit_count": cluster["deposit_count"],
                "total_amount": cluster["total_amount"],
                "transaction_ids": cluster["transaction_ids"],
            },
        })

    return pd.DataFrame(rows, columns=[
        "rule_name", "entity_type", "entity_id", "trigger_date",
        "severity", "reason", "supporting_data"
    ])