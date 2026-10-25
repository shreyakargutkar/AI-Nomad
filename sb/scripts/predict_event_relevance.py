"""
Inference & Personalization Ranking Engine for Local Events & Cultural Intelligence.

Loads the trained `event_relevance_model.pkl` and ranks candidate events
according to traveler destination, travel dates, and personal interests.
"""

import os
import sys
import re
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(SB_ROOT, ".."))
MODEL_PATH = os.path.join(SB_ROOT, "models", "event_relevance_model.pkl")

# Include backend for classifier import
FESTIVALS_DIR = os.path.join(PROJECT_ROOT, "backend", "services", "festivals")
if FESTIVALS_DIR not in sys.path:
    sys.path.insert(0, FESTIVALS_DIR)

try:
    from classifier import TAXONOMY, classify_event, parse_requested_categories
except ImportError:
    TAXONOMY = {
        "ANIME_GAMING": "Anime & Gaming",
        "TECHNOLOGY": "Technology",
        "FOOD_DRINK": "Food & Drink",
        "CULTURE_MATSURI": "Culture & Matsuri",
        "ART_DESIGN": "Art & Design",
        "MUSIC_CONCERTS": "Music & Concerts",
        "SPORTS": "Sports",
    }
    classify_event = None
    parse_requested_categories = None

# Cached model instance
_MODEL = None

REFERENCE_TODAY = date(2026, 10, 24)


def load_event_model(model_path=MODEL_PATH):
    global _MODEL
    if _MODEL is not None and model_path == MODEL_PATH:
        return _MODEL
    if not os.path.isfile(model_path):
        raise FileNotFoundError(
            f"Event relevance model not found at {model_path}. "
            "Run sb/scripts/train_event_relevance_model.py first."
        )
    _MODEL = joblib.load(model_path)
    return _MODEL


def parse_date_safe(date_str):
    """Parses date string into date object or None."""
    if not date_str:
        return None
    if isinstance(date_str, date) and not isinstance(date_str, datetime):
        return date_str
    if isinstance(date_str, datetime):
        return date_str.date()
    
    s = str(date_str).strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %Y", "%b %Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            pass
    return None


def calculate_date_overlap(event_start, event_end, trip_start, trip_end):
    """
    Computes date overlap metric [0.0 - 1.0]:
      1.0 = Event is completely within the trip
      0.8 = Event partially overlaps trip
      0.4 = Event is within 3 days adjacent to trip
      0.05 = Event is outside the trip
    """
    if not trip_start or not trip_end or not event_start:
        return 0.75

    ev_end = event_end or event_start

    # Fully inside
    if trip_start <= event_start <= trip_end and trip_start <= ev_end <= trip_end:
        return 1.0

    # Overlaps
    if max(trip_start, event_start) <= min(trip_end, ev_end):
        return 0.8

    # Adjacent (within 3 days)
    days_gap = min(abs((event_start - trip_end).days), abs((trip_start - ev_end).days))
    if days_gap <= 3:
        return 0.4

    return 0.05


def compute_locality(event_city, event_country, target_city, target_country):
    """
    Returns (locality_score, distance_estimate_km)
    """
    c_event = (event_city or "").strip().lower()
    c_target = (target_city or "").strip().lower()

    if not c_target:
        return 1.0, 5.0

    if c_event and c_target and (c_target in c_event or c_event in c_target):
        return 1.0, 3.5

    # Check known aliases
    city_aliases = {
        "bombay": "mumbai",
        "poona": "pune",
        "bangalore": "bengaluru",
        "madras": "chennai",
        "calcutta": "kolkata",
    }
    c_ev_norm = city_aliases.get(c_event, c_event)
    c_tar_norm = city_aliases.get(c_target, c_target)
    if c_ev_norm == c_tar_norm:
        return 1.0, 3.5

    # State / Region matching (e.g. Maharashtra -> Mumbai, Pune)
    state_regions = {
        "maharashtra": ["mumbai", "pune", "nashik", "nagpur", "thane", "navi mumbai", "bombay", "poona"],
        "karnataka": ["bengaluru", "mysuru", "bangalore"],
        "tamil nadu": ["chennai", "coimbatore", "madras"],
        "delhi ncr": ["delhi", "new delhi", "noida", "gurugram", "gurgaon"],
        "ile-de-france": ["paris", "versailles", "saint-denis"],
        "île-de-france": ["paris", "versailles", "saint-denis"],
        "kansai": ["kyoto", "osaka", "kobe", "nara"],
        "kanto": ["tokyo", "yokohama", "chiba", "saitama"],
    }
    for region, cities in state_regions.items():
        if region in c_tar_norm and (c_ev_norm in cities or any(c in c_ev_norm for c in cities)):
            return 1.0, 5.0

    # Check known metro regions
    metro_regions = {
        "tokyo": ["shibuya", "shinjuku", "odaiba", "chiyoda", "akihabara", "roppongi", "ueno", "asakusa", "yokohama", "ginza", "harajuku", "taito"],
        "paris": ["montmartre", "marais", "latin quarter", "versailles", "saint-germain", "belleville", "la villette"],
        "kyoto": ["gion", "arashiyama", "fushimi", "higashiyama", "nakagyo", "kamigyo", "shimogyo"],
        "mumbai": ["bandra", "bkc", "andheri", "lower parel", "worli", "juhu", "colaba", "fort", "powai", "thane", "navi mumbai"],
        "pune": ["shivajinagar", "koregaon park", "kothrud", "kasba peth", "viman nagar", "baner", "pcmc", "pimpri"],
    }
    for base, suburbs in metro_regions.items():
        if base in c_tar_norm:
            if any(s in c_ev_norm for s in suburbs):
                return 0.95, 6.0

    cntry_event = (event_country or "").strip().lower()
    cntry_target = (target_country or "").strip().lower()

    if cntry_event and cntry_target and cntry_event == cntry_target:
        return 0.0, 75.0

    return 0.0, 110.0


def rank_events(candidate_events, user_profile, model_path=MODEL_PATH):
    """
    Ranks a list of candidate events (which have already passed Stage 1 Hard Filters).

    Args:
        candidate_events: list of dicts with (name, city, country, venue, start_date, end_date, categories, etc.)
        user_profile: dict with (city, country, start_date, end_date, interests, category)

    Returns:
        list of ranked events with appended `event_relevance_score`, `relevance_tier`, and `why_recommended`.
    """
    if not candidate_events:
        return []

    model = load_event_model(model_path)

    target_city = user_profile.get("city") or user_profile.get("destination_city") or ""
    target_country = user_profile.get("country") or user_profile.get("destination_country") or ""
    trip_start = parse_date_safe(user_profile.get("start_date"))
    trip_end = parse_date_safe(user_profile.get("end_date"))
    
    raw_interests = user_profile.get("interests") or ""
    raw_category = user_profile.get("category") or "all"

    # Requested categories
    requested_cats = set()
    if parse_requested_categories:
        req_set, is_all = parse_requested_categories(raw_category, raw_interests)
        requested_cats = req_set if not is_all else set(TAXONOMY.keys())
    else:
        requested_cats = set(TAXONOMY.keys())

    features_list = []
    enriched_events = []

    for ev in candidate_events:
        ev_start = parse_date_safe(ev.get("start_date"))
        ev_end = parse_date_safe(ev.get("end_date")) or ev_start

        # Categories
        cats = ev.get("categories") or [ev.get("category", "CULTURE_MATSURI")]
        primary_cat = cats[0] if cats else "CULTURE_MATSURI"
        if primary_cat not in TAXONOMY:
            primary_cat = "CULTURE_MATSURI"

        # Category Match
        category_match = 1.0 if (not requested_cats or bool(set(cats).intersection(requested_cats))) else 0.0

        # Locality & Distance
        locality, distance = compute_locality(
            ev.get("city"), ev.get("country"), target_city, target_country
        )
        if ev.get("distance_km") is not None:
            distance = float(ev["distance_km"])
            locality = 1.0 if distance <= 15.0 else (0.5 if distance <= 35.0 else 0.0)

        # Date Overlap
        date_overlap = calculate_date_overlap(ev_start, ev_end, trip_start, trip_end)

        # Days until event from today
        days_until = (ev_start - REFERENCE_TODAY).days if ev_start else 25
        days_until = max(1, days_until)

        # Granular Interest Match against user_profile['interests']
        user_int_lower = (raw_interests or "").lower()
        interest_tokens = [tok.strip() for tok in re.split(r"[,/&+]|\band\b", user_int_lower) if tok.strip()]
        event_text = f"{ev.get('name', '')} {ev.get('description', '')} {' '.join(cats)}".lower()

        score_boost = 0.0
        if interest_tokens:
            for tok in interest_tokens:
                if tok in ("food", "culinary", "wine", "dining", "gourmet", "tasting") and "FOOD_DRINK" in cats:
                    score_boost += 0.40
                elif tok in ("music", "concert", "jazz", "live music", "band", "live") and "MUSIC_CONCERTS" in cats:
                    score_boost += 0.40
                elif tok in ("art", "design", "museum", "gallery", "photography") and "ART_DESIGN" in cats:
                    score_boost += 0.40
                elif tok in ("tech", "technology", "ai", "software", "robotics") and "TECHNOLOGY" in cats:
                    score_boost += 0.40
                elif tok in ("anime", "gaming", "manga", "cosplay", "video games") and "ANIME_GAMING" in cats:
                    score_boost += 0.40
                elif tok in ("culture", "matsuri", "temple", "traditional", "festival") and "CULTURE_MATSURI" in cats:
                    score_boost += 0.40
                elif tok in event_text:
                    score_boost += 0.20

            interest_match = min(0.98, 0.40 + score_boost) if score_boost > 0 else 0.45
            user_int_sim = min(0.95, 0.35 + score_boost) if score_boost > 0 else 0.40
        else:
            interest_match = 0.85 if category_match == 1.0 else 0.20
            user_int_sim = 0.80 if category_match == 1.0 else 0.15

        popularity = int(ev.get("popularity", 8))
        source_rel = float(ev.get("source_reliability", 0.95 if ev.get("source_url") else 0.80))
        price_afford = float(ev.get("price_affordability", 0.9 if "free" in str(ev.get("price", "")).lower() else 0.75))
        duration = max(1, (ev_end - ev_start).days + 1) if (ev_start and ev_end) else 1

        row = {
            "category_match": float(category_match),
            "distance_from_destination": float(distance),
            "date_overlap": float(date_overlap),
            "days_until_event": int(days_until),
            "interest_match": float(interest_match),
            "event_category": primary_cat,
            "event_popularity": int(popularity),
            "event_source_reliability": float(source_rel),
            "event_locality": float(locality),
            "price_affordability": float(price_afford),
            "user_interest_similarity": float(user_int_sim),
            "event_duration": int(duration),
        }
        features_list.append(row)

        ev_copy = dict(ev)
        ev_copy["primary_category"] = primary_cat
        ev_copy["category_label"] = TAXONOMY.get(primary_cat, primary_cat)
        ev_copy["distance_km"] = distance
        ev_copy["date_overlap"] = date_overlap
        ev_copy["category_match"] = category_match
        enriched_events.append(ev_copy)

    # ML Inference
    df_features = pd.DataFrame(features_list)
    raw_scores = model.predict(df_features)

    for i, score in enumerate(raw_scores):
        clamped_score = int(round(float(np.clip(score, 0.0, 100.0))))
        ev = enriched_events[i]
        ev["event_relevance_score"] = clamped_score
        ev["relevance_score"] = clamped_score

        if clamped_score >= 80:
            ev["relevance_tier"] = "Top Match"
        elif clamped_score >= 60:
            ev["relevance_tier"] = "Recommended"
        elif clamped_score >= 40:
            ev["relevance_tier"] = "Moderate Match"
        else:
            ev["relevance_tier"] = "Low Relevance"

        # Deterministic rationale strictly referencing verified facts and matching category
        cat_label = ev["category_label"]
        venue_str = f"at {ev.get('venue')}" if ev.get("venue") else f"in {ev.get('city')}"
        if ev["category_match"] == 1.0:
            if ev["date_overlap"] >= 0.8:
                ev["why_recommended"] = (
                    f"Recommended because this verified {cat_label} event {venue_str} matches "
                    f"your interest and takes place during your {target_city or ev.get('city')} trip."
                )
            else:
                ev["why_recommended"] = (
                    f"Matches your interest in {cat_label} {venue_str}, closely aligning with your itinerary."
                )
        else:
            ev["why_recommended"] = f"General local event in {target_city or ev.get('city')}."

    # Sort descending by ML predicted relevance score
    enriched_events.sort(key=lambda x: x["event_relevance_score"], reverse=True)
    return enriched_events
