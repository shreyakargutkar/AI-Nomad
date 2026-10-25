"""
Flask API for the Smart Day Planner (port 5013).

Endpoints:
    POST /optimize  — Sort places, calculate routes/ETAs, recommend transport, and simulate disruptions.
    GET  /health    — Health check.
"""

import os
import sys
import math
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import traffic_service helper
_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
if _SERVICE_DIR not in sys.path:
    sys.path.insert(0, _SERVICE_DIR)
import traffic_service  # noqa: E402

# Print startup log to verify loading
print("MODEL: Smart Day Planner Premium Upgrade Engine (TomTom Traffic + ORS)")

app = Flask(__name__)
CORS(app)

ORS_API_KEY = os.getenv("ORS_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points in kilometers."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
    r_lat1, r_lon1, r_lat2, r_lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = r_lat2 - r_lat1
    dlon = r_lon2 - r_lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    r = 6371.0
    return c * r

def get_mumbai_region(lat, lng, place_name=""):
    """Classify coordinates and names into distinct Mumbai regions."""
    if lat is None or lng is None:
        return "Unknown"
    
    name_lower = (place_name or "").lower()
    if any(k in name_lower for k in ["colaba", "leopold", "gateway", "cuffe parade"]):
        return "Colaba"
    if any(k in name_lower for k in ["marine drive", "churchgate", "nariman", "cst", "chhatrapati", "fort", "crawford", "kalaghoda", "asiatic"]):
        return "South Mumbai"
    if any(k in name_lower for k in ["bandra", "khar", "santacruz", "bandstand", "carter"]):
        return "Bandra"
    if any(k in name_lower for k in ["powai", "hiranandani", "vikhroli"]):
        return "Powai"
    if any(k in name_lower for k in ["ghatkopar", "mulund", "bhandup", "r city", "khau galli"]):
        return "Ghatkopar/Mulund"

    # Geo-coordinate fallbacks
    if lat < 18.93:
        return "Colaba"
    elif lat < 18.98:
        return "South Mumbai"
    elif 19.03 <= lat < 19.08 and lng < 72.86:
        return "Bandra"
    elif 19.08 <= lat < 19.15 and 72.87 <= lng < 72.93:
        return "Powai"
    elif 19.07 <= lat < 19.23 and lng >= 72.89:
        return "Ghatkopar/Mulund"
    
    return "Central Mumbai"

def get_real_nearby_places(lat, lng, region):
    """Fetch real nearby places using OpenStreetMap (Overpass API) with a curated local fallback."""
    import requests
    
    osm_places = []
    url = "https://overpass-api.de/api/interpreter"
    query = f"""[out:json][timeout:2];
    (
      node["amenity"~"cafe|restaurant"](around:2000, {lat}, {lng});
      node["shop"="mall"](around:2000, {lat}, {lng});
      node["leisure"="park"](around:2000, {lat}, {lng});
      node["tourism"~"attraction|museum|aquarium|theme_park"](around:2000, {lat}, {lng});
    );
    out body 12;"""
    
    try:
        res = requests.post(url, data=query, timeout=2.0)
        if res.status_code == 200:
            data = res.json()
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name")
                if not name:
                    continue
                
                # Determine type emoji
                emoji = "📍"
                if "cafe" in tags.get("amenity", ""):
                    emoji = "☕"
                elif "restaurant" in tags.get("amenity", ""):
                    emoji = "🍜"
                elif "park" in tags.get("leisure", ""):
                    emoji = "🌳"
                elif "mall" in tags.get("shop", ""):
                    emoji = "🛍️"
                
                p_lat = element.get("lat")
                p_lng = element.get("lon")
                dist = haversine_distance(lat, lng, p_lat, p_lng)
                
                osm_places.append({
                    "name": name,
                    "emoji": emoji,
                    "distance_km": round(dist, 1),
                    "lat": p_lat,
                    "lng": p_lng,
                    "type": tags.get("amenity") or tags.get("leisure") or tags.get("tourism") or "attraction"
                })
    except Exception as e:
        print(f"[OSM Overpass] Failed to fetch live places: {e}")
        
    osm_places.sort(key=lambda x: x["distance_km"])
    
    # If we got at least 3 unique real places from OSM, return them!
    if len(osm_places) >= 3:
        seen = set()
        unique_osm = []
        for p in osm_places:
            if p["name"].lower() not in seen:
                seen.add(p["name"].lower())
                unique_osm.append(p)
        if len(unique_osm) >= 3:
            return unique_osm[:5]

    # Otherwise, fallback to our curated list of real Mumbai establishments
    curated_fallback = {
        "Colaba": [
            {"name": "Leopold Cafe (historic Irani style)", "emoji": "🍜", "lat": 18.9224, "lng": 72.8317},
            {"name": "Cafe Mondegar (retro jukebox vibes)", "emoji": "☕", "lat": 18.9224, "lng": 72.8317},
            {"name": "Colaba Causeway Street Shopping", "emoji": "🛍️", "lat": 18.9150, "lng": 72.8279},
            {"name": "Gateway of India Plaza", "emoji": "📍", "lat": 18.9220, "lng": 72.8347},
            {"name": "Taj Mahal Palace Heritage Walk", "emoji": "🌳", "lat": 18.9217, "lng": 72.8331}
        ],
        "South Mumbai": [
            {"name": "Pizza By The Bay (sea-facing)", "emoji": "🍜", "lat": 18.9354, "lng": 72.8225},
            {"name": "K. Rustom & Co. Ice Cream Sandwiches", "emoji": "☕", "lat": 18.9328, "lng": 72.8241},
            {"name": "Asiatic Society Library Steps", "emoji": "📍", "lat": 18.9313, "lng": 72.8354},
            {"name": "Jehangir Art Gallery", "emoji": "🎨", "lat": 18.9274, "lng": 72.8318},
            {"name": "Horniman Circle Gardens", "emoji": "🌳", "lat": 18.9321, "lng": 72.8351}
        ],
        "Bandra": [
            {"name": "Bandra Bandstand Promenade", "emoji": "🌳", "lat": 19.0427, "lng": 72.8191},
            {"name": "Carter Road Sunset Walk", "emoji": "🌳", "lat": 19.0596, "lng": 72.8228},
            {"name": "Subko Coffee Roasters (famous craft brew)", "emoji": "☕", "lat": 19.0543, "lng": 72.8285},
            {"name": "Candies Cafe (multi-tiered terrace)", "emoji": "☕", "lat": 19.0631, "lng": 72.8252},
            {"name": "Historic Bandra Fort Viewpoint", "emoji": "📍", "lat": 19.0409, "lng": 72.8164}
        ],
        "Powai": [
            {"name": "Powai Lake Promenade", "emoji": "🌳", "lat": 19.1281, "lng": 72.9069},
            {"name": "Hiranandani Heritage Park", "emoji": "🌳", "lat": 19.1182, "lng": 72.9080},
            {"name": "Aromas Cafe & Bistro Powai", "emoji": "☕", "lat": 19.1189, "lng": 72.9068},
            {"name": "Galleria Shopping Mall", "emoji": "🛍️", "lat": 19.1185, "lng": 72.9075},
            {"name": "Poetry by Love and Cheesecake", "emoji": "☕", "lat": 19.1176, "lng": 72.9060}
        ],
        "Ghatkopar/Mulund": [
            {"name": "R City Mall (Ghatkopar's largest mall)", "emoji": "🛍️", "lat": 19.0997, "lng": 72.9163},
            {"name": "Ghatkopar Khau Galli (street food)", "emoji": "🍜", "lat": 19.0864, "lng": 72.9082},
            {"name": "Snow Kingdom Amusement Area", "emoji": "📍", "lat": 19.0995, "lng": 72.9165},
            {"name": "Mulund Sambhaji Park Walk", "emoji": "🌳", "lat": 19.1750, "lng": 72.9550},
            {"name": "Achija Veg Restaurant (pav bhaji spot)", "emoji": "🍜", "lat": 19.0855, "lng": 72.9075}
        ]
    }
    
    fallback_list = curated_fallback.get(region, curated_fallback["South Mumbai"])
    results = []
    for item in fallback_list:
        dist = haversine_distance(lat, lng, item["lat"], item["lng"])
        results.append({
            "name": item["name"],
            "emoji": item["emoji"],
            "distance_km": round(dist, 1),
            "lat": item["lat"],
            "lng": item["lng"],
            "type": "attraction"
        })
        
    results.sort(key=lambda x: x["distance_km"])
    return results[:5]

def generate_interpolated_route(lat1, lon1, lat2, lon2, steps=15):
    """Generate a list of lat/lng coordinates representing a simulated path with slight curves."""
    coordinates = []
    for i in range(steps + 1):
        t = i / steps
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t
        
        if 0 < i < steps:
            offset_factor = math.sin(t * math.pi) * 0.0015
            wave = math.cos(t * math.pi * 3) * 0.0005
            lat += offset_factor + wave
            lon -= offset_factor - wave
            
        coordinates.append([lat, lon])
    return coordinates

def estimate_leg_cost(distance_m, mode):
    """Estimate leg cost in INR (₹) based on distance and mode."""
    km = distance_m / 1000.0
    mode_lower = mode.lower()
    if "walk" in mode_lower:
        return 0
    elif "metro" in mode_lower:
        return 25
    elif "cab" in mode_lower:
        return max(50, round(50 + km * 22))
    return 0

def calculate_leg_details(start_place, end_place, index, style, disruption_enabled=False, tracking_flags=None):
    """Calculate distance, duration, recommended mode, and polyline coordinates for a leg."""
    lat1, lon1 = start_place.get("lat"), start_place.get("lng")
    lat2, lon2 = end_place.get("lat"), end_place.get("lng")
    
    distance_km = haversine_distance(lat1, lon1, lat2, lon2)
    distance_m = distance_km * 1000.0
    
    r1 = get_mumbai_region(lat1, lon1, start_place.get("place_name"))
    r2 = get_mumbai_region(lat2, lon2, end_place.get("place_name"))
    
    # 1. Transport Mode Rules with Overrides
    if r1 in ["Colaba", "South Mumbai"] and r2 in ["Colaba", "South Mumbai"] and distance_km <= 2.5:
        recommended_mode = "Walking"
    elif distance_km > 15.0:
        recommended_mode = "Metro"
    else:
        # Standard: 0-1.5km walking, 1.5-8km Metro, 8km+ Cab
        if distance_km <= 1.5:
            recommended_mode = "Walking"
        elif distance_km <= 8.0:
            recommended_mode = "Metro"
        else:
            recommended_mode = "Cab"
            
    # Speed & Duration calculation based on Mode & Style
    if recommended_mode == "Walking":
        speed_kmh = 5.0
        duration_mins = (distance_km / speed_kmh) * 60.0
    elif recommended_mode == "Metro":
        speed_kmh = 25.0
        duration_mins = (distance_km / speed_kmh) * 60.0 + 6.0
    else: # Cab
        speed_kmh = 35.0
        if style == "fastest":
            speed_kmh = 45.0
        duration_mins = (distance_km / speed_kmh) * 60.0 + 3.0

    duration_mins = max(2.0, round(duration_mins))
    route_geometry = generate_interpolated_route(lat1, lon1, lat2, lon2)
    
    disruption = None
    real_traffic_used = False
    traffic_status = "Clear"
    confidence = "High"

    # 2. Try TomTom Traffic flow seg details
    if TOMTOM_API_KEY:
        try:
            traffic_report = traffic_service.analyze_traffic_for_leg(
                lat1, lon1, lat2, lon2,
                start_place.get("place_name"), end_place.get("place_name"),
                recommended_mode
            )
            if traffic_report:
                real_traffic_used = True
                if tracking_flags is not None:
                    tracking_flags["real_traffic_active"] = True
                
                delay_mins = traffic_report["delay_mins"]
                if delay_mins > 0:
                    duration_mins += delay_mins
                    
                congestion_level = traffic_report["congestion_level"]
                traffic_status = congestion_level.capitalize()
                
                # If TomTom reports heavy traffic congestion, display warning badge
                if congestion_level in ["heavy", "moderate"] and delay_mins > 0:
                    disruption = {
                        "title": f"Live Traffic: {congestion_level.capitalize()} Delay",
                        "message": traffic_report["warnings"][0] if traffic_report["warnings"] else f"Traffic buildup near {end_place.get('place_name').split(',')[0]}",
                        "delay_mins": delay_mins,
                        "alternative_mode": traffic_report["alternative_mode"] or "No alternate needed",
                        "is_real_traffic": True
                    }
                    if traffic_report["alternative_mode"]:
                        recommended_mode = traffic_report["alternative_mode"]
        except Exception as e:
            print(f"[TomTom Traffic] Failed to check live traffic: {e}")

    # 3. Simulated Fallback Disruption
    if not real_traffic_used and disruption_enabled and index == 1:
        if "walk" in recommended_mode.lower():
            disruption = {
                "title": "Sudden Heavy Downpour (Simulation)",
                "message": "Sudden heavy rainfall in this sector. Walking is slow and waterlogging reported.",
                "delay_mins": 15,
                "alternative_mode": "Cab (Rerouted to avoid waterlogging)"
            }
            duration_mins += 15
            recommended_mode = "Cab"
        elif "metro" in recommended_mode.lower():
            disruption = {
                "title": "Metro Signal Outage (Simulation)",
                "message": "Technical issues on Line 2. Trains delayed up to 25 minutes.",
                "delay_mins": 25,
                "alternative_mode": "Cab (Direct highway route)"
            }
            duration_mins += 25
            recommended_mode = "Cab"
        else:
            disruption = {
                "title": "Major Traffic Congestion (Simulation)",
                "message": "Accident on Main Bridge. Traffic backed up 3 km.",
                "delay_mins": 20,
                "alternative_mode": "Walking (Detour via local lanes)"
            }
            duration_mins += 20
            recommended_mode = "Cab (Detour via Side Roads)"

    # Determine traffic status and confidence:
    if real_traffic_used:
        if recommended_mode in ["Walking", "Metro"]:
            confidence = "High"
        else: # Cab
            if traffic_status == "Heavy":
                confidence = "Medium"
            else:
                confidence = "High"
    else:
        if disruption:
            traffic_status = "Heavy"
            confidence = "Medium"
        else:
            if recommended_mode in ["Walking", "Metro"]:
                traffic_status = "Clear"
                confidence = "High"
            else:
                if distance_km > 10.0:
                    traffic_status = "Moderate"
                    confidence = "Medium"
                else:
                    traffic_status = "Light"
                    confidence = "High"
            
    return {
        "start_place_name": start_place.get("place_name"),
        "end_place_name": end_place.get("place_name"),
        "distance_m": round(distance_m),
        "duration_mins": duration_mins,
        "recommended_mode": recommended_mode,
        "route_geometry": route_geometry,
        "disruption": disruption,
        "traffic_status": traffic_status,
        "confidence": confidence
    }

def sort_places_by_style(places, style, anchor_event=None):
    """Sort the input places based on the chosen day style, including anchor event logic."""
    if len(places) <= 2:
        return places

    start_place = places[0]
    remaining = places[1:]
    
    priority_weights = {"high": 3, "medium": 2, "low": 1}
    
    sunset_attraction = None
    if style == "scenic":
        for p in remaining:
            name_lower = p.get("place_name", "").lower()
            if "marine drive" in name_lower or "beach" in name_lower or "sea" in name_lower or "point" in name_lower:
                sunset_attraction = p
                break
        if sunset_attraction:
            remaining = [p for p in remaining if p != sunset_attraction]

    # Create temporary anchor node to participate in spatial TSP sorting
    anchor_node = None
    if anchor_event and (anchor_event.get("place_name") or anchor_event.get("event_name")):
        anchor_node = {
            "place_name": anchor_event.get("event_name") or anchor_event.get("place_name"),
            "lat": anchor_event.get("lat"),
            "lng": anchor_event.get("lng"),
            "priority": "high",
            "is_anchor_node": True
        }

    import itertools
    
    def calculate_region_backtracks(start_pt, perm_nodes):
        route = [start_pt] + list(perm_nodes)
        regions = [get_mumbai_region(p.get("lat"), p.get("lng"), p.get("place_name")) for p in route]
        
        backtracks = 0
        for idx in range(len(regions) - 2):
            if regions[idx] == regions[idx+2] and regions[idx] != regions[idx+1]:
                backtracks += 1
                
        # Adjacent South areas grouped together to avoid zig-zags
        adjacent_south = ["Colaba", "South Mumbai"]
        for idx in range(len(regions) - 2):
            r1, r2, r3 = regions[idx], regions[idx+1], regions[idx+2]
            if r1 in adjacent_south and r3 in adjacent_south and r2 not in adjacent_south:
                backtracks += 1
        return backtracks

    # Nodes to permute
    nodes_to_permute = list(remaining)
    if anchor_node:
        nodes_to_permute.append(anchor_node)
        
    candidates = []
    for perm in itertools.permutations(nodes_to_permute):
        total_dist = 0.0
        curr = start_place
        for p in perm:
            total_dist += haversine_distance(
                curr.get("lat"), curr.get("lng"),
                p.get("lat"), p.get("lng")
            )
            curr = p
        
        # Calculate region backtracking penalty
        backtracks = calculate_region_backtracks(start_place, perm)
        
        # Anchor event proximity bonus: group same-region stops next to anchor
        anchor_adj_bonus = 0.0
        if anchor_node:
            anchor_idx = perm.index(anchor_node)
            anchor_region = get_mumbai_region(anchor_node["lat"], anchor_node["lng"], anchor_node["place_name"])
            
            adjacents = []
            if anchor_idx > 0:
                adjacents.append(perm[anchor_idx - 1])
            if anchor_idx < len(perm) - 1:
                adjacents.append(perm[anchor_idx + 1])
                
            for adj in adjacents:
                adj_region = get_mumbai_region(adj.get("lat"), adj.get("lng"), adj.get("place_name"))
                if adj_region == anchor_region:
                    # Discount distance (5.0 km equivalent) for same-region adjacency to anchor event
                    anchor_adj_bonus += 5.0
        
        effective_dist = total_dist + (backtracks * 15.0) - anchor_adj_bonus
        candidates.append((perm, total_dist, backtracks, effective_dist))
        
    if not candidates:
        sorted_places = [start_place] + remaining
    else:
        # Sort by effective distance (backtracks penalized heavily)
        min_eff_dist = min(c[3] for c in candidates)
        threshold = min_eff_dist + 5.0  # Tight threshold tolerance
        valid_candidates = [c for c in candidates if c[3] <= threshold]
        if not valid_candidates:
            valid_candidates = candidates
            
        best_perm = None
        best_priority_score = -1.0
        min_dist_for_best = float('inf')
        
        for perm, dist, backtracks, eff_dist in valid_candidates:
            p_score = 0.0
            # Exclude the temporary anchor node for original priority scoring
            original_only_perm = [p for p in perm if not p.get("is_anchor_node")]
            for idx, p in enumerate(original_only_perm):
                weight = priority_weights.get(p.get("priority", "medium").lower(), 2)
                p_score += weight / (idx + 1.0)
                
            if p_score > best_priority_score or (abs(p_score - best_priority_score) < 1e-5 and dist < min_dist_for_best):
                best_priority_score = p_score
                best_perm = original_only_perm
                min_dist_for_best = dist
                
        sorted_places = [start_place] + list(best_perm)
        
    if style == "scenic" and sunset_attraction:
        sorted_places.append(sunset_attraction)
        
    return sorted_places

def get_wait_gap_options(anchor_place):
    """Generate 4 structured interactive wait gap options for wait gaps > 90 minutes."""
    lat = anchor_place.get("lat")
    lng = anchor_place.get("lng")
    place_name = anchor_place.get("place_name", "")
    
    region = get_mumbai_region(lat, lng, place_name)
    
    # Fetch real nearby places using the helper
    all_places = get_real_nearby_places(lat, lng, region)
    
    # Classify places into attractions and cafes
    attractions = []
    cafes = []
    
    for p in all_places:
        t = p.get("type", "").lower()
        if "cafe" in t or "restaurant" in t or p.get("emoji") in ["☕", "🍜"]:
            cafes.append(p)
        else:
            attractions.append(p)
            
    # Fallback to general list if empty
    if not attractions:
        attractions = [p for p in all_places if p.get("emoji") not in ["☕", "🍜"]]
    if not cafes:
        cafes = [p for p in all_places if p.get("emoji") in ["☕", "🍜"]]
        
    # Generate custom itineraries and text descriptions
    anchor_name = place_name.split(',')[0]
    
    # 1. Explore Sights
    explore_desc = f"Explore attractions and historical spots around {anchor_name}."
    explore_itinerary = ""
    if attractions:
        first_att = attractions[0]["name"]
        explore_itinerary = f"Walk to {first_att} ({attractions[0]['distance_km']} km away) and spend 45 mins exploring. Take a leisurely walk back to {anchor_name}."
    else:
        explore_itinerary = f"Explore local heritage alleys, check out street murals, and enjoy a pleasant stroll around {anchor_name}."
        
    # 2. Relax at Cafe
    cafe_desc = f"Unwind or grab a bite at a nearby café or diner."
    cafe_itinerary = ""
    if cafes:
        first_cafe = cafes[0]["name"]
        cafe_itinerary = f"Head over to {first_cafe} ({cafes[0]['distance_km']} km) for refreshing drinks or light bites. Enjoy the local neighborhood vibe."
    else:
        cafe_itinerary = f"Sip tea or coffee at a local Irani cafe near {anchor_name} and unwind."

    # 3. Move Closer
    move_closer_desc = f"Beat Mumbai's traffic by heading to the anchor event location early."
    move_closer_itinerary = f"Commute to {anchor_name} ahead of schedule. Wait at a nearby lobby, public plaza, or park to guarantee you arrive perfectly on time."

    # 4. Free Time
    free_time_desc = "Unstructured time for you to check in, relax, or plan on the fly."
    free_time_itinerary = "Free time. No activities scheduled. Recommended to check in to your stay, refresh, or catch up on messages."

    options = [
        {
            "id": "explore",
            "title": "Explore Sights",
            "emoji": "🏛️",
            "description": explore_desc,
            "itinerary": explore_itinerary,
            "places": attractions[:3]
        },
        {
            "id": "cafe",
            "title": "Relax at Cafe",
            "emoji": "☕",
            "description": cafe_desc,
            "itinerary": cafe_itinerary,
            "places": cafes[:3]
        },
        {
            "id": "move_closer",
            "title": "Move Closer",
            "emoji": "🚶‍♂️",
            "description": move_closer_desc,
            "itinerary": move_closer_itinerary,
            "places": []
        },
        {
            "id": "free_time",
            "title": "Free Time",
            "emoji": "⏳",
            "description": free_time_desc,
            "itinerary": free_time_itinerary,
            "places": []
        }
    ]
    
    return options

def optimize_timeline_for_style(places, style, disruption_enabled=False, anchor_event=None, tracking_flags=None):
    """Generate optimized timeline, legs, and metrics for a specific style."""
    sorted_places = sort_places_by_style(places, style, anchor_event)
    
    if style == "fastest":
        visit_duration = 60
        add_traffic_buffer = False
    elif style == "budget":
        visit_duration = 90
        add_traffic_buffer = True
    elif style == "relaxed":
        visit_duration = 120
        add_traffic_buffer = True
    elif style == "scenic":
        visit_duration = 90
        add_traffic_buffer = True
    elif style == "max_places":
        visit_duration = 45
        add_traffic_buffer = False
    else:
        visit_duration = 90
        add_traffic_buffer = True
        
    start_time_str = "09:00"
    curr_time = datetime.strptime(start_time_str, "%H:%M")
    
    timeline = []
    legs = []
    
    anchor_inserted = False
    anchor_place = None
    anchor_target_time = None
    anchor_buffer_mins = 0
    anchor_dur = 60
    
    if anchor_event and (anchor_event.get("place_name") or anchor_event.get("event_name")):
        event_label = anchor_event.get("event_name")
        place_label = anchor_event.get("place_name")
        if event_label and place_label:
            if event_label.lower() in place_label.lower():
                display_name = place_label
            elif place_label.lower() in event_label.lower():
                display_name = event_label
            else:
                display_name = f"{event_label} at {place_label}"
        else:
            display_name = event_label or place_label

        anchor_place = {
            "place_name": display_name,
            "lat": anchor_event.get("lat"),
            "lng": anchor_event.get("lng"),
            "priority": "high",
            "is_anchor": True
        }
        anchor_target_time = datetime.strptime(anchor_event.get("time", "13:00"), "%H:%M")
        anchor_buffer_mins = int(anchor_event.get("arrival_buffer", 0))
        anchor_dur = int(anchor_event.get("duration_mins", 60))
        
    for i, p in enumerate(sorted_places):
        if anchor_place and not anchor_inserted and i > 0:
            leg_to_anchor = calculate_leg_details(sorted_places[i-1], anchor_place, len(legs), style, disruption_enabled, tracking_flags)
            travel_mins = leg_to_anchor["duration_mins"]
            
            req_arrival_time = anchor_target_time - timedelta(minutes=anchor_buffer_mins)
            est_arrival = curr_time + timedelta(minutes=travel_mins)
            
            if est_arrival >= (req_arrival_time - timedelta(minutes=60)) or i >= len(sorted_places) - 1:
                leg_to_anchor["departure_time"] = curr_time.strftime("%H:%M")
                
                if est_arrival < req_arrival_time:
                    wait_mins = int((req_arrival_time - est_arrival).total_seconds() / 60)
                    curr_time = est_arrival
                    leg_to_anchor["arrival_time"] = curr_time.strftime("%H:%M")
                    legs.append(leg_to_anchor)
                    
                    if wait_mins > 90:
                        buf_place_name = "Explore Nearby & Relax"
                        buf_desc = f"You have a long wait gap of {wait_mins} mins. Instead of sitting idle, consider exploring nearby sights or dining options."
                        buf_recs = get_wait_gap_options(anchor_place)
                    else:
                        buf_place_name = "Snack & Buffer Stop"
                        buf_desc = f"Buffer time to ensure on-time arrival for {anchor_place['place_name']}."
                        buf_recs = None

                    timeline.append({
                        "type": "buffer",
                        "place_name": buf_place_name,
                        "description": buf_desc,
                        "arrival_time": curr_time.strftime("%H:%M"),
                        "duration_mins": wait_mins,
                        "departure_time": req_arrival_time.strftime("%H:%M"),
                        "recommendations": buf_recs
                    })
                    curr_time = req_arrival_time
                else:
                    curr_time = est_arrival
                    leg_to_anchor["arrival_time"] = curr_time.strftime("%H:%M")
                    legs.append(leg_to_anchor)
                    
                timeline.append({
                    "type": "anchor_event",
                    "place_name": anchor_place["place_name"],
                    "lat": anchor_place["lat"],
                    "lng": anchor_place["lng"],
                    "arrival_time": curr_time.strftime("%H:%M"),
                    "duration_mins": anchor_dur,
                    "departure_time": (curr_time + timedelta(minutes=anchor_dur)).strftime("%H:%M")
                })
                
                curr_time += timedelta(minutes=anchor_dur)
                anchor_inserted = True
                
                leg_from_anchor = calculate_leg_details(anchor_place, p, len(legs), style, disruption_enabled, tracking_flags)
                leg_from_anchor["departure_time"] = curr_time.strftime("%H:%M")
                curr_time += timedelta(minutes=leg_from_anchor["duration_mins"])
                leg_from_anchor["arrival_time"] = curr_time.strftime("%H:%M")
                legs.append(leg_from_anchor)
            
        if i > 0:
            if not (anchor_inserted and timeline[-1]["type"] == "anchor_event"):
                leg = calculate_leg_details(sorted_places[i-1], p, len(legs), style, disruption_enabled, tracking_flags)
                if add_traffic_buffer and leg["distance_m"] > 6000:
                    leg["duration_mins"] += 15
                    leg["traffic_buffer_added"] = 15
                
                leg["departure_time"] = curr_time.strftime("%H:%M")
                curr_time += timedelta(minutes=leg["duration_mins"])
                leg["arrival_time"] = curr_time.strftime("%H:%M")
                legs.append(leg)
                
        arr_time = curr_time.strftime("%H:%M")
        dep_time = (curr_time + timedelta(minutes=visit_duration)).strftime("%H:%M")
        
        timeline.append({
            "type": "attraction",
            "place_name": p.get("place_name"),
            "lat": p.get("lat"),
            "lng": p.get("lng"),
            "priority": p.get("priority", "medium"),
            "arrival_time": arr_time,
            "duration_mins": visit_duration,
            "departure_time": dep_time
        })
        
        curr_time += timedelta(minutes=visit_duration)
        
        if style == "relaxed" and i == 1 and len(sorted_places) > 2:
            break_arr = curr_time.strftime("%H:%M")
            break_dep = (curr_time + timedelta(minutes=30)).strftime("%H:%M")
            timeline.append({
                "type": "buffer",
                "place_name": "Mid-Day Snack & Rest Break",
                "description": "Relaxed schedule snack break.",
                "arrival_time": break_arr,
                "duration_mins": 30,
                "departure_time": break_dep
            })
            curr_time += timedelta(minutes=30)
            
    if anchor_place and not anchor_inserted:
        leg_to_anchor = calculate_leg_details(sorted_places[-1], anchor_place, len(legs), style, disruption_enabled, tracking_flags)
        leg_to_anchor["departure_time"] = curr_time.strftime("%H:%M")
        curr_time += timedelta(minutes=leg_to_anchor["duration_mins"])
        leg_to_anchor["arrival_time"] = curr_time.strftime("%H:%M")
        legs.append(leg_to_anchor)
        
        timeline.append({
            "type": "anchor_event",
            "place_name": anchor_place["place_name"],
            "lat": anchor_place["lat"],
            "lng": anchor_place["lng"],
            "arrival_time": curr_time.strftime("%H:%M"),
            "duration_mins": anchor_dur,
            "departure_time": (curr_time + timedelta(minutes=anchor_dur)).strftime("%H:%M")
        })
        anchor_inserted = True
        
    total_travel_time = sum(leg["duration_mins"] for leg in legs)
    total_distance_m = sum(leg["distance_m"] for leg in legs)
    total_cost = sum(estimate_leg_cost(leg["distance_m"], leg["recommended_mode"]) for leg in legs)
    total_walk_m = sum(leg["distance_m"] for leg in legs if "walk" in leg["recommended_mode"].lower())
    
    return {
        "optimized_places": sorted_places,
        "timeline": timeline,
        "legs": legs,
        "summary": {
            "start_time": start_time_str,
            "end_time": timeline[-1]["departure_time"],
            "total_travel_time_mins": total_travel_time,
            "total_distance_m": total_distance_m,
            "total_cost_inr": total_cost,
            "total_walk_m": total_walk_m,
            "disrupted_leg_index": 1 if (disruption_enabled and len(legs) > 1) else None
        }
    }

def generate_human_insights(active_plan, selected_style, anchor_event, places, proximity_alerts, real_traffic_active):
    insights = []
    
    # 1. Real traffic mode indicator
    if real_traffic_active:
        insights.append({
            "type": "success",
            "message": "🟢 Real-time traffic is active: Transit times and recommendations are updated with live TomTom congestion data."
        })
        
        # Check for delays in legs
        for leg in active_plan["legs"]:
            disruption = leg.get("disruption")
            if disruption and disruption.get("is_real_traffic"):
                insights.append({
                    "type": "warning",
                    "message": f"🚗 Traffic Alert: {disruption['message']}. Suggest taking {disruption['alternative_mode']} instead."
                })
    else:
        insights.append({
            "type": "info",
            "message": "⚪ Using historical fallback profiles: TomTom live API is currently not available, but routing fallback speeds are active."
        })
        
    # 2. Anchor awareness explanations
    if anchor_event and (anchor_event.get("place_name") or anchor_event.get("event_name")):
        event_name = anchor_event.get("event_name") or anchor_event.get("place_name").split(',')[0]
        anchor_lat = anchor_event.get("lat")
        anchor_lng = anchor_event.get("lng")
        
        pre_anchor = []
        post_anchor = []
        
        timeline = active_plan["timeline"]
        anchor_idx = -1
        for idx, item in enumerate(timeline):
            if item["type"] == "anchor_event":
                anchor_idx = idx
                break
                
        if anchor_idx != -1:
            for item in timeline[:anchor_idx]:
                if item["type"] == "attraction":
                    pre_anchor.append(item["place_name"].split(',')[0])
            for item in timeline[anchor_idx+1:]:
                if item["type"] == "attraction":
                    post_anchor.append(item["place_name"].split(',')[0])
                    
        if pre_anchor and post_anchor:
            insights.append({
                "type": "success",
                "message": f"📍 We clustered {', '.join(pre_anchor[:2])} beforehand to minimize your driving time prior to {event_name}, then scheduled {', '.join(post_anchor[:2])} for later."
            })
        elif pre_anchor:
            insights.append({
                "type": "success",
                "message": f"📍 Your day finishes at {event_name}. We've structured the preceding stops ({', '.join(pre_anchor[:3])}) to route you smoothly in that direction."
            })
        elif post_anchor:
            insights.append({
                "type": "success",
                "message": f"📍 Starting your day at {event_name}. We've lined up {', '.join(post_anchor[:3])} afterwards in a natural sequence to avoid zig-zagging across town."
            })
        else:
            insights.append({
                "type": "success",
                "message": f"📍 Your itinerary has been fully aligned around your fixed event: {event_name}."
            })
            
    # 3. Day style feedback
    if selected_style == "relaxed":
        insights.append({
            "type": "success",
            "message": "☕ Laid-back pacing: This plan gives you ample time (2 hours per stop) and includes a dedicated snack break to keep you refreshed."
        })
    elif selected_style == "fastest":
        insights.append({
            "type": "success",
            "message": "⚡ Express pacing: Transits are optimized using the fastest available modes to maximize your exploration time."
        })
    elif selected_style == "budget":
        insights.append({
            "type": "info",
            "message": "💰 Cost-effective transit: Budget options are preferred, suggesting walking and public transit where feasible."
        })
    elif selected_style == "scenic":
        insights.append({
            "type": "success",
            "message": "🌅 Scenic routing: We aligned the stops to ensure you visit waterfront areas or coastal views during the golden hour."
        })
        
    # 4. Proximity & walking feedback
    walk_km = active_plan["summary"]["total_walk_m"] / 1000.0
    if walk_km > 3.5:
        insights.append({
            "type": "warning",
            "message": f"👟 Highly active day: You'll be walking around {walk_km:.1f} km. Comfortable shoes are highly recommended."
        })
    elif walk_km < 1.0:
        insights.append({
            "type": "success",
            "message": "🚶‍♂️ Low-fatigue route: Very little walking required between transits, making it ideal for a relaxed day out."
        })
        
    # 5. Commute warnings
    for alert in proximity_alerts:
        if alert["type"] == "far":
            clean_msg = alert["message"].replace("⚠️ Far jump: ", "⚠️ Long distance commute: ")
            insights.append({
                "type": "warning",
                "message": clean_msg
            })
        elif alert["type"] == "close":
            clean_msg = alert["message"].replace("💡 ", "💡 Walking Tip: ")
            insights.append({
                "type": "success",
                "message": clean_msg
            })
            
    return insights

@app.route("/optimize", methods=["POST"])
def optimize_endpoint():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "No JSON payload received"}), 400
            
        places = data.get("places")
        if not places or not isinstance(places, list):
            return jsonify({"error": "Field 'places' must be a non-empty list"}), 400
            
        if len(places) < 2 or len(places) > 6:
            return jsonify({"error": "Must submit between 2 and 6 places"}), 400
            
        selected_style = data.get("route_type", "balanced")
        if selected_style == "efficient":
            selected_style = "balanced"
            
        disruption_enabled = data.get("disruption_enabled", False)
        anchor_event = data.get("anchor_event")
        
        # Flags dictionary to track across thread if TomTom API was queried successfully
        tracking_flags = {"real_traffic_active": False}
        
        # 1. Pre-calculate details for ALL 6 styles to return comparison cards
        styles_list = ["fastest", "budget", "relaxed", "scenic", "max_places", "balanced"]
        comparison_cards = {}
        
        for style in styles_list:
            style_plan = optimize_timeline_for_style(places, style, disruption_enabled, anchor_event, tracking_flags)
            sumry = style_plan["summary"]
            
            walk_km = sumry["total_walk_m"] / 1000.0
            walk_level = "Low" if walk_km < 1.5 else "Medium" if walk_km < 3.5 else "High"
            
            highlight = ""
            if style == "fastest":
                highlight = f"⚡ Saves {max(5, 50 - sumry['total_travel_time_mins'])}m travel"
            elif style == "budget":
                highlight = "💰 Lowest transport cost"
            elif style == "relaxed":
                highlight = "☕ Coffee breaks included"
            elif style == "scenic":
                highlight = "🌅 Sunset views aligned"
            elif style == "max_places":
                highlight = "🚀 Packs maximum stops"
            else:
                highlight = "⚖️ Balanced transit blend"
                
            comparison_cards[style] = {
                "travel_time_mins": sumry["total_travel_time_mins"],
                "total_cost_inr": sumry["total_cost_inr"],
                "walk_level": walk_level,
                "walk_km": round(walk_km, 1),
                "highlight": highlight
            }
            
        # 2. Get full plan details for the selected style
        active_plan = optimize_timeline_for_style(places, selected_style, disruption_enabled, anchor_event, tracking_flags)
        active_summary = active_plan["summary"]
        
        # Add real traffic flag to active summary
        active_summary["real_traffic_active"] = tracking_flags["real_traffic_active"]
        
        # 3. Rule-Based Smart Travel Insights & Proximity Intelligence
        proximity_alerts = []
        for i in range(len(places)):
            for j in range(i+1, len(places)):
                p1, p2 = places[i], places[j]
                dist_km = haversine_distance(p1["lat"], p1["lng"], p2["lat"], p2["lng"])
                if dist_km < 0.9:
                    proximity_alerts.append({
                        "type": "close",
                        "places": [p1["place_name"], p2["place_name"]],
                        "message": f"💡 {p1['place_name'].split(',')[0]} + {p2['place_name'].split(',')[0]} are close ({dist_km*1000:.0f}m apart). Perfect for walking!"
                    })
                elif dist_km > 12.0:
                    proximity_alerts.append({
                        "type": "far",
                        "places": [p1["place_name"], p2["place_name"]],
                        "message": f"⚠️ Far jump: Traveling between {p1['place_name'].split(',')[0]} and {p2['place_name'].split(',')[0]} ({dist_km:.1f} km) will increase travel time."
                    })

        insights = generate_human_insights(
            active_plan=active_plan,
            selected_style=selected_style,
            anchor_event=anchor_event,
            places=places,
            proximity_alerts=proximity_alerts,
            real_traffic_active=tracking_flags["real_traffic_active"]
        )

        # 4. Day Health Score Calculation
        score = 100
        score_breakdown = []
        
        if selected_style == "max_places":
            score -= 15
            score_breakdown.append("-15 for Rushed Pacing")
        elif selected_style == "relaxed":
            score += 5
            score_breakdown.append("+5 for Rest Buffers")
            
        if active_summary["total_travel_time_mins"] > 100:
            score -= 10
            score_breakdown.append("-10 for High Travel Time")
            
        if walk_km > 4.5:
            score -= 15
            score_breakdown.append("-15 for Extreme Walking")
        elif walk_km < 1.0:
            score += 5
            score_breakdown.append("+5 for Low Walking Fatigue")
            
        if active_summary["total_cost_inr"] > 400:
            score -= 10
            score_breakdown.append("-10 for High Transit Cost (cabs)")
        elif active_summary["total_cost_inr"] < 100:
            score += 5
            score_breakdown.append("+5 for Budget Savings")
            
        fars = [a for a in proximity_alerts if a["type"] == "far"]
        if fars:
            score -= 15
            score_breakdown.append("-15 for Far Travel Jumps")
            
        score = max(35, min(99, score))
        
        if score >= 85:
            health_message = "Highly Optimized Day Plan"
        elif score >= 70:
            health_message = "Well Balanced Itinerary"
        elif score >= 50:
            health_message = "Moderately Rushed / Demanding Day"
        else:
            health_message = "High Travel Fatigue Alert"

        response_payload = {
            "optimized_places": active_plan["optimized_places"],
            "timeline": active_plan["timeline"],
            "legs": active_plan["legs"],
            "summary": {
                **active_summary,
                "health_score": score,
                "health_message": health_message,
                "health_breakdown": score_breakdown
            },
            "comparison_cards": comparison_cards,
            "smart_insights": insights,
            "proximity_alerts": proximity_alerts
        }
        
        return jsonify(response_payload), 200
        
    except Exception as e:
        return jsonify({"error": f"Internal server error during optimization: {e}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "smart_day_planner_upgraded",
        "ors_key_configured": bool(ORS_API_KEY),
        "tomtom_key_configured": bool(TOMTOM_API_KEY)
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5013))
    app.run(host="0.0.0.0", port=port, debug=True)
