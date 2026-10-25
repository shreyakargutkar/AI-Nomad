"""Scoring engine for contextual recommendations."""

import hashlib
import math

from ai_client import enrich_explanations, explanation_provider
from cache_store import get_places, get_response, set_places, set_response
from cities import CITY_META, DEFAULT_CITY
from config import GOOGLE_PLACES_API_KEY, PLACES_PROVIDER, WEATHER_API_KEY
from places_client import fetch_places_for_city
from weather_client import fetch_live_context

ARCHETYPE_WEIGHTS = {
    "explorer": {"env": 0.30, "user": 0.25, "rt": 0.45},
    "planner": {"env": 0.35, "user": 0.40, "rt": 0.25},
    "budget": {"env": 0.35, "user": 0.45, "rt": 0.20},
    "family": {"env": 0.40, "user": 0.35, "rt": 0.25},
    "luxury": {"env": 0.30, "user": 0.50, "rt": 0.20},
    "nomad": {"env": 0.25, "user": 0.30, "rt": 0.45},
    "culture": {"env": 0.30, "user": 0.45, "rt": 0.25},
    "relaxed": {"env": 0.32, "user": 0.38, "rt": 0.30},
    "foodie": {"env": 0.28, "user": 0.42, "rt": 0.30},
    "photographer": {"env": 0.38, "user": 0.22, "rt": 0.40},
}

BUDGET_ORDER = {"budget": 0, "mid": 1, "luxury": 2}

TRAVELER_MAP = {
    "solo": "solo",
    "couple": "couple",
    "family": "family",
    "friends": "small_group",
    "group": "small_group",
}

STYLE_MAP = {
    "explorer": "explorer",
    "budget": "budget",
    "luxury": "luxury",
    "relaxed": "relaxed",
    "foodie": "foodie",
    "photographer": "photographer",
}

STYLE_PREFERENCES = {
    "foodie": ["food", "culture"],
    "photographer": ["outdoor", "culture", "nature", "walk"],
    "relaxed": ["cozy", "food", "wellness"],
    "luxury": ["culture", "food", "evening"],
    "budget": ["culture", "outdoor", "food"],
    "explorer": ["outdoor", "culture", "walk"],
    "family": ["culture", "food", "outdoor"],
}


def normalize_hour(hour):
    h = int(hour) % 24
    if h >= 21 or h < 6:
        return "late_night"
    if h >= 17:
        return "evening"
    if h >= 11:
        return "afternoon"
    return "morning"


def context_fingerprint(ctx):
    key = "|".join(
        str(ctx.get(k, ""))
        for k in (
            "city",
            "time_band",
            "weather",
            "activity_state",
            "budget_tier",
            "group_size",
            "archetype",
            "preferences",
        )
    )
    return hashlib.md5(key.encode()).hexdigest()[:12]


def select_primary_categories(ctx):
    weather = ctx.get("weather", "clear")
    band = ctx.get("time_band", "afternoon")
    state = ctx.get("activity_state", "stationary")
    archetype = ctx.get("archetype", "explorer")

    if archetype == "foodie":
        base = ["food", "cozy", "culture"]
    elif archetype == "photographer":
        base = ["outdoor", "culture", "walk", "evening"]
    elif archetype == "luxury":
        base = ["evening", "culture", "food"]
    elif archetype == "family":
        base = ["culture", "food", "outdoor", "indoor"]
    else:
        base = None

    if weather == "rain":
        if band in ("evening", "late_night"):
            return base or ["cozy", "food", "indoor", "nightlife"]
        return base or ["indoor", "cozy", "culture", "food"]

    if weather == "extreme_heat":
        if band in ("afternoon", "morning"):
            return ["indoor", "culture", "wellness", "food"]
        return base or ["evening", "food", "outdoor", "culture"]

    if band == "late_night":
        return ["nightlife", "food", "cozy", "indoor"]

    if band == "evening":
        if weather == "clear":
            return base or ["evening", "food", "culture", "outdoor"]
        return ["food", "cozy", "culture"]

    if state == "moving" and weather == "clear":
        return base or ["outdoor", "food", "walk", "culture"]

    if weather == "clear" and band == "afternoon":
        return base or ["outdoor", "culture", "nature", "walk"]

    if weather == "snow":
        return ["indoor", "cozy", "wellness", "culture"]

    return base or ["culture", "food", "outdoor", "cozy"]


def weather_fit(venue, weather, outdoor_pref):
    scores = venue.get("weather_scores", {})
    base = scores.get(weather, 0.5)
    if venue.get("indoor_outdoor") == "outdoor" and weather in ("rain", "snow", "extreme_heat"):
        base *= 0.35
    if venue.get("indoor_outdoor") in ("indoor", "covered") and weather in ("rain", "snow", "extreme_heat"):
        base = min(1.0, base * 1.15)
    if outdoor_pref and weather == "clear" and venue.get("indoor_outdoor") == "outdoor":
        base = min(1.0, base * 1.2)
    return base


def time_fit(venue, time_band):
    bands = venue.get("time_bands", [])
    if time_band in bands:
        return 1.0
    if time_band == "late_night" and "evening" in bands:
        return 0.6
    if time_band == "afternoon" and "morning" in bands:
        return 0.5
    return 0.15


def preference_fit(venue, preferences):
    if not preferences:
        return 0.6
    prefs = set(p.lower() for p in preferences)
    cats = set(venue.get("categories", []))
    overlap = len(prefs & cats) / max(len(prefs), 1)
    return 0.4 + 0.6 * overlap


def budget_fit(venue, tier):
    v = BUDGET_ORDER.get(venue.get("budget_tier", "mid"), 1)
    u = BUDGET_ORDER.get(tier, 1)
    if v <= u:
        return 1.0 - (u - v) * 0.15
    return max(0.1, 1.0 - (v - u) * 0.45)


def group_fit(venue, group_size):
    sizes = venue.get("group_sizes", [])
    if group_size in sizes:
        return 1.0
    if group_size == "family" and "small_group" in sizes:
        return 0.7
    if group_size == "small_group" and "couple" in sizes:
        return 0.85
    return 0.3


def distance_score(km, activity_state):
    decay = {"moving": 0.8, "transitioning": 1.5, "stationary": 2.5}.get(activity_state, 2.0)
    return math.exp(-km / decay)


def crowd_fit(venue, crowd_averse):
    levels = {"low": 1.0, "moderate": 0.75, "high": 0.45}
    base = levels.get(venue.get("crowd", "moderate"), 0.6)
    if crowd_averse:
        return base
    return 0.7 + base * 0.3


def category_boost(venue, primary_categories):
    cats = venue.get("categories", [])
    for i, cat in enumerate(primary_categories):
        if cat in cats:
            return 1.0 - i * 0.08
    return 0.4


def build_moment_summary(ctx):
    city = ctx.get("city_display", ctx.get("city", "your area").title())
    band = ctx.get("time_band", "afternoon").replace("_", " ")
    weather = ctx.get("weather", "clear")
    day = ctx.get("day_type", "weekday")
    weather_phrase = {
        "clear": "clear skies",
        "rain": "rain",
        "cloudy": "cloud cover",
        "snow": "snow",
        "extreme_heat": "heat",
    }.get(weather, weather)
    live = ctx.get("live_weather") or {}
    if live.get("temp_c") is not None:
        weather_phrase = f"{weather_phrase}, {live['temp_c']}°C"
    return f"{day.title()} · {band} · {weather_phrase} in {city}"


def normalize_request(data: dict) -> dict:
    """Map public API fields to internal engine fields. Weather/time are never taken from client."""
    normalized = {k: v for k, v in data.items() if k not in ("weather", "hour", "day_type")}

    traveler = data.get("travelerType") or data.get("traveler_type")
    if traveler:
        normalized["group_size"] = TRAVELER_MAP.get(str(traveler).lower(), "couple")

    style = data.get("travelStyle") or data.get("travel_style")
    if style:
        style_key = str(style).lower()
        normalized["archetype"] = STYLE_MAP.get(style_key, "explorer")
        if not data.get("preferences"):
            normalized["preferences"] = STYLE_PREFERENCES.get(style_key, ["culture", "food"])

    if data.get("budget"):
        budget = str(data["budget"]).lower()
        if budget in ("low", "cheap", "budget"):
            normalized["budget_tier"] = "budget"
        elif budget in ("high", "premium", "luxury"):
            normalized["budget_tier"] = "luxury"
        else:
            normalized["budget_tier"] = "mid"

    return normalized


def get_venue_pool(city_key: str, primary_categories: list) -> list:
    cached = get_places(city_key)
    if cached:
        return cached
    venues = fetch_places_for_city(city_key, primary_categories, broad=True)
    if venues:
        set_places(city_key, venues)
    return venues


def _places_source_label() -> str:
    if GOOGLE_PLACES_API_KEY and PLACES_PROVIDER != "osm":
        return "Google Places API (+ OpenStreetMap fallback)"
    return "OpenStreetMap (Overpass + Nominatim)"


def generate_recommendations(data: dict) -> dict:
    data = normalize_request(data)
    city_key = (data.get("city") or DEFAULT_CITY).lower().strip()
    city_meta = CITY_META.get(city_key, CITY_META[DEFAULT_CITY])

    live_ctx = fetch_live_context(
        city_meta["lat"],
        city_meta["lon"],
        city_meta.get("timezone", "UTC"),
    )
    hour = live_ctx["hour"]
    time_band = normalize_hour(hour)
    weather = live_ctx["condition"]

    archetype = data.get("archetype", "explorer")
    preferences = data.get("preferences") or STYLE_PREFERENCES.get(archetype, ["culture", "food"])

    ctx = {
        "city": city_key,
        "city_display": city_meta["display_name"],
        "time_band": time_band,
        "hour": hour,
        "local_time": live_ctx.get("local_time"),
        "weather": weather,
        "live_weather": live_ctx,
        "activity_state": data.get("activity_state", "stationary"),
        "budget_tier": data.get("budget_tier", "mid"),
        "group_size": data.get("group_size", "couple"),
        "archetype": archetype,
        "preferences": preferences,
        "day_type": live_ctx.get("day_type", "weekday"),
        "weekday_name": live_ctx.get("weekday_name"),
        "crowd_averse": data.get("crowd_averse", False),
        "outdoor_preference": "outdoor" in preferences,
    }

    fp = context_fingerprint(ctx)
    cached = get_response(fp)
    if cached:
        return cached

    weights = ARCHETYPE_WEIGHTS.get(ctx["archetype"], ARCHETYPE_WEIGHTS["explorer"])
    primary_categories = select_primary_categories(ctx)

    venues = get_venue_pool(city_key, primary_categories)
    if not venues:
        raise RuntimeError("Could not fetch places for this city. Try again in a moment.")

    scored = []
    for venue in venues:
        if ctx["group_size"] == "family" and "nightlife" in venue.get("categories", []):
            continue
        if time_fit(venue, time_band) < 0.2 and venue.get("indoor_outdoor") != "indoor":
            continue
        if budget_fit(venue, ctx["budget_tier"]) < 0.25:
            continue

        env = (
            weather_fit(venue, ctx["weather"], ctx["outdoor_preference"]) * 0.45
            + time_fit(venue, time_band) * 0.35
            + 0.2
        )
        user = (
            preference_fit(venue, ctx["preferences"]) * 0.45
            + budget_fit(venue, ctx["budget_tier"]) * 0.30
            + group_fit(venue, ctx["group_size"]) * 0.25
        )
        rt = (
            distance_score(venue.get("distance_km", 2), ctx["activity_state"]) * 0.40
            + crowd_fit(venue, ctx["crowd_averse"]) * 0.30
            + (0.9 if venue.get("availability") == "open_now" else 0.65) * 0.30
        )

        base = weights["env"] * env + weights["user"] * user + weights["rt"] * rt
        final = base * category_boost(venue, primary_categories)

        if ctx["weather"] == "clear" and "outdoor" in primary_categories:
            if venue.get("indoor_outdoor") == "outdoor":
                final *= 1.18
            elif venue.get("indoor_outdoor") == "indoor" and "food" not in venue.get("categories", []):
                final *= 0.92
        if ctx["weather"] in ("rain", "snow", "extreme_heat"):
            if venue.get("indoor_outdoor") in ("indoor", "covered"):
                final *= 1.1

        conflict_note = None
        if ctx["outdoor_preference"] and ctx["weather"] == "rain" and venue.get("indoor_outdoor") == "outdoor":
            final *= 0.3
            conflict_note = "Outdoor preference deprioritized due to rain"
        if (
            ctx["outdoor_preference"]
            and ctx["weather"] == "rain"
            and venue.get("indoor_outdoor") in ("indoor", "covered")
        ):
            final *= 1.12
            conflict_note = "Rain pivot — covered pick matching your vibe"

        scored.append(
            {
                "id": venue["id"],
                "name": venue["name"],
                "categories": venue.get("categories", []),
                "indoor_outdoor": venue.get("indoor_outdoor"),
                "score": round(final, 3),
                "distance_km": venue.get("distance_km"),
                "duration_min": venue.get("duration_min"),
                "travel_time": venue.get("duration_min"),
                "budget_tier": venue.get("budget_tier"),
                "availability": venue.get("availability"),
                "cost": venue.get("cost"),
                "rating": venue.get("rating"),
                "best_visiting_time": venue.get("best_visiting_time"),
                "why_now": "",
                "conflict_note": conflict_note,
                "signals_used": [
                    ctx["time_band"],
                    ctx["weather"],
                    ctx["activity_state"],
                    ctx["archetype"],
                ],
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)

    top = []
    cat_counts = {}
    for item in scored:
        primary_cat = item["categories"][0] if item["categories"] else "other"
        if cat_counts.get(primary_cat, 0) >= 2 and len(top) < 5:
            continue
        top.append(item)
        cat_counts[primary_cat] = cat_counts.get(primary_cat, 0) + 1
        if len(top) >= 6:
            break

    moment_summary = build_moment_summary(ctx)
    top, moment_summary, contrast_note = enrich_explanations(top, ctx, moment_summary)
    for rec in top:
        rec["reason"] = rec.get("why_now", "")

    refresh_hints = []
    if ctx["weather"] == "rain":
        refresh_hints.append("Will refresh when weather clears")
    if ctx["time_band"] == "afternoon":
        refresh_hints.append("Evening picks unlock after 5 PM")
    if ctx["activity_state"] == "moving":
        refresh_hints.append("Nearby bias while you're on the move")
    if live_ctx.get("weather_live"):
        refresh_hints.append(f"Live in {city_meta['display_name']}: {live_ctx.get('description', weather)} at {live_ctx.get('local_time')}")
    else:
        refresh_hints.append(f"Local time in {city_meta['display_name']}: {live_ctx.get('local_time')}")

    result = {
        "context_fingerprint": fp,
        "moment_summary": moment_summary,
        "context": ctx,
        "live_context": {
            "city": city_key,
            "city_display": city_meta["display_name"],
            "weather": weather,
            "weather_description": live_ctx.get("description"),
            "temp_c": live_ctx.get("temp_c"),
            "hour": hour,
            "local_time": live_ctx.get("local_time"),
            "time_band": time_band,
            "day_type": ctx["day_type"],
            "weekday_name": live_ctx.get("weekday_name"),
            "source": live_ctx.get("source"),
            "weather_live": live_ctx.get("weather_live", False),
        },
        "primary_categories": primary_categories,
        "weight_profile": weights,
        "recommendations": top,
        "total_candidates": len(scored),
        "refresh_triggers": [
            "Time band change (morning → afternoon → evening → late night)",
            "Weather condition change",
            "City selection change",
            "Activity state change (moving ↔ stationary)",
        ],
        "next_refresh_hint": refresh_hints[0] if refresh_hints else "Stable for this moment — pull to refresh anytime",
        "contrast_note": contrast_note,
        "data_sources": {
            "places": _places_source_label(),
            "weather": live_ctx.get("source"),
            "weather_configured": bool(WEATHER_API_KEY),
            "time": "openweathermap_timezone" if live_ctx.get("weather_live") else "city_timezone",
            "explanations": explanation_provider(),
        },
    }

    set_response(fp, result)
    return result
