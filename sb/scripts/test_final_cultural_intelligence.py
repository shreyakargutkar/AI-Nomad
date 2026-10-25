"""
Comprehensive End-to-End Validation Script for Cultural Intelligence
Tests Scenarios A through E strictly according to requirements.
"""

import json
import requests
import sys

BASE_URL = "http://127.0.0.1:5004"

def run_test_a():
    print("\n" + "="*70)
    print("RUNNING TEST A — PARIS + ART & DESIGN")
    print("="*70)
    payload = {
        "location": "Paris",
        "start_date": "2026-11-17",
        "end_date": "2026-11-24",
        "category": "ART_DESIGN",
        "interests": "Art & Design",
    }
    resp = requests.post(f"{BASE_URL}/api/festivals", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    events = data.get("events", [])
    debug_counts = data.get("pipeline_debug_counts", {})
    
    print(f"Total events returned: {len(events)}")
    print(f"Header Title: {data.get('header_title')}")
    print(f"Pipeline Debug Counts: {json.dumps(debug_counts, indent=2)}")
    
    assert len(events) > 0, "TEST A FAILED: No events returned for Paris Art & Design!"
    
    for ev in events:
        name = ev.get("name")
        city = ev.get("city")
        cat = ev.get("category")
        cats = ev.get("categories", [])
        venue = ev.get("venue")
        score = ev.get("event_relevance_score")
        
        print(f"  • [{cat}] {name} ({city} | Venue: {venue}) -> ML Score: {score}%")
        
        # Verify City is Paris
        assert city.lower() == "paris", f"TEST A FAILED: Event {name} city is {city}, expected Paris!"
        # Verify not an article
        assert "not to miss" not in name.lower(), f"TEST A FAILED: Article returned as event: {name}"
        assert "exhibitions in paris" not in name.lower(), f"TEST A FAILED: Article returned as event: {name}"
        # Verify no cross-city contamination
        assert "shanghai" not in (ev.get("description", "") + name + venue).lower(), f"TEST A FAILED: Shanghai found in {name}!"
        # Verify category
        assert cat == "ART_DESIGN" or "ART_DESIGN" in cats, f"TEST A FAILED: {name} category is {cat}, expected ART_DESIGN!"
        # Verify source exists
        assert ev.get("source_url"), f"TEST A FAILED: Missing source_url for {name}"
        assert ev.get("venue"), f"TEST A FAILED: Missing venue for {name}"
    
    print(">>> TEST A PASSED! All Paris Art & Design events verified.")
    return data

def run_test_b():
    print("\n" + "="*70)
    print("RUNNING TEST B — KYOTO + ANIME & GAMING")
    print("="*70)
    payload = {
        "location": "Kyoto",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "ANIME_GAMING",
        "interests": "Anime & Gaming",
    }
    resp = requests.post(f"{BASE_URL}/api/festivals", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    events = data.get("events", [])
    debug_counts = data.get("pipeline_debug_counts", {})
    
    print(f"Total events returned: {len(events)}")
    print(f"Pipeline Debug Counts: {json.dumps(debug_counts, indent=2)}")
    
    assert len(events) > 0, "TEST B FAILED: No events returned for Kyoto Anime & Gaming!"
    
    for ev in events:
        name = ev.get("name")
        city = ev.get("city")
        cat = ev.get("category")
        cats = ev.get("categories", [])
        score = ev.get("event_relevance_score")
        
        print(f"  • [{cat}] {name} ({city} | Venue: {ev.get('venue')}) -> ML Score: {score}%")
        
        # Verify Gion foliage walk is NEVER returned for Anime
        assert "foliage" not in name.lower() and "illumination" not in name.lower(), f"TEST B FAILED: Illumination walk returned for Anime: {name}"
        assert city.lower() == "kyoto", f"TEST B FAILED: Event {name} city is {city}, expected Kyoto!"
        assert cat == "ANIME_GAMING" or "ANIME_GAMING" in cats, f"TEST B FAILED: {name} category is {cat}, expected ANIME_GAMING!"
    
    print(">>> TEST B PASSED! Autumn Foliage Illumination walk rejected; only genuine Anime/Gaming events returned.")
    return data

def run_test_c():
    print("\n" + "="*70)
    print("RUNNING TEST C — FRANCE (COUNTRY SEARCH) + ALL EVENTS (FOOD & LIVE MUSIC INTERESTS)")
    print("="*70)
    payload = {
        "location": "France",
        "start_date": "2026-11-25",
        "end_date": "2026-11-30",
        "category": "all",
        "interests": "Food, Live Music",
    }
    resp = requests.post(f"{BASE_URL}/api/festivals", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    events = data.get("events", [])
    debug_counts = data.get("pipeline_debug_counts", {})
    
    print(f"Header Title: {data.get('header_title')}")
    print(f"Destination Type: {data.get('destination', {}).get('type')}")
    print(f"Total events returned across France: {len(events)}")
    print(f"Pipeline Debug Counts: {json.dumps(debug_counts, indent=2)}")
    
    assert len(events) > 0, "TEST C FAILED: Country search for France returned zero events!"
    assert data.get("header_title") == "Verified Events Across France", f"TEST C FAILED: Expected 'Verified Events Across France', got {data.get('header_title')}"
    
    cities_found = set()
    for ev in events:
        name = ev.get("name")
        city = ev.get("city")
        country = ev.get("country")
        cat = ev.get("category")
        score = ev.get("event_relevance_score")
        venue = ev.get("venue")
        
        cities_found.add(city)
        print(f"  • [{cat}] {name} in {city}, {country} ({venue}) -> ML Score: {score}%")
        
        assert country.lower() == "france", f"TEST C FAILED: Event {name} country is {country}, expected France!"
        assert city.lower() != "france", f"TEST C FAILED: Event city is 'France' instead of specific French city!"
        assert ev.get("source_url"), f"TEST C FAILED: Missing source_url for {name}"
    
    print(f"Cities represented across France: {cities_found}")
    assert len(cities_found) >= 2, f"TEST C FAILED: Expected multiple French cities, found {cities_found}"
    
    # Verify ML Ranking: Food & Music events should score higher than Art/Tech
    food_music_scores = [ev["event_relevance_score"] for ev in events if ev["category"] in ("FOOD_DRINK", "MUSIC_CONCERTS")]
    other_scores = [ev["event_relevance_score"] for ev in events if ev["category"] not in ("FOOD_DRINK", "MUSIC_CONCERTS")]
    
    print(f"Food/Music scores: {food_music_scores}")
    print(f"Other category scores: {other_scores}")
    
    if food_music_scores and other_scores:
        assert max(food_music_scores) >= max(other_scores), "TEST C FAILED: Food/Music events did not rank higher for Food/Music interests!"
    
    print(">>> TEST C PASSED! Country search successfully queried multiple French cities with ML preference for Food/Music.")
    return data

def run_test_d():
    print("\n" + "="*70)
    print("RUNNING TEST D — PARIS + FOOD & DRINK ONLY")
    print("="*70)
    payload = {
        "location": "Paris",
        "start_date": "2026-11-25",
        "end_date": "2026-11-30",
        "category": "FOOD_DRINK",
        "interests": "Food & Drink",
    }
    resp = requests.post(f"{BASE_URL}/api/festivals", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    events = data.get("events", [])
    debug_counts = data.get("pipeline_debug_counts", {})
    
    print(f"Total events returned: {len(events)}")
    print(f"Pipeline Debug Counts: {json.dumps(debug_counts, indent=2)}")
    
    assert len(events) > 0, "TEST D FAILED: No events returned for Paris Food & Drink!"
    
    for ev in events:
        name = ev.get("name")
        city = ev.get("city")
        cat = ev.get("category")
        cats = ev.get("categories", [])
        score = ev.get("event_relevance_score")
        
        print(f"  • [{cat}] {name} ({city} | Venue: {ev.get('venue')}) -> ML Score: {score}%")
        
        assert city.lower() == "paris", f"TEST D FAILED: Event {name} city is {city}, expected Paris!"
        assert cat == "FOOD_DRINK" or "FOOD_DRINK" in cats, f"TEST D FAILED: Non-food event returned in Food & Drink: {name} ({cat})"
    
    print(">>> TEST D PASSED! Only genuine Food & Drink events returned for Paris.")
    return data

def run_test_e():
    print("\n" + "="*70)
    print("RUNNING TEST E — NO MATCH COMBINATION (ZERO HALLUCINATION)")
    print("="*70)
    # Search for sports events in Kyoto on dates where none exist
    payload = {
        "location": "Kyoto",
        "start_date": "2026-12-10",
        "end_date": "2026-12-12",
        "category": "SPORTS",
        "interests": "Marathon, Sumo",
    }
    resp = requests.post(f"{BASE_URL}/api/festivals", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    events = data.get("events", [])
    debug_counts = data.get("pipeline_debug_counts", {})
    
    print(f"Total events returned: {len(events)}")
    print(f"Response message: {data.get('message')}")
    print(f"Alternative options offered: can_show_outside_dates={data.get('can_show_outside_dates')}, can_show_nearby={data.get('can_show_nearby')}, can_show_all_categories={data.get('can_show_all_categories')}")
    print(f"Pipeline Debug Counts: {json.dumps(debug_counts, indent=2)}")
    
    assert len(events) == 0, f"TEST E FAILED: Expected 0 events, got {len(events)} (hallucinated events detected)!"
    assert "No verified" in data.get("message", ""), "TEST E FAILED: Missing clear zero-match message!"
    assert data.get("can_show_outside_dates") is True, "TEST E FAILED: Missing can_show_outside_dates alternative!"
    assert data.get("can_show_nearby") is True, "TEST E FAILED: Missing can_show_nearby alternative!"
    assert data.get("can_show_all_categories") is True, "TEST E FAILED: Missing can_show_all_categories alternative!"
    
    print(">>> TEST E PASSED! Clean zero-match returned with helpful alternatives and zero hallucinated events.")
    return data

if __name__ == "__main__":
    print("="*70)
    print("STARTING CULTURAL INTELLIGENCE END-TO-END SUITE")
    print("="*70)
    
    test_a_res = run_test_a()
    test_b_res = run_test_b()
    test_c_res = run_test_c()
    test_d_res = run_test_d()
    test_e_res = run_test_e()
    
    print("\n" + "="*70)
    print("ALL TESTS (A, B, C, D, E) PASSED SUCCESSFULLY!")
    print("="*70)
