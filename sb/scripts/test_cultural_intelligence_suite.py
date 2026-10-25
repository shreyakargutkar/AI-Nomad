#!/usr/bin/env python3
"""
Comprehensive 6-Scenario Test Runner for Cultural Intelligence Overhaul.
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

def run_tests():
    print("=" * 65)
    print("RUNNING 6 VERIFICATION TEST CASES FOR CULTURAL INTELLIGENCE")
    print("=" * 65)

    # TEST 1: Tokyo, Nov 2026, Anime + Technology
    status, data = make_request({
        "location": "Tokyo, Japan",
        "start_date": "2026-11-10",
        "end_date": "2026-11-17",
        "interests": "Anime, technology, gaming"
    })
    total_1 = data.get("total_found", 0)
    top_e = data.get("events", [])[0] if data.get("events") else {}
    print(f"\n[TEST 1] Tokyo + Nov 2026 + Anime/Tech:")
    print(f"Status: {status} | Total Events: {total_1}")
    print(f"Top Event: {top_e.get('name')} (Score: {top_e.get('event_relevance_score')}% - Category: {top_e.get('category')})")
    print(f"Why: {top_e.get('why_recommended')}")
    assert status == 200, f"Expected 200, got {status}"
    assert total_1 > 0, "Expected events found"
    assert "2026" in top_e.get("start_date", ""), "Expected 2026 date"
    print("✓ PASS: Test 1 Verified current Tokyo 2026 anime/tech event!")

    # TEST 2: Paris, Dec 2026, Food + Art
    status, data = make_request({
        "location": "Paris, France",
        "start_date": "2026-12-01",
        "end_date": "2026-12-08",
        "interests": "Food, art, exhibitions, wine"
    })
    total_2 = data.get("total_found", 0)
    top_paris = data.get("events", [])[0] if data.get("events") else {}
    print(f"\n[TEST 2] Paris + Dec 2026 + Food/Art:")
    print(f"Status: {status} | Total Events: {total_2}")
    print(f"Top Event: {top_paris.get('name')} (Score: {top_paris.get('event_relevance_score')}% - Category: {top_paris.get('category')})")
    print(f"Venue: {top_paris.get('venue')} | Dates: {top_paris.get('start_date')} to {top_paris.get('end_date')}")
    assert status == 200, f"Expected 200, got {status}"
    assert total_2 > 0, "Expected Paris events"
    assert "Paris" in top_paris.get("city", "") or "Paris" in top_paris.get("venue", "") or "Paris" in top_paris.get("name", "")
    assert "2026" in top_paris.get("start_date", "")
    print("✓ PASS: Test 2 Verified Paris 2026 food/art event!")

    # TEST 3: Destination with very few/no events (e.g. Tristan da Cunha Island)
    status, data = make_request({
        "location": "Tristan da Cunha Island",
        "start_date": "2026-11-10",
        "end_date": "2026-11-17",
        "interests": "Anime, tech"
    })
    print(f"\n[TEST 3] Remote Destination with No Events:")
    print(f"Status: {status} | Total: {data.get('total_found')}")
    print(f"Message: {data.get('message')}")
    assert data.get("total_found") == 0
    assert "No verified local events" in data.get("message", "")
    print("✓ PASS: Test 3 Clean no-results handling without hallucinated events!")

    # TEST 4: Search for a past date (e.g. 2025-03-17)
    status, data = make_request({
        "location": "Tokyo, Japan",
        "start_date": "2025-03-17",
        "end_date": "2025-03-24",
        "interests": "Culture"
    })
    print(f"\n[TEST 4] Past Date Search (March 2025):")
    print(f"Status: {status} | Error: {data.get('error')}")
    assert status == 400
    assert data.get("is_past_date") is True
    assert "in the past" in data.get("error", "")
    print("✓ PASS: Test 4 Past date correctly rejected and flagged as historical!")

    # TEST 5: Change interests for same Tokyo trip -> ranking changes
    status_a, data_a = make_request({
        "location": "Tokyo, Japan",
        "start_date": "2026-11-10",
        "end_date": "2026-11-17",
        "interests": "Anime, gaming, cosplay"
    })
    status_b, data_b = make_request({
        "location": "Tokyo, Japan",
        "start_date": "2026-11-10",
        "end_date": "2026-11-17",
        "interests": "Culinary, seafood, sake tasting"
    })
    top_a = data_a.get("events", [])[0].get("name")
    top_b = data_b.get("events", [])[0].get("name")
    print(f"\n[TEST 5] Personalization Ranking Comparison:")
    print(f"User A (Anime/Gaming): {top_a}")
    print(f"User B (Food/Sake):     {top_b}")
    assert top_a != top_b, f"Expected different top events, got both: {top_a}"
    print("✓ PASS: Test 5 Personalization shifts ranking based on user interests!")

    # TEST 6: Change destination -> previous destination events disappear
    status_tokyo, data_tokyo = make_request({
        "location": "Tokyo",
        "start_date": "2026-11-10",
        "end_date": "2026-11-17",
        "interests": "Food"
    })
    status_paris, data_paris = make_request({
        "location": "Paris",
        "start_date": "2026-11-10",
        "end_date": "2026-11-17",
        "interests": "Food"
    })
    tokyo_events = [e.get("name") for e in data_tokyo.get("events", [])]
    paris_events = [e.get("name") for e in data_paris.get("events", [])]
    print(f"\n[TEST 6] Destination Isolation:")
    print(f"Tokyo Events: {tokyo_events[:2]}")
    print(f"Paris Events: {paris_events[:2]}")
    assert not set(tokyo_events).intersection(set(paris_events)), "Overlap detected between Tokyo and Paris!"
    for e in data_paris.get("events", []):
        assert "Tokyo" not in e.get("city", "")
    print("✓ PASS: Test 6 Changing destination removes previous destination events!")

    print("\n" + "=" * 65)
    print("ALL 6 CULTURAL INTELLIGENCE TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
