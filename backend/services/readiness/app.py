from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow importing predict_readiness from sb/scripts/
_SB_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "sb", "scripts"))
if _SB_SCRIPTS not in sys.path:
    sys.path.insert(0, _SB_SCRIPTS)

try:
    from predict_readiness import predict_readiness
except Exception as _import_err:
    logger.warning("Could not import predict_readiness: %s", _import_err)
    predict_readiness = None

load_dotenv = None
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"), override=True)
except ImportError:
    pass

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

DESTINATION_MAP = {
    "tokyo": ("japan", "tokyo"),
    "kyoto": ("japan", "tokyo"),
    "osaka": ("japan", "tokyo"),
    "japan": ("japan", "tokyo"),
    "paris": ("france", "paris"),
    "france": ("france", "paris"),
    "lyon": ("france", "paris"),
    "santorini": ("greece", "santorini"),
    "athens": ("greece", "santorini"),
    "greece": ("greece", "santorini"),
    "bali": ("indonesia", "bali"),
    "ubud": ("indonesia", "bali"),
    "indonesia": ("indonesia", "bali"),
    "bangkok": ("thailand", "bangkok"),
    "thailand": ("thailand", "bangkok"),
    "phuket": ("thailand", "bangkok"),
    "chiang mai": ("thailand", "bangkok"),
}

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


countries_data = load_json("countries.json")
attractions_data = load_json("attractions.json")
packing_data = load_json("packing.json")
weather_data = load_json("weather.json")


def get_season(month):
    month_num = int(month) if isinstance(month, str) else month
    if month_num in (12, 1, 2):
        return "winter"
    if month_num in (3, 4, 5):
        return "spring"
    if month_num in (6, 7, 8):
        return "summer"
    return "autumn"


def resolve_destination(destination):
    if not destination:
        return {"country": "", "city": "", "display": ""}
    raw = destination.strip().lower()
    parts = [p.strip() for p in re.split(r"[,/|]", raw) if p.strip()]
    primary = parts[0] if parts else raw
    country, city = DESTINATION_MAP.get(primary, (primary, primary))
    if country not in countries_data and primary in countries_data:
        country = primary
        city = primary
    display = countries_data.get(country, {}).get("display_name", destination.strip())
    return {"country": country, "city": city, "display": display, "raw": destination.strip()}


def parse_duration_days(start_date, end_date):
    if not start_date or not end_date:
        return 5
    try:
        start = datetime.strptime(start_date[:10], "%Y-%m-%d")
        end = datetime.strptime(end_date[:10], "%Y-%m-%d")
        days = (end - start).days + 1
        return max(1, min(days, 90))
    except ValueError:
        return 5


def extract_month(start_date):
    if start_date and len(start_date) >= 7:
        try:
            return int(start_date.split("-")[1])
        except ValueError:
            pass
    return 5


def extract_activities(itinerary_text):
    if not itinerary_text:
        return []
    text = itinerary_text.replace("\n", ",").replace(";", ",")
    items = []
    for part in re.split(r",|•|\||\d+\.\s*", text):
        cleaned = part.strip()
        if cleaned and len(cleaned) > 2:
            items.append(cleaned)
    return items


def detect_activity_types(activities):
    types = set()
    keywords = packing_data.get("activity_keywords", {})
    blob = " ".join(activities).lower()
    for activity_type, words in keywords.items():
        if any(w in blob for w in words):
            types.add(activity_type)
    return types


def get_weather_context(city_key, month):
    month_name = MONTH_NAMES[month - 1] if 1 <= month <= 12 else "May"
    city_weather = weather_data.get(city_key, {})
    temps = city_weather.get("avg_temp_by_month", {}).get(month_name, {})
    precip = city_weather.get("precipitation_chance", {}).get(month_name, 40)
    climate = city_weather.get("climate", "temperate")
    season = get_season(month)
    return {
        "month": month_name,
        "season": season,
        "avg_temp": temps.get("avg"),
        "min_temp": temps.get("min"),
        "max_temp": temps.get("max"),
        "precipitation_chance": precip,
        "climate": climate,
        "summary": _weather_summary(temps, precip, season),
    }


def _weather_summary(temps, precip, season):
    avg = temps.get("avg")
    if avg is None:
        return f"Expect typical {season} conditions — pack layers."
    rain_note = " Rain likely — bring an umbrella." if precip and precip > 50 else ""
    return f"Average {avg}°C during your trip.{rain_note}"


def get_packing_recommendations(dest_info, duration_days, activities, month):
    country = dest_info["country"]
    city = dest_info["city"]
    season = get_season(month)
    weather_ctx = get_weather_context(city, month)
    climate = weather_ctx.get("climate") or "temperate"

    season_packing = packing_data.get(season, packing_data.get("temperate", {}))
    if climate == "tropical" and season in ("summer", "spring"):
        base = {**packing_data.get("tropical", {}), **season_packing}
    elif climate == "cold" or (weather_ctx.get("avg_temp") is not None and weather_ctx["avg_temp"] < 8):
        base = {**packing_data.get("cold", {}), **season_packing}
    else:
        base = season_packing

    essentials = list(dict.fromkeys(base.get("essentials", [])))
    by_activity = []
    activity_types = detect_activity_types(activities)
    activity_items = base.get("activities", {})
    for atype in activity_types:
        by_activity.extend(activity_items.get(atype, []))
    by_activity = list(dict.fromkeys(by_activity))

    duration_extras = []
    if duration_days >= 10:
        duration_extras.append("Laundry detergent sheets or travel wash")
        duration_extras.append("Extra underwear/socks for long trip")
    if duration_days <= 3:
        duration_extras.append("Carry-on sized toiletries (100ml liquids)")

    tips = list(packing_data.get("destination_tips", {}).get(country, []))
    country_info = countries_data.get(country, {})
    if country_info:
        tips.extend(country_info.get("cultural_notes", [])[:2])

    return {
        "essentials": essentials,
        "by_activity": by_activity,
        "duration_extras": duration_extras,
        "universal": packing_data.get("universal", {}),
        "contextual_tips": list(dict.fromkeys(tips))[:5],
        "weather": weather_ctx,
        "checklist_total": len(essentials) + len(by_activity) + len(duration_extras),
    }


def normalize_prebooked(prebooked_items):
    if isinstance(prebooked_items, str):
        prebooked_items = [line.strip() for line in prebooked_items.split("\n") if line.strip()]
    return set(item.lower().strip() for item in (prebooked_items or []) if item)


def matches_prebooked(name, key, prebooked_set):
    name_l = name.lower()
    key_l = key.replace("_", " ").lower()
    key_words = set(key_l.split())
    for pre in prebooked_set:
        if pre in name_l or name_l in pre:
            return True
        if any(w in pre for w in key_words if len(w) > 3):
            return True
        if key_l in pre:
            return True
    return False


def get_booking_intelligence(itinerary_activities, dest_info, prebooked_items):
    city_key = dest_info["city"]
    prebooked_set = normalize_prebooked(prebooked_items)
    known = attractions_data.get(city_key, {})

    booked = []
    pending = []
    guidance = []
    matched_keys = set()

    def add_from_attraction(key, info, activity_label):
        matched_keys.add(key)
        entry_base = {
            "name": info["name"],
            "booking_required": info.get("booking_required", False),
            "best_time": info.get("best_time", "Flexible"),
            "optimal_window": info.get("optimal_booking_window", "No advance booking needed"),
            "avoid_times": info.get("avoid_times", "None"),
            "crowd_pattern": info.get("crowd_pattern", ""),
            "duration": info.get("duration", ""),
            "guidance": info.get("guidance", info.get("note", "")),
            "matched_from": activity_label,
        }
        is_prebooked = matches_prebooked(info["name"], key, prebooked_set)

        if is_prebooked:
            booked.append({**entry_base, "status": "prebooked"})
        elif info.get("booking_required"):
            pending.append({**entry_base, "status": "pending"})
            guidance.append({**entry_base, "priority": "high"})
        else:
            booked.append({**entry_base, "status": "no_booking_needed"})
            guidance.append({**entry_base, "priority": "low"})

    for activity in itinerary_activities:
        activity_norm = re.sub(r"[^a-z0-9 ]", " ", activity.lower()).strip()
        activity_compact = activity_norm.replace(" ", "")
        activity_words = set(activity_norm.split())
        found = False

        for key, info in known.items():
            key_norm = key.replace("_", " ").lower()
            key_compact = key.replace("_", "").lower()
            key_words = set(key_norm.split())
            name_words = set(re.findall(r"[a-z0-9]+", info["name"].lower()))
            if (
                key_norm in activity_norm
                or key_compact in activity_compact
                or activity_compact in key_compact
                or activity_norm in info["name"].lower()
                or (activity_words & key_words)
                or (activity_words & name_words)
            ):
                add_from_attraction(key, info, activity)
                found = True
                break

        if not found:
            is_prebooked = any(activity_norm in pre or pre in activity_norm for pre in prebooked_set)
            generic = {
                "name": activity.strip().title(),
                "booking_required": True,
                "best_time": "Check official website",
                "optimal_window": "Research 1–2 weeks before travel",
                "avoid_times": "Peak weekends if popular attraction",
                "guidance": "Not in our database — verify booking requirements on the official site.",
                "matched_from": activity,
            }
            if is_prebooked:
                booked.append({**generic, "status": "prebooked"})
            else:
                pending.append({**generic, "status": "unknown"})
                guidance.append({**generic, "priority": "medium"})

    return {"booked": booked, "pending": pending, "guidance": guidance}


def get_country_requirements(dest_info):
    country = dest_info["country"]
    data = countries_data.get(country, {})
    if not data:
        return {
            "display_name": dest_info.get("display", dest_info["raw"]),
            "found": False,
            "message": "Country profile not yet in database — general travel prep still applies.",
        }
    return {**data, "found": True}


def score_documents(country_req, user_ack_docs=False):
    if not country_req.get("found", True):
        return 50
    visa = country_req.get("visa", {})
    checklist = country_req.get("document_checklist", [])
    if user_ack_docs:
        return 100
    if visa.get("required"):
        return 35
    base = 70
    if checklist:
        base += 15
    return min(95, base)


def score_country_requirements(country_req, prebooked_set):
    if not country_req.get("found", True):
        return 40
    score = 50
    transport = country_req.get("transportation", [])
    prebooks = country_req.get("prebooking_recommendations", [])
    score += min(20, len(transport) * 5)
    unbooked_high = 0
    for rec in prebooks:
        name = rec.get("name", "").lower()
        if rec.get("priority") == "high" and not any(name in p for p in prebooked_set):
            unbooked_high += 1
    score += max(0, 30 - unbooked_high * 15)
    return min(100, score)


def score_tickets(booking):
    booked = booking.get("booked", [])
    pending = booking.get("pending", [])
    total = len(booked) + len(pending)
    if total == 0:
        return 75
    needs_booking = [b for b in booked if b.get("status") != "no_booking_needed"]
    pending_required = [p for p in pending if p.get("booking_required", True)]
    done = len([b for b in booked if b.get("status") == "prebooked"])
    no_book = len([b for b in booked if b.get("status") == "no_booking_needed"])
    denominator = len(pending_required) + done + max(1, len(pending))
    ratio = (done + no_book * 0.5) / max(denominator, 1)
    return min(100, int(ratio * 100))


def score_packing(packing):
    total = packing.get("checklist_total", 10)
    estimated_packed = max(0, int(total * 0.35))
    return min(85, int((estimated_packed / max(total, 1)) * 100) + 25)


def calculate_readiness(breakdown):
    weights = {
        "packing": 0.2,
        "tickets": 0.35,
        "documents": 0.25,
        "country_requirements": 0.2,
    }
    total = sum(breakdown[k] * weights[k] for k in weights)
    return round(total)


def get_priority_actions(dest_info, country_req, booking, breakdown, prebooked_set):
    actions = []

    for item in booking.get("pending", []):
        if item.get("booking_required"):
            window = item.get("optimal_window", "soon")
            actions.append({
                "text": f"Book {item['name']} — {window}",
                "priority": 1,
                "category": "tickets",
            })

    for rec in country_req.get("prebooking_recommendations", []):
        name = rec.get("name", "").lower()
        if rec.get("priority") == "high" and not any(name in p for p in prebooked_set):
            actions.append({
                "text": f"Book {rec['name']} ({rec.get('days_ahead', 'advance')} ahead)",
                "priority": 2,
                "category": "country",
            })

    if breakdown.get("documents", 100) < 70:
        visa = country_req.get("visa", {})
        if visa.get("required"):
            actions.append({
                "text": "Complete visa application and gather required documents",
                "priority": 1,
                "category": "documents",
            })
        actions.append({
            "text": "Verify passport validity (6+ months beyond return date)",
            "priority": 2,
            "category": "documents",
        })

    if breakdown.get("packing", 100) < 60:
        actions.append({
            "text": "Review packing checklist for weather and planned activities",
            "priority": 3,
            "category": "packing",
        })

    conn = country_req.get("connectivity", {})
    if conn:
        actions.append({
            "text": f"Arrange connectivity: {conn.get('recommendation', 'SIM or eSIM')}",
            "priority": 4,
            "category": "logistics",
        })

    actions.extend([
        {"text": "Download offline maps for your destination cities", "priority": 5, "category": "logistics"},
        {"text": "Purchase or confirm travel insurance coverage", "priority": 5, "category": "documents"},
    ])

    seen = set()
    unique = []
    for a in sorted(actions, key=lambda x: x["priority"]):
        if a["text"] not in seen:
            seen.add(a["text"])
            unique.append(a)
    return unique[:6]


def derive_risk_level(score):
    """
    Transparent risk level classification based on 0-100 preparedness score:
      80-100: LOW (Departure Ready / Well Prepared)
      60-79:  MEDIUM (Moderate Readiness, minor items pending)
      40-59:  HIGH (Significant preparation gaps)
      0-39:   CRITICAL (Severe travel blockers like missing passport/visa)
    """
    if score >= 80:
        return "LOW"
    if score >= 60:
        return "MEDIUM"
    if score >= 40:
        return "HIGH"
    return "CRITICAL"


def map_to_ml_features(data, dest_info, duration_days, season, packing, country_req, booking, prebooked_set, breakdown):
    """
    Map existing user input and parsed context into the 15 features expected by the ML model.
    Reuses existing data without requiring new user inputs.
    """
    # 1. Destination Country
    country = dest_info.get("display") or dest_info.get("country") or "Japan"
    country_clean = country.split(",")[0].strip().title()
    if not country_clean or country_clean.lower() in ("tokyo", "kyoto", "osaka"):
        country_clean = "Japan"
    elif country_clean.lower() in ("paris", "lyon"):
        country_clean = "France"
    elif country_clean.lower() in ("santorini", "athens"):
        country_clean = "Greece"
    elif country_clean.lower() in ("bangkok", "phuket", "chiang mai"):
        country_clean = "Thailand"
    elif country_clean.lower() in ("bali", "ubud"):
        country_clean = "Indonesia"

    # 2. Trip Duration
    trip_duration_days = max(1, duration_days)

    # 3. Season
    season_clean = season.title() if season else "Spring"

    # 4. Previous Trips (experience)
    previous_trips = int(data.get("previous_trips", 3))

    # 5. Flight Booked
    if data.get("flight_booked") is not None:
        flight_booked = 1 if data["flight_booked"] else 0
    else:
        flight_keywords = ("flight", "airline", "air", "ana", "jal", "flying", "plane", "ticket to", "boarding")
        flight_booked = 1 if any(kw in p for p in prebooked_set for kw in flight_keywords) else 0

    # 6. Hotel Booked
    if data.get("hotel_booked") is not None:
        hotel_booked = 1 if data["hotel_booked"] else 0
    else:
        hotel_keywords = ("hotel", "hostel", "inn", "ryokan", "airbnb", "resort", "stay", "room", "apartment", "lodging")
        hotel_booked = 1 if any(kw in p for p in prebooked_set for kw in hotel_keywords) else 0

    # 7. Passport Valid
    if data.get("passport_valid") is not None:
        passport_valid = 1 if data["passport_valid"] else 0
    else:
        passport_valid = 1

    # 8. Visa Required & Ready
    visa_info = country_req.get("visa", {})
    visa_status = str(data.get("visa_status", "")).lower().strip()
    if visa_status in ("not_required", "exempt"):
        visa_required = 0
        visa_ready = 1
    elif visa_status == "yes":
        visa_required = 1
        visa_ready = 1
    elif visa_status in ("not_yet", "no"):
        visa_required = 1
        visa_ready = 0
    else:
        if data.get("visa_required") is not None:
            visa_required = 1 if data["visa_required"] else 0
        else:
            visa_required = 1 if visa_info.get("required") else 0

        if data.get("visa_ready") is not None:
            visa_ready = 1 if data["visa_ready"] else 0
        else:
            if visa_required == 0:
                visa_ready = 1
            else:
                visa_ready = 1 if any("visa" in p for p in prebooked_set) else 0

    # 9. Documents Completed
    if data.get("documents_completed") is not None:
        documents_completed = 1 if data["documents_completed"] else 0
    else:
        documents_completed = 1 if (breakdown.get("documents", 0) >= 70 or (passport_valid == 1 and visa_ready == 1)) else 0

    # 10. Travel Insurance
    if data.get("travel_insurance") is not None:
        travel_insurance = 1 if data["travel_insurance"] else 0
    else:
        travel_insurance = 1 if any("insurance" in p or "policy" in p for p in prebooked_set) else 0

    # 11. Emergency Prepared
    if data.get("emergency_prepared") is not None:
        emergency_prepared = 1 if data["emergency_prepared"] else 0
    else:
        emergency_prepared = 1 if any("emergency" in p or "medical" in p or "doctor" in p for p in prebooked_set) else 0

    # 12. Country Preparation (eSIM, transit cards, currency)
    if data.get("country_preparation") is not None:
        country_preparation = 1 if data["country_preparation"] else 0
    else:
        transit_keywords = ("suica", "pasmo", "jr pass", "sim", "esim", "wifi", "pocket", "pass", "card", "yen", "euro", "currency")
        country_preparation = 1 if any(kw in p for p in prebooked_set for kw in transit_keywords) or breakdown.get("country_requirements", 0) >= 70 else 0

    # 13. Packing Completed
    if data.get("packing_completed") is not None:
        packing_completed = 1 if data["packing_completed"] else 0
    else:
        packing_completed = 0

    # 14. Weather Risk
    if data.get("weather_risk") is not None:
        weather_risk = str(data["weather_risk"]).strip().upper()
    else:
        weather_ctx = packing.get("weather", {})
        precip = weather_ctx.get("precipitation_chance", 30)
        avg_temp = weather_ctx.get("avg_temp")
        if precip >= 60 or (avg_temp is not None and (avg_temp < 0 or avg_temp > 35)):
            weather_risk = "HIGH"
        elif precip >= 40:
            weather_risk = "MEDIUM"
        else:
            weather_risk = "LOW"

    return {
        "destination_country": country_clean,
        "trip_duration_days": trip_duration_days,
        "season": season_clean,
        "previous_trips": previous_trips,
        "flight_booked": flight_booked,
        "hotel_booked": hotel_booked,
        "passport_valid": passport_valid,
        "visa_required": visa_required,
        "visa_ready": visa_ready,
        "documents_completed": documents_completed,
        "travel_insurance": travel_insurance,
        "emergency_prepared": emergency_prepared,
        "country_preparation": country_preparation,
        "packing_completed": packing_completed,
        "weather_risk": weather_risk,
    }


@app.route("/api/readiness", methods=["POST"])
def trip_readiness():
    data = request.get_json() or {}
    destination = data.get("destination", "")
    cities = data.get("cities", "")
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    itinerary = data.get("itinerary", "")
    prebooked = data.get("prebooked", [])

    dest_info = resolve_destination(destination or cities)
    month = extract_month(start_date)
    duration_days = parse_duration_days(start_date, end_date)
    season = get_season(month)
    activities = extract_activities(itinerary)
    prebooked_set = normalize_prebooked(prebooked)

    packing = get_packing_recommendations(dest_info, duration_days, activities, month)
    country_req = get_country_requirements(dest_info)
    booking = get_booking_intelligence(activities, dest_info, prebooked)

    # 1. Existing rule-based breakdown (kept intact as fallback and sub-score metrics)
    breakdown = {
        "packing": score_packing(packing),
        "tickets": score_tickets(booking),
        "documents": score_documents(country_req),
        "country_requirements": score_country_requirements(country_req, prebooked_set),
    }
    rule_based_score = calculate_readiness(breakdown)
    priority = get_priority_actions(dest_info, country_req, booking, breakdown, prebooked_set)

    # 2. Primary ML Prediction with Automatic Rule-Based Fallback
    readiness_score = rule_based_score
    score_source = "rule_based_fallback"
    top_factors = []
    doing_well = []
    needs_attention = []
    ml_features = None

    if predict_readiness is not None:
        try:
            ml_features = map_to_ml_features(
                data, dest_info, duration_days, season, packing, country_req, booking, prebooked_set, breakdown
            )
            ml_pred = predict_readiness(ml_features)
            readiness_score = int(ml_pred["preparedness_score"])
            top_factors = ml_pred.get("top_factors", [])
            doing_well = ml_pred.get("doing_well", [])
            needs_attention = ml_pred.get("needs_attention", [])
            score_source = "ml"
        except Exception as ml_err:
            logger.warning("ML readiness prediction failed, falling back to rule-based: %s", ml_err)
            score_source = "rule_based_fallback"
            readiness_score = rule_based_score
            top_factors = [p["text"] for p in priority[:3]]
            needs_attention = [p["text"] for p in priority[:3]]
            doing_well = ["Trip dates and destination configured"]
    else:
        score_source = "rule_based_fallback"
        readiness_score = rule_based_score
        top_factors = [p["text"] for p in priority[:3]]
        needs_attention = [p["text"] for p in priority[:3]]
        doing_well = ["Trip dates and destination configured"]

    risk_level = derive_risk_level(readiness_score)

    return jsonify({
        "readiness_score": readiness_score,
        "preparedness_score": readiness_score,
        "score_source": score_source,
        "risk_level": risk_level,
        "top_factors": top_factors,
        "doing_well": doing_well,
        "needs_attention": needs_attention,
        "ml_features": ml_features,
        "score_breakdown": breakdown,
        "destination": dest_info,
        "packing_recommendations": packing,
        "country_requirements": country_req,
        "booking_intelligence": booking,
        "priority_actions": [p["text"] for p in priority],
        "before_you_fly": priority,
        "duration_days": duration_days,
        "season": season,
        "activities_parsed": activities,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "readiness"})


if __name__ == "__main__":
    app.run(debug=True, port=5007)
