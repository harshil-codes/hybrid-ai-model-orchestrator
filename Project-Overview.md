# **Hybrid AI Model Orchestration — Financial Services (Loan Approval) — Demo Plan**

## **Summary**

### This project demonstrates an end-to-end hybrid AI architecture combining Google Vertex AI and OpenShift AI to automate loan decisioning. The frontend (React) collects applicant data and sends it to a backend (FastAPI on OpenShift), which first queries a Vertex AI model for loan approval prediction and confidence scoring. If approved, it then calls an OpenShift AI ONNX model to determine the personalized interest rate. The system integrates seamlessly with a conversational Llama-based chatbot to provide applicants personalized financial guidance and loan insights. 

![Architecture Diagram](ai-model-orchestration-arch.png.)

### **1\) High-level summary**

* Two model environments:

  * **GCP / Vertex AI** — trains a **Loan Approval** classifier (approve / manual-review / reject) using historical loan & repayment data in BigQuery.

  * **OpenShift AI** — trains a **Loan Terms** regression model to predict suggested loan amount and interest rate, using the same dataset ingested locally (Spark on OpenShift).

* **Central API Gateway (on OpenShift)** — unified `/api/v1/loan-decision` endpoint that routes calls to the correct model(s) and composes the final decision returned to the business application.

* Business application publishes loan application and repayment events **to both**: Pub/Sub → BigQuery (GCP) and Kafka/Strimzi → Spark (OpenShift) (Option A).

---

### **2\) Top-level components**

1. **Business Application (Producer)**

   * Microservice publishing JSON events (application, repayment, account updates) to Pub/Sub and Kafka.

2. **GCP Ingestion & Storage**

   * Pub/Sub → (optional Dataflow) → BigQuery (raw & feature tables).

3. **OpenShift Ingestion & Storage**

   * Kafka (Strimzi) → Spark Structured Streaming on OpenShift → local feature store (Postgres/MinIO).

4. **Model Training**

   * **Vertex AI**: training pipeline (AutoML or custom), model registry, deployment to Vertex endpoint.

   * **OpenShift AI**: Spark training job or containerized trainer, MLflow model registry (or local artifact store), model served via KServe/Knative.

5. **Model Registry & Metadata**

   * MLflow for OpenShift; Vertex Model Registry for GCP. Optional metadata sync for unified view.

6. **API Gateway / Router (on OpenShift)**

   * Stateless service that accepts inference requests, queries registry/metrics, applies routing policy, forwards to Vertex or OpenShift endpoints, aggregates responses.

7. **Orchestration & CI/CD**

   * Terraform \+ Helm / OpenShift templates, ArgoCD or Tekton for continuous deployment.

8. **Observability**

   * Prometheus \+ Grafana (OpenShift), Cloud Monitoring (GCP), OpenTelemetry traces, ELK/Cloud Logging for logs.

9. **Security & Governance**

   * Workload Identity / service accounts, mTLS, OAuth2/JWT for API, logging & auditing, data residency policies.

---

### **3\) Data model & messages**

Use a single canonical JSON schema for all events (application \+ repayment \+ updates) so both clouds can consume the same payload.

Key fields (examples):

* `event_id`, `event_type` (`application|repayment|account_update`)

* `timestamp`, `entity_type`, `entity_id`, `loan_id`

* `requested_amount`, `requested_tenor_months`

* `payment_due`, `payment_amount`, `outstanding_balance`, `num_past_due`

* `credit_score`, `annual_income`, `employment_status`, `region`

* `metadata` (freeform)

Publish same messages to:

* Pub/Sub topic `loan-events` (GCP)

* Kafka topic `loan-events` (OpenShift)

---

### **4\) End-to-end data flows**

#### **A — Ingest (GCP)**

1. Business app → Pub/Sub `loan-events`.

2. (Optional) Dataflow or Cloud Function subscribes → cleans/enriches → writes raw events to BigQuery.

3. Scheduled Vertex training pipeline reads BigQuery feature tables → trains classifier → registers model → deploys to Vertex endpoint.

#### **B — Ingest (OpenShift)**

1. Business app → Kafka `loan-events` (Strimzi).

2. Spark Structured Streaming consumes Kafka → performs feature engineering → writes features to Postgres/MinIO (feature store).

3. On-schedule or triggered training job consumes feature tables → trains regression model → registers in MLflow → deploys to KServe endpoint.

#### **C — Inference / Orchestration**

1. Business app calls `POST /api/v1/loan-decision` on API Gateway (OpenShift) with application payload.

2. Gateway:

   * Calls Vertex AI classifier endpoint → gets `approval_decision` \+ confidence.

   * If `approved` (or conditional), Gateway calls OpenShift AI regression endpoint → gets `suggested_amount`, `suggested_interest_rate`.

   * Gateway composes final response and returns to the business app.

   * All calls logged for audit; metrics emitted.

---

### **5\) Routing logic (policy examples)**

Routing decisions should be configurable (feature flags / policy store). Example decision tree:

1. If `use_case == loan_approval` → route to **Vertex AI**.

2. If `approval == approved` → route to **OpenShift AI** for terms calculation.

3. If `approval == manual_review` → respond with `manual_review_required` and optionally route partial data to OpenShift for pre-scoring.

4. If Vertex endpoint unavailable → fallback to OpenShift backup (smaller classifier) or return `service_unavailable`.

5. Dynamic metrics adjustments:

   * If OpenShift latency \> threshold, prefer Vertex for regression (if allowed).

   * If `region` requires data residency, force routing to OpenShift.

Pseudo-weighted scoring (example):

```
score = availability*0.4 + latency_score*0.2 + cost_score*0.1 + accuracy*0.3
choose highest score
```

---

### **6\) API design (example)**

`POST /api/v1/loan-decision`  
 Request:

```json
{
  "use_case": "loan_application",
  "payload": { ... canonical event fields ... },
  "requirements": {"max_latency_ms": 300, "data_residency": "on_prem"}
}
```

Response:

```json
{
  "loan_id": "LN-123",
  "approval_status": "approved",
  "approval_confidence": 0.91,
  "suggested_loan_amount": 45000.0,
  "suggested_interest_rate": 6.25,
  "model_metadata": {
    "approval_model": {"id":"gcp-approval-v2", "location":"vertex"},
    "terms_model": {"id":"ocp-terms-v1", "location":"openshift"}
  }
}
```

---

### **7\) Model specifics & data needs**

#### **Vertex AI — Loan Approval (classifier)**

* Input: applicant profile, credit history, repayment history, requested loan details, engineered features (DTI, past delinquency count).

* Label: historical approval label / outcome.

* Training: BigQuery as source, Vertex Pipelines / AutoML or custom training.

### **OpenShift AI — Loan Terms (regression)**

* Input: applicant risk metrics (credit score, recent delinquencies), loan parameters, engineered features (recent payment consistency), optional portfolio-level signals.

* Targets: interest rate (%), approved amount ($).

* Training: Spark on OpenShift reads local feature store created from Kafka stream.

Both models trained from the same canonical dataset but with different feature selections and preprocessing pipelines.


