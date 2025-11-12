curl -X POST -H "Content-Type: application/json" \
-d '{
  "avg_credit_score": 650,
  "avg_annual_income": 250000,
  "avg_requested_amount": 100000
}' \
https://loan-backend-route-loan-app.apps.asa-demo.7mhsq.gcp.redhatworkshops.io/predict -k
