# Polars Engine Overview

polars_engine.py calculates **data quality metrics** for banking transactions using **Polars**, a high-performance Python DataFrame library.  

It focuses on **seven DQ dimensions**: completeness, accuracy, consistency, timeliness, uniqueness, validity, and integrity.  
This module **only computes numeric metrics**; AI agents interpret them for scoring and explanations.

## Key Functions

- load_data(file_path) → Reads CSV and parses dates.  
- completeness_metrics(df) → Counts missing values per column and total missing cells.  
- accuracy_metrics(df) → Detects negative balances and zero-amount transactions.  
- consistency_metrics(df) → Finds conflicting or illogical data (e.g., negative salary).  
- timeliness_metrics(df) → Flags future-dated transactions.  
- uniqueness_metrics(df) → Detects duplicate rows.  
- validity_metrics(df) → Checks allowed values for columns like txn_type and gender.  
- integrity_metrics(df) → Checks missing identifiers (customer_id, merchant_id).  

## How It Works with AI Agents

1. Polars computes **numeric metrics**.  
2. Metrics are sent to **CrewAI agents** (one per DQ dimension).  
3. Each agent interprets metrics, assigns scores, and recommends fixes.  
4. **Master agent** aggregates all dimension scores into a final **data quality score**.

> Polars ensures **speed, scalability, and auditability**, while AI agents provide **explainable insights**.
