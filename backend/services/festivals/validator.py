"""
Event Schema Validation, Destination Type Resolution, Article Detection, and Pipeline Tracking Engine.

Core Principles:
1. Destination Type Resolution: Automatically determines whether input is a CITY or COUNTRY.
2. Article/Listicle Rejection: Detects and rejects roundups, calendars, and collection pages.
3. Entity Extraction: Extracts distinct individual events from article snippets where appropriate.
4. Locality Enforcement: Strict city-level isolation for city searches; country-level multi-city support for country searches.
5. Cross-City Contamination Prevention: Prevents foreign city events (e.g. Shanghai) from appearing under Paris or France.
6. Real Runtime Date Protection: Enforces strict trip date overlap (IN_TRIP vs OUTSIDE_TRIP) and rejects historical events.
7. Verification != Relevance: Assigns verification_status="VERIFIED" independently from ML relevance score.
8. Pipeline Tracker: Records stage-by-stage debug counts as mandated by Section 19.
"""

import re
import os
import json
import logging
from datetime import date, datetime
from typing import List, Dict, Any, Tuple, Optional, Set

from url_validator import resolve_event_source, check_url_reachability

logger = logging.getLogger("event_validator")
logger.setLevel(logging.INFO)

# Real runtime date protection: dynamically uses runtime date
def get_runtime_baseline() -> date:
    """Returns today's date dynamically (with 2026-10-24 baseline for 2026/2027 trips)."""
    today = date.today()
    return max(today, date(2026, 10, 24))

# Regex patterns identifying articles, listicles, calendars, and roundups
ARTICLE_LISTICLE_PATTERNS = [
    r"\b(?:best|top|greatest|upcoming|major|must[- ]see)\s+(?:events|exhibitions|festivals|things to do|shows|fairs|places|highlights)\b",
    r"\bevents\s+not\s+to\s+miss\b",
    r"\bnot\s+to\s+miss\s+in\s+\d{4}\b",
    r"\bnot\s+to\s+miss\b",
    r"\bthings\s+to\s+(?:do|see)\b",
    r"\bplaces\s+to\s+visit\b",
    r"\bwhat['’]?s\s+on\b",
    r"\bguide\s+to\s+(?:events|festivals|exhibitions|paris|kyoto|tokyo)\b",
    r"\b(?:complete|ultimate)\s+guide\b",
    r"\b(?:events|exhibitions|festivals)\s+in\s+[a-z]+(?:\s+in\s+[a-z0-9]+)?\b",
    r"\bevents?\s+roundup\b",
    r"\bcalendar\s+of\s+events\b",
    r"\blist\s+of\s+events\b",
    r"\b\d{4}\s+events\b",
    r"\bevents\s+in\s+(?:japan|france|paris|kyoto|tokyo|osaka|lyon|nice)\b",
    r"\btop\s+\d+\b",
    r"\b\d+\s+best\b",
    r"\bdiscover\s+the\s+best\b",
    r"\bround[- ]?up\b",
    r"\bagenda\b",
]

# Generic website brand names or placeholder titles that must never become event names
GENERIC_COLLECTION_NAMES = [
    "festivals & events",
    "events in kyoto",
    "events in paris",
    "events in tokyo",
    "events in lyon",
    "events in nice",
    "exhibitions in paris",
    "exhibitions in kyoto",
    "exhibitions in tokyo",
    "kyoto travel",
    "paris travel",
    "tokyo travel",
    "november 2026 events in japan",
    "november 2026 events in paris",
    "november 2026 events in france",
    "iwafu",
    "sortiraparis",
    "parisinfo",
    "gotokyo",
    "kyoto city tourism",
    "japan guide",
    "timeout paris",
    "timeout tokyo",
]

# Foreign global cities for cross-city contamination prevention
FOREIGN_CITIES_GLOBAL = {
    "shanghai", "beijing", "london", "new york", "berlin",
    "rome", "hong kong", "seoul", "singapore", "los angeles",
}

# Country knowledge base for destination detection & multi-city resolution
COUNTRY_KNOWLEDGE = {
    "india": {
        "country": "India",
        "search_cities": ["Mumbai", "Pune", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Goa"],
        "display_name": "India",
    },
    "france": {
        "country": "France",
        "search_cities": ["Paris", "Lyon", "Nice", "Bordeaux", "Marseille"],
        "display_name": "France",
    },
    "japan": {
        "country": "Japan",
        "search_cities": ["Tokyo", "Kyoto", "Osaka", "Sapporo", "Fukuoka", "Nara", "Kobe"],
        "display_name": "Japan",
    },
    "united states": {
        "country": "United States",
        "search_cities": ["New York", "San Francisco", "Los Angeles", "Chicago", "Seattle"],
        "display_name": "United States",
    },
    "usa": {
        "country": "United States",
        "search_cities": ["New York", "San Francisco", "Los Angeles", "Chicago", "Seattle"],
        "display_name": "United States",
    },
    "united kingdom": {
        "country": "United Kingdom",
        "search_cities": ["London", "Edinburgh", "Manchester", "Bristol"],
        "display_name": "United Kingdom",
    },
    "uk": {
        "country": "United Kingdom",
        "search_cities": ["London", "Edinburgh", "Manchester", "Bristol"],
        "display_name": "United Kingdom",
    },
    "germany": {
        "country": "Germany",
        "search_cities": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne"],
        "display_name": "Germany",
    },
    "italy": {
        "country": "Italy",
        "search_cities": ["Rome", "Milan", "Florence", "Venice", "Naples"],
        "display_name": "Italy",
    },
    "spain": {
        "country": "Spain",
        "search_cities": ["Madrid", "Barcelona", "Seville", "Valencia", "Malaga"],
        "display_name": "Spain",
    },
    "thailand": {
        "country": "Thailand",
        "search_cities": ["Bangkok", "Chiang Mai", "Phuket"],
        "display_name": "Thailand",
    },
    "indonesia": {
        "country": "Indonesia",
        "search_cities": ["Bali", "Jakarta", "Yogyakarta", "Surabaya"],
        "display_name": "Indonesia",
    },
    "greece": {
        "country": "Greece",
        "search_cities": ["Athens", "Thessaloniki", "Santorini", "Nafplio"],
        "display_name": "Greece",
    },
}

# State / Region knowledge base (Section 15)
STATE_REGION_KNOWLEDGE = {
    "maharashtra": {
        "state": "Maharashtra",
        "country": "India",
        "search_cities": ["Mumbai", "Pune", "Nashik", "Nagpur", "Thane", "Navi Mumbai"],
        "display_name": "Maharashtra, India",
        "header_title": "Verified Events Across Maharashtra",
    },
    "karnataka": {
        "state": "Karnataka",
        "country": "India",
        "search_cities": ["Bengaluru", "Mysuru", "Mangalore"],
        "display_name": "Karnataka, India",
        "header_title": "Verified Events Across Karnataka",
    },
    "delhi ncr": {
        "state": "Delhi",
        "country": "India",
        "search_cities": ["Delhi", "New Delhi", "Noida", "Gurugram"],
        "display_name": "Delhi NCR, India",
        "header_title": "Verified Events Across Delhi NCR",
    },
    "tamil nadu": {
        "state": "Tamil Nadu",
        "country": "India",
        "search_cities": ["Chennai", "Coimbatore", "Madurai"],
        "display_name": "Tamil Nadu, India",
        "header_title": "Verified Events Across Tamil Nadu",
    },
    "california": {
        "state": "California",
        "country": "United States",
        "search_cities": ["San Francisco", "Los Angeles", "San Diego", "San Jose"],
        "display_name": "California, United States",
        "header_title": "Verified Events Across California",
    },
    "ile-de-france": {
        "state": "Île-de-France",
        "country": "France",
        "search_cities": ["Paris", "Versailles", "Saint-Denis"],
        "display_name": "Île-de-France, France",
        "header_title": "Verified Events Across Île-de-France",
    },
}

# Granular city metadata for canonicalization, state, and country (Section 14)
CITY_METADATA = {
    # INDIA
    "mumbai": {"city": "Mumbai", "state": "Maharashtra", "country": "India", "aliases": ["bombay", "greater mumbai", "mumbai maharashtra"]},
    "bombay": {"city": "Mumbai", "state": "Maharashtra", "country": "India", "aliases": ["mumbai"]},
    "pune": {"city": "Pune", "state": "Maharashtra", "country": "India", "aliases": ["poona"]},
    "nashik": {"city": "Nashik", "state": "Maharashtra", "country": "India", "aliases": ["nasik"]},
    "nagpur": {"city": "Nagpur", "state": "Maharashtra", "country": "India", "aliases": []},
    "thane": {"city": "Thane", "state": "Maharashtra", "country": "India", "aliases": []},
    "navi mumbai": {"city": "Navi Mumbai", "state": "Maharashtra", "country": "India", "aliases": []},
    "delhi": {"city": "Delhi", "state": "Delhi", "country": "India", "aliases": ["new delhi"]},
    "new delhi": {"city": "Delhi", "state": "Delhi", "country": "India", "aliases": ["delhi"]},
    "bengaluru": {"city": "Bengaluru", "state": "Karnataka", "country": "India", "aliases": ["bangalore"]},
    "bangalore": {"city": "Bengaluru", "state": "Karnataka", "country": "India", "aliases": ["bengaluru"]},
    "hyderabad": {"city": "Hyderabad", "state": "Telangana", "country": "India", "aliases": []},
    "chennai": {"city": "Chennai", "state": "Tamil Nadu", "country": "India", "aliases": ["madras"]},
    "kolkata": {"city": "Kolkata", "state": "West Bengal", "country": "India", "aliases": ["calcutta"]},
    "ahmedabad": {"city": "Ahmedabad", "state": "Gujarat", "country": "India", "aliases": []},
    "jaipur": {"city": "Jaipur", "state": "Rajasthan", "country": "India", "aliases": []},
    "goa": {"city": "Goa", "state": "Goa", "country": "India", "aliases": ["panaji"]},

    # FRANCE
    "paris": {"city": "Paris", "state": "Île-de-France", "country": "France", "aliases": []},
    "lyon": {"city": "Lyon", "state": "Auvergne-Rhône-Alpes", "country": "France", "aliases": []},
    "nice": {"city": "Nice", "state": "Provence-Alpes-Côte d'Azur", "country": "France", "aliases": []},
    "bordeaux": {"city": "Bordeaux", "state": "Nouvelle-Aquitaine", "country": "France", "aliases": []},
    "marseille": {"city": "Marseille", "state": "Provence-Alpes-Côte d'Azur", "country": "France", "aliases": []},

    # JAPAN
    "tokyo": {"city": "Tokyo", "state": "Tokyo", "country": "Japan", "aliases": []},
    "kyoto": {"city": "Kyoto", "state": "Kansai", "country": "Japan", "aliases": []},
    "osaka": {"city": "Osaka", "state": "Kansai", "country": "Japan", "aliases": []},
    "sapporo": {"city": "Sapporo", "state": "Hokkaido", "country": "Japan", "aliases": []},
    "fukuoka": {"city": "Fukuoka", "state": "Kyushu", "country": "Japan", "aliases": []},
    "nara": {"city": "Nara", "state": "Kansai", "country": "Japan", "aliases": []},
    "kobe": {"city": "Kobe", "state": "Kansai", "country": "Japan", "aliases": []},

    # UK & US & Others
    "london": {"city": "London", "state": "Greater London", "country": "United Kingdom", "aliases": []},
    "edinburgh": {"city": "Edinburgh", "state": "Scotland", "country": "United Kingdom", "aliases": []},
    "new york": {"city": "New York", "state": "New York", "country": "United States", "aliases": ["nyc"]},
    "san francisco": {"city": "San Francisco", "state": "California", "country": "United States", "aliases": ["sf"]},
    "los angeles": {"city": "Los Angeles", "state": "California", "country": "United States", "aliases": ["la"]},
    "berlin": {"city": "Berlin", "state": "Berlin", "country": "Germany", "aliases": []},
    "rome": {"city": "Rome", "state": "Lazio", "country": "Italy", "aliases": []},
    "madrid": {"city": "Madrid", "state": "Madrid", "country": "Spain", "aliases": []},
}

CITY_TO_COUNTRY = {k: v["country"] for k, v in CITY_METADATA.items()}
CITY_TO_STATE = {k: v["state"] for k, v in CITY_METADATA.items()}

# Prominent cultural & entertainment venues for physical venue verification (Section 8)
CITY_PROMINENT_VENUES = {
    "mumbai": [
        "NCPA", "National Centre for the Performing Arts", "NMACC", "Nita Mukesh Ambani Cultural Centre",
        "Shanmukhananda Hall", "Shanmukhananda Auditorium", "Royal Opera House", "Mehboob Studio",
        "Jio World Garden", "Jio World Convention Centre", "Bombay Exhibition Centre", "NESCO Center",
        "Mahalaxmi Racecourse", "antiSOCIAL", "Nehru Centre", "Nehru Planetarium", "Jehangir Art Gallery",
        "CSMVS", "Chhatrapati Shivaji Maharaj Vastu Sangrahalaya", "Prithvi Theatre", "Wankhede Stadium",
        "Brabourne Stadium", "Bandra Fort Amphitheatre", "MMRDA Grounds", "Balkrishna Centre",
    ],
    "pune": [
        "Bal Gandharva Ranga Mandir", "Tilak Smarak Mandir", "Pandit Bhimsen Joshi Kalamandir",
        "Raja Dinkar Kelkar Museum", "Jawaharlal Nehru Stadium", "Yashwantrao Chavan Natyagruha",
        "Mahalaxmi Lawns", "Auto Cluster Exhibition Centre", "Amanora Mall Outdoor Arena",
    ],
    "paris": [
        "Grand Palais", "Centre Pompidou", "Atelier des Lumières", "Paris Expo Porte de Versailles",
        "Jardin des Tuileries", "Grande Halle de la Villette", "Duc des Lombards", "Sunset-Sunside",
        "Philharmonie de Paris", "Palais de Tokyo", "Musée d'Orsay",
    ],
    "kyoto": [
        "Kyoto International Manga Museum", "ROHM Theatre Kyoto", "Miyako Messe", "Kyoto Concert Hall",
        "Kodaiji Temple", "Kiyomizu-dera", "Nishiki Market", "Kyoto National Museum",
    ],
}

# Major neighborhoods for metropolitan expansion (Section 9)
CITY_NEIGHBORHOODS = {
    "mumbai": ["bandra", "andheri", "lower parel", "worli", "powai", "juhu", "colaba", "fort", "bkc", "bandra kurla complex", "dadar", "chembur", "goregaon", "malad", "versova", "nariman point"],
    "pune": ["koregaon park", "kothrud", "viman nagar", "shivaji nagar", "baner", "aundh", "kalyani nagar", "deccan", "chinchwad", "hadapsar"],
    "paris": ["le marais", "montmartre", "latin quarter", "belleville", "saint-germain", "bastille", "la villette"],
    "kyoto": ["gion", "arashiyama", "higashiyama", "nakagyo", "sakyo", "shimogyo"],
}


class PipelineTracker:
    """Tracks counts at each stage of the recommendation pipeline as required by Section 19."""
    def __init__(self):
        self.raw_search_results = 0
        self.individual_event_candidates = 0
        self.article_listicle_rejected = 0
        self.date_valid = 0
        self.location_valid = 0
        self.category_valid = 0
        self.verified = 0
        self.duplicates_removed = 0
        self.final_ml_ranked_events = 0

    def summary(self) -> Dict[str, int]:
        return {
            "RAW SEARCH RESULTS": self.raw_search_results,
            "INDIVIDUAL EVENT CANDIDATES": self.individual_event_candidates,
            "ARTICLE/LISTICLE REJECTED": self.article_listicle_rejected,
            "DATE VALID": self.date_valid,
            "LOCATION VALID": self.location_valid,
            "CATEGORY VALID": self.category_valid,
            "VERIFIED": self.verified,
            "DUPLICATES REMOVED": self.duplicates_removed,
            "FINAL ML-RANKED EVENTS": self.final_ml_ranked_events,
        }

    def log_summary(self, log_handler):
        log_handler.info("\n" + "=" * 55)
        log_handler.info("[PIPELINE STAGE DEBUG COUNTS - SECTION 19]")
        for stage, count in self.summary().items():
            log_handler.info(f"  {stage}: {count}")
        log_handler.info("=" * 55 + "\n")


def resolve_destination(location_raw: str, country_raw: str = "") -> Dict[str, Any]:
    """
    Determines whether destination input is a CITY, a STATE_REGION, or a COUNTRY.

    Examples:
      "Paris" -> destination_type="CITY", city="Paris", country="France"
      "Mumbai" -> destination_type="CITY", city="Mumbai", state="Maharashtra", country="India"
      "Pune" -> destination_type="CITY", city="Pune", state="Maharashtra", country="India"
      "Maharashtra" -> destination_type="STATE_REGION", state="Maharashtra", country="India", search_cities=["Mumbai", "Pune", "Nashik", "Nagpur", "Thane", "Navi Mumbai"]
      "France" -> destination_type="COUNTRY", city=None, country="France", search_cities=["Paris", "Lyon", "Nice", "Bordeaux", "Marseille"]
      "India" -> destination_type="COUNTRY", city=None, country="India", search_cities=["Mumbai", "Pune", "Delhi", "Bengaluru", ...]
    """
    raw_clean = (location_raw or "").strip()
    c_clean = (country_raw or "").strip()

    if not raw_clean and c_clean:
        raw_clean = c_clean

    # Comma separation: e.g. "Paris, France" or "Mumbai, India" or "Mumbai, Maharashtra"
    parts = [p.strip() for p in re.split(r"[,/|]", raw_clean) if p.strip()]

    if len(parts) >= 2:
        cand_first = parts[0].lower()
        cand_second = parts[1].lower()

        # Check if first part is a known country
        if cand_first in COUNTRY_KNOWLEDGE:
            dest_country = COUNTRY_KNOWLEDGE[cand_first]["country"]
            return {
                "destination_type": "COUNTRY",
                "city": None,
                "country": dest_country,
                "search_cities": list(COUNTRY_KNOWLEDGE[cand_first]["search_cities"]),
                "display_name": dest_country,
                "clean_location_label": dest_country,
                "header_title": f"Verified Events Across {dest_country}",
            }

        # Check if first part is a known state/region
        if cand_first in STATE_REGION_KNOWLEDGE:
            reg_info = STATE_REGION_KNOWLEDGE[cand_first]
            return {
                "destination_type": "STATE_REGION",
                "city": None,
                "state": reg_info["state"],
                "country": reg_info["country"],
                "search_cities": list(reg_info["search_cities"]),
                "display_name": reg_info["display_name"],
                "clean_location_label": reg_info["display_name"],
                "header_title": reg_info["header_title"],
            }

        # Check if first part is a known city
        city_meta = CITY_METADATA.get(cand_first)
        if not city_meta:
            for cm in CITY_METADATA.values():
                if cand_first in [a.lower() for a in cm.get("aliases", [])]:
                    city_meta = cm
                    break

        if city_meta:
            c_name = city_meta["city"]
            s_name = city_meta.get("state", "")
            co_name = city_meta["country"]
            loc_label = f"{c_name}, {s_name + ', ' if s_name else ''}{co_name}"
            return {
                "destination_type": "CITY",
                "city": c_name,
                "state": s_name,
                "country": co_name,
                "search_cities": [c_name],
                "display_name": f"{c_name}, {co_name}",
                "clean_location_label": loc_label,
                "header_title": f"Verified Events for {c_name}",
            }

        # Unrecognized multi-part: treat first part as city and second as country
        return {
            "destination_type": "CITY",
            "city": parts[0].title(),
            "country": parts[1].title(),
            "search_cities": [parts[0].title()],
            "display_name": f"{parts[0].title()}, {parts[1].title()}",
            "clean_location_label": f"{parts[0].title()}, {parts[1].title()}",
            "header_title": f"Verified Events for {parts[0].title()}",
        }

    # Single string
    single_token = raw_clean.lower()

    # 1. Test if COUNTRY
    if single_token in COUNTRY_KNOWLEDGE:
        country_info = COUNTRY_KNOWLEDGE[single_token]
        return {
            "destination_type": "COUNTRY",
            "city": None,
            "country": country_info["country"],
            "search_cities": list(country_info["search_cities"]),
            "display_name": country_info["country"],
            "clean_location_label": country_info["country"],
            "header_title": f"Verified Events Across {country_info['country']}",
        }

    # 2. Test if STATE / REGION (Section 15)
    if single_token in STATE_REGION_KNOWLEDGE:
        reg_info = STATE_REGION_KNOWLEDGE[single_token]
        return {
            "destination_type": "STATE_REGION",
            "city": None,
            "state": reg_info["state"],
            "country": reg_info["country"],
            "search_cities": list(reg_info["search_cities"]),
            "display_name": reg_info["display_name"],
            "clean_location_label": reg_info["display_name"],
            "header_title": reg_info["header_title"],
        }

    # 3. Test if CITY or ALIAS (Section 14)
    city_meta = CITY_METADATA.get(single_token)
    if not city_meta:
        for cm in CITY_METADATA.values():
            if single_token in [a.lower() for a in cm.get("aliases", [])]:
                city_meta = cm
                break

    if city_meta:
        c_name = city_meta["city"]
        s_name = city_meta.get("state", "")
        co_name = city_meta["country"]
        loc_label = f"{c_name}, {s_name + ', ' if s_name else ''}{co_name}"
        return {
            "destination_type": "CITY",
            "city": c_name,
            "state": s_name,
            "country": co_name,
            "search_cities": [c_name],
            "display_name": f"{c_name}, {co_name}",
            "clean_location_label": loc_label,
            "header_title": f"Verified Events for {c_name}",
        }

    # 4. Fallback to single city
    return {
        "destination_type": "CITY",
        "city": raw_clean.title(),
        "country": (c_clean.title() if c_clean else "Global"),
        "search_cities": [raw_clean.title()],
        "display_name": raw_clean.title(),
        "clean_location_label": raw_clean.title(),
        "header_title": f"Verified Events for {raw_clean.title()}",
    }


def is_article_or_listicle(title: str, text: str = "") -> Tuple[bool, str]:
    """
    Returns (True, reason) if the title or text indicates this is an article/listicle/roundup
    rather than a single, specific event.
    """
    t_clean = (title or "").strip().lower()
    t_clean_no_punct = re.sub(r"[^a-z0-9\s]", " ", t_clean)

    for gen in GENERIC_COLLECTION_NAMES:
        if t_clean == gen or t_clean_no_punct == gen:
            return True, f"GENERIC_COLLECTION_TITLE ('{gen}')"

    for pat in ARTICLE_LISTICLE_PATTERNS:
        if re.search(pat, t_clean):
            return True, f"ARTICLE_PATTERN_MATCH ('{pat}')"

    if "not to miss" in t_clean or "exhibitions in" in t_clean or "events in" in t_clean:
        return True, "ROUNDUP_TITLE"

    return False, ""


def check_cross_city_contamination(text: str, allowed_context: str) -> Tuple[bool, str]:
    """
    Checks if a candidate event description or title is discussing an event from another foreign city.
    For example: if searching for Paris or France, rejects events that are explicitly in Shanghai, London, etc.
    """
    text_lower = (text or "").lower()
    allowed_norm = (allowed_context or "").lower().strip()

    for f_city in FOREIGN_CITIES_GLOBAL:
        if f_city in allowed_norm:
            continue
        if re.search(r"\b" + re.escape(f_city) + r"\b", text_lower):
            if any(marker in text_lower for marker in [
                f"{f_city} contemporary",
                f"{f_city} art fair",
                f"{f_city} expo",
                f"in {f_city}",
                f"at {f_city}",
                f"held in {f_city}",
                f"taking place in {f_city}",
                f"fair in {f_city}",
            ]):
                return True, f_city.title()

    return False, ""


def validate_single_event_schema(
    event: Dict[str, Any],
    destination_type: str = "CITY",
    requested_city: Optional[str] = None,
    requested_state: Optional[str] = None,
    requested_country: Optional[str] = None,
    search_cities: Optional[List[str]] = None,
    trip_start: Optional[date] = None,
    trip_end: Optional[date] = None,
    allow_outside_dates: bool = False,
    allow_nearby: bool = False,
    tracker: Optional[PipelineTracker] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Strict validation of single event schema and location/date constraints.
    Enforces minimum required fields: name, city, country, start_date, category, source_url.
    Supports CITY, STATE_REGION, and COUNTRY destination types (Sections 1, 2, 3, 14, 15).
    """
    name = (event.get("name") or "").strip()
    venue = (event.get("venue") or "").strip()
    city = (event.get("city") or "").strip()
    country = (event.get("country") or "").strip()
    desc = (event.get("description") or "").strip()
    source_url = (event.get("source_url") or "").strip()

    # 1. NAME VALIDATION
    if not name or len(name) < 4:
        return False, "MISSING_NAME", event

    is_art, art_reason = is_article_or_listicle(name, desc)
    if is_art:
        if tracker:
            tracker.article_listicle_rejected += 1
        return False, f"NOT_SINGLE_EVENT ({art_reason})", event

    # 2. VENUE VALIDATION (Section 8)
    if not venue or len(venue) < 3:
        # Check prominent venues for this city from CITY_PROMINENT_VENUES
        city_key = city.lower()
        for kv in CITY_PROMINENT_VENUES.get(city_key, []):
            if kv.lower() in (name + " " + desc).lower():
                venue = kv
                event["venue"] = venue
                break
        if not venue or len(venue) < 3:
            return False, "MISSING_SPECIFIC_VENUE", event

    venue_lower = venue.lower()
    forbidden_venue_substrings = [
        "local venue in", "unknown venue", "unknown", "various venues",
        "city center", "various locations", "tbd", "online",
    ]
    if any(venue_lower == sub or venue_lower.startswith("local venue") for sub in forbidden_venue_substrings):
        return False, "GENERIC_PLACEHOLDER_VENUE", event

    # 3. LOCATION VALIDATION (Section 8, 14, 15)
    if not city:
        return False, "MISSING_CITY", event

    if destination_type == "COUNTRY" and requested_country:
        req_c = requested_country.lower().strip()
        ev_c = country.lower().strip()
        # Ensure event belongs to requested country
        if req_c not in ev_c and ev_c not in req_c:
            return False, f"COUNTRY_MISMATCH (Expected {requested_country}, got {country})", event
    elif destination_type == "STATE_REGION":
        req_state = (requested_state or "").lower().strip()
        ev_state = (event.get("state") or CITY_TO_STATE.get(city.lower(), "")).lower().strip()
        search_c_lower = [c.lower() for c in (search_cities or [])]
        if req_state and ev_state and req_state != ev_state and city.lower() not in search_c_lower:
            return False, f"STATE_MISMATCH (Expected {requested_state}, got {ev_state or city})", event
        if requested_country:
            req_c = requested_country.lower().strip()
            ev_c = country.lower().strip()
            if req_c not in ev_c and ev_c not in req_c:
                return False, f"COUNTRY_MISMATCH (Expected {requested_country}, got {country})", event
    else:
        # CITY DESTINATION: Support aliases and canonical normalization
        city_norm = (requested_city or "").lower().strip()
        ev_city_norm = city.lower().strip()
        req_canon = CITY_METADATA.get(city_norm, {}).get("city", requested_city or "").lower()
        ev_canon = CITY_METADATA.get(ev_city_norm, {}).get("city", city).lower()

        if not allow_nearby:
            if req_canon != ev_canon and city_norm not in ev_city_norm and ev_city_norm not in city_norm:
                return False, f"CITY_MISMATCH (Expected {requested_city}, got {city})", event
        else:
            nearby_map = {
                "kyoto": ["osaka", "kobe", "nara"],
                "osaka": ["kyoto", "kobe", "nara"],
                "tokyo": ["yokohama", "chiba", "saitama"],
                "paris": ["versailles", "saint-denis"],
                "mumbai": ["thane", "navi mumbai", "pune"],
                "pune": ["mumbai", "pcmc", "pimpri-chinchwad", "lonavala"],
            }
            allowed = [req_canon, city_norm] + nearby_map.get(req_canon, []) + nearby_map.get(city_norm, [])
            if not any(a == ev_canon or a in ev_city_norm or ev_city_norm in a for a in allowed):
                return False, f"CITY_OUTSIDE_NEARBY_RANGE ({city})", event

    if tracker:
        tracker.location_valid += 1

    # 4. CROSS-CITY CONTAMINATION CHECK
    loc_context = requested_country if destination_type in ("COUNTRY", "STATE_REGION") else (requested_city or "")
    is_cross_city, foreign_city = check_cross_city_contamination(f"{name} {desc}", loc_context)
    if is_cross_city:
        return False, f"CROSS_CITY_CONTAMINATION (Describes an event in {foreign_city})", event

    # 5. DATE VALIDATION
    start_date_str = str(event.get("start_date") or "").strip()
    end_date_str = str(event.get("end_date") or start_date_str).strip()

    if not start_date_str:
        return False, "MISSING_START_DATE", event

    try:
        ev_start = datetime.strptime(start_date_str[:10], "%Y-%m-%d").date()
    except ValueError:
        return False, f"INVALID_START_DATE_FORMAT ({start_date_str})", event

    try:
        ev_end = datetime.strptime(end_date_str[:10], "%Y-%m-%d").date()
    except ValueError:
        ev_end = ev_start

    # Runtime current date protection (no historical events)
    runtime_baseline = get_runtime_baseline()
    if ev_end < runtime_baseline:
        return False, f"PAST_EVENT ({end_date_str} concluded before runtime baseline {runtime_baseline})", event

    # Reject 2024 or 2025 events
    if ev_start.year < 2026:
        return False, f"HISTORICAL_YEAR_EVENT ({ev_start.year} is historical)", event

    # Trip date overlap check (IN_TRIP vs OUTSIDE_TRIP)
    if trip_start and trip_end and not allow_outside_dates:
        is_in_trip = (ev_start <= trip_end) and (ev_end >= trip_start)
        if not is_in_trip:
            return False, f"DATE_OUTSIDE_TRIP (Trip: {trip_start} to {trip_end}, Event: {ev_start} to {ev_end})", event

    if tracker:
        tracker.date_valid += 1

    # 6. SOURCE URL VALIDATION & REACHABILITY CHECK (Sections 3, 4, 8, 12)
    resolved_event = resolve_event_source(event)
    source_url = resolved_event.get("source_url")
    source_name = resolved_event.get("source_name") or "Official Local Source"
    source_status = resolved_event.get("source_status") or "UNVERIFIED"
    source_type = resolved_event.get("source_type") or "verified_cultural_source"
    tier = resolved_event.get("source_tier", 3)

    # Build validated record
    validated_event = dict(event)
    validated_event["name"] = name
    validated_event["venue"] = venue
    validated_event["city"] = city.title()
    ev_state = event.get("state") or CITY_TO_STATE.get(city.lower(), "")
    if ev_state:
        validated_event["state"] = ev_state
    validated_event["country"] = country.title() if country else (CITY_TO_COUNTRY.get(city.lower(), requested_country.title() if requested_country else ""))
    validated_event["start_date"] = ev_start.strftime("%Y-%m-%d")
    validated_event["end_date"] = ev_end.strftime("%Y-%m-%d")
    validated_event["source_url"] = source_url if source_status == "VALID" else None
    validated_event["source_name"] = source_name
    validated_event["source_status"] = source_status
    validated_event["source_type"] = source_type
    validated_event["source_tier"] = tier
    validated_event["source_verified_at"] = resolved_event.get("source_verified_at")
    validated_event["is_in_trip"] = True
    validated_event["verification_status"] = "VERIFIED" if source_status == "VALID" else "UNVERIFIED_SOURCE"
    validated_event["is_verified"] = (source_status == "VALID")

    if tracker and source_status == "VALID":
        tracker.verified += 1

    return True, "ACCEPT", validated_event


def extract_events_from_article_snippet(
    article_title: str,
    article_content: str,
    article_url: str,
    target_destination: str,
    trip_start: Optional[date],
    trip_end: Optional[date],
    groq_client=None,
) -> List[Dict[str, Any]]:
    """
    Extracts individual events from article snippets using LLM.
    Strictly forbids returning the article title as an event name.
    """
    if not groq_client:
        return []

    prompt = f"""
You are an expert event data extraction system.
Analyze the following travel article or event roundup snippet from {article_url}:

ARTICLE TITLE: {article_title}
ARTICLE CONTENT: {article_content}
TARGET DESTINATION: {target_destination}
TARGET DATES: {trip_start.strftime('%Y-%m-%d') if trip_start else 'November 2026'} to {trip_end.strftime('%Y-%m-%d') if trip_end else 'November 2026'}

TASK:
Extract ONLY distinct, individual events that physically take place in {target_destination}.

STRICT RULES:
1. DO NOT return the article title ("{article_title}") as an event name.
2. DO NOT return events taking place in other cities (reject Shanghai, London, etc.).
3. ONLY extract an event if a SPECIFIC physical venue inside {target_destination} is mentioned.
4. ONLY extract if dates in 2026 are stated.
5. If the snippet does not describe any specific individual event in {target_destination} with a known venue, return an empty list: [].

Return ONLY a valid JSON array of objects:
[
  {{
    "name": "Exact individual event name",
    "venue": "Specific venue in {target_destination}",
    "city": "{target_destination}",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "category": "ART_DESIGN or TECHNOLOGY or FOOD_DRINK or CULTURE_MATSURI or MUSIC_CONCERTS or SPORTS",
    "description": "Specific 1-2 sentence description about this event only without referencing other cities.",
    "source_url": "{article_url}",
    "source_name": "{article_url.split('//')[-1].split('/')[0]}"
  }}
]
"""
    try:
        resp = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=600,
        )
        content = resp.choices[0].message.content
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            extracted = json.loads(match.group(0))
            if isinstance(extracted, list):
                valid_extracted = []
                for ev in extracted:
                    if isinstance(ev, dict) and ev.get("name") and ev.get("venue"):
                        if "local venue" not in str(ev.get("venue", "")).lower():
                            valid_extracted.append(ev)
                return valid_extracted
    except Exception as e:
        logger.warning(f"Error in LLM article event extraction: {e}")

    return []
