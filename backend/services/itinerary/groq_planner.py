"""Groq organizes verified destination data into daily adventures — no invented places."""
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Set

from config import GROQ_API_KEY
from llm_json import parse_llm_json_response

logger = logging.getLogger(__name__)

_groq_client = None
try:
    from groq import Groq

    if GROQ_API_KEY:
        _groq_client = Groq(api_key=GROQ_API_KEY)
except Exception:
    pass

_FORBIDDEN_ACTIVITY_PHRASES = (
    "explore city",
    "highlight",
    "dinner district",
    "local attraction",
    "sightseeing",
    "city center",
    "near hotel",
    "tourist area",
    "main district",
    "downtown area",
)

SYSTEM_PROMPT = """You are a premium travel planner for AINomad.

You MUST use ONLY place names listed in destination_context.
Never invent attractions, neighborhoods, or restaurants.
Never use placeholders or generic labels.

Forbidden in any activity place field:
- Explore city
- {city} highlight
- Dinner district
- local attraction
- sightseeing
- generic "city center" without a proper name

Every activity "place" must be a SPECIFIC real venue from destination_context.

Plan realistically:
- Day 1: jet-lag friendly, near hotel area, easy pacing
- Middle days: landmarks, culture, food, shopping, neighborhoods
- Final day: relaxed, souvenirs, departure prep

Do not repeat the same location on consecutive days.
Return valid JSON only with a "days" array."""


def _trip_day_count(start_date: str, end_date: str) -> int:
    try:
        s = datetime.strptime(start_date[:10], "%Y-%m-%d")
        e = datetime.strptime(end_date[:10], "%Y-%m-%d")
        return max(1, (e - s).days + 1)
    except ValueError:
        return 5


def _all_context_places(ctx: Dict[str, List[str]]) -> List[str]:
    order = (
        "landmarks",
        "neighborhoods",
        "food_spots",
        "activities",
        "hidden_gems",
        "shopping_areas",
    )
    places: List[str] = []
    seen: Set[str] = set()
    for key in order:
        for p in ctx.get(key) or []:
            k = p.strip().lower()
            if k and k not in seen:
                seen.add(k)
                places.append(p.strip())
    return places


def _is_forbidden_place(place: str) -> bool:
    if not place:
        return True
    low = place.lower().strip()
    if any(p in low for p in _FORBIDDEN_ACTIVITY_PHRASES):
        return True
    if low.endswith(" highlight"):
        return True
    if re.match(r"^[a-z\s]{1,20}$", low) and "highlight" in low:
        return True
    return False


def _pick_place(pool: List[str], used: Set[str], offset: int) -> str:
    if not pool:
        return ""
    for i in range(len(pool)):
        candidate = pool[(offset + i) % len(pool)]
        if candidate.lower() not in used:
            return candidate
    return pool[offset % len(pool)]


def _fallback_days_from_context(
    destination: str,
    count: int,
    destination_context: Dict[str, List[str]],
    hotels: List[dict],
) -> List[dict]:
    """Build days only from Tavily-verified places — no generic filler."""
    landmarks = destination_context.get("landmarks") or []
    food = destination_context.get("food_spots") or []
    neighborhoods = destination_context.get("neighborhoods") or []
    activities = destination_context.get("activities") or []
    gems = destination_context.get("hidden_gems") or []
    shopping = destination_context.get("shopping_areas") or []

    pool = _all_context_places(destination_context)
    if not pool:
        return []

    hotel_area = (hotels[0].get("location") if hotels else destination) or destination
    used: Set[str] = set()
    days: List[dict] = []

    for i in range(count):
        is_first = i == 0
        is_last = i == count - 1
        day_places: List[str] = []

        if is_first:
            day_places.append(_pick_place(neighborhoods or pool, used, i))
            day_places.append(_pick_place(landmarks or pool, used, i + 1))
            day_places.append(_pick_place(food or pool, used, i + 2))
        elif is_last:
            day_places.append(_pick_place(shopping or neighborhoods or pool, used, i))
            day_places.append(_pick_place(gems or landmarks or pool, used, i + 1))
            day_places.append(_pick_place(food or pool, used, i + 2))
        else:
            day_places.append(_pick_place(landmarks or pool, used, i))
            day_places.append(_pick_place(activities or gems or pool, used, i + 1))
            day_places.append(_pick_place(neighborhoods or pool, used, i + 2))
            day_places.append(_pick_place(food or pool, used, i + 3))

        acts = []
        times = ("10:00 AM", "1:30 PM", "4:00 PM", "7:00 PM")
        for j, place in enumerate([p for p in day_places if p]):
            used.add(place.lower())
            detail = (
                f"Light visit after arrival; stay near {hotel_area}."
                if is_first and j == 0
                else (
                    "Souvenirs and relaxed pacing before departure."
                    if is_last and j == 0
                    else f"Pre-book tickets if required; allow transit time in {destination}."
                )
            )
            acts.append({"time": times[j % len(times)], "place": place, "details": detail})

        days.append({"day": f"Day {i + 1}", "activities": acts[:5]})

    return days


def _sanitize_days(
    days: List[dict],
    destination_context: Dict[str, List[str]],
    day_count: int,
    destination: str,
    hotels: List[dict],
) -> List[dict]:
    allowed = {p.lower(): p for p in _all_context_places(destination_context)}
    pool = list(allowed.values())
    used: Set[str] = set()
    clean: List[dict] = []

    for i, day in enumerate(days[:day_count]):
        if not isinstance(day, dict):
            continue
        activities = day.get("activities")
        if not isinstance(activities, list):
            continue
        fixed_acts = []
        for j, act in enumerate(activities):
            if not isinstance(act, dict):
                continue
            place = str(act.get("place") or "").strip()
            if _is_forbidden_place(place) or place.lower() not in allowed:
                replacement = _pick_place(pool, used, i * 4 + j)
                place = replacement or place
            if place:
                used.add(place.lower())
            fixed_acts.append(
                {
                    "time": str(act.get("time") or "10:00 AM"),
                    "place": place,
                    "details": str(act.get("details") or f"Visit {place}."),
                }
            )
        if fixed_acts:
            clean.append(
                {"day": str(day.get("day") or f"Day {i + 1}"), "activities": fixed_acts}
            )

    if len(clean) >= max(1, day_count - 1):
        return clean[:day_count]

    return _fallback_days_from_context(destination, day_count, destination_context, hotels)


def _fallback_days(destination: str, count: int, hotels: List[dict]) -> List[dict]:
    """Legacy entry — prefer context-driven fallback."""
    return []


def generate_daily_plan(
    destination: str,
    departure_location: str,
    start_date: str,
    end_date: str,
    budget: str,
    verified_context: Dict[str, Any],
) -> List[dict]:
    day_count = _trip_day_count(start_date, end_date)
    hotels = verified_context.get("hotels") or []
    destination_context = verified_context.get("destination_context") or {}

    if not _all_context_places(destination_context):
        logger.warning("[itinerary] Empty destination_context for %s", destination)
        return _fallback_days_from_context(destination, day_count, destination_context, hotels)

    if not _groq_client:
        return _fallback_days_from_context(destination, day_count, destination_context, hotels)

    context_json = json.dumps(destination_context, ensure_ascii=False, indent=2)
    hotels_json = json.dumps(
        [{"name": h.get("name"), "location": h.get("location")} for h in hotels[:3]],
        ensure_ascii=False,
    )

    user_prompt = f"""Plan exactly {day_count} days in {destination}.
Dates: {start_date} to {end_date}. Departing from {departure_location}. Budget: {budget}.

destination_context (ONLY use these place names in activities):
{context_json}

Hotel bases (for Day 1 proximity):
{hotels_json}

Create {day_count} days labelled Day 1 … Day {day_count}.
Each day: 3–5 activities. Each activity.place MUST match a name from destination_context exactly.

JSON:
{{
  "days": [
    {{ "day": "Day 1", "activities": [{{"time": "", "place": "", "details": ""}}] }}
  ]
}}
"""

    try:
        response = _groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.35,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content or ""
        parsed = parse_llm_json_response(raw)
        days = parsed.get("days") if isinstance(parsed.get("days"), list) else []

        if days:
            days = _sanitize_days(days, destination_context, day_count, destination, hotels)
            if days and len(days) >= max(1, day_count - 1):
                logger.info("[itinerary] Groq planned %d verified days", len(days))
                return days[:day_count] if len(days) > day_count else days
    except Exception as exc:
        logger.exception("[itinerary] Groq daily plan failed: %s", exc)

    return _fallback_days_from_context(destination, day_count, destination_context, hotels)
