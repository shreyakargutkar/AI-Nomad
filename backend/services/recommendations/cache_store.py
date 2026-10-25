"""File-backed cache for places and recommendation responses."""

import json
import os
import time
from typing import Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "recommendations_cache")

PLACES_TTL = 60 * 60 * 24  # 24 hours
RESPONSE_TTL = 60 * 15  # 15 minutes


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _read_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: str, payload: dict):
    _ensure_cache_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def get_places(city_key: str) -> Optional[list]:
    path = os.path.join(CACHE_DIR, f"{city_key}_places.json")
    cached = _read_json(path)
    if not cached:
        return None
    if time.time() - cached.get("cached_at", 0) > PLACES_TTL:
        return None
    return cached.get("places")


def set_places(city_key: str, places: list):
    path = os.path.join(CACHE_DIR, f"{city_key}_places.json")
    _write_json(path, {"cached_at": time.time(), "places": places})


def get_response(fingerprint: str) -> Optional[dict]:
    path = os.path.join(CACHE_DIR, "responses.json")
    cached = _read_json(path) or {}
    entry = cached.get(fingerprint)
    if not entry:
        return None
    if time.time() - entry.get("cached_at", 0) > RESPONSE_TTL:
        return None
    return entry.get("payload")


def set_response(fingerprint: str, payload: dict):
    path = os.path.join(CACHE_DIR, "responses.json")
    cached = _read_json(path) or {}
    cached[fingerprint] = {"cached_at": time.time(), "payload": payload}
    if len(cached) > 200:
        oldest = sorted(cached.items(), key=lambda x: x[1].get("cached_at", 0))[:50]
        for key, _ in oldest:
            cached.pop(key, None)
    _write_json(path, cached)
