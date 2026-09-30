-- customer_profiling.sql
-- Project 1: Customer Intelligence
-- Segments every Alpha Capital Bank customer by KYC attributes,
-- fixed (policy-style) income bands, relative (percentile) income tiers,
-- and derived fields (age, account count) useful for behavioural baselining.

WITH customer_base AS (
    SELECT
        c.customer_id,
        c.occupation,
        c.income,
        c.residency,
        c.customer_type,
        c.date_of_birth,
        DATE_PART('year', AGE(CURRENT_DATE, c.date_of_birth)) AS age,
        k.risk_category
    FROM customers c
    LEFT JOIN kyc k ON k.customer_id = c.customer_id
),

account_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS account_count
    FROM accounts
    GROUP BY customer_id
),

income_percentiles AS (
    SELECT
        customer_id,
        income,
        NTILE(4) OVER (ORDER BY income) AS income_quartile
    FROM customer_base
)

SELECT
    cb.customer_id,
    cb.occupation,
    cb.income,
    cb.age,
    cb.residency,
    cb.customer_type,
    cb.risk_category,
    COALESCE(ac.account_count, 0) AS account_count,

    -- Fixed, policy-style income bands (monthly income, mass / mass-affluent / affluent / HNI)
    CASE
        WHEN cb.income < 50000 THEN 'Mass'
        WHEN cb.income < 150000 THEN 'Mass Affluent'
        WHEN cb.income < 350000 THEN 'Affluent'
        ELSE 'HNI'
    END AS income_tier_fixed,

    -- Relative, percentile-based income tier (quartile within the customer base)
    CASE ip.income_quartile
        WHEN 1 THEN 'Q1 - Bottom 25%'
        WHEN 2 THEN 'Q2'
        WHEN 3 THEN 'Q3'
        WHEN 4 THEN 'Q4 - Top 25%'
    END AS income_tier_percentile

FROM customer_base cb
LEFT JOIN account_counts ac ON ac.customer_id = cb.customer_id
LEFT JOIN income_percentiles ip ON ip.customer_id = cb.customer_id
ORDER BY cb.customer_id;