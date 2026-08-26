-- Flow Velocity (daily grain)
-- Grain: one row per account, per calendar day.
-- Compares total inflow vs total outflow on the SAME day — a fast
-- proxy for "how much of what came in went right back out," without
-- expensive per-transaction correlated subqueries.

DROP VIEW IF EXISTS flow_velocity;

CREATE VIEW flow_velocity AS
WITH daily_inflow AS (
    SELECT
        receiver_account_id AS account_id,
        DATE_TRUNC('day', timestamp) AS activity_day,
        SUM(amount) AS total_inflow,
        COUNT(*) AS inflow_count
    FROM transactions
    WHERE receiver_account_id IS NOT NULL
    GROUP BY receiver_account_id, DATE_TRUNC('day', timestamp)
),
daily_outflow AS (
    SELECT
        sender_account_id AS account_id,
        DATE_TRUNC('day', timestamp) AS activity_day,
        SUM(amount) AS total_outflow,
        COUNT(*) AS outflow_count
    FROM transactions
    WHERE sender_account_id IS NOT NULL
    GROUP BY sender_account_id, DATE_TRUNC('day', timestamp)
)
SELECT
    COALESCE(i.account_id, o.account_id) AS account_id,
    COALESCE(i.activity_day, o.activity_day) AS activity_day,
    COALESCE(i.total_inflow, 0) AS total_inflow,
    COALESCE(o.total_outflow, 0) AS total_outflow,
    COALESCE(i.inflow_count, 0) AS inflow_count,
    COALESCE(o.outflow_count, 0) AS outflow_count,
    CASE
        WHEN COALESCE(i.total_inflow, 0) = 0 THEN NULL
        ELSE ROUND(COALESCE(o.total_outflow, 0) / i.total_inflow, 2)
    END AS same_day_outflow_ratio
FROM daily_inflow i
FULL OUTER JOIN daily_outflow o
    ON i.account_id = o.account_id AND i.activity_day = o.activity_day
ORDER BY account_id, activity_day;