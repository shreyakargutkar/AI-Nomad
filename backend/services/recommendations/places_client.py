"""Fetch real nearby places — Google Places (primary) or OpenStreetMap (fallback)."""

import hashlib
import math
import re
import time
from typing import Optional

import requests

from cities import CITY_META, DEFAULT_CITY
from config import GOOGLE_PLACES_API_KEY, PLACES_PROVIDER
from google_places import fetch_google_places

USER_AGENT = "ainomad-recommendations/1.0"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

CATEGORY_QUERIES = {
    "indoor": ['node["tourism"="museum"]', 'node["tourism"="gallery"]', 'node["amenity"="library"]'],
    "culture": ['node["tourism"="museum"]', 'node["historic"]', 'node["tourism"="attraction"]'],
    "food": ['node["amenity"="restaurant"]', 'node["amenity"="cafe"]'],
    "cozy": ['node["amenity"="cafe"]', 'node["shop"="bakery"]'],
    "outdoor": ['node["leisure"="park"]', 'node["tourism"="viewpoint"]'],
    "nature": ['node["leisure"="park"]', 'node["natural"]'],
    "walk": ['node["tourism"="viewpoint"]', 'node["historic"]'],
    "evening": ['node["amenity"="restaurant"]', 'node["tourism"="attraction"]'],
    "nightlife": ['node["amenity"="bar"]', 'node["amenity"="pub"]'],
    "wellness": ['node["leisure"="spa"]', 'node["amenity"="public_bath"]'],
}

INDOOR_TYPES = {"museum", "gallery", "library", "arts_centre", "theatre", "cinema"}
OUTDOOR_TYPES = {"park", "viewpoint", "garden", "monument"}
COVERED_HINTS = {"marketplace", "covered", "arcade"}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", (name or "place").lower()).strip("_")
    return base[:48] or "place"


def _infer_indoor_outdoor(tags: dict) -> str:
    tourism = tags.get("tourism", "")
    amenity = tags.get("amenity", "")
    leisure = tags.get("leisure", "")
    if tourism in INDOOR_TYPES or amenity in {"restaurant", "cafe", "bar", "pub", "library"}:
        if tourism in OUTDOOR_TYPES or leisure == "park":
            return "outdoor"
        if tags.get("indoor") == "no":
            return "outdoor"
        return "indoor"
    if tourism in OUTDOOR_TYPES or leisure == "park" or tags.get("natural"):
        return "outdoor"
    if any(h in (tags.get("name") or "").lower() for h in COVERED_HINTS):
        return "covered"
    return "indoor"


def _infer_categories(tags: dict) -> list:
    cats = []
    tourism = tags.get("tourism", "")
    amenity = tags.get("amenity", "")
    leisure = tags.get("leisure", "")
    if tourism in {"museum", "gallery", "artwork", "attraction"} or tags.get("historic"):
        cats.extend(["culture", "indoor"])
    if amenity in {"restaurant", "cafe", "fast_food"}:
        cats.append("food")
    if amenity in {"bar", "pub", "nightclub"}:
        cats.extend(["nightlife", "food"])
    if amenity == "place_of_worship" or tourism in {"temple", "shrine", "monastery"}:
        cats.extend(["culture", "outdoor", "walk"])
    if leisure == "park" or tags.get("natural"):
        cats.extend(["outdoor", "nature"])
    if tourism == "viewpoint":
        cats.extend(["outdoor", "walk"])
    if leisure == "spa":
        cats.append("wellness")
    if leisure == "garden":
        cats.extend(["outdoor", "nature", "culture"])
    if not cats:
        cats = ["culture"]
    return list(dict.fromkeys(cats))


def _infer_time_bands(tags: dict, categories: list) -> list:
    oh = (tags.get("opening_hours") or "").lower()
    if "nightlife" in categories or "bar" in tags.get("amenity", ""):
        return ["evening", "late_night"]
    if "food" in categories and "museum" not in tags.get("tourism", ""):
        return ["morning", "afternoon", "evening", "late_night"]
    if "outdoor" in categories:
        return ["morning", "afternoon", "evening"]
    if "24/7" in oh:
        return ["morning", "afternoon", "evening", "late_night"]
    return ["morning", "afternoon", "evening"]


def _infer_budget(tags: dict) -> str:
    fee = (tags.get("fee") or "").lower()
    if fee in {"no", "false", "0"}:
        return "budget"
    if tags.get("tourism") in {"museum", "gallery"} and fee == "yes":
        return "mid"
    if tags.get("amenity") in {"restaurant", "bar"}:
        return "mid"
    return "budget"


def _estimate_cost(budget_tier: str) -> str:
    return {"budget": "Free–$15", "mid": "$15–$45", "luxury": "$45+"}.get(budget_tier, "$15–$45")


def _estimate_rating(tags: dict) -> float:
    if tags.get("stars"):
        try:
            return min(5.0, float(tags["stars"]))
        except ValueError:
            pass
    base = 4.0
    if tags.get("tourism") == "museum":
        base = 4.3
    if tags.get("wikidata"):
        base += 0.2
    return round(min(5.0, base), 1)


def _best_visiting_time(time_bands: list, categories: list) -> str:
    if "late_night" in time_bands and "nightlife" in categories:
        return "After 9 PM"
    if "morning" in time_bands and "outdoor" in categories:
        return "Morning (before crowds)"
    if "evening" in time_bands:
        return "Early evening"
    if "afternoon" in time_bands:
        return "Afternoon"
    return "Flexible"


def _normalize_element(el: dict, city_lat: float, city_lon: float) -> Optional[dict]:
    tags = el.get("tags") or {}
    name = tags.get("name:en") or tags.get("name") or tags.get("brand")
    if not name:
        return None

    lat = el.get("lat")
    lon = el.get("lon")
    if lat is None or lon is None:
        center = el.get("center") or {}
        lat, lon = center.get("lat"), center.get("lon")
    if lat is None or lon is None:
        return None

    categories = _infer_categories(tags)
    indoor_outdoor = _infer_indoor_outdoor(tags)
    time_bands = _infer_time_bands(tags, categories)
    budget_tier = _infer_budget(tags)
    distance_km = round(haversine_km(city_lat, city_lon, lat, lon), 1)
    duration_min = max(30, min(180, int(distance_km * 12 + 45)))

    weather_scores = {
        "clear": 0.9 if indoor_outdoor == "outdoor" else 0.7,
        "cloudy": 0.8,
        "rain": 0.95 if indoor_outdoor in ("indoor", "covered") else 0.2,
        "snow": 0.9 if indoor_outdoor == "indoor" else 0.35,
        "extreme_heat": 0.95 if indoor_outdoor == "indoor" else 0.45,
    }

    place_id = f"osm_{el.get('type', 'node')}_{el.get('id', _slug(name))}"
    return {
        "id": place_id,
        "name": name,
        "categories": categories,
        "time_bands": time_bands,
        "weather_scores": weather_scores,
        "indoor_outdoor": indoor_outdoor,
        "distance_km": distance_km,
        "budget_tier": budget_tier,
        "group_sizes": ["solo", "couple", "small_group", "family"],
        "duration_min": duration_min,
        "crowd": "moderate",
        "availability": "open_now",
        "rating": _estimate_rating(tags),
        "cost": _estimate_cost(budget_tier),
        "best_visiting_time": _best_visiting_time(time_bands, categories),
        "lat": lat,
        "lon": lon,
        "osm_tags": {k: tags[k] for k in ("tourism", "amenity", "opening_hours", "fee") if k in tags},
    }


def _nominatim_tags(item: dict) -> dict:
    tags = {
        "name": item.get("name") or item.get("display_name", "").split(",")[0],
    }
    cls = item.get("class", "")
    typ = item.get("type", "")
    if cls == "tourism":
        tags["tourism"] = typ
    elif cls == "amenity":
        tags["amenity"] = typ
    elif cls == "leisure":
        tags["leisure"] = typ
    elif cls == "historic":
        tags["historic"] = typ or "yes"
    elif cls == "natural":
        tags["natural"] = typ or "yes"
    elif cls == "building" and typ == "temple":
        tags["amenity"] = "place_of_worship"
    return tags


def _nominatim_search(city_query: str, term: str, limit: int = 8) -> list:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": f"{term} in {city_query}", "format": "json", "limit": limit},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        results = []
        for item in resp.json():
            results.append(
                {
                    "type": "node",
                    "id": item.get("osm_id") or hashlib.md5(item.get("display_name", "").encode()).hexdigest()[:8],
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"]),
                    "tags": _nominatim_tags(item),
                }
            )
        return results
    except (requests.RequestException, ValueError, KeyError):
        return []


def _overpass_query(query: str) -> list:
    for server in OVERPASS_SERVERS:
        try:
            resp = requests.post(
                server,
                data={"data": query},
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                timeout=25,
            )
            if resp.status_code != 200:
                continue
            payload = resp.json()
            return payload.get("elements", [])
        except (requests.RequestException, ValueError):
            continue
    return []


def _overpass_fetch(lat: float, lon: float, radius_m: int, categories: list) -> list:
    fragments = []
    seen = set()
    for cat in categories:
        for q in CATEGORY_QUERIES.get(cat, CATEGORY_QUERIES["culture"]):
            if q not in seen:
                seen.add(q)
                fragments.append(f'{q}(around:{radius_m},{lat},{lon});')

    if not fragments:
        return []

    # Batch queries to avoid Overpass timeouts on large unions
    all_elements = []
    batch_size = 6
    for i in range(0, len(fragments), batch_size):
        batch = fragments[i : i + batch_size]
        query = f'[out:json][timeout:20];({" ".join(batch)});out center 25;'
        all_elements.extend(_overpass_query(query))

    return all_elements


def fetch_places_for_city(city_key: str, primary_categories: list, broad: bool = False) -> list:
    meta = CITY_META.get(city_key, CITY_META[DEFAULT_CITY])
    lat, lon = meta["lat"], meta["lon"]
    city_query = meta["query"]

    search_categories = list(dict.fromkeys(primary_categories))
    if broad:
        search_categories = list(
            dict.fromkeys(
                search_categories
                + ["indoor", "culture", "food", "outdoor", "nature", "walk", "evening", "nightlife", "wellness"]
            )
        )

    use_google = PLACES_PROVIDER == "google" or (
        PLACES_PROVIDER == "auto" and bool(GOOGLE_PLACES_API_KEY)
    )
    if use_google:
        google_venues = fetch_google_places(lat, lon, search_categories)
        if len(google_venues) >= 8:
            return google_venues
        # Partial Google results — continue to OSM to fill gaps
        if google_venues:
            elements = []
            venues = google_venues
            seen_names = {v["name"].lower() for v in venues}
        else:
            elements = []
            venues = []
            seen_names = set()
    else:
        elements = []
        venues = []
        seen_names = set()

    if not use_google or len(venues) < 8:
        if not elements:
            elements = _overpass_fetch(lat, lon, 4000, search_categories)

        # Enrich with Nominatim only when Overpass returned sparse results
        if len(elements) < 12:
            nominatim_terms = ["museum", "restaurant", "cafe", "park", "temple", "historic site"]
            for term in nominatim_terms:
                elements.extend(_nominatim_search(city_query, term, limit=4))
                time.sleep(1.05)

        for el in elements:
            venue = _normalize_element(el, lat, lon)
            if not venue:
                continue
            key = venue["name"].lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            venues.append(venue)

    venues.sort(key=lambda v: v["distance_km"])
    return venues[:50]
