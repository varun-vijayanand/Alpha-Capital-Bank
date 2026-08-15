-- Account Velocity — Core (Transaction + Amount velocity, directional)
-- Grain: one row per transaction, from the perspective of the account
-- that either SENT or RECEIVED it. Every transaction produces exactly
-- one row here (never both directions for the same row — direction
-- reflects which account this row's "account_id" belongs to).

DROP VIEW IF EXISTS account_velocity_core;

CREATE VIEW account_velocity_core AS
WITH directional_transactions AS (
    -- This account was the SENDER (outgoing)
    SELECT
        sender_account_id AS account_id,
        'outgoing' AS direction,
        transaction_id,
        timestamp,
        amount
    FROM transactions
    WHERE sender_account_id IS NOT NULL

    UNION ALL

    -- This account was the RECEIVER (incoming)
    SELECT
        receiver_account_id AS account_id,
        'incoming' AS direction,
        transaction_id,
        timestamp,
        amount
    FROM transactions
    WHERE receiver_account_id IS NOT NULL
)
SELECT
    account_id,
    direction,
    transaction_id,
    timestamp,
    amount,

    -- Transaction velocity: how many transactions (same account, same direction)
    -- occurred in the trailing window, INCLUDING this one
    COUNT(*) OVER (
        PARTITION BY account_id, direction
        ORDER BY timestamp
        RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
    ) AS txn_count_1h,
    COUNT(*) OVER (
        PARTITION BY account_id, direction
        ORDER BY timestamp
        RANGE BETWEEN INTERVAL '24 hours' PRECEDING AND CURRENT ROW
    ) AS txn_count_24h,
    COUNT(*) OVER (
        PARTITION BY account_id, direction
        ORDER BY timestamp
        RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW
    ) AS txn_count_7d,

    -- Amount velocity: total money moved (same account, same direction)
    -- in the trailing window, INCLUDING this one
    SUM(amount) OVER (
        PARTITION BY account_id, direction
        ORDER BY timestamp
        RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
    ) AS amount_sum_1h,
    SUM(amount) OVER (
        PARTITION BY account_id, direction
        ORDER BY timestamp
        RANGE BETWEEN INTERVAL '24 hours' PRECEDING AND CURRENT ROW
    ) AS amount_sum_24h,
    SUM(amount) OVER (
        PARTITION BY account_id, direction
        ORDER BY timestamp
        RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW
    ) AS amount_sum_7d

FROM directional_transactions
ORDER BY account_id, direction, timestamp;