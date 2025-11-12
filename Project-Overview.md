# Hybrid AI Model Orchestration — Financial Services (Loan Approval)

## **Summary**

#### This project demonstrates an end-to-end hybrid AI architecture combining Google Vertex AI and OpenShift AI to automate loan decisioning. The frontend (React) collects applicant data and sends it to a backend (FastAPI on OpenShift), which first queries a Vertex AI model for loan approval prediction and confidence scoring. If approved, it then calls an OpenShift AI ONNX model to determine the personalized interest rate. The system integrates seamlessly with a conversational Llama-based chatbot to provide applicants personalized financial guidance and loan insights. 

### Arcitecture Diagram
![Architecture Diagram](images/ai-model-orchestration-arch.png)

### System Components
🏦 Business Frontend

React + Vite web UI.

Accepts loan input fields: credit_score, annual_income, requested_amount, requested_tenor_months.

Displays model inference results (approval, confidence, interest rate).

Integrates a chatbot panel (bottom-right) that talks to the backend /chat endpoint.

⚙️ Backend (API Gateway / Inference Router)

Implemented in FastAPI, deployed on OpenShift.

Routes requests as follows:

Calls Vertex AI endpoint (loan approval model).

If approved → calls OpenShift AI model (interest rate model).

Stores context for chatbot awareness.

Also serves /chat, which forwards prompts to the Llama model along with recent decision context.

☁️ Vertex AI (Google Cloud)

Dataset: loan_training_data_v5 in BigQuery.
Features: avg_credit_score, avg_annual_income, avg_requested_amount, avg_requested_tenor_months, loan_to_income_ratio.
Target: loan_approval_status.

Model: AutoML Classification trained on BigQuery data.

Endpoint: Deployed Vertex model serving predict requests via REST API.

🔺 OpenShift AI (on OpenShift Cluster)

Interest-rate regression model served through KServe (ONNX).

Llama 8B Instruct model exposed through /v1/completions API for chatbot.

Both models run in the Data Science Cluster environment.

### Data & Flow

User submits loan request via frontend.

Backend calls Vertex AI to classify approval.

If approved → backend queries OpenShift AI ONNX model for predicted interest rate.

Backend returns combined result to frontend.

Chatbot can interpret the last prediction context (approval status, confidence, interest rate, income, etc.) and give guidance such as:

“Your loan was approved at 11% interest — improve your score to 700 to lower it.”

“Your loan was denied — try reducing requested amount or improving income.”

### Technical Highlights

Cross-cloud orchestration: OpenShift AI + Vertex AI via secure service account (GCP key secret mounted in pod).

Containerized deployment: Frontend + Backend built and deployed on OpenShift using BuildConfigs and Routes.

Prompt-engineered chatbot with dynamic context from previous inference results.

BigQuery-based dataset creation and Vertex AI AutoML training pipeline.

No Spark/Kafka components — ingestion simplified via direct Pub/Sub → BigQuery → Vertex.

### Typical End-to-End Flow
[Frontend UI]
    ↓
[Backend API (FastAPI)]
    ├─> Vertex AI Model (Loan Approval)
    │       ↳ Response: approved + confidence
    ├─> OpenShift AI Model (Interest Rate)
    │       ↳ Response: interest rate prediction
    └─> Llama 8B Chatbot (OpenShift AI)
            ↳ Context-aware loan advice

