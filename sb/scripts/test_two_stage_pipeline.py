#!/usr/bin/env python3
"""
Test Suite for 5 Required Two-Stage Recommendation Pipeline Scenarios (Section 12).
"""

import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:5004/api/festivals"

def make_request(payload):
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def run_pipeline_tests():
    print("=" * 70)
    print("RUNNING 5 TWO-STAGE RECOMMENDATION PIPELINE TEST CASES")
    print("=" * 70)

    # TEST A: Kyoto | 18 Nov 2026 - 24 Nov 2026 | Anime & Gaming
    # Expected: ONLY Anime/Gaming events. Foliage illumination MUST NOT appear.
    print("\n[TEST A] Kyoto | 18-24 Nov 2026 | Category: Anime & Gaming")
    status, data = make_request({
        "location": "Kyoto, Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "ANIME_GAMING",
        "interests": "Anime & Gaming"
    })
    events_a = data.get("events", [])
    print(f"Status: {status} | Total Events Returned: {len(events_a)}")
    for ev in events_a:
        print(f"  • {ev.get('name')} | Categories: {ev.get('categories')} | Conf: {ev.get('category_confidence')}")
        assert "foliage" not in ev.get("name", "").lower(), "FAILED! Foliage walk leaked into Anime & Gaming!"
        assert "illumination" not in ev.get("name", "").lower(), "FAILED! Illumination leaked into Anime & Gaming!"
        assert "ANIME_GAMING" in ev.get("categories", []), f"FAILED! Event {ev.get('name')} does not contain ANIME_GAMING!"
    print("✓ PASS: Test A successfully isolated Anime & Gaming. No foliage illumination walk appeared!")

    # TEST B: Kyoto | Category: Culture & Matsuri
    # Expected: Cultural events such as temple/illumination/festival events can appear.
    print("\n[TEST B] Kyoto | Category: Culture & Matsuri")
    status, data = make_request({
        "location": "Kyoto, Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "CULTURE_MATSURI",
        "interests": "Culture & Matsuri"
    })
    events_b = data.get("events", [])
    print(f"Status: {status} | Total Events Returned: {len(events_b)}")
    has_illumination = any("illumination" in ev.get("name", "").lower() for ev in events_b)
    for ev in events_b:
        print(f"  • {ev.get('name')} | Categories: {ev.get('categories')} | Score: {ev.get('event_relevance_score')}%")
        assert "CULTURE_MATSURI" in ev.get("categories", []), f"FAILED! Event {ev.get('name')} is not CULTURE_MATSURI!"
    assert has_illumination, "Expected Gion & Arashiyama Autumn Foliage Illumination Walk to appear for Culture & Matsuri!"
    print("✓ PASS: Test B correctly returned cultural temple & illumination events!")

    # TEST C: Kyoto | Category: Food & Drink
    # Expected: Food-related events only.
    print("\n[TEST C] Kyoto | Category: Food & Drink")
    status, data = make_request({
        "location": "Kyoto, Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "FOOD_DRINK",
        "interests": "Food & Drink"
    })
    events_c = data.get("events", [])
    print(f"Status: {status} | Total Events Returned: {len(events_c)}")
    for ev in events_c:
        print(f"  • {ev.get('name')} | Categories: {ev.get('categories')} | Score: {ev.get('event_relevance_score')}%")
        assert "FOOD_DRINK" in ev.get("categories", []), f"FAILED! Event {ev.get('name')} is not FOOD_DRINK!"
        assert "illumination" not in ev.get("name", "").lower(), "FAILED! Illumination appeared in Food & Drink!"
    has_nishiki = any("Nishiki" in ev.get("name", "") for ev in events_c)
    assert has_nishiki, "Expected Nishiki Market food event in Kyoto for Food & Drink!"
    print("✓ PASS: Test C returned food-related events only (Nishiki Market)! Foliage walk excluded.")

    # TEST D: Kyoto | Category: Anime & Gaming + Food & Drink
    # Expected: Events matching either selected category.
    print("\n[TEST D] Kyoto | Category: Anime & Gaming + Food & Drink")
    status, data = make_request({
        "location": "Kyoto, Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "all",
        "interests": "Anime & Gaming, Food & Drink"
    })
    events_d = data.get("events", [])
    print(f"Status: {status} | Total Events Returned: {len(events_d)}")
    for ev in events_d:
        print(f"  • {ev.get('name')} | Categories: {ev.get('categories')} | Score: {ev.get('event_relevance_score')}%")
        # Every event must have either ANIME_GAMING or FOOD_DRINK
        cats = ev.get("categories", [])
        assert ("ANIME_GAMING" in cats or "FOOD_DRINK" in cats), f"FAILED! Event {ev.get('name')} matches neither Anime nor Food!"
    print("✓ PASS: Test D verified multi-category match (Anime or Food). Other categories rejected!")

    # TEST E: Kyoto | Category: All Events
    # Expected: All valid upcoming local events, ranked by overall relevance.
    print("\n[TEST E] Kyoto | Category: All Events")
    status, data = make_request({
        "location": "Kyoto, Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "all",
        "interests": ""
    })
    events_e = data.get("events", [])
    print(f"Status: {status} | Total Events Returned: {len(events_e)}")
    for ev in events_e:
        print(f"  • {ev.get('name')} | Primary: {ev.get('category')} | Score: {ev.get('event_relevance_score')}%")
    assert len(events_e) >= 2, "Expected multiple diverse events for All Events category"
    print("✓ PASS: Test E returned all valid local events across categories ranked by ML!")

    print("\n" + "=" * 70)
    print("ALL 5 TWO-STAGE RECOMMENDATION PIPELINE TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline_tests()
