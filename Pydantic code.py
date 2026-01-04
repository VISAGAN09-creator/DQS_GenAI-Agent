from pydantic import BaseModel, condecimal, constr, ValidationError, validator
from datetime import datetime
from typing import Literal, List, Dict, Any
import csv

#  Pydantic Transaction model  (Roles 1 & 2: gatekeeper + contract)

class Transaction(BaseModel):
    # Basic identifiers
    txn_id: constr(min_length=1, max_length=20)
    txn_datetime: datetime

    # Customer info
    account_number: constr(regex=r"^X{6}\d{4}$")   # XXXXXX1234
    customer_id: constr(min_length=1, max_length=20)
    customer_name: constr(min_length=3, max_length=80)
    age: int
    gender: Literal["M", "F", "O"]
    monthly_income: condecimal(gt=0)

    # Balances & transaction
    total_balance_before: condecimal()
    total_balance_after: condecimal()
    txn_type: Literal["UPI", "CARD", "NEFT", "CASH_OUT", "TRANSFER"]
    amount: condecimal(gt=0)

    # Merchant data
    merchant_id: constr(min_length=1, max_length=20)
    merchant_name: constr(min_length=2, max_length=80)
    merchant_category: constr(min_length=2, max_length=40)
    merchant_city: constr(min_length=2, max_length=40)
    merchant_country: constr(min_length=2, max_length=2)

    # Fraud label
    is_fraud: int  # 0 or 1

    @validator("age")
    def age_range(cls, v):
        if not 18 <= v <= 100:
            raise ValueError("age must be between 18 and 100")
        return v

    @validator("merchant_country")
    def upper_country(cls, v):
        return v.upper()

    @validator("total_balance_after")
    def balance_logic(cls, new_bal, values):
        # Only run if needed fields are present
        required = {"total_balance_before", "amount", "txn_type"}
        if not required.issubset(values.keys()):
            return new_bal

        before = values["total_balance_before"]
        amount = values["amount"]
        ttype = values["txn_type"]

        if ttype in {"UPI", "CARD", "CASH_OUT", "TRANSFER"}:
            expected = before - amount
        elif ttype == "NEFT":  # salary / incoming
            expected = before + amount
        else:
            expected = new_bal

        # Allow tolerance of 1 unit
        if abs(expected - new_bal) > 1:
            raise ValueError("balance after does not match txn_type and amount")
        return new_bal


#  ROLE 1: Gatekeeper

def load_and_validate(csv_path: str):
    valid: List[Transaction] = []
    errors: List[tuple[int, Any]] = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            try:
                tx = Transaction(**row)       # Role 1 in action
                valid.append(tx)
            except ValidationError as e:
                errors.append((i, e.errors()))
    return valid, errors


#  ROLE 3: DQS penalty & explanation generator

def summarize_pydantic_errors(errors: List[tuple[int, Any]]) -> Dict[str, List[int]]:
    """
    Group Pydantic errors by message → list of row numbers
    """
    reason_map: Dict[str, List[int]] = {}
    for row_no, err_list in errors:
        for err in err_list:
            msg = err["msg"]
            reason_map.setdefault(msg, []).append(row_no)
    return reason_map


def dqs_from_pydantic(total_rows: int, failed_rows: int, base_dqs: int = 100) -> int:
    penalty_per_row = 5
    return max(0, base_dqs - failed_rows * penalty_per_row)



#  ROLE 2: Universal contract used by agents

class AccuracyAgent:
    def run(self, txns: List[Transaction]) -> Dict[str, Any]:
        # Here we assume basic math already checked by Pydantic,
        # we just highlight any remaining anomalies (demo only).
        return {"dimension": "accuracy", "score": 100, "issues": []}


class CompletenessAgent:
    def run(self, txns: List[Transaction], total_rows: int) -> Dict[str, Any]:
        valid_rows = len(txns)
        score = round(valid_rows / total_rows * 100, 2)
        return {"dimension": "completeness", "score": score}


class ConsistencyAgent:
    def run(self, txns: List[Transaction]) -> Dict[str, Any]:
        # Demo: check that txn_type & merchant_category look consistent
        issues = []
        for t in txns:
            if t.txn_type == "NEFT" and t.merchant_category != "SALARY":
                issues.append(t.txn_id)
        score = 100 - len(issues) * 5
        return {"dimension": "consistency", "score": max(score, 0), "issues": issues}


class ValidityAgent:
    def run(self, txns: List[Transaction]) -> Dict[str, Any]:
        # Demo: mark very large transactions vs income
        issues = []
        for t in txns:
            if t.amount > t.monthly_income * 3:
                issues.append(t.txn_id)
        score = 100 - len(issues) * 5
        return {"dimension": "validity", "score": max(score, 0), "issues": issues}


#  ROLE 4: Privacy & role-aware data shaping

class CustomerTransaction(BaseModel):
    txn_id: str
    txn_datetime: datetime
    account_number: str      # already masked in CSV
    customer_name: str
    amount: condecimal(gt=0)
    merchant_name: str
    merchant_category: str
    merchant_city: str
    merchant_country: str


class EmployeeTransaction(Transaction):
    # inherits full Transaction; you can add branch_code, product_code etc.
    pass


def view_for_customer(tx: Transaction) -> CustomerTransaction:
    data = {
        "txn_id": tx.txn_id,
        "txn_datetime": tx.txn_datetime,
        "account_number": tx.account_number,
        "customer_name": tx.customer_name,
        "amount": tx.amount,
        "merchant_name": tx.merchant_name,
        "merchant_category": tx.merchant_category,
        "merchant_city": tx.merchant_city,
        "merchant_country": tx.merchant_country,
    }
    return CustomerTransaction(**data)


def view_for_employee(tx: Transaction) -> EmployeeTransaction:
    return EmployeeTransaction(**tx.dict())


#  ROLE 5: Testing & simulation helper

def make_test_transaction(txn_id: str = "TEST001", bad: bool = False) -> dict:
    base = dict(
        txn_id=txn_id,
        txn_datetime="2025-12-10 10:00:00",
        account_number="XXXXXX9999",
        customer_id="TESTCUST",
        customer_name="Test User",
        age="30",
        gender="M",
        monthly_income="50000",
        total_balance_before="80000",
        total_balance_after="75000",
        txn_type="CARD",
        amount="5000",
        merchant_id="MTEST1",
        merchant_name="Test Store",
        merchant_category="GROCERY",
        merchant_city="Mumbai",
        merchant_country="IN",
        is_fraud="0",
    )
    if bad:
        base["amount"] = "0"
        base["total_balance_after"] = "-1000"
    return base



def main():
    csv_path = "transactions.csv"  # save your CSV sample with this name

    # ---- Role 1: gatekeeper ----
    txns, errors = load_and_validate(csv_path)
    total_rows = len(txns) + len(errors)
    failed_rows = len(errors)

    print(f"Total rows: {total_rows}, Pydantic failed rows: {failed_rows}")

    # ---- Role 3: DQS penalty + reasons ----
    reason_map = summarize_pydantic_errors(errors)
    dqs_after_pyd = dqs_from_pydantic(total_rows, failed_rows)
    print("\nPydantic error summary (Role 3):")
    for msg, rows in reason_map.items():
        print(f"- {msg}: rows {rows}")
    print(f"Pydantic-based DQS start: {dqs_after_pyd}/100\n")

    # ---- Role 2: universal contract sent to agents ----
    acc_agent = AccuracyAgent()
    comp_agent = CompletenessAgent()
    cons_agent = ConsistencyAgent()
    val_agent = ValidityAgent()

    acc_res = acc_agent.run(txns)
    comp_res = comp_agent.run(txns, total_rows)
    cons_res = cons_agent.run(txns)
    val_res = val_agent.run(txns)

    dim_scores = [acc_res["score"], comp_res["score"],
                  cons_res["score"], val_res["score"]]
    dqs_final = sum(dim_scores) / len(dim_scores)

    print("Agent scores (using Transaction model, Role 2):")
    print(acc_res)
    print(comp_res)
    print(cons_res)
    print(val_res)
    print(f"\nFinal DQS (including agent logic): {dqs_final:.2f}/100\n")

    # ---- Role 4: role-aware shaping ----
    print("Customer view of first valid txn (Role 4):")
    if txns:
        cv = view_for_customer(txns[0])
        ev = view_for_employee(txns[0])
        print("CustomerTransaction:", cv.dict())
        print("\nEmployeeTransaction:", {k: ev.dict()[k] for k in list(ev.dict().keys())[:8]}, "...")

    # ---- Role 5: testing helper ----
    print("\nRole 5 test: synthetic bad transaction validation:")
    try:
        Transaction(**make_test_transaction("BAD_TEST", bad=True))
    except ValidationError as e:
        print("Synthetic bad transaction correctly rejected with errors:")
        for err in e.errors():
            print(" -", err["loc"], ":", err["msg"])


if __name__ == "__main__":
    main()
