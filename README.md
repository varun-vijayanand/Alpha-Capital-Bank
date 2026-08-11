# Alpha Capital Bank
### A Financial Crime Data Science Portfolio

Alpha Capital Bank is a fictional financial institution built end-to-end to demonstrate applied Data Science in the Financial Crime domain — covering data engineering, SQL analytics, customer intelligence, transaction monitoring, fraud detection, AML, machine learning, graph analytics, big data, and real-time detection.

The entire portfolio is framed as a single narrative: joining Alpha Capital Bank as a Data Scientist in its Financial Crime Analytics & Data Science team, and progressively building out the bank's analytics capability — one project, one component, at a time.

> **Positioning:** Not "a Financial Crime expert," but a Data Scientist who deliberately built hands-on experience applying data science, SQL, analytics, and big-data technologies to real Financial Crime problems.

---

## The Story

From a distance, this repo tells one story: **building a Financial Crime Analytics Platform for a modern financial institution.**

Up close, it's a series of independent, standalone projects — each solving a real business problem, each usable as its own portfolio piece, all sharing the same underlying bank, customers, and data.

**Guiding principle:** Learn → Build → Break → Investigate → Improve → Document

---

## Repository Structure

```
alpha-capital-bank/
│
├── Project 0/   → Data Foundation
├── Project 1/   → Customer Intelligence
├── Project 2/   → Transaction Monitoring
├── Project 3/   → Customer Financial Crime Risk Scoring
├── Project 4/   → Fraud Detection
├── Project 5/   → AML Machine Learning
├── Project 6/   → Financial Crime Network Analytics
├── Project 7/   → Big Data Financial Crime Platform
├── Project 8/   → Real-Time Financial Crime Detection
├── Project 9/   → Financial Crime Decisioning Platform (Capstone)
│
└── venv/        → shared Python virtual environment
```

Each `Project N/` folder is self-contained (own `README`, own code, own notebooks) but reads from the same underlying synthetic bank database established in Project 0.

---

## Project Roadmap

### Project 0 — Alpha Capital Bank Data Foundation
**Objective:** Build the synthetic banking data ecosystem every later project will use. No ML.
- Customers, accounts, transactions, cards, merchants, devices, KYC, cases, alerts, fraud labels, and screening data
- Python-based realistic synthetic data generation with behavioural scenarios, validation, and reproducibility
- SQL analytical schemas, transformations, joins, aggregations, window functions, and derived datasets
- Realistic normal *and* suspicious behavioural patterns — not random Faker records
- A reusable data-generation framework so later projects can generate new historical or event data

**Primary technologies:** Python, SQL, pandas, NumPy, Faker, PostgreSQL, Git

---

### Project 1 — Customer Intelligence
**Objective:** Understand normal customer and transaction behaviour before trying to detect crime.
- Customer profiles and segmentation
- Transaction distributions and behavioural baselines
- Rolling transaction metrics and customer-level features
- Percentiles, outliers, skewness, correlations, and behavioural analysis
- Thinking in analytical features rather than raw tables

**Primary technologies:** Python, SQL, Statistics, pandas

---

### Project 2 — Transaction Monitoring
**Objective:** Build Alpha Capital Bank's first rule-based AML transaction monitoring engine.
- KYC, AML, transaction monitoring, suspicious activity, and common red flags
- Rules for unusual transaction size, rapid movement, structuring, dormant-account activation, and geographic anomalies
- Risk indicators and alert generation
- Alert volumes, false positives, and investigator workload
- A baseline to compare future ML approaches against

**Primary technologies:** Python, Advanced SQL, Rule engines, Feature engineering

---

### Project 3 — Customer Financial Crime Risk Scoring
**Objective:** Create an interpretable customer-level Financial Crime risk score.
- Combine behavioural, geographic, counterparty, velocity, KYC, and historical-alert signals
- Scoring, weighting, normalization, and threshold logic
- Evaluate whether the score actually prioritizes customers worth reviewing
- Precision, recall, false positives, false negatives, and operational trade-offs

**Primary technologies:** Python, SQL, Statistics, Risk scoring

---

### Project 4 — Fraud Detection
**Objective:** Build a machine-learning system for detecting potentially fraudulent transactions.
- Scenarios for card fraud, account takeover, unusual devices, impossible travel, velocity attacks, and abnormal spending
- Logistic regression and tree-based models
- Class imbalance handling
- Precision, recall, F1, ROC-AUC, and PR-AUC
- Threshold optimization based on business cost, not accuracy alone

**Primary technologies:** Python, SQL, scikit-learn, Tree models, Model evaluation

---

### Project 5 — AML Machine Learning
**Objective:** Move from static rules toward statistical and machine-learning-based AML detection.
- Transaction and customer behavioural features
- Supervised and anomaly-detection approaches
- Interpretable baselines vs. stronger tree-based models
- Class imbalance, threshold selection, calibration, and model explainability
- ML performance compared against the original rule-based engine

**Primary technologies:** Python, Advanced SQL, scikit-learn, XGBoost/LightGBM, Anomaly detection

---

### Project 6 — Financial Crime Network Analytics
**Objective:** Detect suspicious relationships and networks that transaction-level models cannot see.
- Customers, accounts, merchants, and devices as nodes; financial relationships as edges
- Connected components, centrality, communities, and suspicious network structures
- Mule networks, coordinated behaviour, and hidden relationships
- Graph-derived features to feed future risk models

**Primary technologies:** Python, NetworkX, Graph analytics, SQL, Optional Neo4j

---

### Project 7 — Big Data Financial Crime Platform
**Objective:** Scale transaction monitoring from analytical datasets to large-scale processing.
- Apache Spark / PySpark and Spark SQL
- Rebuilding selected AML feature-engineering and monitoring workloads with distributed processing
- Joins, windows, partitions, caching, and performance
- pandas vs. SQL vs. Spark comparisons
- Databricks where practical

**Primary technologies:** PySpark, Spark SQL, Databricks, Python, SQL

---

### Project 8 — Real-Time Financial Crime Detection
**Objective:** Build a streaming architecture capable of reacting to suspicious activity in near real time.
- Transactions modeled as events
- Event streaming and real-time feature processing
- Kafka and Spark Structured Streaming
- Real-time velocity and behavioural signals
- Events passed through a detection/risk layer to generate alerts

**Primary technologies:** Kafka, Spark Structured Streaming, Python, SQL, Streaming concepts

---

### Project 9 — Alpha Capital Bank Financial Crime Decisioning Platform *(Capstone)*
**Objective:** Bring every previous project into one end-to-end Financial Crime analytics ecosystem.
- Integrate customer, KYC, transaction, rule, ML, graph, and streaming components
- A coherent risk-decisioning architecture
- Documented batch and real-time paths
- Alert generation, prioritization, and investigation workflow concepts
- Demonstrates how individual projects fit into a bank-wide Financial Crime analytics platform

**Primary technologies:** Python, SQL, PySpark, Kafka, Graph analytics, ML, Data engineering

---

## Five Continuous Learning Tracks

Each project advances all five tracks simultaneously, at increasing depth:

| Track | Progression |
|---|---|
| **Python** | Data manipulation & generation → feature engineering & ML → modular pipelines, testing, logging → PySpark & streaming |
| **SQL** | Core querying → CTEs & window functions → behavioural feature generation → optimization, analytical SQL & Spark SQL |
| **Financial Crime** | Banking/KYC basics → AML & transaction monitoring → fraud & risk → network crime, real-time detection & model governance |
| **Analytics & Statistics** | Descriptive statistics → anomaly detection & hypothesis testing → imbalanced classification, calibration, thresholds, validation & drift |
| **Technology** | Local analytical workflows → ML tooling → graph analytics → PySpark/Databricks → Kafka & streaming |

---

## Standard Framework for Every Project

Every project in this repo is approached with the same set of questions:

1. What is the business problem?
2. What is the Financial Crime problem?
3. What data do we need?
4. How can the problem be solved analytically before using ML?
5. How would the solution be productionized?
6. How do we know whether the solution works?

---

## What This Roadmap Deliberately Avoids

- Becoming a regulatory/compliance expert instead of a Data Scientist
- Spending months on generic Python or machine-learning theory
- Building unrelated Kaggle projects
- Learning tools without applying them to a concrete problem
- Jumping directly into advanced models before understanding the business problem
- Optimizing models only for generic metrics such as accuracy
- Treating fraud, AML, and Financial Crime as the same problem

---

## Getting Started

Each project folder contains its own setup instructions, but the shared foundation is:

```bash
# from the repo root
python3 -m venv venv
source venv/bin/activate       # Mac/Linux

cd "Project 0"
pip install -r requirements.txt
python main.py                 # regenerates and loads the full synthetic dataset
```

All later projects read from the PostgreSQL database built in **Project 0**.

---

## License

This is a personal learning/portfolio project. All data is synthetic — no real customer, transaction, or institutional data is used anywhere in this repository.

