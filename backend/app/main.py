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


@app.post("/chat")
async def chat(request: Request):
    """Handles chatbot interactions via OpenShift AI Llama model with context awareness."""
    data = await request.json()
    user_message = data.get("message", "")

    last_decision = getattr(app.state, "last_loan_decision", None)

    # Build contextual section
    if last_decision:
        context_summary = (
            f"Loan Approved: {'Yes' if last_decision['loan_approved'] else 'No'}\n"
            f"Confidence: {last_decision['approval_confidence']:.2f}\n"
            f"Predicted Interest Rate: {last_decision.get('predicted_interest_rate', 'N/A')}\n"
            f"Credit Score: {last_decision['avg_credit_score']}\n"
            f"Annual Income: {last_decision['avg_annual_income']}\n"
            f"Requested Amount: {last_decision['avg_requested_amount']}\n"
        )
    else:
        context_summary = "No loan decision context available yet."

    # ✳️ Structured system prompt for better grounding
    prompt = f"""
You are a smart and empathetic financial assistant helping users understand their loan results.

Context from the latest loan prediction:
{context_summary}

User asked: "{user_message}"

Respond based on the above context.
If the loan was denied, explain why and give 2–3 clear improvement tips.
If approved, explain what helped and how to reduce the interest rate further.
Be concise, friendly, and encouraging.
"""

    payload = {
        "prompt": prompt,
        "max_tokens": 250,
        "temperature": 0.5,
    }

    try:
        response = requests.post(LLAMA_URL, json=payload, verify=False)
        response.raise_for_status()
        data = response.json()
        reply = data.get("choices", [{}])[0].get("text", "No reply from model").strip()
        return {"response": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")


@app.post("/predict")
def predict(payload: dict):
    # Step 1️⃣ Preprocess input
    avg_credit_score = float(payload.get("avg_credit_score", 650))
    avg_annual_income = float(payload.get("avg_annual_income", 100000))
    avg_requested_amount = float(payload.get("avg_requested_amount", 50000))
    loan_to_income_ratio = avg_requested_amount / max(avg_annual_income, 1)

    avg_requested_tenor_months = float(payload.get("avg_requested_tenor_months", 60))
    total_past_due = float(payload.get("total_past_due", 0.05))

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

    # Step 2️⃣ Vertex AI call
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
    approval_idx = classes.index("1") if "1" in classes else 0
    approval_score = scores[approval_idx]

    # Step 3️⃣ Decision Logic
    loan_approved = approval_score >= CONFIDENCE_THRESHOLD
    interest_rate = None
    oai_result = {}

    if loan_approved:
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
        if oai_response.status_code == 200:
            oai_result = oai_response.json()
            interest_rate = oai_result.get("outputs", [{}])[0].get("data", [None])[0]

    # 🔹 Always store last decision for chatbot context
    app.state.last_loan_decision = {
        "loan_approved": loan_approved,
        "approval_confidence": approval_score,
        "predicted_interest_rate": interest_rate,
        "avg_credit_score": avg_credit_score,
        "avg_annual_income": avg_annual_income,
        "avg_requested_amount": avg_requested_amount,
    }

    return {
        "loan_approved": loan_approved,
        "approval_confidence": approval_score,
        "predicted_interest_rate": interest_rate,
        "vertex_model_output": vertex_result,
        "openshift_model_output": oai_result,
    }

