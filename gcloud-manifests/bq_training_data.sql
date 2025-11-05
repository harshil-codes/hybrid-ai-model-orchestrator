CREATE OR REPLACE TABLE `loan_data.loan_training_data_relaxed_v3` AS
WITH entity_agg AS (
  SELECT
    entity_id,
    entity_type,
    AVG(credit_score) AS avg_credit_score,
    AVG(annual_income) AS avg_annual_income,
    AVG(requested_amount) AS avg_requested_amount,
    SAFE_DIVIDE(AVG(requested_amount), NULLIF(AVG(annual_income),0)) AS loan_to_income_ratio
  FROM `loan_data.loan_data_table`
  GROUP BY entity_id, entity_type
)
SELECT
  *,
  CASE
    WHEN entity_type = 'business' THEN
      CASE
        WHEN avg_credit_score >= 620 AND loan_to_income_ratio <= 1 THEN 1 ELSE 0 END
    WHEN entity_type = 'individual' THEN
      CASE
        WHEN avg_credit_score >= 640 AND loan_to_income_ratio <= 0.85 THEN 1 ELSE 0 END
    ELSE 0
  END AS loan_approval_status
FROM entity_agg;

