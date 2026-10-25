import os
import math
import requests
from dotenv import load_dotenv

load_dotenv()

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

def get_traffic_flow(lat, lng):
    """
    Query TomTom Flow Segment Data API.
    Ref: https://developer.tomtom.com/traffic-api/documentation/traffic-flow/flow-segment-data
    """
    if not TOMTOM_API_KEY:
        return None
        
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {
        "key": TOMTOM_API_KEY,
        "point": f"{lat},{lng}"
    }
    try:
        # Use a short timeout of 2.0s so that we do not bottleneck the planner
        response = requests.get(url, params=params, timeout=2.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[TomTom Traffic] Error fetching traffic flow: {e}")
    return None

def analyze_traffic_for_leg(start_lat, start_lng, end_lat, end_lng, start_name, end_name, recommended_mode):
    """
    Analyzes traffic for a leg by checking flow conditions at the segment midpoint.
    Returns a traffic report dict or None if API fails.
    """
    if not TOMTOM_API_KEY:
        return None

    # Calculate midpoint coordinates
    mid_lat = (start_lat + end_lat) / 2.0
    mid_lng = (start_lng + end_lng) / 2.0
    
    flow = get_traffic_flow(mid_lat, mid_lng)
    if not flow or "flowSegmentData" not in flow:
        return None
        
    segment = flow["flowSegmentData"]
    current_speed = segment.get("currentSpeed", 0)
    free_flow_speed = segment.get("freeFlowSpeed", 0)
    current_time = segment.get("currentTravelTime", 0)
    free_flow_time = segment.get("freeFlowTravelTime", 0)
    
    # Calculate speed ratio
    speed_ratio = current_speed / free_flow_speed if free_flow_speed > 0 else 1.0
    
    # Compute delay
    delay_sec = current_time - free_flow_time
    delay_mins = max(0, round(delay_sec / 60.0))
    
    # Classify traffic severity
    if speed_ratio <= 0.4:
        level = "heavy"
    elif speed_ratio <= 0.7:
        level = "moderate"
    else:
        level = "light"
        
    warnings = []
    location_name = end_name.split(',')[0]
    
    if level == "heavy":
        warnings.append(f"Heavy congestion near {location_name} (+{delay_mins} mins ETA)")
    elif level == "moderate":
        warnings.append(f"Traffic buildup detected near {location_name}.")
        
    alternative_mode = None
    # If mode is Cab and there is heavy congestion, suggest Metro/Walking instead
    if recommended_mode.lower() == "cab" and level == "heavy" and delay_mins >= 10:
        # Haversine distance
        d_lat = math.radians(end_lat - start_lat)
        d_lng = math.radians(end_lng - start_lng)
        a = math.sin(d_lat / 2)**2 + math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.sin(d_lng / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = c * 6371.0
        
        if distance_km < 2.0:
            alternative_mode = "Walking (Faster than gridlock)"
        else:
            alternative_mode = "Metro (Avoiding traffic delays)"
    return {
        "congestion_level": level,
        "delay_mins": delay_mins,
        "speed_ratio": speed_ratio,
        "warnings": warnings,
        "alternative_mode": alternative_mode
    }
