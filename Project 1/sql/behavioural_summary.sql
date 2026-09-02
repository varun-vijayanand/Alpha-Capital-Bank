-- behavioural_summary.sql
-- Project 1: Customer Intelligence
-- Per-customer, per-month behavioural summary — outgoing (sender-side)
-- transactions only, treated as the customer's own "spend behaviour."
-- Incoming credits tracked separately as a lighter secondary signal.

WITH customer_accounts AS (
    SELECT account_id, customer_id FROM accounts
),

spend_txns AS (
    SELECT
        t.transaction_id,
        t.timestamp,
        ca.customer_id,
        t.amount,
        t.channel,
        t.location_id,
        l.is_domestic,
        DATE_TRUNC('month', t.timestamp) AS txn_month,
        EXTRACT(HOUR FROM t.timestamp) AS txn_hour,
        EXTRACT(DOW FROM t.timestamp) AS txn_dow  -- 0=Sunday .. 6=Saturday
    FROM transactions t
    JOIN customer_accounts ca ON ca.account_id = t.sender_account_id
    LEFT JOIN locations l ON l.location_id = t.location_id
    WHERE t.status = 'Success'
),

credit_txns AS (
    SELECT
        ca.customer_id,
        DATE_TRUNC('month', t.timestamp) AS txn_month,
        t.amount
    FROM transactions t
    JOIN customer_accounts ca ON ca.account_id = t.receiver_account_id
    WHERE t.status = 'Success'
)

SELECT
    s.customer_id,
    s.txn_month,

    -- core spend stats
    COUNT(*) AS spend_txn_count,
    SUM(s.amount) AS total_spend,
    AVG(s.amount) AS avg_txn_amount,
    STDDEV(s.amount) AS stddev_txn_amount,
    MAX(s.amount) AS max_txn_amount,

    -- timing patterns
    MODE() WITHIN GROUP (ORDER BY s.txn_hour) AS most_common_hour,
    COUNT(*) FILTER (WHERE s.txn_hour BETWEEN 23 AND 24 OR s.txn_hour BETWEEN 0 AND 4) AS odd_hour_txn_count,
    MODE() WITHIN GROUP (ORDER BY s.txn_dow) AS most_common_day_of_week,

    -- channel / location diversity
    COUNT(DISTINCT s.channel) AS channel_diversity,
    COUNT(DISTINCT s.location_id) AS location_diversity,
    COUNT(*) FILTER (WHERE s.is_domestic = FALSE) AS international_txn_count,

    -- secondary: incoming credit signal
    COALESCE(c.credit_txn_count, 0) AS credit_txn_count,
    COALESCE(c.total_credit, 0) AS total_credit

FROM spend_txns s
LEFT JOIN (
    SELECT customer_id, txn_month, COUNT(*) AS credit_txn_count, SUM(amount) AS total_credit
    FROM credit_txns
    GROUP BY customer_id, txn_month
) c ON c.customer_id = s.customer_id AND c.txn_month = s.txn_month
GROUP BY s.customer_id, s.txn_month, c.credit_txn_count, c.total_credit
ORDER BY s.customer_id, s.txn_month;