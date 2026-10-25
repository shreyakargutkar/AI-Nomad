"""Geocode cities and resolve airport hints via OpenStreetMap Nominatim."""
import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "AINomad-Itinerary/1.0"


def geocode_place(query: str) -> Optional[Dict[str, Any]]:
    if not query or not str(query).strip():
        return None
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "q": str(query).strip(),
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=12,
        )
        if resp.status_code != 200:
            return None
        rows = resp.json()
        if not rows:
            return None
        row = rows[0]
        address = row.get("address") if isinstance(row.get("address"), dict) else {}
        return {
            "display_name": row.get("display_name"),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "country_code": (address.get("country_code") or "").upper(),
        }
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning("[itinerary] Geocode failed for %s: %s", query, exc)
        return None
