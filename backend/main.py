# backend/main.py
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import requests
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("loan-backend")

app = FastAPI(title="Loan Interest Rate Backend")

# ENV vars
MODEL_ENDPOINT = os.environ.get(
    "MODEL_ENDPOINT",
    "https://interest-rate-loan-rate-model.apps.asa-demo.7mhsq.gcp.redhatworkshops.io/v2/models/interest-rate/infer"
)
# Input tensor name used by the model; many exported TF->ONNX setups use "input:0" or "input"
MODEL_INPUT_NAME = os.environ.get("MODEL_INPUT_NAME", "input:0")
# Output tensor name (optional)
# If empty, we will simply return the outputs array from the model response
MODEL_OUTPUT_NAME = os.environ.get("MODEL_OUTPUT_NAME", "")

# Feature fields - match the model's expected order
FEATURE_FIELDS = [
    "avg_credit_score",
    "avg_annual_income",
    "avg_requested_amount",
    "avg_requested_tenor_months",
    "total_past_due"
]


class LoanRequest(BaseModel):
    # Accept raw JSON fields from the frontend
    avg_credit_score: float = Field(..., example=720)
    avg_annual_income: float = Field(..., example=95000)
    avg_requested_amount: float = Field(..., example=35000)
    avg_requested_tenor_months: float = Field(..., example=60)
    total_past_due: float = Field(..., example=0.04)
    model_version: Optional[str] = Field(None, example="5")  # optional override


@app.get("/health")
def health():
    return {"status": "ok", "model_endpoint": MODEL_ENDPOINT}


@app.post("/predict")
def predict(req: LoanRequest):
    # Build feature vector in the correct order (baked normalization in model)
    inputs = [getattr(req, f) for f in FEATURE_FIELDS]

    # Prepare Triton/ModelMesh style v2 request payload (OpenShift AI/OVMS expects this format)
    # Use MODEL_INPUT_NAME by default
    v2_payload = {
        "inputs": [
            {
                "name": MODEL_INPUT_NAME,
                "shape": [1, len(inputs)],
                "datatype": "FP32",
                # data should be a flattened list or nested list; we send flat list
                "data": inputs
            }
        ]
    }

    # If client provided a model_version, target that model
    url = MODEL_ENDPOINT
    if req.model_version:
        # try to append version to the path if MODEL_ENDPOINT is the base predict path
        # Model endpoints typically are like: .../v2/models/<model>/infer
        # If user provided version, the endpoint will still accept it since we set version as path param earlier.
        # Otherwise we add ?version=...
        if "?" in url:
            url = f"{url}&version={req.model_version}"
        else:
            url = f"{url}?version={req.model_version}"

    logger.info("Calling model endpoint: %s", url)
    try:
        resp = requests.post(url, json=v2_payload, timeout=15)
    except Exception as e:
        logger.exception("Model call failed")
        raise HTTPException(status_code=502, detail=f"Model call failed: {e}")

    if resp.status_code != 200:
        logger.error("Model returned non-200: %s - %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail=f"Model returned {resp.status_code}: {resp.text}")

    j = resp.json()
    # typical successful response structure:
    # { "model_name": "...", "model_version": "...", "outputs":[{ "name":"Identity:0", "shape":[1,1], "datatype":"FP32", "data":[6.123]}] }

    outputs = j.get("outputs")
    if not outputs:
        raise HTTPException(status_code=502, detail=f"Invalid model response: {j}")

    # If MODEL_OUTPUT_NAME provided, pick matching output
    if MODEL_OUTPUT_NAME:
        out_val = None
        for out in outputs:
            if out.get("name") == MODEL_OUTPUT_NAME:
                out_val = out.get("data")
                break
        if out_val is None:
            # fallback to first output
            out_val = outputs[0].get("data")
    else:
        out_val = outputs[0].get("data")

    # Usually out_val is e.g. [6.2] shape [1,1]; return single scalar
    try:
        scalar = out_val[0] if isinstance(out_val, (list, tuple)) and len(out_val) > 0 else out_val
    except Exception:
        scalar = out_val

    return {
        "input": {f: getattr(req, f) for f in FEATURE_FIELDS},
        "model_endpoint": url,
        "raw_model_response": j,
        "predicted_interest_rate": float(scalar)  # return a float for frontend
    }

