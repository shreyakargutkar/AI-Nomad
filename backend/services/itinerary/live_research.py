"""Tavily-backed factual research — flights, hotels, visa (Groq extracts only)."""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

from config import DEFAULT_PASSPORT_COUNTRY, GROQ_API_KEY
from geo_utils import geocode_place
from llm_json import parse_llm_json_response
from web_search import multi_search_snippets, tavily_search

logger = logging.getLogger(__name__)

_groq_client = None
try:
    from groq import Groq

    if GROQ_API_KEY:
        _groq_client = Groq(api_key=GROQ_API_KEY)
except Exception:
    pass

model_name = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
print("MODEL:", model_name)

EXTRACT_SYSTEM = (
    "You extract structured travel data from web search results ONLY. "
    "Return valid JSON only — no prose before or after. "
    "Never use the word 'unavailable', 'N/A', 'unknown', or 'TBD' in any field. "
    "If a detail is missing from sources, provide a realistic estimated range "
    "(e.g. price '₹52,000–₹68,000', time '10:45 AM', rating '4.5 ★'). "
    "Flights: departure and arrival MUST be 'City (CODE) - HH:MM AM/PM' format. "
    "Hotels: rating and price_per_night MUST be filled with numbers or ranges from sources or estimates. "
    "Do not assume visa is not required unless sources clearly state visa-free travel."
)

_BAD_TOKENS = frozenset(
    {
        "unavailable",
        "n/a",
        "na",
        "none",
        "null",
        "unknown",
        "tbd",
        "not available",
        "see reviews",
        "check booking",
        "verify live",
    }
)

_PRICE_RE = re.compile(
    r"(?:₹|INR|Rs\.?)\s*([\d,]+(?:\.\d+)?(?:\s*[–\-—to]+\s*[\d,]+(?:\.\d+)?)?)",
    re.IGNORECASE,
)
_USD_PRICE_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?(?:\s*[–\-—to]+\s*[\d,]+(?:\.\d+)?)?)",
    re.IGNORECASE,
)
_TIME_RE = re.compile(
    r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\b",
    re.IGNORECASE,
)
_AIRPORT_CODE_RE = re.compile(r"\(([A-Z]{3})\)")

_OUTBOUND_DEP_TIMES = ("10:45 AM", "11:30 PM", "6:15 AM", "9:20 PM")
_OUTBOUND_ARR_TIMES = ("6:30 AM", "2:15 PM", "7:45 AM", "11:50 PM")
_RETURN_DEP_TIMES = ("11:00 AM", "5:30 PM", "1:20 PM", "8:45 PM")
_RETURN_ARR_TIMES = ("8:15 PM", "11:40 PM", "6:05 AM", "3:30 PM")

_URL_RE = re.compile(r"https?://[^\s\]>\"')]+", re.IGNORECASE)

_AIRLINE_OFFICIAL_URLS: Dict[str, str] = {
    "singapore airlines": "https://www.singaporeair.com",
    "qatar airways": "https://www.qatarairways.com",
    "emirates": "https://www.emirates.com",
    "air india": "https://www.airindia.com",
    "indigo": "https://www.goindigo.in",
    "spicejet": "https://www.spicejet.com",
    "vistara": "https://www.airindia.com",
    "japan airlines": "https://www.jal.co.jp",
    "jal": "https://www.jal.co.jp",
    "ana": "https://www.ana.co.jp",
    "all nippon": "https://www.ana.co.jp",
    "cathay pacific": "https://www.cathaypacific.com",
    "thai airways": "https://www.thaiairways.com",
    "malaysia airlines": "https://www.malaysiaairlines.com",
    "etihad": "https://www.etihad.com",
    "british airways": "https://www.britishairways.com",
    "lufthansa": "https://www.lufthansa.com",
    "turkish airlines": "https://www.turkishairlines.com",
    "gulf air": "https://www.gulfair.com",
    "air asia": "https://www.airasia.com",
    "scoot": "https://www.flyscoot.com",
    "vietjet": "https://www.vietjetair.com",
    "sri lankan": "https://www.srilankan.com",
    "air france": "https://www.airfrance.com",
    "klm": "https://www.klm.com",
}

_BOOKING_DOMAIN_PRIORITY = (
    ("google.com/travel/flights", "google", "Google Flights"),
    ("skyscanner", "skyscanner", "Skyscanner"),
    ("makemytrip.com", "makemytrip", "MakeMyTrip"),
    ("booking.com/flights", "other", "Booking.com"),
    ("kayak.com", "other", "Kayak"),
)

DESTINATION_EXTRACT_SYSTEM = (
    "Extract ONLY real, named places from web search results. "
    "Return valid JSON only. Each entry must be a specific venue, landmark, neighborhood, or restaurant — "
    "never generic labels like 'city highlight', 'explore city', or 'local attraction'."
)

_FORBIDDEN_PLACE_PHRASES = (
    "explore city",
    "highlight",
    "dinner district",
    "local attraction",
    "sightseeing",
    "city center",
    "tourist area",
    "main district",
    "recommended stay",
    "top-rated stay",
    "option 1",
    "option 2",
    "near hotel",
    "downtown area",
)

_FAKE_HOTEL_PHRASES = (
    "top-rated stay",
    "recommended stay",
    "search top",
    "compare hotels",
    "option 1",
    "option 2",
    "hotel name",
    "real hotel name",
    "verify live",
    "see tripadvisor",
)

_HOTEL_TRUSTED_DOMAINS = (
    "booking.com",
    "tripadvisor",
    "marriott.com",
    "hilton.com",
    "hyatt.com",
    "ihg.com",
    "accor.com",
    "raffles.com",
    "mandarinoriental.com",
    "parkroyalhotels.com",
    "panpacific.com",
    "fullertonhotels.com",
    "mandarinoriental.com",
    "jal.co.jp",
    "apa-hotels.com",
    "gracery.com",
)


def _is_bad_value(val: Any) -> bool:
    if val is None:
        return True
    s = str(val).strip()
    if not s:
        return True
    low = s.lower()
    if low in _BAD_TOKENS:
        return True
    if "unavailable" in low:
        return True
    if low.startswith("verify") or low.startswith("check "):
        return True
    return False


def _clean_text(val: Any, fallback: str) -> str:
    if _is_bad_value(val):
        return fallback
    return str(val).strip()


def _harvest_prices_from_snippets(snippets: List[str]) -> List[str]:
    found: List[str] = []
    for blob in snippets:
        for m in _PRICE_RE.finditer(blob):
            raw = m.group(1).replace(",", "")
            try:
                num = int(float(raw.split("–")[0].split("-")[0].strip()))
                if 5000 <= num <= 500000:
                    found.append(f"₹{m.group(1).strip()}")
            except ValueError:
                continue
        for m in _USD_PRICE_RE.finditer(blob):
            found.append(f"${m.group(1).strip()} (convert to INR on booking site)")
    return found


def _harvest_urls_from_snippets(snippets: List[str]) -> List[str]:
    seen: set = set()
    urls: List[str] = []
    for blob in snippets:
        for m in _URL_RE.finditer(blob):
            url = m.group(0).rstrip(".,;:)")
            if url not in seen and _is_valid_url(url):
                seen.add(url)
                urls.append(url)
    return urls


def _is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    return u.startswith("http") and " " not in u and len(u) < 500


def _airport_code_from_field(route_field: str) -> str:
    m = _AIRPORT_CODE_RE.search(route_field or "")
    return m.group(1).upper() if m else ""


def _slug_airport(code: str, place: str) -> str:
    if code:
        return code.lower()
    mapping = {
        "india": "del",
        "japan": "tyo",
        "tokyo": "tyo",
        "mumbai": "bom",
        "delhi": "del",
        "singapore": "sin",
        "bangkok": "bkk",
        "dubai": "dxb",
        "london": "lon",
        "paris": "par",
    }
    p = (place or "").lower()
    for key, slug in mapping.items():
        if key in p:
            return slug
    return quote_plus((place or "city").split(",")[0].strip().lower())


def _google_flights_url(
    origin_code: str,
    dest_code: str,
    travel_date: str,
    origin_place: str,
    dest_place: str,
) -> str:
    date_part = (travel_date or "")[:10]
    if origin_code and dest_code and date_part:
        q = f"Flights from {origin_code} to {dest_code} on {date_part}"
    else:
        q = f"Flights from {origin_place} to {dest_place}"
    return f"https://www.google.com/travel/flights?q={quote_plus(q)}"


def _skyscanner_url(origin_code: str, dest_code: str, travel_date: str) -> str:
    o = _slug_airport(origin_code, "")
    d = _slug_airport(dest_code, "")
    date_part = (travel_date or "")[:10].replace("-", "")
    yymmdd = date_part[2:] if len(date_part) >= 8 else ""
    if yymmdd:
        return f"https://www.skyscanner.co.in/transport/flights/{o}/{d}/{yymmdd}/"
    return f"https://www.skyscanner.co.in/transport/flights/{o}/{d}/"


def _makemytrip_url(origin_place: str, dest_place: str) -> str:
    o = quote_plus(origin_place.split(",")[0].strip().lower().replace(" ", "-"))
    d = quote_plus(dest_place.split(",")[0].strip().lower().replace(" ", "-"))
    return f"https://www.makemytrip.com/international-flights/{o}-{d}-cheap-airtickets.html"


def _airline_official_url(airline: str) -> Optional[str]:
    low = (airline or "").lower().strip()
    for key, url in _AIRLINE_OFFICIAL_URLS.items():
        if key in low or low in key:
            return url
    return None


def _platform_from_url(url: str) -> str:
    low = url.lower()
    for domain, _kind, label in _BOOKING_DOMAIN_PRIORITY:
        if domain in low:
            return label
    for key in _AIRLINE_OFFICIAL_URLS:
        if _AIRLINE_OFFICIAL_URLS[key].replace("https://www.", "").split(".")[0] in low:
            return key.title()
    return "Book flight"


def _url_priority_score(url: str) -> int:
    low = url.lower()
    if any(
        airline_domain in low
        for airline_domain in (
            "singaporeair.com",
            "qatarairways.com",
            "emirates.com",
            "airindia.com",
            "jal.co.jp",
            "ana.co.jp",
            "goindigo.in",
            "cathaypacific.com",
            "gulfair.com",
        )
    ):
        return 0
    for domain, _kind, _label in _BOOKING_DOMAIN_PRIORITY:
        if domain in low:
            if "google.com/travel/flights" in low:
                return 1
            if "skyscanner" in low:
                return 2
            if "makemytrip" in low:
                return 3
    return 4


def _is_trusted_flight_url(url: str) -> bool:
    if not url:
        return False
    low = url.lower()
    
    # Block untrusted keywords/domains
    blocked_keywords = ["airtrfx.com", "affiliate", "adsystem", "clickserve", "doubleclick", "adroll", "partner", "promo", "redirect", "track", "click", "ad"]
    if any(k in low for k in blocked_keywords):
        return False
        
    # Check if official airline website
    for key, official_url in _AIRLINE_OFFICIAL_URLS.items():
        domain = official_url.replace("https://www.", "").replace("http://www.", "").replace("https://", "").replace("http://", "").split("/")[0]
        if domain in low:
            return True
            
    # Check if trusted booking platform
    trusted_platforms = ["google.com/travel/flights", "google.co.in/travel/flights", "skyscanner.co.in", "skyscanner.com", "makemytrip.com", "booking.com/flights", "kayak.com"]
    if any(p in low for p in trusted_platforms):
        return True
        
    return False


def _resolve_booking_url(
    f: dict,
    airline: str,
    departure_field: str,
    arrival_field: str,
    departure_place: str,
    destination_place: str,
    leg_index: int,
    start_date: str,
    end_date: str,
    url_hints: List[str],
) -> Tuple[str, str]:
    travel_date = end_date if leg_index == 1 else start_date
    origin_code = _airport_code_from_field(departure_field)
    dest_code = _airport_code_from_field(arrival_field)

    # 1. Prioritize official airline website mapping
    official = _airline_official_url(airline)
    if official:
        primary = airline.split("/")[0].strip()
        return official, primary or airline

    # 2. Check if the LLM provided booking URL is valid and trusted
    raw_url = f.get("booking_url")
    if _is_valid_url(str(raw_url or "")) and _is_trusted_flight_url(str(raw_url)):
        return str(raw_url).strip(), _clean_text(
            f.get("booking_platform"), _platform_from_url(str(raw_url))
        )

    # 3. Check url hints for a valid, trusted booking URL
    for hint in url_hints:
        if _is_valid_url(hint) and _is_trusted_flight_url(hint):
            return hint, _platform_from_url(hint)

    # 4. Fallback to Google Flights
    google = _google_flights_url(
        origin_code, dest_code, travel_date, departure_place, destination_place
    )
    return google, "Google Flights"


def _harvest_times_from_snippets(snippets: List[str]) -> List[str]:
    times: List[str] = []
    for blob in snippets:
        for m in _TIME_RE.finditer(blob):
            t = m.group(1).upper().replace("AM", " AM").replace("PM", " PM")
            t = re.sub(r"\s+", " ", t).strip()
            if t not in times:
                times.append(t)
    return times


def _airport_label(place: str, *, prefer_major: bool = True) -> str:
    p = (place or "").lower()
    mapping = [
        (("mumbai", "bombay"), "Mumbai (BOM)"),
        (("delhi", "new delhi"), "New Delhi (DEL)"),
        (("bangalore", "bengaluru"), "Bangalore (BLR)"),
        (("chennai", "madras"), "Chennai (MAA)"),
        (("hyderabad",), "Hyderabad (HYD)"),
        (("kolkata", "calcutta"), "Kolkata (CCU)"),
        (("tokyo",), "Tokyo Narita (NRT)"),
        (("osaka",), "Osaka Kansai (KIX)"),
        (("kyoto",), "Kyoto area (KIX)"),
        (("nagoya",), "Nagoya (NGO)"),
        (("sapporo",), "Sapporo (CTS)"),
        (("paris",), "Paris CDG (CDG)"),
        (("london",), "London Heathrow (LHR)"),
        (("dubai",), "Dubai (DXB)"),
        (("singapore",), "Singapore (SIN)"),
        (("bangkok",), "Bangkok (BKK)"),
    ]
    for keys, label in mapping:
        if any(k in p for k in keys):
            return label
    if "india" in p:
        return "New Delhi (DEL)"
    if "japan" in p:
        return "Tokyo Narita (NRT)"
    city = (place or "City").split(",")[0].strip() or "City"
    return f"{city} Airport"


def _extract_time_from_route_field(field: str) -> Optional[str]:
    if not field or " - " not in field:
        return None
    _, time_part = field.split(" - ", 1)
    time_part = time_part.strip()
    if _is_bad_value(time_part):
        return None
    m = _TIME_RE.search(time_part)
    return m.group(1) if m else time_part if _TIME_RE.fullmatch(time_part.strip()) else None


def _extract_airport_from_route_field(field: str) -> Optional[str]:
    if not field:
        return None
    left = field.split(" - ", 1)[0].strip()
    if _is_bad_value(left):
        return None
    m = _AIRPORT_CODE_RE.search(left)
    if m:
        return left
    if len(left) > 2:
        return left
    return None


def _repair_route_field(field: str, default_airport: str, default_time: str) -> str:
    airport = _extract_airport_from_route_field(field) or default_airport
    time_str = _extract_time_from_route_field(field) or default_time
    if _is_bad_value(airport):
        airport = default_airport
    if _is_bad_value(time_str):
        time_str = default_time
    return f"{airport} - {time_str}"


def _estimate_flight_price(
    departure: str, destination: str, leg_index: int, price_hints: List[str]
) -> str:
    if price_hints:
        return price_hints[leg_index % len(price_hints)]
    dep_l, dest_l = departure.lower(), destination.lower()
    if ("india" in dep_l or "delhi" in dep_l or "mumbai" in dep_l) and (
        "japan" in dest_l or "tokyo" in dest_l
    ):
        return ("₹52,000–₹68,000", "₹48,000–₹62,000")[leg_index % 2]
    return ("₹35,000–₹55,000", "₹32,000–₹50,000")[leg_index % 2]


def _estimate_hotel_rating(name: str, tier: str) -> str:
    low = (name or "").lower()
    if any(k in low for k in ("ritz", "four seasons", "mandarin", "peninsula", "st. regis")):
        return "4.9 ★"
    if any(k in low for k in ("hilton", "hyatt", "marriott", "sheraton", "westin")):
        return "4.6 ★"
    if any(k in low for k in ("mitsui garden", "dorsett", "okura")):
        return "4.5 ★"
    if "apa hotel" in low:
        return "4.1 ★"
    if tier == "luxury":
        return "4.7 ★"
    if tier == "budget":
        return "4.0 ★"
    return "4.4 ★"


def _estimate_hotel_price(destination: str, tier: str, name: str) -> str:
    low_name = (name or "").lower()
    dest = (destination or "").lower()
    if any(k in low_name for k in ("ritz", "four seasons", "mandarin", "hilton", "hyatt")):
        tier = "luxury"
    if "apa hotel" in low_name:
        tier = "budget"
    if "japan" in dest or "tokyo" in dest or "osaka" in dest or "kyoto" in dest:
        table = {
            "budget": "₹6,000–₹11,000",
            "mid-range": "₹12,000–₹22,000",
            "luxury": "₹28,000–₹45,000",
        }
    else:
        table = {
            "budget": "₹3,500–₹7,500",
            "mid-range": "₹8,000–₹16,000",
            "luxury": "₹22,000–₹48,000",
        }
    return table.get(tier, table["mid-range"])


def _finalize_flight(
    f: dict,
    departure: str,
    destination: str,
    start_date: str,
    end_date: str,
    leg_index: int,
    price_hints: List[str],
    time_hints: List[str],
    url_hints: Optional[List[str]] = None,
) -> dict:
    is_return = leg_index == 1
    origin_airport = _airport_label(destination if is_return else departure)
    dest_airport = _airport_label(departure if is_return else destination)

    dep_times = _RETURN_DEP_TIMES if is_return else _OUTBOUND_DEP_TIMES
    arr_times = _RETURN_ARR_TIMES if is_return else _OUTBOUND_ARR_TIMES
    default_dep_time = time_hints[leg_index * 2] if leg_index * 2 < len(time_hints) else dep_times[leg_index % len(dep_times)]
    default_arr_time = (
        time_hints[leg_index * 2 + 1]
        if leg_index * 2 + 1 < len(time_hints)
        else arr_times[leg_index % len(arr_times)]
    )

    airline = _clean_text(f.get("airline"), "Major international carrier")
    departure_field = _repair_route_field(
        str(f.get("departure") or ""),
        origin_airport,
        default_dep_time,
    )
    arrival_field = _repair_route_field(
        str(f.get("arrival") or ""),
        dest_airport,
        default_arr_time,
    )

    price = _clean_text(f.get("price"), "")
    if _is_bad_value(price) or price.lower().startswith("est."):
        price = _estimate_flight_price(departure, destination, leg_index, price_hints)
    if not price.startswith("₹") and "$" not in price and not re.search(r"\d", price):
        price = _estimate_flight_price(departure, destination, leg_index, price_hints)

    booking_url, platform = _resolve_booking_url(
        f,
        airline,
        departure_field,
        arrival_field,
        departure,
        destination,
        leg_index,
        start_date,
        end_date,
        url_hints or [],
    )
    platform = _clean_text(f.get("booking_platform"), platform)
    if platform.lower() in ("skyscanner / google flights", "skyscanner"):
        platform = _platform_from_url(booking_url)

    notes = _clean_text(
        f.get("notes"),
        (
            f"Usually 1-stop via hub; confirm {start_date} schedule on {platform}"
            if not is_return
            else f"Return {end_date}; allow buffer before departure"
        ),
    )

    if not _is_valid_url(booking_url):
        booking_url = _google_flights_url(
            _airport_code_from_field(departure_field),
            _airport_code_from_field(arrival_field),
            end_date if is_return else start_date,
            departure,
            destination,
        )

    return {
        "airline": airline,
        "departure": departure_field,
        "arrival": arrival_field,
        "price": price,
        "booking_platform": platform,
        "booking_url": booking_url,
        "notes": notes,
    }


def _hotel_official_url(
    h: dict, name: str, destination: str, url_hints: List[str]
) -> str:
    raw = h.get("official_url") or h.get("booking_url") or h.get("url")
    if _is_valid_url(str(raw or "")):
        return str(raw).strip()

    name_low = name.lower()
    for url in url_hints:
        if not _is_valid_url(url):
            continue
        low = url.lower()
        if any(d in low for d in _HOTEL_TRUSTED_DOMAINS):
            slug = re.sub(r"[^a-z0-9]", "", name_low.split()[0] if name_low else "")
            if slug and slug in low:
                return url
            if name_low.replace(" ", "")[:8] in low.replace("-", "").replace("_", ""):
                return url

    q = quote_plus(f"{name} {destination}")
    return f"https://www.booking.com/searchresults.html?ss={q}"


def _finalize_hotel(
    h: dict, destination: str, tier: str, url_hints: Optional[List[str]] = None
) -> Optional[dict]:
    name = str(h.get("name") or "").strip()
    if _is_fake_hotel_name(name):
        return None
    rating = _clean_text(h.get("rating"), "")
    if _is_bad_value(rating):
        rating = _estimate_hotel_rating(name, tier)
    elif "★" not in rating and "/" not in rating and "star" not in rating.lower():
        rating = f"{rating} ★" if re.search(r"\d", rating) else _estimate_hotel_rating(name, tier)

    price = _clean_text(h.get("price_per_night"), "")
    if _is_bad_value(price) or price.lower().startswith("est."):
        price = _estimate_hotel_price(destination, tier, name)
    elif price.strip().startswith("$") or re.match(r"^\s*\d+\s*[-–]", price):
        usd_match = _USD_PRICE_RE.search(price)
        if usd_match:
            parts = re.split(r"[–\-—to]+", usd_match.group(1))
            try:
                nums = [int(float(p.replace(",", "").strip())) for p in parts if p.strip()]
                if nums:
                    low_inr = nums[0] * 85
                    high_inr = (nums[-1] if len(nums) > 1 else nums[0]) * 85
                    price = f"₹{low_inr:,}–₹{high_inr:,}"
            except ValueError:
                price = _estimate_hotel_price(destination, tier, name)
    if not re.search(r"[\d₹$]", price):
        price = _estimate_hotel_price(destination, tier, name)
    if "unavailable" in price.lower():
        price = _estimate_hotel_price(destination, tier, name)

    location = _clean_text(h.get("location"), destination)
    if _is_bad_value(location):
        location = destination

    why = _clean_text(
        h.get("why_recommended"),
        "Well-reviewed for tourists; book early in peak season",
    )

    official_url = _hotel_official_url(h, name, destination, url_hints or [])

    return {
        "name": name,
        "rating": rating,
        "price_per_night": price,
        "location": location,
        "why_recommended": why,
        "official_url": official_url,
    }


def _pick_outbound_return(
    flights: List[dict], departure: str, destination: str
) -> List[dict]:
    if len(flights) <= 2:
        return flights
    dest_tokens = destination.lower().split()
    dep_tokens = departure.lower().split()
    outbound: Optional[dict] = None
    ret: Optional[dict] = None
    for f in flights:
        blob = f"{f.get('departure', '')} {f.get('arrival', '')}".lower()
        looks_out = any(t in blob for t in dest_tokens if len(t) > 3) or "nrt" in blob or "hnd" in blob
        looks_ret = any(t in blob for t in dep_tokens if len(t) > 3) or "del" in blob or "bom" in blob
        if looks_out and not outbound:
            outbound = f
        elif looks_ret and outbound is not f and not ret:
            ret = f
    if outbound and ret:
        return [outbound, ret]
    return flights[:2]


def _extract_from_research(
    kind: str,
    snippets: List[str],
    schema_example: str,
    system_prompt: Optional[str] = None,
) -> Optional[dict]:
    if not snippets:
        return None
    if not _groq_client:
        return None

    blob = "\n\n---\n\n".join(snippets[:6])
    prompt = f"""Extract {kind} using ONLY these web search results.
Return ONLY valid JSON matching the schema. No markdown fences or commentary.
Never use "unavailable" in any field — use realistic estimates when sources omit details.

{schema_example}

SEARCH RESULTS:
{blob}
"""

    try:
        resp = _groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt or EXTRACT_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        raw = resp.choices[0].message.content or ""
        return parse_llm_json_response(raw)
    except Exception as exc:
        logger.warning("[itinerary] Extraction failed (%s): %s", kind, exc)
        return None


def _is_valid_place_name(name: str) -> bool:
    if not name or not isinstance(name, str):
        return False
    s = name.strip()
    if len(s) < 3 or len(s) > 120:
        return False
    low = s.lower()
    if any(p in low for p in _FORBIDDEN_PLACE_PHRASES):
        return False
    if low.endswith(" highlight") or low.startswith("explore "):
        return False
    if re.fullmatch(r"[a-z\s]+", low) and len(s.split()) <= 2 and low in (
        "singapore",
        "japan",
        "tokyo",
        "india",
    ):
        return False
    return True


def _is_fake_hotel_name(name: str) -> bool:
    if not name:
        return True
    low = name.strip().lower()
    if any(p in low for p in _FAKE_HOTEL_PHRASES):
        return True
    if re.match(r"^(top|best|recommended|compare|search)\s", low):
        return True
    if "(option" in low:
        return True
    return False


def _dedupe_places(items: List[Any]) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for item in items or []:
        if not isinstance(item, str):
            continue
        s = item.strip()
        key = re.sub(r"\s+", " ", s.lower())
        if key in seen or not _is_valid_place_name(s):
            continue
        seen.add(key)
        out.append(s)
    return out


def _normalize_destination_context(raw: dict) -> Dict[str, List[str]]:
    keys = (
        "landmarks",
        "neighborhoods",
        "food_spots",
        "activities",
        "hidden_gems",
        "shopping_areas",
    )
    ctx: Dict[str, List[str]] = {k: [] for k in keys}
    if not isinstance(raw, dict):
        return ctx
    for key in keys:
        val = raw.get(key)
        if isinstance(val, list):
            ctx[key] = _dedupe_places(val)
    return ctx


def _destination_research_queries(destination: str, budget: str, duration: int) -> List[str]:
    dest = destination.strip()
    tier = budget if isinstance(budget, str) else "mid-range"
    year = datetime.now().year
    queries = [
        f"top tourist attractions in {dest} {year}",
        f"best neighborhoods in {dest} for tourists",
        f"must visit places in {dest}",
        f"top local food places in {dest} hawker centre restaurant",
        f"hidden gems in {dest}",
        f"best things to do in {dest} {tier} budget",
        f"best shopping areas in {dest}",
    ]
    low = dest.lower()
    if low in ("japan",) or low == "japan":
        queries.extend(
            [
                "top attractions Tokyo Japan landmarks",
                "top attractions Kyoto Japan temples shrines",
                "top attractions Osaka Japan Dotonbori",
                "best food Osaka Kyoto Tokyo Japan",
                "best neighborhoods Shibuya Ginza Kyoto Gion",
            ]
        )
    elif "shibuya" in low or ("tokyo" in low and len(dest.split()) <= 4):
        queries.extend(
            [
                "Shibuya Crossing Meiji Shrine Yoyogi Park things to do",
                "Harajuku Takeshita Street Shibuya restaurants",
                "best cafes bars Shibuya Tokyo",
            ]
        )
    elif "singapore" in low:
        queries.extend(
            [
                "Marina Bay Sands Gardens by the Bay Sentosa Singapore attractions",
                "Chinatown Little India Clarke Quay Singapore",
                "Maxwell Food Centre Lau Pa Sat Singapore hawker",
            ]
        )
    return queries


def build_destination_context(
    destination: str, budget: str, duration: int
) -> Dict[str, List[str]]:
    """Tavily-backed structured places — source of truth for daily adventures."""
    queries = _destination_research_queries(destination, budget, duration)
    snippets = multi_search_snippets(queries, max_results=8)

    extracted = _extract_from_research(
        "destination places",
        snippets,
        """{
  "landmarks": ["Marina Bay Sands", "Gardens by the Bay"],
  "neighborhoods": ["Chinatown", "Little India"],
  "food_spots": ["Maxwell Food Centre", "Lau Pa Sat"],
  "activities": ["Singapore River cruise", "Night Safari"],
  "hidden_gems": ["Haji Lane", "Haw Par Villa"],
  "shopping_areas": ["Orchard Road", "Bugis Street"]
}
Use only real place names found in sources. Minimum 3 items per non-empty category when sources allow.""",
        system_prompt=DESTINATION_EXTRACT_SYSTEM,
    )

    ctx = _normalize_destination_context(extracted or {})

    total = sum(len(ctx[k]) for k in ctx)
    if total < 8:
        logger.info("[itinerary] Destination context sparse (%d), retrying Tavily", total)
        retry_snippets = multi_search_snippets(
            [
                f"TripAdvisor things to do {destination}",
                f"Lonely Planet {destination} top sights restaurants neighborhoods",
                f"official tourism board {destination} attractions itinerary",
            ],
            max_results=8,
        )
        retry = _extract_from_research(
            "destination places",
            retry_snippets + snippets[:6],
            """{
  "landmarks": ["Marina Bay Sands", "Gardens by the Bay"],
  "neighborhoods": ["Chinatown", "Little India"],
  "food_spots": ["Maxwell Food Centre", "Lau Pa Sat"],
  "activities": ["Singapore River cruise", "Night Safari"],
  "hidden_gems": ["Haji Lane", "Haw Par Villa"],
  "shopping_areas": ["Orchard Road", "Bugis Street"]
}""",
            system_prompt=DESTINATION_EXTRACT_SYSTEM,
        )
        if retry:
            merged = _normalize_destination_context(retry)
            for key in ctx:
                ctx[key] = _dedupe_places(ctx[key] + merged.get(key, []))

    print("DESTINATION_CONTEXT:", {k: len(v) for k, v in ctx.items()})
    return ctx


def _budget_tier(budget: str) -> str:
    digits = re.sub(r"[^\d.]", "", str(budget or ""))
    if not digits:
        return "mid-range"
    try:
        amount = float(digits)
        if amount < 80000:
            return "budget"
        if amount > 250000:
            return "luxury"
        return "mid-range"
    except ValueError:
        return "mid-range"


def fetch_live_flights(
    departure: str, destination: str, start_date: str, end_date: str
) -> List[dict]:
    year = datetime.now().year
    queries = [
        f"best flights from {departure} to {destination} {start_date} {year}",
        f"cheap flights from {departure} to {destination} {start_date}",
        f"Google Flights {departure} to {destination} {start_date} price",
        f"Skyscanner {departure} to {destination} cheapest airlines",
        f"best airlines for {departure} to {destination} Qatar Emirates Air India Japan Airlines",
        f"return flights {destination} to {departure} {end_date} {year}",
    ]
    snippets = multi_search_snippets(queries, max_results=6)
    price_hints = _harvest_prices_from_snippets(snippets)
    time_hints = _harvest_times_from_snippets(snippets)
    url_hints = _harvest_urls_from_snippets(snippets)

    extracted = _extract_from_research(
        "flights",
        snippets,
        """{
  "flights": [
    {
      "airline": "Airline name from sources",
      "departure": "Origin City (CODE) - 10:45 AM",
      "arrival": "Dest City (CODE) - 6:30 AM",
      "price": "₹52,000–₹68,000 or exact fare from source",
      "booking_platform": "Singapore Airlines or Google Flights or Skyscanner",
      "booking_url": "https://official airline or Google Flights URL from sources",
      "notes": "layover or direct route note"
    }
  ]
}
Include booking_url from source URLs when present. Include outbound and return if available.""",
    )

    raw_flights: List[dict] = []
    if extracted and isinstance(extracted.get("flights"), list):
        for f in extracted["flights"]:
            if isinstance(f, dict) and (f.get("airline") or f.get("departure")):
                raw_flights.append(f)

    if len(raw_flights) < 2:
        answer = ""
        for q in queries[:3]:
            ans = tavily_search(q, max_results=5).get("answer") or ""
            if ans:
                answer = ans
                break
        if answer and _groq_client:
            extra = _extract_from_research(
                "exactly two flights: one outbound and one return",
                [answer] + snippets[:4],
                """{"flights": [
  {"airline":"","departure":"City (CODE) - HH:MM AM","arrival":"City (CODE) - HH:MM AM","price":"₹range","booking_platform":"","booking_url":"","notes":""},
  {"airline":"","departure":"City (CODE) - HH:MM AM","arrival":"City (CODE) - HH:MM AM","price":"₹range","booking_platform":"","booking_url":"","notes":""}
]}""",
            )
            if extra and isinstance(extra.get("flights"), list):
                for f in extra["flights"]:
                    if isinstance(f, dict):
                        raw_flights.append(f)

    raw_flights = _pick_outbound_return(raw_flights, departure, destination)

    flights: List[dict] = []
    for i, f in enumerate(raw_flights[:2]):
        flights.append(
            _finalize_flight(
                f,
                departure,
                destination,
                start_date,
                end_date,
                i,
                price_hints,
                time_hints,
                url_hints,
            )
        )

    if len(flights) == 1:
        flights.append(
            _finalize_flight(
                {
                    "airline": flights[0]["airline"],
                    "departure": "",
                    "arrival": "",
                    "price": "",
                    "booking_platform": flights[0]["booking_platform"],
                    "booking_url": flights[0].get("booking_url"),
                    "notes": "Return sector — confirm schedule on booking platform",
                },
                departure,
                destination,
                start_date,
                end_date,
                1,
                price_hints,
                time_hints,
                url_hints,
            )
        )

    if len(flights) < 2:
        logger.warning("[itinerary] Flight extraction sparse — using route estimates")
        flights = [
            _finalize_flight(
                {
                    "airline": "Qatar Airways / Air India / Japan Airlines",
                    "departure": "",
                    "arrival": "",
                    "price": "",
                    "booking_platform": "Skyscanner",
                    "notes": "Compare 1-stop via Doha or direct on Google Flights",
                },
                departure,
                destination,
                start_date,
                end_date,
                0,
                price_hints,
                time_hints,
                url_hints,
            ),
            _finalize_flight(
                {
                    "airline": "Return carrier (same alliance)",
                    "departure": "",
                    "arrival": "",
                    "price": "",
                    "booking_platform": "MakeMyTrip",
                    "notes": "Book round-trip for better fare",
                },
                departure,
                destination,
                start_date,
                end_date,
                1,
                price_hints,
                time_hints,
                url_hints,
            ),
        ]

    print("FLIGHTS:", flights)
    return flights[:2]


def _extract_hotels_from_snippets(
    snippets: List[str], destination: str, tier: str, url_hints: List[str]
) -> List[dict]:
    extracted = _extract_from_research(
        "hotels",
        snippets,
        """{
  "hotels": [
    {
      "name": "Marina Bay Sands",
      "rating": "4.7 ★",
      "price_per_night": "₹28,000–₹45,000",
      "location": "Marina Bay",
      "why_recommended": "Iconic skyline pool and bay views",
      "official_url": "https://www.marinabaysands.com"
    }
  ]
}
Return 5–8 REAL hotel names from sources only (e.g. Marina Bay Sands, Raffles Singapore). 
Include official_url from source URLs when present. Never invent placeholder names.""",
    )

    hotels: List[dict] = []
    if not extracted or not isinstance(extracted.get("hotels"), list):
        return hotels

    seen_names: set = set()
    for h in extracted["hotels"]:
        if not isinstance(h, dict):
            continue
        name = str(h.get("name") or "").strip()
        if not name or name.lower() in ("unavailable", "n/a", "real hotel name only"):
            continue
        key = name.lower()
        if key in seen_names or _is_fake_hotel_name(name):
            continue
        finalized = _finalize_hotel(h, destination, tier, url_hints)
        if finalized:
            seen_names.add(key)
            hotels.append(finalized)
    return hotels


def fetch_live_hotels(destination: str, budget: str) -> List[dict]:
    tier = _budget_tier(budget)
    year = datetime.now().year

    primary_queries = [
        f"best hotels in {destination} {year}",
        f"top hotels in {destination} TripAdvisor",
        f"Booking.com hotels in {destination} prices",
        f"official hotel websites {destination} luxury",
        f"best tourist hotels in {destination} Marina Bay Raffles",
    ]
    snippets = multi_search_snippets(primary_queries, max_results=8)
    url_hints = _harvest_urls_from_snippets(snippets)
    hotels = _extract_hotels_from_snippets(snippets, destination, tier, url_hints)

    if len(hotels) < 3:
        logger.info("[itinerary] Hotel count %d — retrying stronger Tavily queries", len(hotels))
        retry_queries = [
            f"TripAdvisor best hotels {destination} ranked",
            f"{destination} hotels Marina Bay Sands Raffles Fullerton Pan Pacific official site",
            f"top 10 hotels {destination} Booking.com TripAdvisor 2025 2026",
            f"Hilton Hyatt APA Hotel {destination} official website",
        ]
        if "japan" in destination.lower() or "tokyo" in destination.lower():
            retry_queries.extend(
                [
                    "Hilton Tokyo Mitsui Garden Ginza APA Hotel Shibuya Gracery Shinjuku",
                    "best hotels Tokyo Japan Booking.com official",
                ]
            )
        if "singapore" in destination.lower():
            retry_queries.extend(
                [
                    "Marina Bay Sands Raffles Singapore Pan Pacific PARKROYAL Fullerton hotel",
                    "best hotels Singapore TripAdvisor Booking.com",
                ]
            )
        retry_snippets = multi_search_snippets(retry_queries, max_results=8)
        url_hints = _harvest_urls_from_snippets(snippets + retry_snippets)
        more = _extract_hotels_from_snippets(
            snippets + retry_snippets, destination, tier, url_hints
        )
        seen = {h["name"].lower() for h in hotels}
        for h in more:
            if h["name"].lower() not in seen:
                seen.add(h["name"].lower())
                hotels.append(h)

    hotels = hotels[:5]
    if len(hotels) < 3:
        logger.warning(
            "[itinerary] Only %d verified hotels for %s (no placeholders added)",
            len(hotels),
            destination,
        )

    print("HOTELS:", hotels)
    return hotels


def fetch_live_visa(passport_country: str, destination: str) -> dict:
    year = datetime.now().year
    queries = [
        f"tourist visa for {passport_country} passport holders to {destination} {year}",
        f"{passport_country} citizens visa requirements travel {destination} embassy",
        f"do {passport_country} passport need visa for {destination} tourism official",
    ]
    snippets = multi_search_snippets(queries, max_results=8)

    extracted = _extract_from_research(
        "visa",
        snippets,
        """{
  "required": true,
  "processing_time": "",
  "cost": "",
  "documents_needed": [],
  "travel_notes": ""
}""",
    )

    if extracted and isinstance(extracted, dict):
        docs = extracted.get("documents_needed")
        if not isinstance(docs, list):
            docs = []
        required = extracted.get("required")
        if isinstance(required, str):
            required = required.lower() in ("true", "yes", "required")
        if required is None:
            required = True

        visa = {
            "required": bool(required),
            "processing_time": str(extracted.get("processing_time") or "Verify with embassy"),
            "cost": str(extracted.get("cost") or "Verify official fee"),
            "documents_needed": docs or ["Valid passport", "Visa application if required"],
            "travel_notes": str(
                extracted.get("travel_notes") or extracted.get("notes") or ""
            ),
            "source": "tavily",
        }
        return visa

    # Honest fallback when Tavily/Groq extraction fails
    return {
        "required": True,
        "processing_time": "Typically 5–15 working days for tourist visa (verify embassy)",
        "cost": "Verify current fee on official embassy / VFS site",
        "documents_needed": [
            "Valid passport (6+ months validity)",
            "Completed visa application",
            "Recent photographs",
            "Flight & hotel proof",
            "Financial proof",
        ],
        "travel_notes": (
            f"{passport_country} passport holders usually need a tourist visa for {destination}. "
            "Confirm on official embassy website before travel."
        ),
        "source": "fallback",
    }


def build_verified_context(
    departure_location: str,
    destination: str,
    start_date: str,
    end_date: str,
    budget: str,
    passport_country: Optional[str] = None,
    duration: Optional[int] = None,
) -> Dict[str, Any]:
    passport = passport_country or DEFAULT_PASSPORT_COUNTRY
    logger.info(
        "[itinerary] Tavily research: %s (%s) → %s (%s to %s)",
        passport,
        departure_location,
        destination,
        start_date,
        end_date,
    )

    if duration is None:
        try:
            s = datetime.strptime(start_date[:10], "%Y-%m-%d")
            e = datetime.strptime(end_date[:10], "%Y-%m-%d")
            duration = max(1, (e - s).days + 1)
        except ValueError:
            duration = 5

    destination_context = build_destination_context(destination, budget, duration)
    flights = fetch_live_flights(departure_location, destination, start_date, end_date)
    hotels = fetch_live_hotels(destination, budget)
    visa = fetch_live_visa(passport, destination)

    print("Flights found:", len(flights))
    print("Hotels found:", len(hotels))
    print("Visa:", visa)

    return {
        "flights": flights,
        "hotels": hotels,
        "visa_details": visa,
        "passport_country": passport,
        "destination_context": destination_context,
        "geo": {
            "destination": geocode_place(destination),
            "departure": geocode_place(departure_location),
        },
    }
