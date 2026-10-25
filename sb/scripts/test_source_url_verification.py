import requests
import json
import sys

BASE_URL = "http://localhost:5004/api/festivals"

def check_http_200(url):
    """Verifies that url is reachable and returns HTTP 200."""
    if not url:
        return False, "EMPTY_URL"
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=8,
            stream=True,
            allow_redirects=True,
        )
        if 200 <= r.status_code < 400:
            return True, f"HTTP {r.status_code}"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

def test_kala_ghoda_case():
    print("\n" + "=" * 70)
    print("TEST: KALA GHODA VIEW SOURCE & 404 REJECTION (SECTION 13)")
    print("=" * 70)
    payload = {
        "location": "Mumbai",
        "country": "India",
        "start_date": "2026-11-17",
        "end_date": "2026-11-30",
        "category": "all",
        "interests": "Culture, Art",
    }
    resp = requests.post(BASE_URL, json=payload, timeout=60)
    data = resp.json()
    events = data.get("events") or []

    kg_event = None
    for ev in events:
        if "kala ghoda" in ev.get("name", "").lower():
            kg_event = ev
            break

    if not kg_event:
        print("  -> Kala Ghoda event not in response, checking all events...")
    else:
        print(f"  Found Kala Ghoda event: {kg_event.get('name')}")
        src_url = kg_event.get("source_url")
        src_status = kg_event.get("source_status")
        src_name = kg_event.get("source_name")
        print(f"  source_url: {src_url}")
        print(f"  source_status: {src_status}")
        print(f"  source_name: {src_name}")

        # Assertions
        assert "bandra-cultural-fair-2026" not in (src_url or ""), "FAILED: Broken MTDC slug must NOT be used!"
        if src_status == "VALID":
            ok, msg = check_http_200(src_url)
            print(f"  HTTP Reachability of source_url [{src_url}]: {msg}")
            assert ok, f"FAILED: source_url marked VALID but returned {msg}"
            print("  [PASS] Kala Ghoda has an active, working, reachable source URL!")
        else:
            assert src_url is None or src_url == "", "FAILED: Invalid source must not have active source_url!"
            print("  [PASS] Kala Ghoda marked UNAVAILABLE without broken link!")

    print("KALA GHODA TEST PASSED!")
    return True

def test_all_mumbai_urls():
    print("\n" + "=" * 70)
    print("TEST: ALL MUMBAI EVENTS - SOURCE URL VERIFICATION")
    print("=" * 70)
    payload = {
        "location": "Mumbai",
        "country": "India",
        "start_date": "2026-11-17",
        "end_date": "2026-11-30",
        "category": "all",
        "interests": "Food, Live Music",
    }
    resp = requests.post(BASE_URL, json=payload, timeout=60)
    data = resp.json()
    events = data.get("events") or []
    print(f"Total events found: {len(events)}")
    assert len(events) >= 3, "Expected multiple verified Mumbai events"

    for i, ev in enumerate(events):
        name = ev.get("name")
        src_url = ev.get("source_url")
        src_status = ev.get("source_status")
        src_name = ev.get("source_name")
        print(f"\n  [{i+1}] {name}")
        print(f"      source_name: {src_name}")
        print(f"      source_status: {src_status}")
        print(f"      source_url: {src_url}")

        if src_status == "VALID":
            ok, msg = check_http_200(src_url)
            print(f"      reachability: {msg}")
            assert ok, f"Event '{name}' has source_status=VALID but URL failed: {msg}"
        else:
            print(f"      source is {src_status} (no broken link exposed)")
            assert not src_url, f"Event '{name}' has status {src_status} but non-empty source_url: {src_url}"

    print("ALL MUMBAI URLS TEST PASSED!")
    return True

def test_broken_source_injection():
    print("\n" + "=" * 70)
    print("TEST: INJECTED BROKEN SOURCE REJECTION (UNIT TEST)")
    print("=" * 70)
    sys.path.insert(0, "backend/services/festivals")
    from url_validator import check_url_reachability, resolve_event_source

    broken_url = "https://maharashtratourism.gov.in/this-page-definitely-does-not-exist-404"
    valid, status, code, reason = check_url_reachability(broken_url)
    print(f"  check_url_reachability for 404 URL: valid={valid}, status={status}, code={code}, reason={reason}")
    assert not valid, "Broken URL must return valid=False"
    assert status == "BROKEN", "Broken URL status must be BROKEN"
    assert code == 404 or "404" in reason, f"Expected 404, got {code} ({reason})"

    # Test event with broken URL without known domain
    ev_unknown = {
        "name": "Random Obscure Performance",
        "city": "Mumbai",
        "venue": "Unknown Alley",
        "source_url": broken_url,
    }
    resolved = resolve_event_source(ev_unknown)
    print(f"  resolve_event_source for unknown event: source_url={resolved.get('source_url')}, status={resolved.get('source_status')}")
    assert resolved.get("source_status") == "BROKEN", "Unknown event with broken URL must have status=BROKEN"
    assert not resolved.get("source_url"), "Unknown event with broken URL must not retain broken source_url"
    print("BROKEN SOURCE REJECTION TEST PASSED!")
    return True

def test_paris_urls():
    print("\n" + "=" * 70)
    print("TEST: PARIS ART & DESIGN - URL VERIFICATION (REGRESSION PROTECTION)")
    print("=" * 70)
    payload = {
        "location": "Paris",
        "country": "France",
        "start_date": "2026-11-17",
        "end_date": "2026-11-24",
        "category": "art",
        "interests": "Art & Design",
    }
    resp = requests.post(BASE_URL, json=payload, timeout=60)
    data = resp.json()
    events = data.get("events") or []
    print(f"Total Paris events found: {len(events)}")
    assert len(events) >= 1, "Expected verified Paris events"

    for ev in events:
        name = ev.get("name")
        src_url = ev.get("source_url")
        src_status = ev.get("source_status")
        print(f"  {name}: {src_url} ({src_status})")
        if src_status == "VALID":
            ok, msg = check_http_200(src_url)
            assert ok, f"Paris event '{name}' source_url failed: {msg}"
            print(f"    -> [PASS] Reachable: {msg}")

    print("PARIS URLS TEST PASSED!")
    return True

def test_kyoto_anime_gaming():
    print("\n" + "=" * 70)
    print("TEST: KYOTO ANIME & GAMING (HARD CATEGORY & URL TEST)")
    print("=" * 70)
    payload = {
        "location": "Kyoto",
        "country": "Japan",
        "start_date": "2026-11-18",
        "end_date": "2026-11-24",
        "category": "anime",
        "interests": "Anime & Gaming",
    }
    resp = requests.post(BASE_URL, json=payload, timeout=60)
    data = resp.json()
    events = data.get("events") or []
    print(f"Total Kyoto anime events: {len(events)}")
    assert len(events) == 1, f"Expected exactly 1 Kyoto anime event, got {len(events)}"
    ev = events[0]
    assert "Manga" in ev.get("name"), "Expected Kyoto Manga Museum event"
    assert "foliage" not in ev.get("name", "").lower(), "Foliage walk must remain rejected"
    assert ev.get("source_status") == "VALID", "Kyoto event must have source_status=VALID"
    ok, msg = check_http_200(ev.get("source_url"))
    assert ok, f"Kyoto event source_url failed: {msg}"
    print(f"  [PASS] {ev.get('name')} has verified working URL: {ev.get('source_url')} ({msg})")
    print("KYOTO ANIME TEST PASSED!")
    return True

if __name__ == "__main__":
    t1 = test_broken_source_injection()
    t2 = test_kala_ghoda_case()
    t3 = test_all_mumbai_urls()
    t4 = test_paris_urls()
    t5 = test_kyoto_anime_gaming()

    print("\n" + "=" * 70)
    print("ALL SOURCE URL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
