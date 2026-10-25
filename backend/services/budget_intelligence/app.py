from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import re
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"), override=True)
except ImportError:
    pass

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

DESTINATION_MAP = {
    "tokyo": "japan",
    "kyoto": "japan",
    "osaka": "japan",
    "japan": "japan",
    "disney": "japan",
    "paris": "france",
    "france": "france",
    "lyon": "france",
    "bangkok": "thailand",
    "thailand": "thailand",
    "phuket": "thailand",
    "istanbul": "turkey",
    "turkey": "turkey",
    "bali": "indonesia",
    "indonesia": "indonesia",
}

STYLE_KEYS = {"budget": "budget", "mid-range": "mid", "mid": "mid", "luxury": "luxury"}


def load_json(name):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


budget_profiles = load_json("budget_profiles.json")
attractions_data = load_json("attractions.json")


def resolve_country(destination):
    if not destination:
        return "japan", destination or "Tokyo"
    raw = destination.strip().lower()
    parts = [p.strip() for p in re.split(r"[,/|]", raw) if p.strip()]
    primary = parts[0] if parts else raw
    country = DESTINATION_MAP.get(primary, primary)
    if country not in budget_profiles:
        country = "japan"
    return country, destination.strip()


def parse_days(start_date, end_date, explicit_days):
    if explicit_days:
        return max(1, min(int(explicit_days), 90))
    if start_date and end_date:
        try:
            s = datetime.strptime(start_date[:10], "%Y-%m-%d")
            e = datetime.strptime(end_date[:10], "%Y-%m-%d")
            return max(1, min((e - s).days + 1, 90))
        except ValueError:
            pass
    return 7


def normalize_style(style):
    key = (style or "mid-range").strip().lower()
    return STYLE_KEYS.get(key, "mid")


def extract_blob(*texts):
    return " ".join(t for t in texts if t).lower()


def match_triggers(blob, triggers):
    return any(t in blob for t in triggers)


def itinerary_activity_cost(country_key, blob, profile):
    costs = profile.get("activity_costs_inr", {})
    total = 0
    matched = []
    if match_triggers(blob, ["disneyland", "disney sea", "disneysea", "disney"]):
        if "disneyland" in blob and ("disneysea" in blob or "disney sea" in blob):
            total += costs.get("disney_combo", 24000)
            matched.append("Disneyland + DisneySea combo")
        else:
            total += costs.get("disneyland", 12000)
            matched.append("Disney park day")
    for key, amount in costs.items():
        if key in ("disney_combo", "disneyland", "disneysea"):
            continue
        key_words = key.replace("_", " ")
        if key_words in blob or key.replace("_", "") in blob.replace(" ", ""):
            total += amount
            matched.append(key_words.title())
    city_attractions = attractions_data.get(
        "tokyo" if country_key == "japan" else "paris" if country_key == "france" else "",
        {},
    )
    for key, info in city_attractions.items():
        name_l = info.get("name", "").lower()
        key_l = key.replace("_", " ")
        if key_l in blob or name_l in blob or any(w in blob for w in name_l.split() if len(w) > 4):
            est = costs.get(key, costs.get(key_l.replace(" ", "_"), 2500))
            if est and name_l not in [m.lower() for m in matched]:
                total += est if isinstance(est, int) else 2500
                matched.append(info["name"])
    return total, matched


def food_multiplier(food_prefs):
    prefs = (food_prefs or "").lower()
    if any(w in prefs for w in ("fine dining", "michelin", "omakase", "luxury")):
        return 1.35
    if any(w in prefs for w in ("vegetarian", "vegan", "halal", "kosher")):
        return 1.12
    if any(w in prefs for w in ("street food", "budget", "konbini", "local")):
        return 0.88
    return 1.0


def shopping_allowance(shopping_prefs, style, days):
    prefs = (shopping_prefs or "").lower()
    base = {"budget": 3000, "mid": 8000, "luxury": 22000}[style]
    if any(w in prefs for w in ("luxury", "designer", "boutique")):
        base *= 1.8
    elif any(w in prefs for w in ("minimal", "no shopping", "souvenir only")):
        base *= 0.4
    elif any(w in prefs for w in ("outlet", "duty-free")):
        base *= 1.2
    return int(base * (1 + (days - 5) * 0.05))


def build_alerts(profile, blob, itinerary):
    alerts = []
    for tmpl in profile.get("alert_templates", []):
        if match_triggers(blob, tmpl.get("trigger", [])):
            area = "your selected area"
            for area_key in ("shinjuku", "ginza", "montmartre", "champs"):
                if area_key in blob:
                    area = area_key.title()
                    break
            msg = tmpl["message"].replace("{area}", area)
            alerts.append({
                "title": tmpl["title"],
                "message": msg,
                "severity": tmpl.get("severity", "medium"),
                "potential_overage_inr": tmpl.get("overage_inr", 0),
            })
    return alerts[:5]


def build_smart_fixes(profile, blob):
    fixes = []
    for fix in profile.get("smart_fixes", []):
        conditions = fix.get("conditions", [])
        if not conditions or match_triggers(blob, conditions):
            fixes.append({
                "id": fix["id"],
                "title": fix["title"],
                "savings_inr": fix["savings_inr"],
                "steps": fix["steps"],
            })
    fixes.sort(key=lambda x: x["savings_inr"], reverse=True)
    return fixes[:5]


def compute_health_score(total_budget, projected_total, hidden_total, alert_count):
    if total_budget <= 0:
        return 50
    ratio = projected_total / total_budget
    score = 100
    if ratio > 1.15:
        score -= 35
    elif ratio > 1.05:
        score -= 22
    elif ratio > 0.95:
        score -= 12
    elif ratio > 0.85:
        score -= 5
    hidden_pct = hidden_total / max(total_budget, 1)
    if hidden_pct > 0.15:
        score -= 10
    score -= min(15, alert_count * 4)
    return max(0, min(100, round(score)))


def day_by_day_forecast(days, total_budget, projected_daily_avg, style):
    forecast = []
    cumulative = 0
    exhaust_day = None
    for d in range(1, days + 1):
        variance = 1.0 + (0.08 if d in (1, days) else 0)
        if d == 3 and "shop" in style:
            variance += 0.15
        day_spend = int(projected_daily_avg * variance)
        cumulative += day_spend
        remaining = total_budget - cumulative
        forecast.append({
            "day": d,
            "spend_inr": day_spend,
            "cumulative_inr": cumulative,
            "remaining_inr": remaining,
            "status": "ok" if remaining > total_budget * 0.15 else ("warning" if remaining > 0 else "depleted"),
        })
        if exhaust_day is None and remaining <= 0:
            exhaust_day = d
    return forecast, exhaust_day


def analyze_budget(data):
    destination = data.get("destination", "Tokyo, Japan")
    total_budget = int(data.get("total_budget") or 75000)
    travel_style = normalize_style(data.get("travel_style"))
    itinerary = data.get("itinerary", "")
    shopping = data.get("shopping_preferences", "")
    food = data.get("food_preferences", "")
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    days = parse_days(start_date, end_date, data.get("days"))

    country_key, display_dest = resolve_country(destination)
    profile = budget_profiles.get(country_key, budget_profiles["japan"])
    blob = extract_blob(destination, itinerary, shopping, food)

    daily_base = profile["daily_base_inr"][travel_style]
    food_mult = food_multiplier(food)
    daily_with_food = int(daily_base * food_mult)
    core_trip = daily_with_food * days

    activity_cost, activities_matched = itinerary_activity_cost(country_key, blob, profile)
    shopping_cost = shopping_allowance(shopping, travel_style, days)
    hidden = profile.get("hidden_costs", [])
    hidden_total = sum(h.get("amount_inr", 0) for h in hidden)

    projected_total = core_trip + activity_cost + shopping_cost + hidden_total
    projected_daily_avg = projected_total / days

    alerts = build_alerts(profile, blob, itinerary)
    smart_fixes = build_smart_fixes(profile, blob)
    total_fix_savings = sum(f["savings_inr"] for f in smart_fixes[:3])

    health_score = compute_health_score(
        total_budget, projected_total, hidden_total, len(alerts)
    )

    forecast, exhaust_day = day_by_day_forecast(
        days, total_budget, projected_daily_avg, shopping.lower()
    )

    over_under = projected_total - total_budget
    risk_label = (
        "High overspend risk"
        if over_under > total_budget * 0.1
        else ("Moderate — watch daily burn" if over_under > 0 else "Within budget envelope")
    )

    return {
        "destination": {"country": country_key, "display": profile["display_name"], "input": display_dest},
        "trip_budget_health_score": health_score,
        "risk_label": risk_label,
        "inputs_summary": {
            "total_budget_inr": total_budget,
            "travel_style": travel_style,
            "days": days,
            "food_multiplier": round(food_mult, 2),
        },
        "projection": {
            "projected_total_inr": projected_total,
            "vs_budget_inr": over_under,
            "daily_average_inr": int(projected_daily_avg),
            "breakdown": {
                "accommodation_food_transport_inr": core_trip,
                "itinerary_activities_inr": activity_cost,
                "shopping_inr": shopping_cost,
                "hidden_costs_inr": hidden_total,
            },
            "activities_matched": activities_matched,
        },
        "overspending_alerts": alerts,
        "hidden_costs": hidden,
        "smart_fixes": smart_fixes,
        "potential_savings_top3_inr": total_fix_savings,
        "day_by_day_forecast": forecast,
        "budget_exhaust_day": exhaust_day,
        "budget_exhaust_message": (
            f"At this pace, budget exhausts by Day {exhaust_day}"
            if exhaust_day
            else f"Budget holds through Day {days} with ~₹{total_budget - forecast[-1]['cumulative_inr']:,} buffer"
        ),
        "currency": "INR",
    }


@app.route("/api/budget-intelligence", methods=["POST"])
def budget_intelligence():
    data = request.get_json() or {}
    if not data.get("destination"):
        return jsonify({"error": "destination is required"}), 400
    try:
        result = analyze_budget(data)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "budget_intelligence"})


if __name__ == "__main__":
    app.run(debug=True, port=5009)
