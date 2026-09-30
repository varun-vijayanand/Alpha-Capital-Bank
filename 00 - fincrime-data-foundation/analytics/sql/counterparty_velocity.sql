-- Counterparty Velocity (daily grain)
-- Grain: one row per account, per direction, per calendar day.
-- Trades exact rolling-window precision for a fast, simple GROUP BY —
-- still clearly exposes fan-in/fan-out shape (mule accounts, ATO bursts)
-- without an expensive per-row correlated subquery.

DROP VIEW IF EXISTS counterparty_velocity;

CREATE VIEW counterparty_velocity AS
WITH directional_transactions AS (
    SELECT
        sender_account_id AS account_id,
        'outgoing' AS direction,
        timestamp,
        receiver_account_id AS counterparty_id
    FROM transactions
    WHERE sender_account_id IS NOT NULL

    UNION ALL

    SELECT
        receiver_account_id AS account_id,
        'incoming' AS direction,
        timestamp,
        sender_account_id AS counterparty_id
    FROM transactions
    WHERE receiver_account_id IS NOT NULL
)
SELECT
    account_id,
    direction,
    DATE_TRUNC('day', timestamp) AS activity_day,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT counterparty_id) AS unique_counterparties
FROM directional_transactions
GROUP BY account_id, direction, DATE_TRUNC('day', timestamp)
ORDER BY account_id, direction, activity_day;