"""AI-powered contextual explanations — Gemini (primary) or Groq (fallback)."""

import json
from typing import Optional

from config import GEMINI_API_KEY, GROQ_API_KEY

groq_client = None
gemini_client = None

try:
    from groq import Groq

    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
except Exception:
    pass

try:
    if GEMINI_API_KEY:
        from google import genai

        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    pass


def _fallback_why(venue: dict, ctx: dict) -> str:
    name = venue.get("name", "This spot")
    weather = ctx.get("weather", "clear")
    band = ctx.get("time_band", "afternoon").replace("_", " ")
    indoor = venue.get("indoor_outdoor", "indoor")
    archetype = ctx.get("archetype", "explorer")
    live = ctx.get("live_weather") or {}
    desc = live.get("description", weather)

    if weather == "rain" and indoor in ("indoor", "covered"):
        return f"{desc.capitalize()} tonight — {name} keeps you dry and fits a {band} visit."
    if weather == "clear" and indoor == "outdoor":
        return f"Clear {band} weather makes {name} worth the short trip right now."
    if weather == "snow" and indoor == "indoor":
        return f"Snow outside — {name} is a warm, {archetype}-friendly pick for {band}."
    if weather == "extreme_heat" and indoor == "indoor":
        return f"Heat advisory — {name} offers AC relief during this {band} window."
    if band == "late_night":
        return f"Late night in {ctx.get('city_display', 'town')} — {name} suits safe evening plans."
    return f"Strong match for {band} in {ctx.get('city_display', 'your city')} given your {archetype} style."


def _contrast_fallback(ctx: dict) -> str:
    weather = ctx.get("weather", "clear")
    band = ctx.get("time_band", "afternoon")
    if weather == "rain" and band in ("evening", "late_night"):
        return "Indoor-forward feed for rainy night hours — flip to clear + afternoon for outdoor picks."
    if weather == "clear" and band == "afternoon":
        return "Outdoor-forward feed — would pivot to cozy indoor if rain starts."
    if weather == "extreme_heat":
        return "Heat-aware picks favor shade and AC — evening outdoor options unlock later."
    return "Change city or traveler style to see the feed regenerate."


def _build_prompt(payload: dict) -> str:
    return f"""You are an expert travel concierge. Given this live context and ranked places, write:
1. moment_summary: one vivid headline (max 12 words)
2. contrast_note: one sentence on how this feed differs from opposite weather/time (max 25 words)
3. explanations: array of why_now strings, one per place in order (max 28 words each, mention weather/time/group/style)

Return ONLY valid JSON:
{{"moment_summary":"...","contrast_note":"...","explanations":["..."]}}

Context and places:
{json.dumps(payload, ensure_ascii=False)}"""


def _parse_ai_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _call_gemini(prompt: str) -> Optional[str]:
    if not gemini_client:
        return None
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.65, "max_output_tokens": 900},
        )
        return response.text
    except Exception:
        return None


def _call_groq(prompt: str) -> Optional[str]:
    if not groq_client:
        return None
    try:
        response = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            messages=[
                {"role": "system", "content": "You output strict JSON only. Be specific, warm, and contextual."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.65,
            max_tokens=900,
        )
        return response.choices[0].message.content
    except Exception:
        return None


def enrich_explanations(recommendations: list, ctx: dict, moment_summary: str) -> tuple[list, str, str]:
    """Return (recommendations with why_now, moment_summary, contrast_note)."""
    if not recommendations:
        return recommendations, moment_summary, "Adjust context above to regenerate picks."

    for rec in recommendations:
        if not rec.get("why_now"):
            rec["why_now"] = _fallback_why(rec, ctx)

    payload = {
        "context": {
            "city": ctx.get("city_display"),
            "time_band": ctx.get("time_band"),
            "hour": ctx.get("hour"),
            "weather": ctx.get("weather"),
            "live_weather": ctx.get("live_weather"),
            "group_size": ctx.get("group_size"),
            "archetype": ctx.get("archetype"),
            "activity_state": ctx.get("activity_state"),
            "budget_tier": ctx.get("budget_tier"),
        },
        "places": [
            {
                "name": r["name"],
                "categories": r.get("categories", []),
                "indoor_outdoor": r.get("indoor_outdoor"),
                "distance_km": r.get("distance_km"),
                "cost": r.get("cost"),
                "rating": r.get("rating"),
                "best_visiting_time": r.get("best_visiting_time"),
            }
            for r in recommendations
        ],
    }

    prompt = _build_prompt(payload)
    raw = _call_gemini(prompt) or _call_groq(prompt)

    if not raw:
        return recommendations, moment_summary, _contrast_fallback(ctx)

    try:
        parsed = _parse_ai_json(raw)
        explanations = parsed.get("explanations") or []
        for i, rec in enumerate(recommendations):
            if i < len(explanations) and explanations[i]:
                rec["why_now"] = explanations[i]
        return (
            recommendations,
            parsed.get("moment_summary") or moment_summary,
            parsed.get("contrast_note") or _contrast_fallback(ctx),
        )
    except Exception:
        return recommendations, moment_summary, _contrast_fallback(ctx)


def explanation_provider() -> str:
    if gemini_client:
        return "gemini"
    if groq_client:
        return "groq"
    return "template"
