"""
Inference & Explainability Module for AI-Nomad Travel Readiness ML Predictor.

Exposes:
    predict_readiness(input_data: dict) -> dict
    load_readiness_model() -> Pipeline
"""

import os
import joblib
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MODEL_PATH = os.path.join(SB_ROOT, "models", "readiness_model.pkl")

# Cached model instance
_MODEL = None

VALID_SEASONS = {"spring", "summer", "autumn", "fall", "winter"}
VALID_WEATHER_RISKS = {"low", "medium", "high"}

REQUIRED_FIELDS = [
    "destination_country",
    "trip_duration_days",
    "season",
    "previous_trips",
    "flight_booked",
    "hotel_booked",
    "passport_valid",
    "visa_required",
    "visa_ready",
    "documents_completed",
    "travel_insurance",
    "emergency_prepared",
    "country_preparation",
    "packing_completed",
    "weather_risk",
]

BINARY_FIELDS = [
    "flight_booked",
    "hotel_booked",
    "passport_valid",
    "visa_required",
    "visa_ready",
    "documents_completed",
    "travel_insurance",
    "emergency_prepared",
    "country_preparation",
    "packing_completed",
]


def load_readiness_model(model_path=MODEL_PATH):
    """Load and cache the trained readiness pipeline."""
    global _MODEL
    if _MODEL is not None and model_path == MODEL_PATH:
        return _MODEL

    if not os.path.isfile(model_path):
        raise FileNotFoundError(
            f"Readiness model file not found at {model_path}. "
            "Run sb/scripts/train_readiness_model.py first."
        )

    _MODEL = joblib.load(model_path)
    return _MODEL


def validate_readiness_input(data):
    """
    Validate input dictionary and return cleaned, standardized dictionary.
    Raises ValueError on invalid or missing fields.
    """
    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")

    cleaned = {}

    # Check for missing required fields
    missing = [f for f in REQUIRED_FIELDS if f not in data or data[f] is None or data[f] == ""]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    # 1. destination_country
    country = str(data["destination_country"]).strip()
    if not country:
        raise ValueError("Field 'destination_country' cannot be empty.")
    cleaned["destination_country"] = country.title()

    # 2. season
    season_raw = str(data["season"]).strip().lower()
    if season_raw == "fall":
        season_raw = "autumn"
    if season_raw not in VALID_SEASONS:
        raise ValueError(f"Invalid season '{data['season']}'. Must be one of: Spring, Summer, Autumn, Winter.")
    cleaned["season"] = season_raw.title()

    # 3. weather_risk
    weather_raw = str(data["weather_risk"]).strip().upper()
    if weather_raw.lower() not in VALID_WEATHER_RISKS:
        raise ValueError(f"Invalid weather_risk '{data['weather_risk']}'. Must be LOW, MEDIUM, or HIGH.")
    cleaned["weather_risk"] = weather_raw

    # 4. trip_duration_days
    try:
        duration = int(data["trip_duration_days"])
        if duration <= 0:
            raise ValueError()
        cleaned["trip_duration_days"] = duration
    except (ValueError, TypeError):
        raise ValueError("Field 'trip_duration_days' must be a positive integer >= 1.")

    # 5. previous_trips
    try:
        trips = int(data["previous_trips"])
        if trips < 0:
            raise ValueError()
        cleaned["previous_trips"] = trips
    except (ValueError, TypeError):
        raise ValueError("Field 'previous_trips' must be an integer >= 0.")

    # 6. Binary fields
    for field in BINARY_FIELDS:
        val = data[field]
        if isinstance(val, bool):
            cleaned[field] = 1 if val else 0
        elif isinstance(val, (int, float)) and val in (0, 1):
            cleaned[field] = int(val)
        elif str(val).strip() in ("0", "1"):
            cleaned[field] = int(val)
        else:
            raise ValueError(f"Field '{field}' must be 0 or 1 (or True/False). Got: {val}")

    # Logical consistency: if visa_required == 0, visa_ready defaults to 1
    if cleaned["visa_required"] == 0:
        cleaned["visa_ready"] = 1

    return cleaned


def explain_prediction(data, score):
    """
    Placement-ready Explainability Engine:
    Identifies top positive drivers and critical bottlenecks dragging down readiness,
    ranked by feature importance and domain impact.
    """
    strengths = []
    bottlenecks = []

    # Passport
    if data["passport_valid"] == 1:
        strengths.append("Passport is verified valid")
    else:
        bottlenecks.append("CRITICAL: Passport is invalid or missing (<6 months validity)")

    # Visa
    if data["visa_required"] == 1:
        if data["visa_ready"] == 1:
            strengths.append("Visa is approved and ready")
        else:
            bottlenecks.append("CRITICAL: Mandatory travel visa is not yet obtained")
    else:
        strengths.append("Destination is visa-exempt")

    # Bookings
    if data["flight_booked"] == 1:
        strengths.append("Flight is booked and confirmed")
    else:
        bottlenecks.append("Flight is not yet booked")

    if data["hotel_booked"] == 1:
        strengths.append("Accommodations are confirmed")
    else:
        bottlenecks.append("Hotel / lodging is not yet booked")

    # Packing & Weather
    if data["packing_completed"] == 1:
        if data["weather_risk"] == "HIGH":
            strengths.append("Packed appropriately for high weather risk conditions")
        else:
            strengths.append("Packing checklist is completed")
    else:
        if data["weather_risk"] == "HIGH":
            bottlenecks.append("Packing is incomplete despite HIGH weather risk")
        else:
            bottlenecks.append("Packing is incomplete")

    # Safety & Insurance
    if data["travel_insurance"] == 1:
        strengths.append("Travel insurance policy active")
    else:
        if data["trip_duration_days"] >= 21:
            bottlenecks.append("Extended stay (>3 weeks) lacks travel medical insurance")
        else:
            bottlenecks.append("Travel insurance is not purchased")

    # Emergency Preparation
    if data["emergency_prepared"] == 1:
        strengths.append("Emergency contacts and offline maps saved")
    else:
        bottlenecks.append("Emergency numbers and local clinics not documented")

    # Country preparation
    if data["country_preparation"] == 1:
        strengths.append("Country prep (connectivity/transit card) completed")
    else:
        bottlenecks.append("Country prep (eSIM, transit passes, currency) incomplete")

    # Experience
    if data["previous_trips"] >= 8:
        strengths.append(f"Experienced traveler ({data['previous_trips']} past trips)")

    # Combine into top 3-5 factors, prioritizing bottlenecks if score is low, or strengths if high
    top_factors = []
    if score < 50:
        # Prioritize bottlenecks
        top_factors = bottlenecks[:3] + strengths[:2]
    elif score < 80:
        top_factors = bottlenecks[:2] + strengths[:2]
    else:
        top_factors = strengths[:3] + bottlenecks[:1]

    # Clean up empty
    top_factors = [f for f in top_factors if f]

    return top_factors, strengths, bottlenecks


def predict_readiness(input_data, model_path=MODEL_PATH):
    """
    Primary API entry point for ML Travel Readiness Prediction.

    Args:
        input_data (dict): Dictionary containing traveler features.
        model_path (str, optional): Custom model file path.

    Returns:
        dict:
            preparedness_score (int): Clamped score 0 to 100.
            top_factors (list): 3-4 key explanatory factors.
            readiness_band (str): Critical Risk / Moderate / High / Departure Ready.
    """
    # 1. Validate inputs
    cleaned_data = validate_readiness_input(input_data)

    # 2. Load model
    model = load_readiness_model(model_path)

    # 3. Convert to DataFrame matching training schema
    df_input = pd.DataFrame([cleaned_data])

    # 4. Predict
    raw_pred = model.predict(df_input)[0]

    # 5. Clamp final score to 0 - 100
    clamped_score = int(round(float(np.clip(raw_pred, 0.0, 100.0))))

    # 6. Explainability factors
    top_factors, strengths, bottlenecks = explain_prediction(cleaned_data, clamped_score)

    # Readiness band categorization
    if clamped_score < 40:
        band = "Critical Risk"
    elif clamped_score < 70:
        band = "Moderate Readiness"
    elif clamped_score < 90:
        band = "High Readiness"
    else:
        band = "Departure Ready"

    return {
        "preparedness_score": clamped_score,
        "readiness_band": band,
        "top_factors": top_factors,
        "doing_well": strengths,
        "needs_attention": bottlenecks,
    }


if __name__ == "__main__":
    sample_input = {
        "destination_country": "Japan",
        "trip_duration_days": 8,
        "season": "Spring",
        "previous_trips": 4,
        "flight_booked": 1,
        "hotel_booked": 1,
        "passport_valid": 1,
        "visa_required": 1,
        "visa_ready": 1,
        "documents_completed": 1,
        "travel_insurance": 1,
        "emergency_prepared": 1,
        "country_preparation": 1,
        "packing_completed": 0,
        "weather_risk": "LOW",
    }
    result = predict_readiness(sample_input)
    print("Sample Inference Result:")
    import json
    print(json.dumps(result, indent=2))
