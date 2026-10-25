"""
Smart Budget Predictor — CLI prediction engine for AI-Nomad.

Loads the trained ML model from sb/models/budget_model.pkl, accepts travel
inputs, runs a cost prediction, and returns risk level + recommendations.

Usage:
    python sb/scripts/predict_budget.py
    python sb/scripts/predict_budget.py --country Japan --days 8 --budget 70000
"""

import argparse
import os
import sys

import joblib
import pandas as pd

# ---------------------------------------------------------------------------
# Paths — model lives next to this script under sb/models/
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SB_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(SB_ROOT, "models", "budget_model.pkl")

# USD → INR conversion used when comparing against user budget (INR)
EXCHANGE_RATE_INR = 83

# Cached model — loaded once, reused for every prediction
_MODEL = None


def load_model():
    """Load and cache the trained budget model."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Run sb/scripts/train_model.py first."
        )

    _MODEL = joblib.load(MODEL_PATH)
    return _MODEL


def get_country_economic_data(country_name, inflation=None, gdp=None, tourism_expenditures=None):
    """
    Return economic indicators for a destination country.

    Caller may override inflation, gdp, or tourism_expenditures; otherwise
    we use built-in defaults (or generic fallbacks for unknown countries).
    """
    country_data = {
        "JAPAN": {
            "gdp": 4.9e12,
            "inflation": 2.5,
            "tourism_expenditures": 4.5e10,
            "avg_tourist_spending": 2000,
            "tourism_revenue": 3.5e10,
        },
        "USA": {
            "gdp": 2.5e13,
            "inflation": 3.2,
            "tourism_expenditures": 2.5e11,
            "avg_tourist_spending": 2500,
            "tourism_revenue": 2.8e11,
        },
        "UNITED KINGDOM": {
            "gdp": 3.1e12,
            "inflation": 4.0,
            "tourism_expenditures": 5.2e10,
            "avg_tourist_spending": 1800,
            "tourism_revenue": 4.8e10,
        },
        "FRANCE": {
            "gdp": 2.9e12,
            "inflation": 2.8,
            "tourism_expenditures": 6.0e10,
            "avg_tourist_spending": 1600,
            "tourism_revenue": 5.5e10,
        },
        "GERMANY": {
            "gdp": 4.1e12,
            "inflation": 3.5,
            "tourism_expenditures": 4.8e10,
            "avg_tourist_spending": 1700,
            "tourism_revenue": 4.5e10,
        },
        "INDIA": {
            "gdp": 3.4e12,
            "inflation": 5.5,
            "tourism_expenditures": 3.0e10,
            "avg_tourist_spending": 800,
            "tourism_revenue": 2.8e10,
        },
        "ITALY": {
            "gdp": 2.1e12,
            "inflation": 3.0,
            "tourism_expenditures": 4.2e10,
            "avg_tourist_spending": 1500,
            "tourism_revenue": 4.0e10,
        },
        "SPAIN": {
            "gdp": 1.5e12,
            "inflation": 3.8,
            "tourism_expenditures": 5.5e10,
            "avg_tourist_spending": 1400,
            "tourism_revenue": 5.2e10,
        },
        "AUSTRALIA": {
            "gdp": 1.7e12,
            "inflation": 4.2,
            "tourism_expenditures": 3.8e10,
            "avg_tourist_spending": 2200,
            "tourism_revenue": 3.5e10,
        },
        "CANADA": {
            "gdp": 2.1e12,
            "inflation": 3.0,
            "tourism_expenditures": 3.5e10,
            "avg_tourist_spending": 1900,
            "tourism_revenue": 3.2e10,
        },
    }

    default_data = {
        "gdp": 1.0e12,
        "inflation": 3.0,
        "tourism_expenditures": 2.0e10,
        "avg_tourist_spending": 1500,
        "tourism_revenue": 2.0e10,
    }

    base = country_data.get(country_name.upper(), default_data).copy()

    if inflation is not None:
        base["inflation"] = float(inflation)
    if gdp is not None:
        base["gdp"] = float(gdp)
    if tourism_expenditures is not None:
        base["tourism_expenditures"] = float(tourism_expenditures)

    return base


def generate_recommendation(risk_level, hotel, total_stays, room_type, budget_ratio):
    """Return a plain-language recommendation based on risk level."""
    if risk_level == "HIGH":
        tips = []
        if hotel == "Resort Hotel":
            tips.append("Try City Hotel instead of Resort Hotel")
        if total_stays > 7:
            tips.append("Reduce stay duration by 1–2 days")
        if room_type in ("A", "B"):
            tips.append("Choose a cheaper room type (C or D)")
        if budget_ratio > 1.5:
            tips.append("Consider a lower-cost destination")
        if not tips:
            tips.append("Review your budget or travel in off-season")
        return ". ".join(tips) + "."

    if risk_level == "MEDIUM":
        return "Monitor transport and dining spending — you are close to your budget limit."

    return "Your budget looks safe! You have room for premium activities or dining."


def validate_travel_inputs(data):
    """
    Validate a travel-input dictionary.

    Returns (cleaned_data, error_message). error_message is None when valid.
    """
    if not data:
        return None, "No input data provided"

    required = [
        "destination_country",
        "total_stays",
        "adults",
        "children",
        "hotel",
        "reserved_room_type",
        "budget",
    ]

    missing = []
    for field in required:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)

    if missing:
        return None, f"Missing or empty fields: {', '.join(missing)}"

    try:
        cleaned = {
            "destination_country": str(data["destination_country"]).strip(),
            "total_stays": int(data["total_stays"]),
            "adults": int(data["adults"]),
            "children": int(data["children"]),
            "hotel": str(data["hotel"]).strip(),
            "reserved_room_type": str(data["reserved_room_type"]).strip(),
            "budget": float(data["budget"]),
            "customer_type": str(data.get("customer_type") or "Transient"),
            "budget_level": str(data.get("budget_level") or "Mid-range"),
        }
    except (TypeError, ValueError) as exc:
        return None, f"Invalid input value: {exc}"

    if cleaned["total_stays"] <= 0:
        return None, "total_stays must be greater than 0"
    if cleaned["adults"] <= 0:
        return None, "adults must be greater than 0"
    if cleaned["children"] < 0:
        return None, "children cannot be negative"
    if cleaned["budget"] <= 0:
        return None, "budget must be greater than 0"

    # Optional economic overrides
    for key in ("inflation", "gdp", "tourism_expenditures"):
        if data.get(key) is not None:
            try:
                cleaned[key] = float(data[key])
            except (TypeError, ValueError):
                return None, f"Invalid value for {key}"

    return cleaned, None


def predict_budget(
    destination_country,
    total_stays,
    adults,
    children,
    hotel,
    reserved_room_type,
    budget,
    customer_type="Transient",
    budget_level="Mid-range",
    inflation=None,
    gdp=None,
    tourism_expenditures=None,
):
    """
    Predict travel spend from individual parameters.

    Returns a dict with predicted_spend, risk_level, status,
    overspending_amount, and recommendation.
    """
    return predict_budget_from_dict(
        {
            "destination_country": destination_country,
            "total_stays": total_stays,
            "adults": adults,
            "children": children,
            "hotel": hotel,
            "reserved_room_type": reserved_room_type,
            "budget": budget,
            "customer_type": customer_type,
            "budget_level": budget_level,
            "inflation": inflation,
            "gdp": gdp,
            "tourism_expenditures": tourism_expenditures,
        }
    )


def predict_budget_from_dict(data):
    """
    Accept a JSON-style dict and return prediction results.

    This is the function reused by the Flask API service.
    """
    cleaned, error = validate_travel_inputs(data)
    if error:
        return {"error": error}

    try:
        model = load_model()
    except Exception as exc:
        return {
            "error": f"Failed to load model: {exc}",
            "predicted_spend": None,
            "risk_level": None,
            "status": None,
            "overspending_amount": None,
            "recommendation": None,
        }

    economic = get_country_economic_data(
        cleaned["destination_country"],
        inflation=cleaned.get("inflation"),
        gdp=cleaned.get("gdp"),
        tourism_expenditures=cleaned.get("tourism_expenditures"),
    )

    input_df = pd.DataFrame(
        {
            "hotel": [cleaned["hotel"]],
            "country": [cleaned["destination_country"].upper()],
            "total_stays": [cleaned["total_stays"]],
            "adults": [cleaned["adults"]],
            "children": [cleaned["children"]],
            "customer_type": [cleaned["customer_type"]],
            "reserved_room_type": [cleaned["reserved_room_type"]],
            "budget_level": [cleaned["budget_level"]],
            "tourism_expenditures": [economic["tourism_expenditures"]],
            "gdp": [economic["gdp"]],
            "inflation": [economic["inflation"]],
            "avg_tourist_spending": [economic["avg_tourist_spending"]],
            "tourism_revenue": [economic["tourism_revenue"]],
        }
    )

    try:
        prediction_usd = float(model.predict(input_df)[0])
    except Exception as exc:
        return {
            "error": f"Prediction failed: {exc}",
            "predicted_spend": None,
            "risk_level": None,
            "status": None,
            "overspending_amount": None,
            "recommendation": None,
        }

    budget = cleaned["budget"]
    predicted_spend_inr = prediction_usd * EXCHANGE_RATE_INR
    budget_ratio = predicted_spend_inr / budget if budget > 0 else 0

    # Risk thresholds: LOW ≤ 80%, MEDIUM 80–100%, HIGH > 100%
    if budget_ratio <= 0.8:
        risk_level = "LOW"
        status = "Under Budget"
    elif budget_ratio <= 1.0:
        risk_level = "MEDIUM"
        status = "Near Budget"
    else:
        risk_level = "HIGH"
        status = "Over Budget"

    overspending_amount = max(0.0, predicted_spend_inr - budget)
    recommendation = generate_recommendation(
        risk_level,
        cleaned["hotel"],
        cleaned["total_stays"],
        cleaned["reserved_room_type"],
        budget_ratio,
    )

    return {
        "predicted_spend": round(predicted_spend_inr, 2),
        "predicted_spend_usd": round(prediction_usd, 2),
        "risk_level": risk_level,
        "status": status,
        "overspending_amount": round(overspending_amount, 2),
        "budget_ratio": round(budget_ratio, 2),
        "recommendation": recommendation,
        "budget": round(budget, 2),
    }


def print_budget_analysis(result):
    """Print a formatted trip budget analysis to the terminal."""
    if result.get("error"):
        print(f"\nError: {result['error']}\n")
        return

    budget = result.get("budget", 0)
    predicted = result["predicted_spend"]
    overspend = result["overspending_amount"]

    print("\n## Trip Budget Analysis\n")
    print(f"Budget: ₹{budget:,.0f}")
    print(f"Predicted Spend: ₹{predicted:,.0f}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Status: {result['status']}")
    if overspend > 0:
        print(f"Overspending Amount: ₹{overspend:,.0f}")
    print("Recommendation:")
    print(result["recommendation"])
    print()


def _parse_args():
    parser = argparse.ArgumentParser(description="AI-Nomad Smart Budget Predictor")
    parser.add_argument("--country", default="Japan", help="Destination country")
    parser.add_argument("--days", type=int, default=8, help="Trip duration (days)")
    parser.add_argument("--adults", type=int, default=2)
    parser.add_argument("--children", type=int, default=0)
    parser.add_argument("--hotel", default="Resort Hotel", choices=["Resort Hotel", "City Hotel"])
    parser.add_argument("--room", default="A", dest="room_type", help="Room type A–E")
    parser.add_argument("--budget", type=float, default=70000, help="Budget in INR")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    output = predict_budget(
        destination_country=args.country,
        total_stays=args.days,
        adults=args.adults,
        children=args.children,
        hotel=args.hotel,
        reserved_room_type=args.room_type,
        budget=args.budget,
    )

    print_budget_analysis(output)

    if output.get("error"):
        sys.exit(1)
