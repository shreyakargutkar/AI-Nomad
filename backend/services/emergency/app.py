from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import re

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"), override=True)
except ImportError:
    pass

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

SOS_KEYWORDS = {
    "lost_passport": ["passport", "lost document", "stolen passport", "missing passport"],
    "missed_train": ["missed train", "missed flight", "missed shinkansen", "late for train", "no train"],
    "medical_emergency": ["doctor", "hospital", "ambulance", "sick", "injured", "allergic", "medical"],
    "pickpocket": ["stolen wallet", "pickpocket", "robbed", "theft"],
    "scam": ["scam", "cheated", "overcharged", "fake"],
}


def load_json(name):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


emergency_profiles = load_json("emergency_profiles.json")
destination_aliases = load_json("emergency_destinations.json")
city_overlays = load_json("emergency_cities.json")

# Sorted longest-first for substring matching
_ALIAS_KEYS = sorted(destination_aliases.keys(), key=len, reverse=True)


def resolve_destination(destination):
    """Resolve free-text destination to (country_key, city_key)."""
    if not destination or not destination.strip():
        return "japan", "tokyo"

    raw = destination.strip().lower()
    parts = [p.strip() for p in re.split(r"[,/|]", raw) if p.strip()]
    tokens = parts + raw.split()
    search_strings = list(dict.fromkeys(parts + [raw] + tokens))

    # Exact match on parts and full string (longest aliases first)
    for s in search_strings:
        if s in destination_aliases:
            loc = destination_aliases[s]
            return loc["country"], loc["city"]

    for alias in _ALIAS_KEYS:
        for s in search_strings:
            if alias in s or s in alias:
                loc = destination_aliases[alias]
                return loc["country"], loc["city"]

    # Country key directly (e.g. "France" already normalized)
    for part in parts:
        if part in emergency_profiles:
            country = part
            city = emergency_profiles[country].get("default_city", country)
            return country, city

    # Unknown — use first supported country mention in string
    for alias in _ALIAS_KEYS:
        if alias in raw:
            loc = destination_aliases[alias]
            return loc["country"], loc["city"]

    return "japan", "tokyo"


def merge_city_profile(country_key, city_key):
    """Merge country profile with city-specific hospital/pharmacy/scams."""
    profile = emergency_profiles.get(country_key, emergency_profiles["japan"])
    country_cities = city_overlays.get(country_key, {})
    city = country_cities.get(city_key) or country_cities.get(
        profile.get("default_city"), {}
    )

    essentials = {**profile.get("essentials", {})}
    if city.get("essentials"):
        for key, val in city["essentials"].items():
            essentials[key] = {**essentials.get(key, {}), **val} if isinstance(val, dict) else val

    scams = list(profile.get("scam_warnings", []))
    extra = city.get("scam_warnings_extra", [])
    # Prepend city-specific scams so they appear first
    city_titles = {s["title"] for s in extra}
    scams = extra + [s for s in scams if s["title"] not in city_titles]

    city_display = city.get("display_name") or city_key.replace("_", " ").title()
    country_display = profile["display_name"]

    return {
        "country_key": country_key,
        "city_key": city_key,
        "display_name": country_display,
        "city_display": city_display,
        "location_label": f"{city_display}, {country_display}",
        "flag": profile.get("flag", ""),
        "emergency_numbers": profile.get("emergency_numbers", {}),
        "embassy": profile.get("embassy_example", {}),
        "essentials": essentials,
        "scam_warnings": scams[:6],
        "translations": profile.get("translations", {}),
        "supported": country_key in emergency_profiles,
    }


def match_sos_workflow(query):
    q = (query or "").lower()
    for workflow_key, keywords in SOS_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return workflow_key
    return None


def build_sos_response(country_key, query):
    profile = emergency_profiles.get(country_key, emergency_profiles["japan"])
    workflows = profile.get("sos_workflows", {})
    workflow_key = match_sos_workflow(query)

    if workflow_key and workflow_key in workflows:
        wf = workflows[workflow_key]
        return {
            "matched": True,
            "workflow_id": workflow_key,
            "title": wf["title"],
            "reassurance": wf.get("reassurance", "Stay calm — help is available."),
            "steps": wf["steps"],
            "contacts": wf.get("contacts", []),
            "local_resources": profile.get("essentials", {}),
        }

    return {
        "matched": False,
        "title": "General assistance",
        "reassurance": "Stay calm. Describe your situation clearly to local authorities or your embassy.",
        "steps": [
            "Share your live location with a trusted contact.",
            f"For emergencies dial: {profile.get('emergency_numbers', {})}",
            "Open translation cards below to communicate with locals.",
            "Visit nearest hospital or pharmacy listed on your Emergency Essentials card.",
        ],
        "contacts": [
            f"Police: {profile.get('emergency_numbers', {}).get('police', 'local')}",
            profile.get("embassy_example", {}).get("label", "Your embassy"),
        ],
        "local_resources": profile.get("essentials", {}),
        "suggestion": "Try: 'lost passport', 'missed train', or 'need doctor'",
    }


@app.route("/api/emergency/detect", methods=["POST"])
def detect_destination():
    data = request.get_json() or {}
    destination = data.get("destination", "")
    country_key, city_key = resolve_destination(destination)
    merged = merge_city_profile(country_key, city_key)

    return jsonify({
        **merged,
        "auto_activated": True,
        "emergency_essentials": {
            "hospital": merged["essentials"].get("hospital", {}),
            "pharmacy": merged["essentials"].get("pharmacy", {}),
            "taxi_apps": merged["essentials"].get("taxi_apps", []),
            "safe_transport": merged["essentials"].get("safe_transport", ""),
        },
    })


@app.route("/api/emergency/destinations", methods=["GET"])
def list_destinations():
    """Return quick-pick destinations grouped by region for the UI."""
    picks = [
        {"label": "Tokyo", "value": "Tokyo, Japan", "flag": "🇯🇵"},
        {"label": "Kyoto", "value": "Kyoto, Japan", "flag": "🇯🇵"},
        {"label": "Paris", "value": "Paris, France", "flag": "🇫🇷"},
        {"label": "Bangkok", "value": "Bangkok, Thailand", "flag": "🇹🇭"},
        {"label": "Phuket", "value": "Phuket, Thailand", "flag": "🇹🇭"},
        {"label": "Istanbul", "value": "Istanbul, Turkey", "flag": "🇹🇷"},
        {"label": "Santorini", "value": "Santorini, Greece", "flag": "🇬🇷"},
        {"label": "Bali", "value": "Bali, Indonesia", "flag": "🇮🇩"},
        {"label": "Barcelona", "value": "Barcelona, Spain", "flag": "🇪🇸"},
        {"label": "Rome", "value": "Rome, Italy", "flag": "🇮🇹"},
        {"label": "Dubai", "value": "Dubai, UAE", "flag": "🇦🇪"},
        {"label": "Singapore", "value": "Singapore", "flag": "🇸🇬"},
        {"label": "London", "value": "London, UK", "flag": "🇬🇧"},
        {"label": "New York", "value": "New York, USA", "flag": "🇺🇸"},
        {"label": "Seoul", "value": "Seoul, South Korea", "flag": "🇰🇷"},
        {"label": "Sydney", "value": "Sydney, Australia", "flag": "🇦🇺"},
        {"label": "Delhi", "value": "Delhi, India", "flag": "🇮🇳"},
        {"label": "Ho Chi Minh", "value": "Ho Chi Minh City, Vietnam", "flag": "🇻🇳"},
    ]
    return jsonify({"destinations": picks, "total_countries": len(emergency_profiles)})


@app.route("/api/emergency/sos", methods=["POST"])
def sos_assistant():
    data = request.get_json() or {}
    destination = data.get("destination", "Japan")
    query = data.get("query", "")
    country_key, _ = resolve_destination(destination)
    if not query.strip():
        return jsonify({"error": "query is required"}), 400
    response = build_sos_response(country_key, query)
    response["country"] = emergency_profiles[country_key]["display_name"]
    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "emergency",
        "countries": len(emergency_profiles),
        "city_overlays": sum(len(v) for v in city_overlays.values()),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5010)
