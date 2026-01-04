"""
polars_engine.py
----------------
This module performs high-performance data quality metric calculations
using the Polars library.

It analyzes banking transaction data to compute numerical metrics for
seven data quality dimensions such as completeness, accuracy,
consistency, timeliness, uniqueness, validity, and integrity.

The output of this module is purely quantitative and is later
interpreted by AI agents for explanation and scoring.
"""


import polars as pl

def load_data(file_path):
    return pl.read_csv(file_path, try_parse_dates=True)

# 1. Completeness
def completeness_metrics(df):
    missing_per_col = df.null_count()
    total_missing = missing_per_col.sum_horizontal().item()
    return {
        "total_missing_cells": total_missing,
        "missing_per_column": missing_per_col.to_dicts()
    }

# 2. Accuracy
def accuracy_metrics(df):
    negative_balance = df.filter(pl.col("total_balance_after") < 0).height
    zero_amount = df.filter(pl.col("amount") == 0).height
    return {
        "negative_balance_txns": negative_balance,
        "zero_amount_txns": zero_amount
    }

# 3. Consistency
def consistency_metrics(df):
    inconsistent_txns = df.filter(
        (pl.col("txn_type") == "UPI") & (pl.col("merchant_category") == "SALARY")
    ).height
    return {"inconsistent_txns": inconsistent_txns}

# 4. Timeliness
def timeliness_metrics(df):
    future_txns = df.filter(pl.col("txn_datetime") > pl.lit("2026-01-01")).height
    return {"future_dated_txns": future_txns}

# 5. Uniqueness
def uniqueness_metrics(df):
    duplicate_txns = df.filter(df.is_duplicated()).height
    return {"duplicate_txns": duplicate_txns}

# 6. Validity
def validity_metrics(df):
    invalid_txn_type = df.filter(
        ~pl.col("txn_type").is_in(["UPI", "CARD", "NEFT", "CASH_OUT", "TRANSFER"])
    ).height
    return {"invalid_txn_type": invalid_txn_type}

# 7. Integrity
def integrity_metrics(df):
    missing_customer = df.filter(pl.col("customer_id").is_null()).height
    return {"missing_customer_id": missing_customer}
