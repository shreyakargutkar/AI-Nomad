"""
Flask API for the Smart Budget Predictor (port 5012).

Endpoint:
    POST /predict-budget  — run ML budget prediction
    GET  /health          — service health check
"""

import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

# Allow importing budget_predictor.py from backend/services/
_SERVICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVICES_DIR not in sys.path:
    sys.path.insert(0, _SERVICES_DIR)

from budget_predictor import predict_budget, warm_up_model  # noqa: E402

app = Flask(__name__)
CORS(app)

# Pre-load model when the service starts
_MODEL_READY = warm_up_model()


@app.route("/predict-budget", methods=["POST"])
def predict_budget_endpoint():
    """
    Accept travel inputs as JSON and return budget prediction.

    Example input:
    {
        "destination_country": "Japan",
        "total_stays": 8,
        "adults": 2,
        "children": 0,
        "hotel": "Resort Hotel",
        "reserved_room_type": "A",
        "budget": 70000
    }

    Returns:
    {
        "predicted_spend": 82000,
        "risk_level": "HIGH",
        "status": "Over Budget",
        "overspending_amount": 12000,
        "recommendation": "Try City Hotel instead of Resort Hotel."
    }
    """
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "No data provided. Send a JSON body."}), 400

        # Reject completely empty string values early
        for key, value in data.items():
            if isinstance(value, str) and not value.strip():
                return jsonify({"error": f"Field '{key}' cannot be empty"}), 400

        result = predict_budget(data)

        if "error" in result:
            # Validation errors vs model errors
            status = 400 if result.get("predicted_spend") is None and "Invalid" in result["error"] or "Missing" in result["error"] or "empty" in result["error"] else 500
            if any(kw in result["error"] for kw in ("Missing", "Invalid", "empty", "must be", "cannot be")):
                status = 400
            elif "Failed to load model" in result["error"]:
                status = 503
            else:
                status = 500
            return jsonify(result), status

        return jsonify(result), 200

    except Exception as exc:
        return jsonify({"error": f"Internal server error: {exc}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check — confirms the service and model are ready."""
    return jsonify(
        {
            "status": "healthy" if _MODEL_READY else "degraded",
            "service": "budget_predictor",
            "model_loaded": _MODEL_READY,
        }
    ), 200 if _MODEL_READY else 503


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5012))
    app.run(host="0.0.0.0", port=port, debug=True)
