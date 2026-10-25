from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import config  # noqa: F401 — loads .env before other modules
from cities import CITY_META
from config import GEMINI_API_KEY, GOOGLE_PLACES_API_KEY, GROQ_API_KEY, WEATHER_API_KEY
from engine import generate_recommendations

app = Flask(__name__)
CORS(app)


def _handle_recommendations(data):
    if not data.get("city"):
        return jsonify({"error": "city is required"}), 400
    result = generate_recommendations(data)
    return jsonify(result)


@app.route("/api/recommendations", methods=["POST"])
def recommendations():
    data = request.get_json() or {}
    try:
        return _handle_recommendations(data)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/recommendations/contextual", methods=["POST"])
def contextual_recommendations():
    data = request.get_json() or {}
    try:
        return _handle_recommendations(data)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/recommendations/cities", methods=["GET"])
def list_cities():
    return jsonify(
        {
            "cities": [
                {"key": k, "name": v["display_name"], "country": v["country"]}
                for k, v in CITY_META.items()
            ]
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "recommendations",
            "providers": {
                "weather": "openweathermap" if WEATHER_API_KEY else "timezone_fallback",
                "places": "google+osm" if GOOGLE_PLACES_API_KEY else "openstreetmap",
                "ai": "gemini" if GEMINI_API_KEY else ("groq" if GROQ_API_KEY else "template"),
            },
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5011, debug=False)
