-- Alpha Capital Bank — Project 0 Schema
-- Order matters: tables are dropped in reverse-dependency order,
-- then created in dependency order (referenced tables first).

DROP TABLE IF EXISTS beneficiaries CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS merchants CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS kyc CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id      VARCHAR(20) PRIMARY KEY,
    date_of_birth     DATE NOT NULL,
    occupation        VARCHAR(50) NOT NULL,
    income            NUMERIC(12,2) NOT NULL,
    residency         VARCHAR(20) NOT NULL,
    customer_type     VARCHAR(20) NOT NULL,
    onboarding_date   DATE NOT NULL
);

CREATE TABLE locations (
    location_id   VARCHAR(20) PRIMARY KEY,
    city          VARCHAR(50) NOT NULL,
    region        VARCHAR(50) NOT NULL,
    country       VARCHAR(50) NOT NULL,
    is_domestic   BOOLEAN NOT NULL
);

CREATE TABLE kyc (
    customer_id               VARCHAR(20) PRIMARY KEY REFERENCES customers(customer_id),
    kyc_status                VARCHAR(20) NOT NULL,
    verification_date         DATE NOT NULL,
    risk_category             VARCHAR(20) NOT NULL,
    occupation                VARCHAR(50) NOT NULL,
    source_of_funds           VARCHAR(50) NOT NULL,
    expected_monthly_volume   NUMERIC(14,2) NOT NULL
);

CREATE TABLE accounts (
    account_id      VARCHAR(20) PRIMARY KEY,
    customer_id     VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    account_type    VARCHAR(20) NOT NULL,
    opening_date    DATE NOT NULL,
    closing_date    DATE,
    branch_id       VARCHAR(10) NOT NULL,
    currency        VARCHAR(5) NOT NULL,
    status          VARCHAR(20) NOT NULL
);

CREATE TABLE devices (
    device_id           VARCHAR(20) PRIMARY KEY,
    customer_id         VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    device_type         VARCHAR(20) NOT NULL,
    operating_system    VARCHAR(20) NOT NULL,
    ip_address          VARCHAR(45) NOT NULL,
    first_seen          DATE NOT NULL
);

CREATE TABLE merchants (
    merchant_id             VARCHAR(20) PRIMARY KEY,
    merchant_name           VARCHAR(150) NOT NULL,
    merchant_category       VARCHAR(50) NOT NULL,
    business_type           VARCHAR(30) NOT NULL,
    location_id             VARCHAR(20) NOT NULL REFERENCES locations(location_id),
    is_high_risk_category   BOOLEAN NOT NULL
);

CREATE TABLE cards (
    card_id       VARCHAR(20) PRIMARY KEY,
    customer_id   VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    account_id    VARCHAR(20) REFERENCES accounts(account_id),
    card_type     VARCHAR(10) NOT NULL,
    issue_date    DATE NOT NULL,
    status        VARCHAR(15) NOT NULL
);

CREATE TABLE transactions (
    transaction_id       VARCHAR(20) PRIMARY KEY,
    timestamp             TIMESTAMP NOT NULL,
    sender_account_id     VARCHAR(20) REFERENCES accounts(account_id),
    receiver_account_id   VARCHAR(20) REFERENCES accounts(account_id),
    amount                NUMERIC(14,2) NOT NULL,
    currency              VARCHAR(5) NOT NULL,
    transaction_type      VARCHAR(30) NOT NULL,
    channel               VARCHAR(15) NOT NULL,
    merchant_id           VARCHAR(20) REFERENCES merchants(merchant_id),
    device_id             VARCHAR(20) REFERENCES devices(device_id),
    location_id           VARCHAR(20) REFERENCES locations(location_id),
    status                VARCHAR(15) NOT NULL
);

CREATE TABLE beneficiaries (
    beneficiary_id           VARCHAR(20) PRIMARY KEY,
    account_id               VARCHAR(20) NOT NULL REFERENCES accounts(account_id),
    beneficiary_name         VARCHAR(150) NOT NULL,
    beneficiary_type         VARCHAR(10) NOT NULL,
    beneficiary_account_id   VARCHAR(20) REFERENCES accounts(account_id),
    beneficiary_bank         VARCHAR(50) NOT NULL
);