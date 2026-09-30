-- Behavioural Deviation
-- For each transaction, compares its amount against the SENDING
-- account's own historical average (excluding the current transaction),
-- expressed as a ratio. A ratio far from 1.0 means "very different
-- from what this account usually does."

DROP VIEW IF EXISTS behavioural_deviation;

CREATE VIEW behavioural_deviation AS
WITH outgoing_only AS (
    SELECT
        sender_account_id AS account_id,
        transaction_id,
        timestamp,
        amount
    FROM transactions
    WHERE sender_account_id IS NOT NULL
),
with_running_stats AS (
    SELECT
        account_id,
        transaction_id,
        timestamp,
        amount,

        -- Average of all PRIOR transactions for this account (excludes current row)
        AVG(amount) OVER (
            PARTITION BY account_id
            ORDER BY timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS historical_average,

        -- Count of prior transactions, so we can tell "no history yet" apart from "genuinely typical"
        COUNT(*) OVER (
            PARTITION BY account_id
            ORDER BY timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS prior_transaction_count

    FROM outgoing_only
)
SELECT
    account_id,
    transaction_id,
    timestamp,
    amount AS current_transaction_value,
    ROUND(historical_average, 2) AS historical_average,
    prior_transaction_count,
    CASE
        WHEN prior_transaction_count = 0 THEN NULL  -- first-ever transaction, nothing to compare against
        WHEN historical_average = 0 THEN NULL
        ELSE ROUND(amount / historical_average, 2)
    END AS deviation_from_average
FROM with_running_stats
ORDER BY account_id, timestamp;