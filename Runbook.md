* Deploy an OCP cluster on GCP  
* Enable api’s for artifactory, pub/sub, bigquery  
* Give the right service accounts correct privileges, for the demo set to admin  
* Build the app image and push to artifactory  
* Test the app locally and publish messages to pub/sub  
* Define bq table schema and send messages from pub/sub to bq  
* Create project, create GCP service account secret.  
* Deploy the app on OCP and verify messages are being pushed to pub/sub topic  
* Create a table to have a column for loan\_approval\_status, the query for creating table is below  
* Table to create loan\_approval\_status column:

``CREATE OR REPLACE TABLE `loan_data.loan_training_data_synthetic` AS``  
`WITH entity_agg AS (`  
 `SELECT`  
   `entity_id,`  
   `entity_type,`  
   `ANY_VALUE(loan_id) AS loan_id,`  
   `AVG(credit_score) AS avg_credit_score,`  
   `AVG(annual_income) AS avg_annual_income,`  
   `ANY_VALUE(employment_status) AS employment_status,`  
   `ANY_VALUE(region) AS region,`  
   `AVG(requested_amount) AS avg_requested_amount,`  
   `AVG(requested_tenor_months) AS avg_requested_tenor_months,`  
   `AVG(num_past_due) AS total_past_due,`  
   `AVG(payment_amount) AS avg_payment_amount,`  
   `AVG(payment_due) AS avg_payment_due,`  
   `MAX(outstanding_balance) AS max_outstanding_balance,`  
   `-- Derived ratios`  
   `SAFE_DIVIDE(AVG(requested_amount), NULLIF(AVG(annual_income),0)) AS loan_to_income_ratio,`  
   `SAFE_DIVIDE(AVG(payment_amount), NULLIF(AVG(payment_due),0)) AS payment_coverage_ratio`  
 `` FROM `loan_data.loan_data_table` ``  
 `GROUP BY entity_id, entity_type`  
`)`  
`SELECT`  
 `*,`  
 `CASE`  
   `WHEN entity_type = 'business' THEN`  
     `CASE`  
       `WHEN avg_credit_score >= 660`  
            `AND total_past_due <= 2`  
            `AND loan_to_income_ratio <= 0.8`  
            `AND payment_coverage_ratio >= 0.9`  
       `THEN 1 ELSE 0 END`  
   `WHEN entity_type = 'individual' THEN`  
     `CASE`  
       `WHEN avg_credit_score >= 700`  
            `AND total_past_due <= 1`  
            `AND loan_to_income_ratio <= 0.6`  
            `AND payment_coverage_ratio >= 0.95`  
       `THEN 1 ELSE 0 END`  
   `ELSE 0`  
 `END AS loan_approval_status`  
`FROM entity_agg;`

* Table to create training Data:

``CREATE OR REPLACE TABLE `loan_data.loan_training_data_relaxed_v3` AS``  
`WITH entity_agg AS (`  
  `SELECT`  
    `entity_id,`  
    `entity_type,`  
    `AVG(credit_score) AS avg_credit_score,`  
    `AVG(annual_income) AS avg_annual_income,`  
    `AVG(requested_amount) AS avg_requested_amount,`  
    `SAFE_DIVIDE(AVG(requested_amount), NULLIF(AVG(annual_income),0)) AS loan_to_income_ratio`  
  `` FROM `loan_data.loan_data_table` ``  
  `GROUP BY entity_id, entity_type`  
`)`  
`SELECT`  
  `*,`  
  `CASE`  
    `WHEN entity_type = 'business' THEN`  
      `CASE`  
        `WHEN avg_credit_score >= 620 AND loan_to_income_ratio <= 1 THEN 1 ELSE 0 END`  
    `WHEN entity_type = 'individual' THEN`  
      `CASE`  
        `WHEN avg_credit_score >= 640 AND loan_to_income_ratio <= 0.85 THEN 1 ELSE 0 END`  
    `ELSE 0`  
  `END AS loan_approval_status`  
`FROM entity_agg;`

CREATE OR REPLACE TABLE \`loan\_data.loan\_training\_data\_raw\_v3\` AS  
WITH entity\_agg AS (  
  SELECT  
    entity\_id,  
    entity\_type,  
    AVG(credit\_score) AS avg\_credit\_score,  
    AVG(annual\_income) AS avg\_annual\_income,  
    AVG(requested\_amount) AS avg\_requested\_amount,  
    SAFE\_DIVIDE(AVG(requested\_amount), NULLIF(AVG(annual\_income), 0)) AS loan\_to\_income\_ratio  
  FROM \`loan\_data.loan\_data\_table\`  
  GROUP BY entity\_id, entity\_type  
)  
SELECT  
  avg\_credit\_score,  
  avg\_annual\_income,  
  avg\_requested\_amount,  
  CASE  
    WHEN entity\_type \= 'business' THEN  
      CASE  
        WHEN avg\_credit\_score \>= 620  
             AND loan\_to\_income\_ratio \<= 1 THEN 1 ELSE 0 END  
    WHEN entity\_type \= 'individual' THEN  
      CASE  
        WHEN avg\_credit\_score \>= 640  
             AND loan\_to\_income\_ratio \<= 0.85 THEN 1 ELSE 0 END  
    ELSE 0  
  END AS loan\_approval\_status  
FROM entity\_agg;

* Create dataset from the bq table  
* Using vertex AI train the model  
* Serve the model in vertex AI

OpenShift

* Install OCP AI from Operatorhub, create Data Science Cluster  
* Install OCP Service mesh operator  
* Install OCP Serverless Operator  
* Create Workbench, train the model  
* Deploy the model and Serve using OpenShift AI  
* Deploy the backend app to consume both the models  
* Deploy frontend app to connect to the backend

