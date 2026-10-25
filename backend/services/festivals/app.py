import os
import sys
import re
import json
import logging
from datetime import datetime, date
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Allow importing predict_event_relevance from sb/scripts/
_SB_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "sb", "scripts"))
if _SB_SCRIPTS not in sys.path:
    sys.path.insert(0, _SB_SCRIPTS)

try:
    from predict_event_relevance import rank_events, parse_date_safe
except Exception as _import_err:
    logging.warning("Could not import predict_event_relevance: %s", _import_err)
    rank_events = None
    parse_date_safe = None

from classifier import (
    TAXONOMY,
    classify_event,
    parse_requested_categories,
    matches_category,
)
from live_events import discover_events
from validator import (
    resolve_destination,
    get_runtime_baseline,
    PipelineTracker,
)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"), override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cultural_intelligence")

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    groq_client = None


def generate_llm_explanations(valid_ranked_events, user_profile, requested_categories_labels):
    """
    Calls Groq ONLY to explain why the verified events are recommended.
    STRICT CONSTRAINT:
      - Must reference the ACTUAL matching category.
      - NEVER invent an anime/gaming or fictional connection for non-matching events.
      - Never invent dates, locations, or fictional events.
    """
    if not groq_client or not valid_ranked_events:
        return valid_ranked_events

    dest_label = user_profile.get("label") or user_profile.get("city") or user_profile.get("country", "")
    interests = user_profile.get("interests", "")
    category_context = ", ".join(requested_categories_labels) if requested_categories_labels else "Local Culture"

    events_summary = [
        {
            "id": i,
            "name": e["name"],
            "category": e.get("category_label") or e.get("category", ""),
            "venue": e.get("venue", ""),
            "city": e.get("city", ""),
            "country": e.get("country", ""),
            "dates": f"{e.get('start_date')} to {e.get('end_date')}",
        }
        for i, e in enumerate(valid_ranked_events[:5])
    ]

    prompt = f"""
You are AI-Nomad's Cultural Intelligence travel assistant.
The traveler is visiting {dest_label}.
Traveler selected interest/category: {category_context} ({interests})

Here are verified local events that have PASSED all hard category, date, and locality filters:
{json.dumps(events_summary, indent=2)}

For each event, write a single concise, engaging sentence explaining why it is recommended specifically for someone interested in {category_context} visiting {dest_label}.

STRICT RULES:
1. You must reference the ACTUAL verified category ({category_context}).
2. NEVER invent an anime or gaming connection if the event is not an anime/gaming event.
3. Only reference the verified facts provided above. Do NOT invent dates, ticket prices, venues, or events.
4. Return a valid JSON object mapping event ID (as string "0", "1", etc.) to the explanation sentence.
Example:
{{
  "0": "Recommended because this verified art exhibition at Grand Palais matches your passion for visual arts during your Paris trip.",
  "1": "Matches your interest in culinary culture with autumn street food tastings in Chuo City."
}}
"""
    try:
        resp = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )
        content = resp.choices[0].message.content
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            explanations = json.loads(match.group(0))
            for i, ev in enumerate(valid_ranked_events[:5]):
                str_id = str(i)
                if str_id in explanations and explanations[str_id]:
                    ev["why_recommended"] = explanations[str_id].strip()
    except Exception as e:
        logger.warning(f"Groq explanation generator failed (using verified ML template): {e}")

    return valid_ranked_events


@app.route("/api/festivals", methods=["POST"])
def find_festivals():
    data = request.get_json() or {}

    location_raw = data.get("location") or data.get("destination") or data.get("city") or ""
    country_raw = data.get("country") or ""
    start_date = data.get("start_date") or ""
    end_date = data.get("end_date") or ""
    interests = data.get("interests") or ""
    category = data.get("category") or "all"
    allow_outside_dates = bool(data.get("allow_outside_dates", False))
    allow_nearby = bool(data.get("allow_nearby", False))

    if not location_raw.strip() and not country_raw.strip():
        return jsonify({"error": "Destination is required"}), 400

    # 1. DESTINATION TYPE DETECTION & RESOLUTION (Section 1, 2, 3)
    dest_info = resolve_destination(location_raw, country_raw)
    dest_type = dest_info.get("destination_type", "CITY")
    city = dest_info.get("city")
    country = dest_info.get("country", "")
    clean_label = dest_info.get("clean_location_label") or dest_info.get("display_name") or (city or country or "Destination")
    header_title = dest_info.get("header_title") or f"Verified Events for {clean_label}"

    # =========================================================================
    # STAGE 1: HARD FILTERS (DATE, LOCATION, CATEGORY)
    # =========================================================================

    # 1.1 STRICT DATE VALIDATION (Never allow past dates - Section 6, 7)
    runtime_today = get_runtime_baseline()
    parsed_start = None
    if start_date:
        try:
            parsed_start = datetime.strptime(start_date[:10], "%Y-%m-%d").date()
        except ValueError:
            pass

    if parsed_start and parsed_start < runtime_today:
        return jsonify({
            "error": f"The selected date ({start_date}) is in the past. Cultural Intelligence provides real-time event discovery for upcoming travel. Please select a current or upcoming date (current date baseline: {runtime_today.strftime('%B %Y')}).",
            "is_past_date": True,
            "events": [],
            "total_found": 0,
        }), 400

    # Initialize Debug Pipeline Tracker (Section 19)
    tracker = PipelineTracker()

    # 1.2 PARSE REQUESTED CATEGORIES FROM USER INPUT (Section 9, 10, 11, 12)
    requested_categories, is_all_categories = parse_requested_categories(category, interests)
    requested_labels = [TAXONOMY.get(c, c) for c in requested_categories]

    logger.info(
        f"\n=================================================================\n"
        f"[PIPELINE START] Destination: {clean_label} (Type: {dest_type}) | Dates: {start_date} to {end_date}\n"
        f"User Input Category: '{category}' | Interests: '{interests}'\n"
        f"Parsed Taxonomy Constraints: {requested_labels} (is_all={is_all_categories})\n"
        f"================================================================="
    )

    # 1.3 DISCOVER CANDIDATE EVENTS (Live Tavily Search + Verified Registry)
    raw_candidates = discover_events(
        destination_info=dest_info,
        start_date=start_date,
        end_date=end_date,
        interests=interests,
        category=category,
        allow_outside_dates=allow_outside_dates,
        allow_nearby=allow_nearby,
        tracker=tracker,
    )

    # 1.4 APPLY HARD CATEGORY CONSTRAINT WITH DEBUG LOGGING (Section 10, 11)
    valid_events = []

    for ev in raw_candidates:
        ev_name = ev.get("name", "Unknown Event")
        ev_raw_cat = ev.get("category", "")
        ev_cats = ev.get("categories") or [ev_raw_cat]
        ev_conf = float(ev.get("category_confidence", 0.85))

        # Check Category Match
        category_match = is_all_categories or matches_category(
            ev_cats, ev_conf, requested_categories, confidence_threshold=0.55
        )

        decision = "ACCEPT" if category_match else "REJECT"
        reason_str = "" if category_match else f"\nREASON:\nCATEGORY_MISMATCH (Requested: {list(requested_categories)})"

        logger.info(
            f"\n[PIPELINE CANDIDATE EVALUATION]\n"
            f"EVENT:\n{ev_name}\n"
            f"TYPE:\nINDIVIDUAL_EVENT\n"
            f"CITY:\n{ev.get('city')}\n"
            f"VENUE:\n{ev.get('venue')}\n"
            f"DATE:\nverified ({ev.get('start_date')} to {ev.get('end_date')})\n"
            f"CATEGORY:\n{ev.get('category')} {ev_cats}\n"
            f"CITY_MATCH:\nTRUE\n"
            f"DATE_MATCH:\nTRUE\n"
            f"CATEGORY_MATCH:\n{'TRUE' if category_match else 'FALSE'}\n"
            f"DECISION:\n{decision}"
            f"{reason_str}"
        )

        if category_match:
            tracker.category_valid += 1
            valid_events.append(ev)

    logger.info(f"[PIPELINE FILTER RESULT] {len(valid_events)} of {len(raw_candidates)} events survived Stage 1 Hard Filters.")

    # 1.5 ZERO-MATCH BEHAVIOR (Section 18, 20)
    # If no verified events survive the hard category filter, NEVER fall back to unrelated events!
    if not valid_events:
        cat_display = " & ".join(requested_labels) if not is_all_categories else "local"
        logger.info(f"[ZERO MATCH] No verified {cat_display} events in {clean_label} for {start_date} to {end_date}.")
        tracker.log_summary(logger)
        return jsonify({
            "events": [],
            "total_found": 0,
            "message": f"No verified {cat_display} events were found in {clean_label} for your selected dates.",
            "destination": {"city": city, "state": dest_info.get("state", ""), "country": country, "type": dest_type, "label": clean_label},
            "header_title": header_title,
            "dates": {"start_date": start_date, "end_date": end_date},
            "interests": interests,
            "category": category,
            "requested_categories": list(requested_categories),
            "pipeline_debug_counts": tracker.summary(),
            "can_show_outside_dates": True,
            "can_show_nearby": True,
            "can_show_all_categories": True,
        })

    # =========================================================================
    # STAGE 2: ML PERSONALIZED RANKING (ONLY on Stage 1 surviving events!)
    # =========================================================================
    user_profile = {
        "city": city or "",
        "state": dest_info.get("state", ""),
        "country": country or "",
        "destination_type": dest_type,
        "label": clean_label,
        "start_date": start_date,
        "end_date": end_date,
        "interests": interests,
        "category": category,
    }

    if rank_events is not None:
        try:
            ranked_events = rank_events(valid_events, user_profile)
            ranking_source = "ml_event_relevance_model"
            for ev in ranked_events:
                logger.info(f"  → [ML RANKED] {ev.get('name')}: {ev.get('event_relevance_score')}% ({ev.get('relevance_tier')})")
        except Exception as ml_err:
            logger.warning(f"ML ranking failed, falling back to heuristic sorting: {ml_err}")
            ranked_events = valid_events
            ranking_source = "heuristic_fallback"
    else:
        ranked_events = valid_events
        ranking_source = "heuristic_fallback"

    tracker.final_ml_ranked_events = len(ranked_events)
    tracker.log_summary(logger)

    # =========================================================================
    # STAGE 3: CONSTRAINED LLM EXPLANATION (Referencing actual matching category)
    # =========================================================================
    enriched_events = generate_llm_explanations(ranked_events, user_profile, requested_labels)

    # =========================================================================
    # STAGE 4: RETURN STRUCTURED RESULT TO UI
    # =========================================================================
    return jsonify({
        "events": enriched_events,
        "total_found": len(enriched_events),
        "destination": {"city": city, "country": country, "type": dest_type, "label": clean_label},
        "header_title": header_title,
        "dates": {"start_date": start_date, "end_date": end_date},
        "interests": interests,
        "category": category,
        "requested_categories": list(requested_categories),
        "ranking_source": ranking_source,
        "pipeline_debug_counts": tracker.summary(),
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "cultural-intelligence",
        "reference_date": get_runtime_baseline().strftime("%Y-%m-%d"),
        "ml_model_loaded": rank_events is not None,
        "taxonomy": TAXONOMY,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5004)