import pandas as pd
import great_expectations as ge

# Load transaction dataset
pdf = pd.read_csv("data/transactions_error.csv")

# Convert pandas dataframe to Great Expectations dataframe
df = ge.from_pandas(pdf)

# -------------------------------
# DATA QUALITY CHECKS
# -------------------------------

# 1. COMPLETENESS
# Amount should not be missing
df.expect_column_values_to_not_be_null("amount")

# 2. UNIQUENESS
# Transaction ID should be unique
df.expect_column_values_to_be_unique("txn_id")

# 3. ACCURACY
# Transaction amount should be greater than 0
df.expect_column_values_to_be_between("amount", min_value=1)

# 4. VALIDITY
# Status should contain only valid values
df.expect_column_values_to_be_in_set(
    "status", ["SUCCESS", "FAILED", "PENDING"]
)

# -------------------------------
# RUN VALIDATION
# -------------------------------
results = df.validate()

