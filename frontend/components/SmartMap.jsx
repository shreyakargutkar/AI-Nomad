'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Mumbai Region Classifier
const getMumbaiRegion = (lat, lng, placeName = '') => {
  if (!lat || !lng) return 'Unknown';
  const nameLower = (placeName || '').toLowerCase();
  if (nameLower.includes('colaba') || nameLower.includes('leopold') || nameLower.includes('gateway') || nameLower.includes('cuffe parade')) {
    return 'Colaba';
  }
  if (nameLower.includes('marine drive') || nameLower.includes('churchgate') || nameLower.includes('nariman') || nameLower.includes('cst') || nameLower.includes('chhatrapati') || nameLower.includes('fort') || nameLower.includes('crawford') || nameLower.includes('kalaghoda') || nameLower.includes('asiatic')) {
    return 'South Mumbai';
  }
  if (nameLower.includes('bandra') || nameLower.includes('khar') || nameLower.includes('santacruz') || nameLower.includes('bandstand') || nameLower.includes('carter')) {
    return 'Bandra';
  }
  if (nameLower.includes('powai') || nameLower.includes('hiranandani') || nameLower.includes('vikhroli')) {
    return 'Powai';
  }
  if (nameLower.includes('ghatkopar') || nameLower.includes('mulund') || nameLower.includes('bhandup') || nameLower.includes('r city') || nameLower.includes('khau galli')) {
    return 'Ghatkopar/Mulund';
  }
  if (lat < 18.93) return 'Colaba';
  if (lat < 18.98) return 'South Mumbai';
  if (lat >= 19.03 && lat < 19.08 && lng < 72.86) return 'Bandra';
  if (lat >= 19.08 && lat < 19.15 && lng >= 72.87 && lng < 72.93) return 'Powai';
  if (lat >= 19.07 && lat < 19.23 && lng >= 72.89) return 'Ghatkopar/Mulund';
  return 'Central Mumbai';
};

// Distance Helper (haversine in meters)
const computeDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371e3; // meters
  const rLat1 = (lat1 * Math.PI) / 180;
  const rLat2 = (lat2 * Math.PI) / 180;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(rLat1) * Math.cos(rLat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

export default function SmartMap({
  places,
  legs,
  disruptionEnabled,
  disruptedLegIndex,
  highlightedPlaceName,
  suggestedPlaces = [],
  onMarkerClick,
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const polylinesRef = useRef([]);

  // Handle map and path rendering
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize map if not already done
    if (!mapRef.current) {
      mapRef.current = L.map(mapContainerRef.current, {
        zoomControl: true,
        scrollWheelZoom: true,
      }).setView([19.076, 72.8775], 12); // Default Mumbai center

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(mapRef.current);
    }

    const map = mapRef.current;

    // Clear old markers
    markersRef.current.forEach((marker) => map.removeLayer(marker));
    markersRef.current = [];

    // Clear old polylines/circles
    polylinesRef.current.forEach((line) => map.removeLayer(line));
    polylinesRef.current = [];

    if (!places || places.length === 0) return;

    const bounds = L.latLngBounds();

    // Create marker helper with custom HTML
    const createCustomMarker = (lat, lng, label, placeName, color = '#1E3F2E', isAnchor = false) => {
      const icon = L.divIcon({
        html: `
          <div style="
            background-color: ${color};
            color: white;
            border-radius: ${isAnchor ? '6px' : '50%'};
            border: 2.5px solid white;
            width: ${isAnchor ? '34px' : '30px'};
            height: ${isAnchor ? '34px' : '30px'};
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: ${isAnchor ? '14px' : '11px'};
            box-shadow: 0 4px 12px rgba(30,34,41,0.25);
            transition: transform 0.2s ease, background-color 0.2s;
          " class="map-circle-icon">
            ${isAnchor ? '🍽️' : label}
          </div>
        `,
        className: 'custom-map-marker',
        iconSize: isAnchor ? [34, 34] : [30, 30],
        iconAnchor: isAnchor ? [17, 17] : [15, 15],
      });

      const marker = L.marker([lat, lng], { icon }).addTo(map);
      marker.placeName = placeName; // save for cross-highlight search

      marker.bindPopup(`
        <div style="font-family: system-ui, sans-serif; padding: 4px; max-width: 200px;">
          <strong style="color: #1E3F2E; font-size: 13px; display: block; margin-bottom: 2px;">${placeName}</strong>
          ${isAnchor ? '<div style="color: #C85A32; font-size: 10px; font-weight: bold; text-transform: uppercase; margin-bottom: 4px;">📅 LOCKED ANCHOR EVENT</div>' : ''}
          <div style="color: #666; font-size: 10px;">Coordinates: ${lat.toFixed(5)}, ${lng.toFixed(5)}</div>
          <p style="color: #2D6A8F; font-size: 10px; font-weight: bold; margin-top: 4px; cursor: pointer;">✨ Click to highlight in timeline</p>
        </div>
      `);

      // Callback when marker is clicked (cross-highlights timeline)
      marker.on('click', () => {
        if (onMarkerClick) {
          onMarkerClick(placeName);
        }
      });

      markersRef.current.push(marker);
      bounds.extend([lat, lng]);
    };

    // Add attraction markers
    places.forEach((place, index) => {
      if (place.lat && place.lng) {
        const color = index === 0 ? '#1E3F2E' : '#2D6A8F'; // First green, others blue
        createCustomMarker(place.lat, place.lng, String(index + 1), place.place_name, color, false);
      }
    });

    // Group attractions by region and draw circular boundaries
    const regions = {};
    places.forEach((p) => {
      if (!p.lat || !p.lng) return;
      const r = getMumbaiRegion(p.lat, p.lng, p.place_name);
      if (!regions[r]) regions[r] = [];
      regions[r].push(p);
    });

    Object.entries(regions).forEach(([regionName, pts]) => {
      if (pts.length < 2) return; // Only draw for clusters of 2 or more stops!

      // Calculate centroid coordinates
      const sumLat = pts.reduce((acc, p) => acc + p.lat, 0);
      const sumLng = pts.reduce((acc, p) => acc + p.lng, 0);
      const centerLat = sumLat / pts.length;
      const centerLng = sumLng / pts.length;

      // Find max distance to shape the radius
      let maxDist = 800; // minimum radius 800m
      pts.forEach((p) => {
        const dist = computeDistance(centerLat, centerLng, p.lat, p.lng);
        if (dist > maxDist) maxDist = dist;
      });

      const circle = L.circle([centerLat, centerLng], {
        radius: maxDist + 250, // add a 250m buffer
        color: '#E2B659', // Premium gold outline
        weight: 1.5,
        dashArray: '6, 6',
        fillColor: '#E2B659',
        fillOpacity: 0.04,
        interactive: false,
      }).addTo(map);

      polylinesRef.current.push(circle);
    });

    // Draw suggested Places (Wait Gap options)
    if (suggestedPlaces && suggestedPlaces.length > 0) {
      suggestedPlaces.forEach((spot) => {
        if (!spot.lat || !spot.lng) return;

        const goldIcon = L.divIcon({
          html: `
            <div style="
              background-color: #E2B659;
              color: white;
              border-radius: 50%;
              border: 1.8px solid #C85A32;
              width: 24px;
              height: 24px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 11px;
              box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            ">
              ${spot.emoji || '📍'}
            </div>
          `,
          className: 'suggested-map-marker',
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([spot.lat, spot.lng], { icon: goldIcon }).addTo(map);
        marker.placeName = spot.name;

        marker.bindPopup(`
          <div style="font-family: system-ui, sans-serif; padding: 4px; max-width: 200px;">
            <div style="color: #C85A32; font-size: 9px; font-weight: bold; text-transform: uppercase; margin-bottom: 2px;">💡 Recommended Stop</div>
            <strong style="color: #1E3F2E; font-size: 12px; display: block; margin-bottom: 2px;">${spot.name}</strong>
            <div style="color: #666; font-size: 10px;">Distance: ${spot.distance_km} km away</div>
          </div>
        `);

        markersRef.current.push(marker);
        bounds.extend([spot.lat, spot.lng]);
      });
    }

    // Draw routing polylines
    if (legs && legs.length > 0) {
      legs.forEach((leg, index) => {
        const geom = leg.route_geometry;
        if (!geom || geom.length === 0) return;

        const latLngs = geom.map((pt) => [pt[0], pt[1]]);

        const isDisrupted = disruptionEnabled && index === disruptedLegIndex;
        let color = '#C85A32';
        let dashArray = null;

        if (isDisrupted) {
          color = '#A54422'; // Disrupted Red
          dashArray = '5, 6';
        } else {
          const mode = leg.recommended_mode?.toLowerCase() || '';
          if (mode.includes('walk')) {
            color = '#1E3F2E'; // Walk Green
            dashArray = '3, 4';
          } else if (mode.includes('metro')) {
            color = '#2D6A8F'; // Metro Blue
          } else {
            color = '#C85A32'; // Cab Orange
          }
        }

        const polyline = L.polyline(latLngs, {
          color,
          weight: isDisrupted ? 6 : 4.5,
          opacity: 0.85,
          dashArray,
        }).addTo(map);

        polyline.bindPopup(`
          <div style="font-family: system-ui, sans-serif; padding: 4px;">
            <strong style="color: ${color}; font-size: 12px;">${leg.recommended_mode || 'Travel'} Segment</strong>
            <div style="font-size: 11px; margin-top: 3px; line-height: 1.4;">
              <strong>From:</strong> ${leg.start_place_name.split(',')[0]}<br/>
              <strong>To:</strong> ${leg.end_place_name.split(',')[0]}<br/>
              <strong>Distance:</strong> ${(leg.distance_m / 1000).toFixed(2)} km<br/>
              <strong>Duration:</strong> ${leg.duration_mins} mins
            </div>
            ${isDisrupted && leg.disruption ? `
              <div style="color: #A54422; font-size: 10px; margin-top: 6px; border-top: 1px dashed #EAE3D2; padding-top: 4px; font-weight: bold;">
                ⚠️ Disruption: ${leg.disruption.title}
              </div>
            ` : ''}
          </div>
        `);

        polylinesRef.current.push(polyline);
        latLngs.forEach((pt) => bounds.extend(pt));

        // Add visual warning marker on map for disruption
        if (isDisrupted && leg.disruption) {
          const midPoint = latLngs[Math.floor(latLngs.length / 2)];
          const warningIcon = L.divIcon({
            html: `
              <div style="
                background-color: #A54422;
                color: white;
                border-radius: 50%;
                border: 2px solid white;
                width: 26px;
                height: 26px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                animation: pulse 1.5s infinite;
              ">⚠️</div>
            `,
            className: 'warning-marker-glow',
            iconSize: [26, 26],
            iconAnchor: [13, 13],
          });
          const warningMarker = L.marker(midPoint, { icon: warningIcon }).addTo(map);
          warningMarker.bindPopup(`
            <div style="font-family: system-ui, sans-serif; font-size: 11px; color: #A54422;">
              <strong>${leg.disruption.title}</strong><br/>
              ${leg.disruption.message}<br/>
              <strong>Alternative:</strong> ${leg.disruption.alternative_mode}
            </div>
          `);
          markersRef.current.push(warningMarker);
        }
      });
    }

    // Add anchor events markers
    places.forEach((place) => {
      if (place.is_anchor && place.lat && place.lng) {
        createCustomMarker(place.lat, place.lng, '🍽️', place.place_name, '#C85A32', true);
      }
    });

    // Fit map bounds
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }

    // Invalidate size helper
    setTimeout(() => {
      map.invalidateSize();
    }, 100);

  }, [places, legs, disruptionEnabled, disruptedLegIndex, suggestedPlaces, onMarkerClick]);

  // Handle timeline selection highlighting (focus and zoom to location)
  useEffect(() => {
    if (!highlightedPlaceName || !mapRef.current) return;

    // Find marker matching the place name
    const marker = markersRef.current.find(
      (m) => m.placeName && m.placeName.toLowerCase().includes(highlightedPlaceName.toLowerCase())
    );

    if (marker) {
      marker.openPopup();
      mapRef.current.setView(marker.getLatLng(), 14.5);
    }
  }, [highlightedPlaceName]);

  return (
    <div
      ref={mapContainerRef}
      className="w-full h-full rounded-2xl border border-[#EAE3D2] shadow-inner relative"
      style={{ minHeight: '400px', zIndex: 1 }}
    />
  );
}
