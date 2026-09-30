-- category_mix.sql
-- Project 1: Customer Intelligence
-- Per-customer, per-month, per-merchant-category spend breakdown (long format).

WITH customer_accounts AS (
    SELECT account_id, customer_id FROM accounts
)

SELECT
    ca.customer_id,
    DATE_TRUNC('month', t.timestamp) AS txn_month,
    m.merchant_category,
    COUNT(*) AS category_txn_count,
    SUM(t.amount) AS category_spend
-- category_mix.sql
FROM transactions t
JOIN customer_accounts ca ON ca.account_id = t.sender_account_id
JOIN merchants m ON m.merchant_id = t.merchant_id
WHERE t.status = 'Success'
GROUP BY ca.customer_id, DATE_TRUNC('month', t.timestamp), m.merchant_category
ORDER BY ca.customer_id, txn_month, m.merchant_category;