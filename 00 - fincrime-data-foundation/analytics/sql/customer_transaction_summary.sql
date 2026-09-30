-- Customer Transaction Summary
-- Grain: one row per customer per calendar month.
-- Combines a customer's activity as SENDER and as RECEIVER into one view.

DROP VIEW IF EXISTS customer_transaction_summary;

CREATE VIEW customer_transaction_summary AS
WITH customer_activity AS (
    -- Customer acting as SENDER
    SELECT
        a.customer_id,
        DATE_TRUNC('month', t.timestamp) AS txn_month,
        t.amount,
        t.receiver_account_id AS counterparty_account_id
    FROM transactions t
    JOIN accounts a ON t.sender_account_id = a.account_id

    UNION ALL

    -- Customer acting as RECEIVER
    SELECT
        a.customer_id,
        DATE_TRUNC('month', t.timestamp) AS txn_month,
        t.amount,
        t.sender_account_id AS counterparty_account_id
    FROM transactions t
    JOIN accounts a ON t.receiver_account_id = a.account_id
)
SELECT
    customer_id,
    txn_month,
    COUNT(*) AS monthly_transaction_count,
    SUM(amount) AS monthly_transaction_value,
    ROUND(AVG(amount), 2) AS average_transaction_value,
    COUNT(DISTINCT counterparty_account_id) AS unique_counterparties
FROM customer_activity
GROUP BY customer_id, txn_month
ORDER BY customer_id, txn_month;