from fastapi import FastAPI, Request, HTTPException
import requests
import os
import google.auth
import google.auth.transport.requests as grequests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Loan Approval + Interest Rate Predictor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-loan-app.apps.asa-demo.7mhsq.gcp.redhatworkshops.io",
        "https://loan-frontend-route-loan-app.apps.asa-demo.7mhsq.gcp.redhatworkshops.io",
        "*"  # optional: for quick testing, allows any origin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# --- Environment Configuration ---
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
VERTEX_REGION = os.getenv("VERTEX_REGION", "us-central1")
VERTEX_ENDPOINT_ID = os.getenv("VERTEX_ENDPOINT_ID")
OPENSHIFT_MODEL_URL = os.getenv("OPENSHIFT_MODEL_URL")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

if not (VERTEX_PROJECT_ID and VERTEX_ENDPOINT_ID and OPENSHIFT_MODEL_URL):
    raise RuntimeError("Missing environment configuration for Vertex AI or OpenShift AI model.")


# --- Llama Chatbot Model URL (OpenShift AI) ---
LLAMA_URL = os.getenv(
    "LLAMA_URL",
    "https://redhataillama-31-8b-instruct-loan-rate-model.apps.asa-demo.7mhsq.gcp.redhatworkshops.io/v1/completions"
)

# --- Chat Endpoint ---
@app.post("/chat")
async def chat(request: Request):
    """Handles chatbot interactions via OpenShift AI Llama model"""
    data = await request.json()
    user_message = data.get("message", "")

    # Prompt engineering for context
    system_prompt = (
        "You are an intelligent financial assistant specializing in loan guidance. "
        "If the loan is approved, explain how the user can lower their interest rate "
        "(e.g., improving credit score, shorter tenors, or reducing debt ratio). "
        "If the loan is rejected, give actionable advice for approval next time "
        "(e.g., improving income, reducing requested loan amount, or repaying debts). "
        "Be concise, empathetic, and use simple terms."
    )

    # Create the model input
    payload = {
        "prompt": f"{system_prompt}\n\nUser: {user_message}\nAssistant:",
        "max_tokens": 200,
        "temperature": 0.4
    }

    try:
        response = requests.post(LLAMA_URL, json=payload, verify=False)
        response.raise_for_status()
        result = response.json()
        model_reply = result.get("choices", [{}])[0].get("text", "").strip()
        return {"response": model_reply}

    except Exception as e:
        return {"error": f"Chat service error: {str(e)}"}



@app.post("/predict")
def predict(payload: dict):
    """
    Step 1: Validate input and compute derived features
    Step 2: Query Vertex AI model for loan approval
    Step 3: If approved (confidence ≥ threshold), query OpenShift AI model for interest rate
    """

    # --- Step 1️⃣ Validate and preprocess input ---
    avg_credit_score = float(payload.get("avg_credit_score", 650))
    avg_annual_income = float(payload.get("avg_annual_income", 100000))
    avg_requested_amount = float(payload.get("avg_requested_amount", 50000))

    # Derived ratio
    loan_to_income_ratio = avg_requested_amount / max(avg_annual_income, 1)

    # Placeholder defaults (used by interest rate model)
    avg_requested_tenor_months = float(payload.get("avg_requested_tenor_months", 60))
    total_past_due = float(payload.get("total_past_due", 0.05))

    # Build payload for Vertex AI
    vertex_input = {
        "instances": [
            {
                "avg_credit_score": avg_credit_score,
                "avg_annual_income": avg_annual_income,
                "avg_requested_amount": avg_requested_amount,
                "loan_to_income_ratio": loan_to_income_ratio,
            }
        ]
    }

    # --- Step 2️⃣ Query Vertex AI Model (loan approval) ---
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = grequests.Request()
    creds.refresh(auth_req)
    token = creds.token

    vertex_url = (
        f"https://{VERTEX_REGION}-aiplatform.googleapis.com/v1/"
        f"projects/{VERTEX_PROJECT_ID}/locations/{VERTEX_REGION}/endpoints/{VERTEX_ENDPOINT_ID}:predict"
    )

    vertex_response = requests.post(
        vertex_url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=vertex_input,
    )

    if vertex_response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Vertex AI error: {vertex_response.text}")

    vertex_result = vertex_response.json()
    predictions = vertex_result.get("predictions", [])[0]
    classes = predictions.get("classes", [])
    scores = predictions.get("scores", [])

    # Find confidence for class "1" (approved)
    approval_idx = classes.index("1") if "1" in classes else 0
    approval_score = scores[approval_idx]

    # --- Step 3️⃣ Approval Decision ---
    if approval_score < CONFIDENCE_THRESHOLD:
        return {
            "loan_approved": False,
            "approval_confidence": approval_score,
            "reason": f"Confidence below threshold ({CONFIDENCE_THRESHOLD})",
            "vertex_response": vertex_result,
        }

    # --- Step 4️⃣ Query OpenShift AI Model (interest rate) ---
    openshift_payload = {
        "inputs": [
            {
                "name": "input:0",
                "shape": [1, 5],
                "datatype": "FP32",
                "data": [
                    avg_credit_score,
                    avg_annual_income,
                    avg_requested_amount,
                    avg_requested_tenor_months,
                    total_past_due,
                ],
            }
        ]
    }

    oai_response = requests.post(OPENSHIFT_MODEL_URL, json=openshift_payload, verify=False)
    if oai_response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"OpenShift AI error: {oai_response.text}")

    oai_result = oai_response.json()
    interest_rate = oai_result.get("outputs", [{}])[0].get("data", [None])[0]

    # --- Step 5️⃣ Final Response ---
    return {
        "loan_approved": True,
        "approval_confidence": approval_score,
        "predicted_interest_rate": interest_rate,
        "vertex_model_output": vertex_result,
        "openshift_model_output": oai_result,
    }

