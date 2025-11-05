import React, { useState } from "react";
import axios from "axios";

const App = () => {
  const [form, setForm] = useState({
    avg_credit_score: "",
    avg_annual_income: "",
    avg_requested_amount: ""
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const backendUrl = import.meta.env.VITE_BACKEND_URL || "http://loan-backend-route-loan-app.apps.asa-demo.7mhsq.gcp.redhatworkshops.io/predict";

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setResult(null);

  try {
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        avg_credit_score: Number(form.avg_credit_score),
        avg_annual_income: Number(form.avg_annual_income),
        avg_requested_amount: Number(form.avg_requested_amount),
      }),
    });

    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

    const data = await response.json();
    setResult(data);
  } catch (err) {
    console.error("❌ API Error:", err);
    alert("Something went wrong. Please try again.");
  } finally {
    setLoading(false);
  }
};


  return (
    <div style={{ fontFamily: "Inter, sans-serif", padding: "40px", maxWidth: "600px", margin: "auto" }}>
      <h2>💰 Loan Approval & Interest Rate Predictor</h2>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <label>
          Credit Score:
          <input type="number" name="avg_credit_score" value={form.avg_credit_score} onChange={handleChange} required />
        </label>
        <label>
          Annual Income:
          <input type="number" name="avg_annual_income" value={form.avg_annual_income} onChange={handleChange} required />
        </label>
        <label>
          Requested Amount:
          <input type="number" name="avg_requested_amount" value={form.avg_requested_amount} onChange={handleChange} required />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Predicting..." : "Submit"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: "20px", padding: "20px", border: "1px solid #ddd", borderRadius: "8px" }}>
          {result.error ? (
            <p style={{ color: "red" }}>{result.error}</p>
          ) : (
            <>
              <p><strong>Loan Approved:</strong> {result.loan_approved ? "✅ Yes" : "❌ No"}</p>
              <p><strong>Confidence:</strong> {(result.approval_confidence * 100).toFixed(2)}%</p>
              {result.loan_approved && (
                <p><strong>Predicted Interest Rate:</strong> {result.predicted_interest_rate.toFixed(2)}%</p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default App;

