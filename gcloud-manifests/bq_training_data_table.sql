CREATE OR REPLACE TABLE `loan_data.loan_training_data_v4` AS
WITH entity_agg AS (
  SELECT
    entity_id,
    entity_type,
    AVG(credit_score) AS avg_credit_score,
    AVG(annual_income) AS avg_annual_income,
    AVG(requested_amount) AS avg_requested_amount
  FROM `loan_data.loan_data_table`
  GROUP BY entity_id, entity_type
)
SELECT
  entity_type,
  avg_credit_score,
  avg_annual_income,
  avg_requested_amount,
  CASE
    WHEN entity_type = 'business' THEN
      CASE
        WHEN avg_credit_score >= 620
             AND SAFE_DIVIDE(avg_requested_amount, avg_annual_income) <= 1 THEN 1 ELSE 0 END
    WHEN entity_type = 'individual' THEN
      CASE
        WHEN avg_credit_score >= 640
             AND SAFE_DIVIDE(avg_requested_amount, avg_annual_income) <= 0.85 THEN 1 ELSE 0 END
    ELSE 0
  END AS loan_approval_status
FROM entity_agg;
