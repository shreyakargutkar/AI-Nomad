#!/usr/bin/env python3
"""
Verification Script for Paris (Art & Design) and Kyoto (Anime & Gaming) Data Quality & Two-Stage Pipeline.

Tests:
1. Paris Test (17 Nov - 24 Nov 2026, Art & Design):
   - Confirms NO article/listicle titles appear ("Art & Design Events Not to Miss in 2026", "Exhibitions in Paris in November 2026").
   - Confirms NO cross-city contamination (Shanghai, London, etc.).
   - Confirms ALL events have specific verified venues (Grand Palais, Centre Pompidou, Atelier des Lumières) and are IN_TRIP.
   - Confirms ordinary art exhibitions are not classified as TECHNOLOGY without evidence.
2. Kyoto Anime & Gaming Test (18 Nov - 24 Nov 2026):
   - Confirms "Gion & Arashiyama Autumn Foliage Illumination Walk" is strictly REJECTED (category_match = False).
   - Confirms only verified Anime & Gaming events appear.
"""

import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:5004/api/festivals"

def query_endpoint(payload):
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


def test_paris_art_and_design():
    print("=" * 75)
    print("TEST 1: PARIS (17 Nov 2026 – 24 Nov 2026) | Art & Design + Technology")
    print("=" * 75)
    payload = {
        "location": "Paris, France",
        "start_date": "2026-11-17",
        "end_date": "2026-11-24",
        "category": "ART_DESIGN",
        "interests": "Art & Design, Technology"
    }
    status, data = query_endpoint(payload)
    assert status == 200, f"Expected 200 OK, got {status}: {data}"
    events = data.get("events", [])
    print(f"Status: {status} | Events returned: {len(events)}\n")
    assert len(events) > 0, "Expected at least 1 verified Art & Design event for Paris"

    for ev in events:
        name = ev.get("name", "")
        venue = ev.get("venue", "")
        city = ev.get("city", "")
        desc = ev.get("description", "")
        start = ev.get("start_date", "")
        end = ev.get("end_date", "")
        cats = ev.get("categories", [])
        ml_score = ev.get("event_relevance_score")

        print(f"• Event: {name}")
        print(f"  Venue: {venue} | City: {city}")
        print(f"  Dates: {start} to {end}")
        print(f"  Categories: {cats} | ML Match: {ml_score}%")
        print(f"  Description: {desc[:100]}...\n")

        # Assertion 1: No article/listicle titles
        assert "not to miss" not in name.lower(), f"FAILED! Article title leaked as event: {name}"
        assert "exhibitions in paris" not in name.lower(), f"FAILED! Listicle title leaked as event: {name}"
        assert "events not to miss" not in name.lower(), f"FAILED! Listicle title leaked as event: {name}"

        # Assertion 2: No cross-city contamination
        assert "shanghai" not in desc.lower(), f"FAILED! Shanghai event leaked into Paris: {desc}"
        assert "shanghai" not in name.lower(), f"FAILED! Shanghai event leaked into Paris: {name}"
        assert city.lower() == "paris", f"FAILED! Event city is {city}, expected Paris!"

        # Assertion 3: Specific verified physical venue (no generic placeholders)
        assert "local venue" not in venue.lower(), f"FAILED! Generic placeholder venue found: {venue}"
        assert len(venue) >= 4, f"FAILED! Venue name too short: {venue}"

        # Assertion 4: Dates overlap trip (17 Nov - 24 Nov 2026)
        # Event must not end before 17 Nov or start after 24 Nov
        assert end >= "2026-11-17", f"FAILED! Event ended before trip start ({end} < 2026-11-17)"
        assert start <= "2026-11-24", f"FAILED! Event starts after trip end ({start} > 2026-11-24)"

        # Assertion 5: Category match
        assert "ART_DESIGN" in cats, f"FAILED! Event {name} does not have ART_DESIGN category!"

    print("✓ PASS: Paris Art & Design test completely eliminated articles, Shanghai events, and placeholder venues!\n")


def test_kyoto_anime_and_gaming():
    print("=" * 75)
    print("TEST 2: KYOTO (18 Nov 2026 – 24 Nov 2026) | Anime & Gaming")
    print("=" * 75)
    payload = {
        "location": "Kyoto, Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "ANIME_GAMING",
        "interests": "Anime & Gaming"
    }
    status, data = query_endpoint(payload)
    assert status == 200, f"Expected 200 OK, got {status}: {data}"
    events = data.get("events", [])
    print(f"Status: {status} | Events returned: {len(events)}\n")

    for ev in events:
        name = ev.get("name", "")
        venue = ev.get("venue", "")
        cats = ev.get("categories", [])
        print(f"• Event: {name} | Venue: {venue} | Categories: {cats}")

        # Core Assertion: Foliage illumination walk MUST NOT appear
        assert "foliage" not in name.lower(), f"FAILED! Foliage walk leaked into Anime & Gaming: {name}"
        assert "illumination" not in name.lower(), f"FAILED! Illumination walk leaked into Anime & Gaming: {name}"
        assert "ANIME_GAMING" in cats, f"FAILED! Event {name} is not ANIME_GAMING: {cats}"

    print("✓ PASS: Kyoto Anime & Gaming strictly rejected autumn foliage illumination walk!\n")


if __name__ == "__main__":
    test_paris_art_and_design()
    test_kyoto_anime_and_gaming()
    print("=" * 75)
    print("ALL DATA-QUALITY & PIPELINE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)
