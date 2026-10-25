import requests
import json
import sys

BASE_URL = "http://localhost:5004/api/festivals"

def run_test(name, payload, checks):
    print("\n" + "=" * 70)
    print(f"RUNNING: {name}")
    print(f"PAYLOAD: {json.dumps(payload, indent=2)}")
    print("=" * 70)
    
    resp = requests.post(BASE_URL, json=payload, timeout=30)
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    
    events = data.get("events") or []
    total = len(events)
    counts = data.get("pipeline_debug_counts") or {}
    print(f"Total Found: {total}")
    print(f"Pipeline Debug Counts: {json.dumps(counts, indent=2)}")
    
    for i, ev in enumerate(events):
        print(f"  [{i+1}] {ev.get('name')}")
        print(f"      City: {ev.get('city')} | State: {ev.get('state')} | Country: {ev.get('country')}")
        print(f"      Venue: {ev.get('venue')}")
        print(f"      Dates: {ev.get('start_date')} to {ev.get('end_date')}")
        print(f"      Category: {ev.get('category')} / {ev.get('categories')}")
        print(f"      ML Score: {ev.get('event_relevance_score')}% ({ev.get('relevance_tier')})")
        print(f"      Source: {ev.get('source_name')} ({ev.get('source_url')})")
        print(f"      Why Recommended: {ev.get('why_recommended')}")
    
    failures = []
    for check_desc, check_fn in checks:
        passed = check_fn(data, events)
        status = "PASS" if passed else "FAIL"
        print(f"  -> Check [{status}]: {check_desc}")
        if not passed:
            failures.append(check_desc)
            
    if failures:
        print(f"TEST FAILED: {failures}")
        return False, data
    else:
        print("TEST PASSED!")
        return True, data

if __name__ == "__main__":
    all_passed = True
    results = {}

    # TEST 1: Mumbai All Events (Interests: Food, Live Music)
    p1 = {
        "location": "Mumbai",
        "country": "India",
        "start_date": "2026-11-17",
        "end_date": "2026-11-30",
        "category": "all",
        "interests": "Food, Live Music",
    }
    checks1 = [
        ("Returns multiple verified events", lambda d, evs: len(evs) >= 2),
        ("All events are in Mumbai", lambda d, evs: all(e.get("city") == "Mumbai" for e in evs)),
        ("All events have specific venues", lambda d, evs: all(bool(e.get("venue")) for e in evs)),
        ("All dates overlap 17-30 Nov 2026", lambda d, evs: all("2026-11" in e.get("start_date") for e in evs)),
        ("Contains Food or Music events", lambda d, evs: any(e.get("category") in ("music", "food", "MUSIC_CONCERTS", "FOOD_DRINK") for e in evs)),
    ]
    ok, res1 = run_test("TEST 1: Mumbai All Events (Interests: Food, Live Music)", p1, checks1)
    results["TEST 1"] = (ok, res1)
    if not ok: all_passed = False

    # TEST 2: Mumbai Music & Concerts
    p2 = {
        "location": "Mumbai",
        "country": "India",
        "start_date": "2026-11-17",
        "end_date": "2026-11-30",
        "category": "music",
        "interests": "Music, Concerts",
    }
    checks2 = [
        ("Returns music events", lambda d, evs: len(evs) >= 1),
        ("All returned events belong to music taxonomy", lambda d, evs: all("music" in e.get("category", "").lower() or "MUSIC_CONCERTS" in (e.get("categories") or []) for e in evs)),
        ("Does not include unrelated categories", lambda d, evs: not any(e.get("category") == "food" and "MUSIC_CONCERTS" not in (e.get("categories") or []) for e in evs)),
    ]
    ok, res2 = run_test("TEST 2: Mumbai Music & Concerts", p2, checks2)
    results["TEST 2"] = (ok, res2)
    if not ok: all_passed = False

    # TEST 3: Mumbai Food & Drink
    p3 = {
        "location": "Mumbai",
        "country": "India",
        "start_date": "2026-11-17",
        "end_date": "2026-11-30",
        "category": "food",
        "interests": "Food, Culinary",
    }
    checks3 = [
        ("Returns food events", lambda d, evs: len(evs) >= 1),
        ("All returned events belong to food taxonomy", lambda d, evs: all("food" in e.get("category", "").lower() or "FOOD_DRINK" in (e.get("categories") or []) for e in evs)),
    ]
    ok, res3 = run_test("TEST 3: Mumbai Food & Drink", p3, checks3)
    results["TEST 3"] = (ok, res3)
    if not ok: all_passed = False

    # TEST 4: Pune All Events
    p4 = {
        "location": "Pune",
        "country": "India",
        "start_date": "2026-11-17",
        "end_date": "2026-11-30",
        "category": "all",
        "interests": "Music, Culture",
    }
    checks4 = [
        ("Returns local Pune events", lambda d, evs: len(evs) >= 1),
        ("Events have city == Pune", lambda d, evs: all(e.get("city") == "Pune" for e in evs)),
    ]
    ok, res4 = run_test("TEST 4: Pune All Events", p4, checks4)
    results["TEST 4"] = (ok, res4)
    if not ok: all_passed = False

    # TEST 5: Maharashtra All Events (State / Region level)
    p5 = {
        "location": "Maharashtra",
        "country": "India",
        "start_date": "2026-11-17",
        "end_date": "2026-11-30",
        "category": "all",
        "interests": "Culture, Music, Food",
    }
    checks5 = [
        ("Returns events across Maharashtra cities", lambda d, evs: len(evs) >= 2),
        ("Events retain their actual cities (Mumbai or Pune)", lambda d, evs: all(e.get("city") in ("Mumbai", "Pune", "Nashik", "Nagpur") for e in evs)),
        ("Events retain state == Maharashtra", lambda d, evs: all(e.get("state") == "Maharashtra" for e in evs)),
        ("Does NOT set city == Maharashtra", lambda d, evs: all(e.get("city") != "Maharashtra" for e in evs)),
    ]
    ok, res5 = run_test("TEST 5: Maharashtra State / Region Search", p5, checks5)
    results["TEST 5"] = (ok, res5)
    if not ok: all_passed = False

    # TEST 6: Paris Art & Design (Regression Protection)
    p6 = {
        "location": "Paris",
        "country": "France",
        "start_date": "2026-11-17",
        "end_date": "2026-11-24",
        "category": "art",
        "interests": "Art & Design",
    }
    checks6 = [
        ("Returns verified Paris art events (e.g. Paris Photo)", lambda d, evs: len(evs) >= 1),
        ("All events are in Paris", lambda d, evs: all(e.get("city") == "Paris" for e in evs)),
        ("No articles as events", lambda d, evs: all("Not to Miss" not in e.get("name") for e in evs)),
    ]
    ok, res6 = run_test("TEST 6: Paris Art & Design (Regression Protection)", p6, checks6)
    results["TEST 6"] = (ok, res6)
    if not ok: all_passed = False

    # TEST 7: Kyoto + Anime & Gaming (Hard Category Protection)
    p7 = {
        "location": "Kyoto",
        "country": "Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "anime",
        "interests": "Anime & Gaming",
    }
    checks7 = [
        ("Foliage / temple walk MUST remain rejected", lambda d, evs: not any("foliage" in e.get("name", "").lower() or "gion" in e.get("name", "").lower() for e in evs)),
        ("Only Anime & Gaming events pass", lambda d, evs: all("ANIME_GAMING" in (e.get("categories") or []) or "anime" in e.get("category", "").lower() for e in evs)),
    ]
    ok, res7 = run_test("TEST 7: Kyoto + Anime & Gaming (Foliage Walk Protection)", p7, checks7)
    results["TEST 7"] = (ok, res7)
    if not ok: all_passed = False

    print("\n" + "=" * 70)
    print("FINAL SUMMARY OF ALL 7 TESTS:")
    for t_name, (passed, _) in results.items():
        print(f"  {t_name}: {'PASSED [OK]' if passed else 'FAILED [X]'}")
    print("=" * 70)

    sys.exit(0 if all_passed else 1)
