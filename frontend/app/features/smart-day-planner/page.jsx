'use client';

import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Compass,
  MapPin,
  Calendar,
  Clock,
  Sparkles,
  AlertTriangle,
  Plus,
  Trash2,
  Save,
  Star,
  Map,
  Link2,
  Navigation,
  Info,
  Layers,
  ArrowRight,
  TrendingUp,
  Wallet,
  Coffee,
  Sun,
  Flame,
  Scale,
  Footprints,
  Train,
  Car,
  Hourglass,
  HelpCircle,
  Activity,
  CheckCircle,
  Lock,
  RefreshCw,
} from 'lucide-react';
import { useAuthContext } from '@/context/AuthProvider';
import { supabase } from '@/lib/supabase';

// Dynamically load Map component to prevent window-not-defined errors in Next.js SSR
const SmartMap = dynamic(() => import('@/components/SmartMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[400px] md:h-full min-h-[400px] bg-[#EAE3D2]/35 animate-pulse rounded-2xl flex items-center justify-center border border-[#EAE3D2]">
      <div className="text-center">
        <Compass className="animate-spin text-[#1E3F2E] mx-auto mb-2" size={32} />
        <p className="text-xs font-mono text-[#1E2229]/60">Loading Interactive Map...</p>
      </div>
    </div>
  ),
});

// Selectable Styles Configuration
const STYLE_OPTIONS = [
  {
    id: 'fastest',
    title: 'Fastest Route',
    icon: Flame,
    color: '#A54422',
    description: 'Uses cabs and optimized paths to minimize transit.',
    highlight: '⚡ Speed priority',
  },
  {
    id: 'budget',
    title: 'Budget Friendly',
    icon: Wallet,
    color: '#1E3F2E',
    description: 'Prioritizes walking and metro to save on fares.',
    highlight: '💰 Cost-saving',
  },
  {
    id: 'relaxed',
    title: 'Relaxed Day',
    icon: Coffee,
    color: '#2D6A8F',
    description: 'Longer stays with built-in coffee/snack buffers.',
    highlight: '☕ Comfort-focused',
  },
  {
    id: 'scenic',
    title: 'Scenic Experience',
    icon: Sun,
    color: '#C85A32',
    description: 'Coordinates coastal spots to align with sunset views.',
    highlight: '🌅 Sunset aligned',
  },
  {
    id: 'max_places',
    title: 'Max Places',
    icon: Sparkles,
    color: '#D4AF37',
    description: 'Short stays to fit maximum destinations in one day.',
    highlight: '🚀 Action-packed',
  },
  {
    id: 'balanced',
    title: 'Balanced Path',
    icon: Scale,
    color: '#1E2229',
    description: 'Default blend of cost, pacing, and travel time.',
    highlight: '⚖️ Optimized mix',
  },
];

export default function SmartDayPlanner() {
  const { user, isAuthenticated } = useAuthContext();
  const timelineRefs = useRef({});

  // App States
  const [places, setPlaces] = useState([
    { place_name: 'Gateway of India, Mumbai', lat: 18.9220, lng: 72.8347, priority: 'high' },
    { place_name: 'Marine Drive, Mumbai', lat: 18.9431, lng: 72.8230, priority: 'high' },
    { place_name: 'Colaba Causeway, Mumbai', lat: 18.9150, lng: 72.8279, priority: 'medium' },
    { place_name: 'Chhatrapati Shivaji Terminus, Mumbai', lat: 18.9400, lng: 72.8354, priority: 'medium' },
  ]);

  const [anchorEnabled, setAnchorEnabled] = useState(false);
  const [isAnchorLocked, setIsAnchorLocked] = useState(false);
  const [anchorEvent, setAnchorEvent] = useState({
    event_name: 'Dinner',
    place_name: 'Leopold Cafe, Colaba, Mumbai',
    lat: 18.9224,
    lng: 72.8317,
    time: '19:00',
    duration_mins: 90,
    arrival_buffer: 30, // Reach 30 mins early
  });

  const [routeType, setRouteType] = useState('balanced');
  const [selectedWaitGapOptions, setSelectedWaitGapOptions] = useState({});
  const [disruptionEnabled, setDisruptionEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Database integration states
  const [trips, setTrips] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState('');
  const [savedPlaces, setSavedPlaces] = useState([]);
  const [savedPlans, setSavedPlans] = useState([]);
  const [planDate, setPlanDate] = useState(new Date().toISOString().split('T')[0]);
  const [saveStatus, setSaveStatus] = useState('');

  // Autocomplete search states
  const [activeSearchIndex, setActiveSearchIndex] = useState(null); 
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Cross-highlighting states
  const [highlightedPlaceName, setHighlightedPlaceName] = useState(null);

  // Fetch initial database items (Trips, Saved Places, User's Plans)
  useEffect(() => {
    if (!supabase || !user?.id) return;

    supabase
      .from('trips')
      .select('trip_id, destination, start_date, end_date')
      .eq('user_id', user.id)
      .then(({ data }) => {
        if (data) setTrips(data);
      });

    supabase
      .from('saved_places')
      .select('*')
      .eq('user_id', user.id)
      .then(({ data }) => {
        if (data) setSavedPlaces(data);
      });

    supabase
      .from('smart_day_plans')
      .select('plan_id, plan_date, selected_places, route_type, created_at')
      .order('created_at', { ascending: false })
      .then(({ data }) => {
        if (data) setSavedPlans(data);
      });
  }, [user]);

  // Run initial path optimization on mount
  useEffect(() => {
    optimizePlan();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync routeType backend trigger
  useEffect(() => {
    optimizePlan();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeType, disruptionEnabled, anchorEnabled, isAnchorLocked]);

  // Photon Autocomplete Geocoder Call
  const handleSearch = async (query, indexStr) => {
    if (!query || query.length < 3) {
      setSearchResults([]);
      return;
    }
    setSearchLoading(true);
    try {
      const res = await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=5`);
      const data = await res.json();
      if (data && data.features) {
        const formatted = data.features.map((f) => {
          const props = f.properties;
          const label = [
            props.name,
            props.city || props.town || props.state,
            props.country,
          ]
            .filter(Boolean)
            .join(', ');
          return {
            label,
            lat: f.geometry.coordinates[1],
            lng: f.geometry.coordinates[0],
          };
        });
        setSearchResults(formatted);
      }
    } catch (err) {
      console.error('Photon search failed:', err);
    }
    setSearchLoading(false);
  };

  const selectSearchResult = (item, index) => {
    if (index === 'anchor') {
      setAnchorEvent({
        ...anchorEvent,
        place_name: item.label,
        lat: item.lat,
        lng: item.lng,
      });
    } else {
      const updated = [...places];
      updated[index] = {
        ...updated[index],
        place_name: item.label,
        lat: item.lat,
        lng: item.lng,
      };
      setPlaces(updated);
    }
    setActiveSearchIndex(null);
    setSearchResults([]);
  };

  // Add / Delete Destinations
  const addPlaceInput = () => {
    if (places.length >= 6) {
      setError('You can add a maximum of 6 places to optimize your day schedule.');
      return;
    }
    setError(null);
    setPlaces([...places, { place_name: '', lat: null, lng: null, priority: 'medium' }]);
  };

  const removePlaceInput = (idx) => {
    if (places.length <= 2) {
      setError('You must plan for at least 2 places in your day planner.');
      return;
    }
    setError(null);
    const updated = places.filter((_, i) => i !== idx);
    setPlaces(updated);
  };

  // Set Place priority
  const setPriority = (idx, priority) => {
    const updated = [...places];
    updated[idx].priority = priority;
    setPlaces(updated);
  };

  // Quick select a saved place
  const selectSavedPlace = (placeItem, index) => {
    const updated = [...places];
    updated[index] = {
      ...updated[index],
      place_name: placeItem.place_name,
      lat: placeItem.lat,
      lng: placeItem.lng,
    };
    setPlaces(updated);
  };

  // Trigger Path Optimization Backend Call
  const optimizePlan = async () => {
    setLoading(true);
    setError(null);

    // Verify all places have coordinates
    const incomplete = places.some((p) => !p.lat || !p.lng || !p.place_name.trim());
    if (incomplete) {
      setError('Please search and select valid addresses for all destinations first.');
      setLoading(false);
      return;
    }

    if (anchorEnabled && isAnchorLocked && (!anchorEvent.lat || !anchorEvent.lng || !anchorEvent.place_name.trim())) {
      setError('Please search and select a valid location for your anchor event.');
      setLoading(false);
      return;
    }

    try {
      const payload = {
        places,
        route_type: routeType,
        disruption_enabled: disruptionEnabled,
        anchor_event: (anchorEnabled && isAnchorLocked) ? anchorEvent : null,
      };

      const res = await fetch('/api/smart-day-planner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Path optimization failed.');
      }
      setResult(data);
    } catch (err) {
      setError(err.message || 'Could not connect to optimization service.');
    }
    setLoading(false);
  };

  // Save current day plan to Supabase
  const handleSavePlan = async () => {
    if (!isAuthenticated) {
      setSaveStatus('Please sign in to save plans.');
      return;
    }
    if (!result) {
      setSaveStatus('Generate an optimized plan before saving.');
      return;
    }

    setSaveStatus('Saving Day Plan...');
    try {
      const { data, error: pgError } = await supabase
        .from('smart_day_plans')
        .insert({
          trip_id: selectedTripId || null,
          plan_date: planDate,
          selected_places: places,
          anchor_event: (anchorEnabled && isAnchorLocked) ? anchorEvent : null,
          optimized_routes: result,
          selected_route_type: routeType,
          disruption_enabled: disruptionEnabled,
        })
        .select()
        .single();

      if (pgError) throw pgError;

      setSaveStatus('✓ Day Plan Saved successfully!');
      setSavedPlans([
        {
          plan_id: data.plan_id,
          plan_date: data.plan_date,
          selected_places: places,
          route_type: routeType,
          created_at: new Date().toISOString(),
        },
        ...savedPlans,
      ]);
    } catch (err) {
      setSaveStatus(`Failed to save: ${err.message}`);
    }
  };

  // Save a single place to saved_places database table
  const handleSavePlace = async (placeItem) => {
    if (!isAuthenticated) {
      alert('Sign in to save custom places.');
      return;
    }
    if (!placeItem.lat || !placeItem.lng || !placeItem.place_name) {
      alert('Select a valid location before saving.');
      return;
    }

    try {
      const { data, error: pgError } = await supabase
        .from('saved_places')
        .insert({
          user_id: user.id,
          place_name: placeItem.place_name,
          lat: placeItem.lat,
          lng: placeItem.lng,
          category: 'Sights',
        })
        .select()
        .single();

      if (pgError) throw pgError;

      setSavedPlaces([...savedPlaces, data]);
      alert('✓ Place added to your saved locations!');
    } catch (err) {
      alert(`Error saving location: ${err.message}`);
    }
  };

  // Load a previously saved plan
  const loadSavedPlan = async (planId) => {
    setLoading(true);
    setSaveStatus('');
    try {
      const { data, error: pgError } = await supabase
        .from('smart_day_plans')
        .select('*')
        .eq('plan_id', planId)
        .single();

      if (pgError) throw pgError;

      if (data) {
        setPlaces(data.selected_places);
        if (data.anchor_event) {
          setAnchorEnabled(true);
          setIsAnchorLocked(true);
          setAnchorEvent(data.anchor_event);
        } else {
          setAnchorEnabled(false);
          setIsAnchorLocked(false);
        }
        setRouteType(data.selected_route_type);
        setDisruptionEnabled(data.disruption_enabled);
        setPlanDate(data.plan_date);
        setSelectedTripId(data.trip_id || '');
        setResult(data.optimized_routes);
      }
    } catch (err) {
      setError(`Failed to load plan: ${err.message}`);
    }
    setLoading(false);
  };

  // Estimate INR Taxi/Cab Fare
  const getTaxiFareEstimate = (distanceM) => {
    const km = distanceM / 1000.0;
    const fare = Math.round(50 + km * 22);
    return `₹${fare.toLocaleString('en-IN')}`;
  };

  // Handle marker click (Scrolls timeline card into view)
  const handleMarkerClick = (placeName) => {
    setHighlightedPlaceName(placeName);
    const element = timelineRefs.current[placeName];
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Apply a brief glowing highlight class/state
      element.style.outline = '2px solid #C85A32';
      setTimeout(() => {
        element.style.outline = 'none';
      }, 2000);
    }
  };

  // Get Lucide icon for transport mode
  const getTransportIcon = (modeStr) => {
    const mode = modeStr.toLowerCase();
    if (mode.includes('walk')) return <Footprints size={14} className="text-[#1E3F2E]" />;
    if (mode.includes('metro')) return <Train size={14} className="text-[#2D6A8F]" />;
    return <Car size={14} className="text-[#C85A32]" />;
  };

  const getTransportColorClass = (modeStr) => {
    const mode = modeStr.toLowerCase();
    if (mode.includes('walk')) return 'bg-emerald-50 text-emerald-800 border-emerald-200/50';
    if (mode.includes('metro')) return 'bg-blue-50 text-blue-800 border-blue-200/50';
    return 'bg-amber-50 text-amber-800 border-amber-200/50';
  };

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 relative font-sans">
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-40 pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 md:px-6 relative z-10">
        
        {/* Header Block */}
        <div className="text-center mb-8 pt-6">
          <h1 className="text-4xl font-extrabold text-[#1E2229] font-display tracking-tight">Smart Day Planner</h1>
        </div>

        {/* TOP LEVEL: 6 Selectable Style Cards */}
        <div className="mb-8">
          <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase block mb-3 text-center">
            Select Travel Day Style
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {STYLE_OPTIONS.map((style) => {
              const IconComp = style.icon;
              const isSelected = routeType === style.id;
              
              // Extract details if result comparison card is ready
              const compData = result?.comparison_cards?.[style.id];

              return (
                <button
                  key={style.id}
                  type="button"
                  onClick={() => setRouteType(style.id)}
                  className={`p-4 rounded-xl border text-left flex flex-col justify-between transition-all relative overflow-hidden h-32 hover:shadow-md cursor-pointer ${
                    isSelected
                      ? 'bg-white border-[#C85A32] shadow-sm ring-1 ring-[#C85A32]'
                      : 'bg-white border-[#EAE3D2]/80 hover:border-gray-300'
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <IconComp
                        size={16}
                        style={{ color: style.color }}
                        className={isSelected ? 'animate-pulse' : ''}
                      />
                      <span className="text-[8px] font-bold text-[#1E2229]/50 uppercase tracking-wide">
                        {style.highlight.split(' ')[0]}
                      </span>
                    </div>
                    <h3 className="text-xs font-extrabold text-[#1E2229]">{style.title}</h3>
                    <p className="text-[9px] text-[#1E2229]/50 mt-1 leading-normal">
                      {style.description}
                    </p>
                  </div>
                  
                  {compData && (
                    <div className="text-[9px] font-mono text-[#C85A32] font-semibold mt-2 border-t border-[#EAE3D2]/50 pt-1.5 flex justify-between">
                      <span>{compData.travel_time_mins}m travel</span>
                      <span>₹{compData.total_cost_inr}</span>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Split UI Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT COLUMN: Input Panels & Configuration */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* Trip Association & Plans Settings */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm">
              <h2 className="text-xs font-mono font-bold text-[#1E3F2E] uppercase mb-4 flex items-center gap-2">
                <Link2 size={14} /> Association & Date Settings
              </h2>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-[#1E2229]/65 block mb-1">
                    Link to Active Trip
                  </label>
                  <select
                    value={selectedTripId}
                    onChange={(e) => setSelectedTripId(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-xs font-semibold text-[#1E2229]/80"
                  >
                    <option value="">Standalone Plan (No trip)</option>
                    {trips.map((t) => (
                      <option key={t.trip_id} value={t.trip_id}>
                        {t.destination} ({t.start_date ? new Date(t.start_date).toLocaleDateString(undefined, { month: 'short', year: 'numeric' }) : 'No Date'})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-[#1E2229]/65 block mb-1">
                    Day Plan Date
                  </label>
                  <input
                    type="date"
                    value={planDate}
                    onChange={(e) => setPlanDate(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-xs font-mono text-[#1E2229]/80"
                  />
                </div>
              </div>

              {/* Saved Plans Quick List */}
              {savedPlans.length > 0 && (
                <div className="mt-4 pt-4 border-t border-[#EAE3D2]/50">
                  <label className="text-[10px] font-bold text-[#1E2229]/65 block mb-1.5">
                    Previously Saved Plans
                  </label>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {savedPlans.map((plan) => (
                      <button
                        key={plan.plan_id}
                        onClick={() => loadSavedPlan(plan.plan_id)}
                        className="px-3 py-1.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] hover:bg-[#EAE3D2]/25 text-[10px] whitespace-nowrap shrink-0 transition font-medium"
                      >
                        📅 {plan.plan_date} ({plan.selected_places?.length || 0} stops)
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Destinations Form Block */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm space-y-4">
              <div className="flex justify-between items-center pb-2 border-b border-[#EAE3D2]/60">
                <h2 className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-2">
                  <MapPin size={14} /> Destinations (Minimum 2 Places)
                </h2>
                <span className="text-[10px] font-mono font-bold text-[#2D6A8F] bg-[#2D6A8F]/10 px-2 py-0.5 rounded">
                  Stops: {places.length}/6
                </span>
              </div>

              {/* Form Warnings */}
              {error && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-[#A54422] flex items-start gap-2">
                  <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Places Inputs Loop */}
              <div className="space-y-4">
                {places.map((place, idx) => (
                  <div key={idx} className="p-3 bg-[#FBF9F6] border border-[#EAE3D2] rounded-xl relative space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-[#1E3F2E]">
                        Stop #{idx + 1} {idx === 0 ? '(Start Location)' : ''}
                      </span>
                      
                      <div className="flex items-center gap-1.5">
                        {/* Save location to database */}
                        <button
                          type="button"
                          onClick={() => handleSavePlace(place)}
                          title="Save this location to profile"
                          className="p-1 hover:text-[#C85A32] text-[#1E2229]/40 transition"
                        >
                          <Star size={12} />
                        </button>
                        
                        {/* Delete Stop */}
                        <button
                          type="button"
                          onClick={() => removePlaceInput(idx)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded transition disabled:opacity-40"
                          disabled={places.length <= 2}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>

                    {/* Geocoder Autocomplete Input */}
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Search attraction, landmark, restaurant..."
                        value={place.place_name}
                        onChange={(e) => {
                          const updated = [...places];
                          updated[idx].place_name = e.target.value;
                          setPlaces(updated);
                          setActiveSearchIndex(idx);
                          handleSearch(e.target.value, idx);
                        }}
                        className="w-full p-2.5 rounded-lg border border-[#EAE3D2] bg-white text-xs text-[#1E2229] font-medium"
                      />

                      {/* Dropdown for Geocoder Autocomplete results */}
                      {activeSearchIndex === idx && (searchResults.length > 0 || searchLoading) && (
                        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#EAE3D2] rounded-lg shadow-lg z-50 py-1 max-h-48 overflow-y-auto">
                          {searchLoading && (
                            <div className="px-3 py-2 text-[10px] text-[#1E2229]/60 italic">Searching locations...</div>
                          )}
                          {searchResults.map((resultItem, sIdx) => (
                            <button
                              key={sIdx}
                              type="button"
                              onClick={() => selectSearchResult(resultItem, idx)}
                              className="w-full text-left px-3 py-2.5 text-xs hover:bg-[#FBF9F6] text-[#1E2229] border-b border-[#EAE3D2]/30 last:border-0 font-medium"
                            >
                              📍 {resultItem.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Controls Row: Priority Picker & Saved Places selection */}
                    <div className="flex items-center justify-between gap-2 pt-1">
                      <div className="flex gap-1 items-center">
                        <span className="text-[9px] font-mono text-[#1E2229]/50 mr-1">Priority:</span>
                        {['low', 'medium', 'high'].map((p) => (
                          <button
                            key={p}
                            type="button"
                            onClick={() => setPriority(idx, p)}
                            className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold capitalize transition ${
                              place.priority === p
                                ? p === 'high'
                                  ? 'bg-red-100 text-red-700'
                                  : p === 'medium'
                                    ? 'bg-amber-100 text-amber-800'
                                    : 'bg-green-100 text-green-700'
                                : 'bg-white hover:bg-gray-100 text-[#1E2229]/60 border border-[#EAE3D2]'
                            }`}
                          >
                            {p}
                          </button>
                        ))}
                      </div>

                      {/* Saved Places list */}
                      {savedPlaces.length > 0 && (
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              const found = savedPlaces.find((sp) => sp.place_id === e.target.value);
                              if (found) selectSavedPlace(found, idx);
                            }
                            e.target.value = '';
                          }}
                          className="p-1 rounded border border-[#EAE3D2] bg-white text-[9px] text-[#1E2229]/75 max-w-[125px]"
                        >
                          <option value="">★ Add Saved Place...</option>
                          {savedPlaces.map((sp) => (
                            <option key={sp.place_id} value={sp.place_id}>
                              {sp.place_name.split(',')[0]}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Add Stop Button */}
              <button
                type="button"
                onClick={addPlaceInput}
                disabled={places.length >= 6}
                className="w-full py-3 border border-dashed border-[#2D6A8F]/40 text-[#2D6A8F] hover:bg-[#2D6A8F]/5 text-xs font-mono font-bold rounded-xl flex items-center justify-center gap-1.5 transition disabled:opacity-40 cursor-pointer"
              >
                <Plus size={14} /> Add Next Destination (Max 6)
              </button>
            </div>

            {/* FULL Anchor Event Form Block */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[#EAE3D2]/60">
                <h2 className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-2">
                  <Clock size={14} /> Locked Anchor Event
                </h2>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={anchorEnabled}
                    onChange={(e) => {
                      setAnchorEnabled(e.target.checked);
                      if (!e.target.checked) {
                        setIsAnchorLocked(false);
                      }
                    }}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#C85A32]"></div>
                </label>
              </div>

              <AnimatePresence>
                {anchorEnabled && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden space-y-3"
                  >
                    {isAnchorLocked ? (
                      <div className="bg-emerald-50/50 border border-emerald-100 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                        <div className="flex items-start gap-2.5">
                          <div className="p-2 bg-emerald-500 text-white rounded-lg mt-0.5 shadow-sm">
                            <CheckCircle size={16} />
                          </div>
                          <div>
                            <span className="text-[10px] font-mono font-bold text-emerald-800 uppercase tracking-wider block">✓ Event Locked</span>
                            <h4 className="text-xs font-bold text-[#1E2229] mt-0.5">
                              {anchorEvent.event_name || 'Fixed Event'}
                            </h4>
                            <p className="text-[10px] text-[#1E2229]/65 mt-1 font-medium">
                              📍 {anchorEvent.place_name || 'Churchgate'}
                            </p>
                            <p className="text-[10px] text-[#1E2229]/60 mt-0.5 font-mono">
                              ⏰ {anchorEvent.time || '19:00'} • ⏳ {anchorEvent.duration_mins || 60} mins • ⏱️ {anchorEvent.arrival_buffer || 0}m buffer
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setIsAnchorLocked(false)}
                          className="self-end md:self-center px-3 py-1.5 text-[10px] font-mono font-bold uppercase text-[#C85A32] border border-[#C85A32]/20 hover:border-[#C85A32]/40 hover:bg-[#C85A32]/5 rounded-lg transition"
                        >
                          Edit Event
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <p className="text-[10px] text-[#1E2229]/60 leading-normal">
                          Specify an event lock (e.g. Dinner bookings, tours, concerts). The system will schedule travel buffers to ensure you reach the venue before the event starts.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <label className="text-[9px] font-bold text-[#1E2229]/65 block mb-1">Event Type / Name</label>
                            <input
                              type="text"
                              value={anchorEvent.event_name || ''}
                              placeholder="e.g. Leopold Cafe Dinner"
                              onChange={(e) => setAnchorEvent({ ...anchorEvent, event_name: e.target.value })}
                              className="w-full p-2 rounded-lg border border-[#EAE3D2] text-xs text-[#1E2229] font-medium"
                            />
                          </div>
                          <div>
                            <label className="text-[9px] font-bold text-[#1E2229]/65 block mb-1">Target Time</label>
                            <input
                              type="time"
                              value={anchorEvent.time || ''}
                              onChange={(e) => setAnchorEvent({ ...anchorEvent, time: e.target.value })}
                              className="w-full p-2 rounded-lg border border-[#EAE3D2] text-xs font-mono text-[#1E2229]"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-[9px] font-bold text-[#1E2229]/65 block mb-1">Duration</label>
                            <select
                              value={anchorEvent.duration_mins || 60}
                              onChange={(e) => setAnchorEvent({ ...anchorEvent, duration_mins: Number(e.target.value) })}
                              className="w-full p-2 rounded-lg border border-[#EAE3D2] text-xs"
                            >
                              <option value={30}>30 mins</option>
                              <option value={60}>1 hour</option>
                              <option value={90}>1.5 hours</option>
                              <option value={120}>2 hours</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-[9px] font-bold text-[#1E2229]/65 block mb-1">Arrival Buffer</label>
                            <select
                              value={anchorEvent.arrival_buffer || 0}
                              onChange={(e) => setAnchorEvent({ ...anchorEvent, arrival_buffer: Number(e.target.value) })}
                              className="w-full p-2 rounded-lg border border-[#EAE3D2] text-xs text-[#C85A32] font-semibold"
                            >
                              <option value={0}>On Time</option>
                              <option value={15}>15 mins early</option>
                              <option value={30}>30 mins early</option>
                              <option value={45}>45 mins early</option>
                              <option value={60}>1 hour early</option>
                            </select>
                          </div>
                        </div>

                        <div>
                          <label className="text-[9px] font-bold text-[#1E2229]/65 block mb-1">Location Address</label>
                          <div className="relative">
                            <input
                              type="text"
                              placeholder="Search address for the event..."
                              value={anchorEvent.place_name || ''}
                              onChange={(e) => {
                                setAnchorEvent({ ...anchorEvent, place_name: e.target.value });
                                setActiveSearchIndex('anchor');
                                handleSearch(e.target.value, 'anchor');
                              }}
                              className="w-full p-2.5 rounded-lg border border-[#EAE3D2] text-xs text-[#1E2229]"
                            />

                            {/* Dropdown for Geocoder Autocomplete results */}
                            {activeSearchIndex === 'anchor' && (searchResults.length > 0 || searchLoading) && (
                              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#EAE3D2] rounded-lg shadow-lg z-50 py-1 max-h-48 overflow-y-auto">
                                {searchLoading && (
                                  <div className="px-3 py-2 text-[10px] text-[#1E2229]/60 italic">Searching locations...</div>
                                )}
                                {searchResults.map((resultItem, sIdx) => (
                                  <button
                                    key={sIdx}
                                    type="button"
                                    onClick={() => selectSearchResult(resultItem, 'anchor')}
                                    className="w-full text-left px-3 py-2.5 text-xs hover:bg-[#FBF9F6] text-[#1E2229] border-b border-[#EAE3D2]/30 last:border-0 font-medium"
                                  >
                                    📍 {resultItem.label}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* CTA button */}
                        <div className="pt-2">
                          <button
                            type="button"
                            onClick={() => {
                              if (!anchorEvent.event_name?.trim()) {
                                setError('Please enter a valid event type or name.');
                                return;
                              }
                              if (!anchorEvent.time) {
                                setError('Please select a target time for your anchor event.');
                                return;
                              }
                              if (!anchorEvent.lat || !anchorEvent.lng || !anchorEvent.place_name?.trim()) {
                                setError('Please search and select a valid location address for your anchor event.');
                                return;
                              }
                              setError(null);
                              setIsAnchorLocked(true);
                            }}
                            className="w-full py-2.5 px-4 bg-[#C85A32] text-white hover:bg-[#B04C27] active:scale-[0.98] font-mono text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-sm transition-all"
                          >
                            <Lock size={12} /> Lock Event & Refresh Plan
                          </button>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Simulated Live Disruption Panel */}
            <div className="bg-[#A54422]/10 border border-[#A54422]/20 rounded-2xl p-6 shadow-sm space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-mono font-bold text-[#A54422] uppercase flex items-center gap-2">
                  <AlertTriangle size={14} /> Live Disruption Simulation
                </h3>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={disruptionEnabled}
                    onChange={(e) => setDisruptionEnabled(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#A54422]"></div>
                </label>
              </div>
              <p className="text-[10px] text-[#A54422]/90 leading-relaxed">
                Toggling this simulates real-time traffic jams, metro delays, or weather disruptions, automatically adjusting the travel timeline and showing detours.
              </p>
            </div>

            {/* Save Day Plan Trigger */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm flex items-center justify-between">
              <span className="text-[10px] font-mono text-[#1E2229]/50">
                {saveStatus ? saveStatus : 'Save day plan to database'}
              </span>
              <button
                type="button"
                onClick={handleSavePlan}
                className="px-4 py-2 bg-[#1E3F2E] hover:bg-[#2c5b43] text-white font-bold rounded-lg text-xs flex items-center gap-2 transition cursor-pointer"
              >
                <Save size={12} /> Save Plan
              </button>
            </div>

          </div>

          {/* RIGHT COLUMN: Map, Health Score, Route Option Comparison, Timeline */}
          <div className="lg:col-span-7 space-y-6">
            
            {/* Interactive Map Component */}
            {(() => {
              const suggestedPlacesForMap = [];
              if (result && result.timeline) {
                result.timeline.forEach((item, idx) => {
                  if (item.type === 'buffer' && Array.isArray(item.recommendations)) {
                    const activeOptionId = selectedWaitGapOptions[idx] || item.recommendations[0]?.id;
                    const activeOption = item.recommendations.find(opt => opt.id === activeOptionId);
                    if (activeOption && activeOption.places) {
                      suggestedPlacesForMap.push(...activeOption.places);
                    }
                  }
                });
              }
              return (
                <div className="bg-white border border-[#EAE3D2] rounded-2xl p-4 shadow-sm h-[400px] lg:h-[450px]">
                  <SmartMap
                    places={result?.optimized_places || places.filter((p) => p.lat && p.lng)}
                    legs={result?.legs}
                    disruptionEnabled={disruptionEnabled}
                    disruptedLegIndex={result?.summary?.disrupted_leg_index}
                    highlightedPlaceName={highlightedPlaceName}
                    suggestedPlaces={suggestedPlacesForMap}
                    onMarkerClick={handleMarkerClick}
                  />
                </div>
              );
            })()}

            {/* Route Summary Box */}
            {result?.summary && (
              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm">
                <div className="flex flex-col justify-between w-full space-y-4">
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-3 rounded-xl bg-[#FBF9F6] border border-[#EAE3D2]/80">
                      <span className="text-[9px] font-mono uppercase text-[#1E2229]/45">Transit time</span>
                      <p className="text-sm font-bold text-[#1E2229] mt-1">
                        {result.summary.total_travel_time_mins} mins
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#FBF9F6] border border-[#EAE3D2]/80">
                      <span className="text-[9px] font-mono uppercase text-[#1E2229]/45">Transit Cost (INR)</span>
                      <p className="text-sm font-bold text-[#C85A32] mt-1">
                        ₹{result.summary.total_cost_inr}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#FBF9F6] border border-[#EAE3D2]/80">
                      <span className="text-[9px] font-mono uppercase text-[#1E2229]/45">Total Walk Distance</span>
                      <p className="text-sm font-bold text-[#1E3F2E] mt-1">
                        {(result.summary.total_walk_m / 1000).toFixed(1)} km
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-xs font-mono border-t border-[#EAE3D2]/50 pt-3 px-1">
                    <div>
                      <span className="text-[#1E2229]/50">Start Time:</span> <strong className="text-[#1E2229]/80">{result.summary.start_time} AM</strong>
                    </div>
                    <div>
                      <span className="text-[#1E2229]/50">End Time:</span> <strong className="text-[#1E2229]/80">{result.summary.end_time}</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Smart Travel Insights & Proximity Alerts Panel */}
            {result?.smart_insights && (
              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm space-y-4">
                <h3 className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-2 pb-2 border-b border-[#EAE3D2]/50">
                  <Activity size={14} className="text-[#2D6A8F]" /> Smart Travel Insights
                </h3>

                {/* Proximity Warning items */}
                {result.proximity_alerts?.length > 0 && (
                  <div className="space-y-2">
                    {result.proximity_alerts.map((alert, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                          alert.type === 'close'
                            ? 'bg-emerald-50/50 border-emerald-100 text-emerald-800'
                            : 'bg-amber-50/50 border-amber-100 text-amber-800'
                        }`}
                      >
                        {alert.type === 'close' ? <CheckCircle size={14} /> : <AlertTriangle size={14} />}
                        <span className="font-medium">{alert.message}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Routing & sunset suggestion items */}
                <div className="space-y-2.5">
                  {result.smart_insights.map((insight, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                        insight.type === 'warning'
                          ? 'bg-red-50/50 border-red-100 text-[#A54422]'
                          : insight.type === 'success'
                            ? 'bg-emerald-50/50 border-emerald-100 text-emerald-800'
                            : 'bg-blue-50/50 border-blue-100 text-[#2D6A8F]'
                      }`}
                    >
                      <Info size={14} className="shrink-0 mt-0.5" />
                      <p className="leading-relaxed font-medium">{insight.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ROUTE COMPARISON CARDS */}
            {result?.comparison_cards && (
              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm space-y-3">
                <h3 className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-2">
                  <Layers size={14} /> Route Option Comparison
                </h3>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {['fastest', 'budget', 'balanced'].map((styleId) => {
                    const comp = result.comparison_cards[styleId];
                    if (!comp) return null;
                    const styleMeta = STYLE_OPTIONS.find((s) => s.id === styleId);
                    const isActive = routeType === styleId;

                    return (
                      <button
                        key={styleId}
                        type="button"
                        onClick={() => setRouteType(styleId)}
                        className={`p-3.5 rounded-xl border text-left flex flex-col justify-between transition cursor-pointer ${
                          isActive
                            ? 'bg-[#1E3F2E] border-[#1E3F2E] text-white'
                            : 'bg-[#FBF9F6] border-[#EAE3D2]/80 text-[#1E2229] hover:bg-gray-50'
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-xs font-extrabold">{styleMeta?.title}</span>
                            <span className={`text-[8px] font-mono px-1 rounded uppercase font-bold ${
                              isActive ? 'bg-white/20 text-white' : 'bg-gray-200 text-gray-700'
                            }`}>
                              {comp.walk_level} Walk
                            </span>
                          </div>
                          
                          <p className={`text-[9px] font-bold ${isActive ? 'text-white/80' : 'text-[#C85A32]'}`}>
                            {comp.highlight}
                          </p>
                        </div>

                        <div className="mt-3 pt-2 border-t border-[#EAE3D2]/20 flex justify-between items-center text-[10px] font-mono font-semibold">
                          <span>⏱️ {comp.travel_time_mins}m</span>
                          <span>₹{comp.total_cost_inr}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Redesigned Premium Timeline */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm">
              <h3 className="text-xs font-mono font-bold text-[#1E3F2E] uppercase mb-6 flex flex-wrap items-center gap-2 pb-2 border-b border-[#EAE3D2]/60 w-full">
                <Layers size={14} /> Day Schedule Timeline
                {result?.summary?.real_traffic_active ? (
                  <span className="ml-auto inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[9px] font-mono font-bold border border-emerald-200">
                    🟢 Real Traffic Mode
                  </span>
                ) : result ? (
                  <span className="ml-auto inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-800 text-[9px] font-mono font-bold border border-gray-200">
                    ⚪ Simulation Fallback Mode
                  </span>
                ) : null}
              </h3>

              {!result ? (
                <div className="text-center py-12 text-[#1E2229]/50 text-xs">
                  <Map className="mx-auto text-[#EAE3D2] mb-3" size={24} />
                  Complete destinations to optimize your visual timeline.
                </div>
              ) : (
                <div className="relative border-l-2 border-[#EAE3D2] ml-4 pl-6 space-y-6">
                  {result.timeline.map((item, index) => {
                    const isAnchor = item.type === 'anchor_event';
                    const isBuffer = item.type === 'buffer';
                    
                    const cardTitle = item.place_name.split(',')[0];
                    const cardDetails = item.place_name.split(',').slice(1).join(',').trim();

                    return (
                      <div
                        key={index}
                        ref={(el) => {
                          if (el) timelineRefs.current[item.place_name] = el;
                        }}
                        className="relative group transition-all"
                      >
                        {/* Bullet Dot indicator */}
                        <div
                          className="absolute -left-[31px] top-2 w-4 h-4 rounded-full border-2 border-white shadow-sm flex items-center justify-center transition-transform group-hover:scale-110"
                          style={{
                            backgroundColor: isAnchor ? '#C85A32' : isBuffer ? '#D4AF37' : index === 0 ? '#1E3F2E' : '#2D6A8F',
                          }}
                        />

                        {/* Rich Timeline Card */}
                        <div
                          onClick={() => {
                            if (!isBuffer) setHighlightedPlaceName(item.place_name);
                          }}
                          className={`p-4 rounded-xl border transition-all cursor-pointer ${
                            isAnchor
                              ? 'bg-orange-50/30 border-[#C85A32] shadow-sm hover:shadow-md'
                              : isBuffer
                                ? 'bg-amber-50/20 border-dashed border-[#D4AF37]/60'
                                : 'bg-[#FBF9F6] border-[#EAE3D2] hover:shadow-md hover:bg-white'
                          }`}
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="flex-1">
                              {/* Small Category Badge */}
                              <div className="flex gap-2 items-center mb-1.5">
                                <span
                                  className={`inline-block px-2 py-0.5 rounded text-[8px] font-mono font-bold uppercase tracking-wider ${
                                    isAnchor
                                      ? 'bg-[#C85A32]/10 text-[#C85A32] border border-[#C85A32]/20'
                                      : isBuffer
                                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                        : index === 0
                                          ? 'bg-green-100 text-green-800'
                                          : 'bg-blue-100 text-blue-800'
                                  }`}
                                >
                                  {isAnchor ? '🔒 Locked meeting' : isBuffer ? '⏱️ Wait buffer' : `Stop #${index + 1}`}
                                </span>
                                
                                {item.priority && (
                                  <span className="text-[7px] font-mono uppercase text-gray-400">
                                    • {item.priority} priority
                                  </span>
                                )}
                              </div>
                              
                              <h4 className="text-xs font-bold text-[#1E2229] leading-snug">
                                {cardTitle}
                              </h4>
                              
                              {cardDetails && (
                                <p className="text-[10px] text-[#1E2229]/50 mt-0.5">
                                  {cardDetails}
                                </p>
                              )}

                              {isBuffer && (
                                <div className="mt-2 space-y-2">
                                  <p className="text-[10px] text-amber-800/80 italic leading-relaxed">
                                    {item.description || 'Pacing buffer time.'}
                                  </p>
                                  {item.recommendations && Array.isArray(item.recommendations) && (
                                    <div className="bg-[#FAF6EE] border border-[#EAE3D2] rounded-xl p-3 mt-2 space-y-2 text-left shadow-sm">
                                      <span className="text-[9px] font-mono font-bold uppercase text-[#C85A32] tracking-wide block mb-1">
                                        💡 Local Wait Gap Suggestions
                                      </span>
                                      
                                      {/* Interactive Tabs */}
                                      <div className="flex border-b border-[#EAE3D2] mb-3">
                                        {item.recommendations.map((opt) => {
                                          const activeOptionId = selectedWaitGapOptions[index] || item.recommendations[0]?.id;
                                          return (
                                            <button
                                              key={opt.id}
                                              type="button"
                                              onClick={(e) => {
                                                e.stopPropagation(); // Avoid highlighting parent container click
                                                setSelectedWaitGapOptions({
                                                  ...selectedWaitGapOptions,
                                                  [index]: opt.id,
                                                });
                                              }}
                                              className={`flex-1 py-1.5 text-[9px] font-bold uppercase border-b-2 transition-all flex items-center justify-center gap-1 cursor-pointer ${
                                                activeOptionId === opt.id
                                                  ? 'border-[#C85A32] text-[#C85A32]'
                                                  : 'border-transparent text-[#1E2229]/50 hover:text-[#1E2229]'
                                              }`}
                                            >
                                              <span>{opt.emoji}</span>
                                              <span>{opt.title.split(' ')[0]}</span>
                                            </button>
                                          );
                                        })}
                                      </div>

                                      {/* Selected Tab Content */}
                                      {(() => {
                                        const activeOptionId = selectedWaitGapOptions[index] || item.recommendations[0]?.id;
                                        const activeOption = item.recommendations.find(opt => opt.id === activeOptionId) || item.recommendations[0];
                                        return (
                                          <div className="space-y-2">
                                            <p className="text-[10px] font-medium text-[#1E2229]/80 leading-normal">
                                              {activeOption.description}
                                            </p>
                                            {activeOption.itinerary && (
                                              <div className="p-2 bg-white border border-[#EAE3D2]/45 rounded-lg text-[9px] text-[#1E2229]/75 font-mono leading-relaxed">
                                                {activeOption.itinerary}
                                              </div>
                                            )}
                                            {activeOption.places && activeOption.places.length > 0 && (
                                              <div className="pt-1.5">
                                                <span className="text-[8px] font-mono uppercase text-[#1E2229]/50 block mb-1.5">Recommended Spots:</span>
                                                <div className="space-y-1">
                                                  {activeOption.places.map((place, pIdx) => (
                                                    <div key={pIdx} className="flex justify-between items-center bg-white p-1.5 rounded-lg border border-[#EAE3D2]/50 text-[10px]">
                                                      <span className="font-semibold text-[#1E3F2E] flex items-center gap-1">
                                                        <span>{place.emoji}</span>
                                                        <span>{place.name.split('(')[0].trim()}</span>
                                                      </span>
                                                      <span className="font-mono text-gray-400 text-[8px]">
                                                        {place.distance_km} km
                                                      </span>
                                                    </div>
                                                  ))}
                                                </div>
                                              </div>
                                            )}
                                          </div>
                                        );
                                      })()}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>

                            {/* Timeline times */}
                            <div className="text-right shrink-0">
                              <div className="text-xs font-mono font-bold text-[#1E3F2E] flex items-center gap-1">
                                <Clock size={11} /> {item.arrival_time} - {item.departure_time}
                              </div>
                              <span className="text-[9px] font-mono text-[#1E2229]/50 block mt-0.5">
                                duration: {item.duration_mins} mins
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Render travel segment to next stop if not last */}
                        {index < result.timeline.length - 1 && (() => {
                          const leg = result.legs.find(l => 
                            l.start_place_name === item.place_name || 
                            l.start_place_name.toLowerCase().includes(item.place_name.toLowerCase().split(',')[0])
                          );
                          if (!leg) return null;
                          const legIdx = result.legs.indexOf(leg);
                          const isLegDisrupted = disruptionEnabled && legIdx === result.summary.disrupted_leg_index;
                          
                          return (
                            <div className="my-4 ml-2 p-3 bg-white border border-[#EAE3D2]/70 rounded-xl text-xs space-y-2 relative shadow-sm hover:border-[#2D6A8F]/40 transition">
                              
                              {/* Left line mode indicator */}
                              <div className="flex flex-wrap items-center justify-between text-[11px] font-mono font-semibold">
                                <span className={`flex items-center gap-1.5 px-2 py-0.5 border rounded-lg ${getTransportColorClass(leg.recommended_mode)}`}>
                                  {getTransportIcon(leg.recommended_mode)}
                                  <span>{leg.recommended_mode}</span>
                                </span>
                                <span className="text-[#1E2229]/50 flex items-center gap-1">
                                  📏 {(leg.distance_m / 1000).toFixed(2)} km
                                </span>
                              </div>

                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[#EAE3D2]/45 text-[10px] font-mono">
                                <div>
                                  <span className="text-[#1E2229]/40 block text-[9px] uppercase">Schedule</span>
                                  <span className="font-bold text-[#1E2229]/85">{leg.departure_time || '00:00'} - {leg.arrival_time || '00:00'}</span>
                                </div>
                                <div>
                                  <span className="text-[#1E2229]/40 block text-[9px] uppercase">Duration</span>
                                  <span className="font-bold text-[#1E2229]/85">{leg.duration_mins} mins</span>
                                </div>
                                <div>
                                  <span className="text-[#1E2229]/40 block text-[9px] uppercase">Traffic Status</span>
                                  <span className={`inline-block px-1.5 py-0.2 rounded font-bold ${
                                    leg.traffic_status === 'Heavy'
                                      ? 'bg-red-50 text-red-700 border border-red-200/50'
                                      : leg.traffic_status === 'Moderate'
                                        ? 'bg-amber-50 text-amber-700 border border-amber-200/50'
                                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200/50'
                                  }`}>
                                    {leg.traffic_status || 'Clear'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[#1E2229]/40 block text-[9px] uppercase">Confidence</span>
                                  <span className={`font-bold ${
                                    leg.confidence === 'High' ? 'text-[#1E3F2E]' : 'text-[#C85A32]'
                                  }`}>
                                    🛡️ {leg.confidence || 'High'}
                                  </span>
                                </div>
                              </div>

                              {leg.recommended_mode?.toLowerCase().includes('cab') && (
                                <div className="text-[10px] font-mono text-[#C85A32] font-bold pt-1 text-right">
                                  Est. Fare: {getTaxiFareEstimate(leg.distance_m)}
                                </div>
                              )}

                              {/* Traffic delay indicator */}
                              {leg.traffic_buffer_added && (
                                <div className="text-[9px] text-amber-700 font-mono italic">
                                  ⚠️ Injected +{leg.traffic_buffer_added}m transit buffer for travel jump
                                </div>
                              )}

                              {/* Warnings & disruption details */}
                              {leg.disruption && (
                                <div className="mt-2.5 p-3 bg-[#A54422]/10 border border-[#A54422]/20 rounded-lg text-[10px] text-[#A54422] space-y-1">
                                  <div className="font-bold flex items-center gap-1.5">
                                    <AlertTriangle size={12} /> Disruption: {leg.disruption.title}
                                  </div>
                                  <p className="opacity-90">{leg.disruption.message}</p>
                                  <div className="pt-1.5 border-t border-[#A54422]/15 font-semibold text-[9px] uppercase tracking-wider flex justify-between">
                                    <span>detour option</span>
                                    <span>{leg.disruption.alternative_mode} (+{leg.disruption.delay_mins}m)</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })()}

                      </div>
                    );
                  })}
                </div>
              )}
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}
