"""
Backend service for the Smart Budget Predictor.

This module wraps the ML prediction engine in sb/scripts/predict_budget.py
and exposes a single JSON-friendly entry point for the Flask API.

Structure:
    sb/scripts/predict_budget.py  → core ML logic + validation
    backend/services/budget_predictor.py  → this file (API adapter)
    backend/services/budget_predictor/app.py  → Flask routes on port 5012
"""

import os
import sys

# Add sb/scripts to the import path so we can reuse the prediction engine
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SB_SCRIPTS = os.path.join(_PROJECT_ROOT, "sb", "scripts")

if _SB_SCRIPTS not in sys.path:
    sys.path.insert(0, _SB_SCRIPTS)

from predict_budget import (  # noqa: E402
    load_model,
    predict_budget_from_dict,
    validate_travel_inputs,
)


def predict_budget(data):
    """
    Run a budget prediction from a JSON-style dictionary.

    Args:
        data: dict with keys:
            destination_country, total_stays, adults, children,
            hotel, reserved_room_type, budget
            Optional: inflation, gdp, tourism_expenditures,
                      customer_type, budget_level

    Returns:
        dict with predicted_spend, risk_level, status,
        overspending_amount, recommendation
        (or {"error": "..."} on failure)
    """
    if not isinstance(data, dict):
        return {"error": "Input must be a JSON object"}

    result = predict_budget_from_dict(data)

    if "error" in result:
        return result

    # API response — only the fields the frontend needs
    return {
        "predicted_spend": result["predicted_spend"],
        "predicted_spend_usd": result.get("predicted_spend_usd"),
        "risk_level": result["risk_level"],
        "status": result["status"],
        "overspending_amount": result["overspending_amount"],
        "recommendation": result["recommendation"],
        "budget": result.get("budget"),
        "budget_ratio": result.get("budget_ratio"),
    }


def warm_up_model():
    """Pre-load the ML model at startup so the first request is fast."""
    try:
        load_model()
        return True
    except Exception:
        return False
