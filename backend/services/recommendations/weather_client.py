"""OpenWeatherMap integration — live weather + city-local time."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from config import WEATHER_API_KEY
OWM_URL = "https://api.openweathermap.org/data/2.5/weather"

CONDITION_MAP = {
    "clear": "clear",
    "clouds": "cloudy",
    "rain": "rain",
    "drizzle": "rain",
    "thunderstorm": "rain",
    "snow": "snow",
    "mist": "cloudy",
    "fog": "cloudy",
    "haze": "cloudy",
}


def normalize_condition(main: str, temp_c: float) -> str:
    key = (main or "").lower()
    if temp_c >= 32:
        return "extreme_heat"
    mapped = CONDITION_MAP.get(key, "cloudy")
    if mapped == "clear" and temp_c >= 28:
        return "extreme_heat"
    return mapped


def _local_datetime_from_owm(data: dict) -> datetime:
    """Convert OWM payload to city-local wall-clock time."""
    tz_offset = int(data.get("timezone", 0))
    dt_utc = datetime.fromtimestamp(data["dt"], tz=timezone.utc)
    return dt_utc + timedelta(seconds=tz_offset)


def city_local_now(timezone_name: str) -> datetime:
    """Fallback local time when weather API is unavailable."""
    return datetime.now(ZoneInfo(timezone_name))


def fetch_live_context(lat: float, lon: float, timezone_name: str) -> dict:
    """
    Fetch live weather and city-local time for coordinates.
    Time comes from OpenWeatherMap timezone offset (city-local, not server clock).
    """
    if not WEATHER_API_KEY:
        now = city_local_now(timezone_name)
        return {
            "condition": "cloudy",
            "description": "Weather API key not configured",
            "temp_c": None,
            "humidity": None,
            "wind_speed": None,
            "hour": now.hour,
            "minute": now.minute,
            "local_time": now.strftime("%H:%M"),
            "day_type": "weekend" if now.weekday() >= 5 else "weekday",
            "weekday_name": now.strftime("%A"),
            "source": "timezone_fallback",
            "weather_live": False,
        }

    try:
        resp = requests.get(
            OWM_URL,
            params={"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"},
            timeout=8,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Weather API returned {resp.status_code}")

        data = resp.json()
        main = (data.get("weather") or [{}])[0]
        temp = data.get("main", {}).get("temp", 20)
        condition = normalize_condition(main.get("main", "Clear"), temp)
        local_dt = _local_datetime_from_owm(data)

        return {
            "condition": condition,
            "description": main.get("description", condition),
            "temp_c": round(temp, 1),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "hour": local_dt.hour,
            "minute": local_dt.minute,
            "local_time": local_dt.strftime("%H:%M"),
            "day_type": "weekend" if local_dt.weekday() >= 5 else "weekday",
            "weekday_name": local_dt.strftime("%A"),
            "timezone_offset_sec": data.get("timezone"),
            "source": "openweathermap",
            "weather_live": True,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except (requests.RequestException, ValueError, KeyError, RuntimeError):
        now = city_local_now(timezone_name)
        return {
            "condition": "cloudy",
            "description": "Live weather temporarily unavailable",
            "temp_c": None,
            "humidity": None,
            "wind_speed": None,
            "hour": now.hour,
            "minute": now.minute,
            "local_time": now.strftime("%H:%M"),
            "day_type": "weekend" if now.weekday() >= 5 else "weekday",
            "weekday_name": now.strftime("%A"),
            "source": "timezone_fallback",
            "weather_live": False,
        }
