# Pydantic :
* A Python library
* Used to validate & manage data using python type hints.
## Key roles:
* Auto data validation
* Detailed error handling
* Easy data integrity
* Type coercion and parsing
## Role of Pydantic in DQS (Data Quality Scores):
1.Gatekeeper role:

* Rejects malformed rows before they reach our Master AI agents(validates).
* Converts strings to types (CSV text → datetime, float, int)
* Enforces schema (all required columns present, correct formats)
  
**Diagram Flow:**  
Raw CSV -> Pydantic ->  clean transactions -> Master agent.

2.Universal data contract for all agents:

* a single, strict Transaction model that every quality agent (Accuracy, Completeness, Consistency, Validity) uses
* Hence all see the same clean structure instead of raw CSV rows.
    
**Diagram Flow:**  
CSV rows → Transaction model list → Polars Data Frame → Master Agent → Accuracy Agent → Completeness Agent → Consistency Agent → Validity Agent.

3.DQS penalty & explanation generator:

* Pydantic’s errors become inputs to your DQS score and to the recommendations shown to customer and employee.
  
**Diagram Flow:**  
CSV → Pydantic validation → collect errors → compute penalties → DQS ↓ + alerts.

4.Privacy & role-aware data shaping:

* After validation, you can use different Pydantic models or views derived from the same Transaction to enforce privacy:

1.Customer-safe view:
* Hide internal or sensitive fields.
   
2.Employee-detailed view:
* Show extra internal fields.
   
**Diagram Flow:**  
CSV → Pydantic Transaction (full) → 
   if role=CUSTOMER  → CustomerTransaction view → customer UI
   if role=EMPLOYEE  → EmployeeTransaction view → ops dashboard

5.Testing & simulation helper:
* Easy to generate and test synthetic transactions for your agents.
  
**Diagram flow:**  
Synthetic rules / edge cases  
        ↓  
  Pydantic Transaction model factory  
        ↓  
Synthetic Transaction list (valid + invalid)  
        ↓  
Polars Test DataFrame  
        ↓  
Master Agent (test mode)  
      ↓         ↓           ↓            ↓  
 Accuracy    Completeness  Consistency  Validity  Agents  
        ↓  
Test DQS + Expected Alerts  
        ↓  
  CI/CD decision (pass/fail before release)


 
