"""Google Places API (Nearby Search) — primary place source when API key is configured."""

import math
from typing import Optional

import requests

from config import GOOGLE_PLACES_API_KEY

NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

CATEGORY_TYPES = {
    "indoor": ["museum", "art_gallery", "library"],
    "culture": ["museum", "tourist_attraction", "art_gallery", "church"],
    "food": ["restaurant", "cafe", "bakery"],
    "cozy": ["cafe", "bakery"],
    "outdoor": ["park", "tourist_attraction"],
    "nature": ["park", "campground"],
    "walk": ["tourist_attraction", "point_of_interest"],
    "evening": ["restaurant", "tourist_attraction"],
    "nightlife": ["bar", "night_club"],
    "wellness": ["spa", "beauty_salon"],
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _price_level_to_budget(price_level: Optional[int]) -> str:
    if price_level is None:
        return "mid"
    if price_level <= 1:
        return "budget"
    if price_level >= 3:
        return "luxury"
    return "mid"


def _price_to_cost(price_level: Optional[int]) -> str:
    return {
        0: "Free",
        1: "Under $15",
        2: "$15–$45",
        3: "$45–$80",
        4: "$80+",
    }.get(price_level if price_level is not None else 2, "$15–$45")


def _types_to_categories(types: list) -> list:
    cats = []
    tset = set(types or [])
    if tset & {"museum", "art_gallery", "church", "place_of_worship", "tourist_attraction"}:
        cats.extend(["culture", "indoor"])
    if tset & {"restaurant", "cafe", "bakery", "meal_takeaway"}:
        cats.append("food")
    if tset & {"bar", "night_club"}:
        cats.extend(["nightlife", "food"])
    if tset & {"park", "campground", "natural_feature"}:
        cats.extend(["outdoor", "nature"])
    if tset & {"spa"}:
        cats.append("wellness")
    if not cats:
        cats = ["culture"]
    return list(dict.fromkeys(cats))


def _infer_indoor_outdoor(types: list) -> str:
    tset = set(types or [])
    if tset & {"park", "campground", "natural_feature"}:
        return "outdoor"
    if tset & {"museum", "art_gallery", "restaurant", "cafe", "bar", "spa", "shopping_mall"}:
        return "indoor"
    if tset & {"tourist_attraction", "point_of_interest"}:
        return "outdoor"
    return "indoor"


def _time_bands_from_types(types: list, categories: list) -> list:
    if "nightlife" in categories:
        return ["evening", "late_night"]
    if "food" in categories:
        return ["morning", "afternoon", "evening", "late_night"]
    if "outdoor" in categories:
        return ["morning", "afternoon", "evening"]
    return ["morning", "afternoon", "evening"]


def _normalize_place(item: dict, city_lat: float, city_lon: float) -> Optional[dict]:
    name = item.get("name")
    if not name:
        return None

    loc = item.get("geometry", {}).get("location", {})
    lat, lon = loc.get("lat"), loc.get("lng")
    if lat is None or lon is None:
        return None

    types = item.get("types") or []
    categories = _types_to_categories(types)
    indoor_outdoor = _infer_indoor_outdoor(types)
    time_bands = _time_bands_from_types(types, categories)
    budget_tier = _price_level_to_budget(item.get("price_level"))
    distance_km = round(haversine_km(city_lat, city_lon, lat, lon), 1)
    duration_min = max(20, min(120, int(distance_km * 10 + 35)))
    rating = item.get("rating") or 4.0

    weather_scores = {
        "clear": 0.95 if indoor_outdoor == "outdoor" else 0.75,
        "cloudy": 0.85,
        "rain": 0.95 if indoor_outdoor == "indoor" else 0.25,
        "snow": 0.92 if indoor_outdoor == "indoor" else 0.35,
        "extreme_heat": 0.95 if indoor_outdoor == "indoor" else 0.45,
    }

    open_now = item.get("opening_hours", {}).get("open_now")
    availability = "open_now" if open_now else "walk_in"

    place_id = item.get("place_id") or item.get("name", "place")
    return {
        "id": f"gplaces_{place_id[:32]}",
        "name": name,
        "categories": categories,
        "time_bands": time_bands,
        "weather_scores": weather_scores,
        "indoor_outdoor": indoor_outdoor,
        "distance_km": distance_km,
        "budget_tier": budget_tier,
        "group_sizes": ["solo", "couple", "small_group", "family"],
        "duration_min": duration_min,
        "crowd": "high" if (item.get("user_ratings_total") or 0) > 500 else "moderate",
        "availability": availability,
        "rating": round(float(rating), 1),
        "cost": _price_to_cost(item.get("price_level")),
        "best_visiting_time": "Evening" if "nightlife" in categories else "Afternoon",
        "lat": lat,
        "lon": lon,
        "source": "google_places",
    }


def _nearby_search(lat: float, lon: float, place_type: str, radius: int = 4000) -> list:
    if not GOOGLE_PLACES_API_KEY:
        return []
    try:
        resp = requests.get(
            NEARBY_URL,
            params={
                "location": f"{lat},{lon}",
                "radius": radius,
                "type": place_type,
                "key": GOOGLE_PLACES_API_KEY,
            },
            timeout=12,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            return []
        return data.get("results") or []
    except (requests.RequestException, ValueError):
        return []


def fetch_google_places(lat: float, lon: float, primary_categories: list) -> list:
    """Fetch places from Google Places Nearby Search."""
    if not GOOGLE_PLACES_API_KEY:
        return []

    types_to_fetch = []
    for cat in primary_categories:
        types_to_fetch.extend(CATEGORY_TYPES.get(cat, []))
    types_to_fetch = list(dict.fromkeys(types_to_fetch))[:12]

    venues = []
    seen_ids = set()

    for place_type in types_to_fetch:
        for item in _nearby_search(lat, lon, place_type):
            pid = item.get("place_id")
            if not pid or pid in seen_ids:
                continue
            seen_ids.add(pid)
            venue = _normalize_place(item, lat, lon)
            if venue:
                venues.append(venue)

    venues.sort(key=lambda v: (-(v.get("rating") or 0), v["distance_km"]))
    return venues[:50]
