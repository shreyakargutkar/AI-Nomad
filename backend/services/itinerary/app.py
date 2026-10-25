import logging
import os

# Bootstrap .env before modules that bind GROQ_API_KEY / Groq clients at import time
import config  # noqa: F401

from flask import Flask, jsonify, request
from flask_cors import CORS

from groq_planner import generate_daily_plan, _trip_day_count
from live_research import build_verified_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


def _ensure_complete_itinerary(
    itinerary: dict,
    destination: str,
    start_date: str,
    end_date: str,
    departure_location: str = "",
) -> dict:
    """Guarantee non-empty sections for frontend."""
    flights = itinerary.get("flights") or []
    hotels = itinerary.get("hotels") or []
    days = itinerary.get("days") or []
    visa = itinerary.get("visa_details") or {}

    if len(flights) < 2:
        from live_research import _finalize_flight

        flights = (flights + [
            _finalize_flight(
                {"airline": "Major carrier", "booking_platform": "Skyscanner"},
                departure_location or "Origin",
                destination,
                start_date,
                end_date,
                len(flights),
                [],
                [],
                [],
            ),
        ])[:2]

    need = _trip_day_count(start_date, end_date)
    if len(days) < need:
        from groq_planner import _fallback_days_from_context

        ctx = itinerary.get("destination_context") or {}
        days = _fallback_days_from_context(destination, need, ctx, hotels) or days

    if not visa:
        visa = {
            "required": True,
            "processing_time": "Verify embassy",
            "cost": "Verify official fee",
            "documents_needed": ["Passport"],
            "travel_notes": "Confirm visa rules before booking flights",
        }

    visa.setdefault("travel_notes", visa.pop("notes", "") or "")
    if visa.get("required") is None:
        visa["required"] = True

    return {
        "days": days,
        "flights": flights,
        "hotels": hotels[:5],
        "visa_details": visa,
    }


@app.route("/api/itinerary", methods=["POST"])
def generate_itinerary():
    data = request.get_json() or {}
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    location = data.get("location")
    departure_location = data.get("departure_location")
    budget = data.get("budget")
    passport_country = data.get("passport_country") or data.get("nationality")

    if not start_date or not end_date or not location or not departure_location or not budget:
        return jsonify({"error": "Start date, end date, location, departure location, and budget are required"}), 400

    try:
        logger.info(
            "[itinerary] Tavily pipeline: %s (%s) → %s",
            departure_location,
            passport_country or "India (default)",
            location,
        )

        verified = build_verified_context(
            departure_location=departure_location,
            destination=location,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            passport_country=passport_country,
        )

        days = generate_daily_plan(
            destination=location,
            departure_location=departure_location,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            verified_context=verified,
        )

        merged = {
            "days": days,
            "flights": verified.get("flights") or [],
            "hotels": verified.get("hotels") or [],
            "visa_details": verified.get("visa_details") or {},
            "destination_context": verified.get("destination_context") or {},
        }

        itinerary = _ensure_complete_itinerary(
            merged, location, start_date, end_date, departure_location
        )

        print("Flights found:", len(itinerary["flights"]))
        print("Hotels found:", len(itinerary["hotels"]))
        print("Visa:", itinerary["visa_details"])

        logger.info(
            "[itinerary] Final: days=%d flights=%d hotels=%d visa=%s",
            len(itinerary["days"]),
            len(itinerary["flights"]),
            len(itinerary["hotels"]),
            itinerary["visa_details"].get("required"),
        )

        return jsonify(itinerary)

    except Exception as e:
        logger.exception("[itinerary] Generation failed")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5005)
