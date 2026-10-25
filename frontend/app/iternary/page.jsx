"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plane, Calendar, MapPin, DollarSign, ArrowLeft, ArrowRight, Compass, Sparkles, BookOpen } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { saveTrip } from "@/lib/tripsApi";

export default function HolidayItinerary() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [formStep, setFormStep] = useState(0);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [location, setLocation] = useState("");
  const [departureLocation, setDepartureLocation] = useState("");
  const [budget, setBudget] = useState("150000");
  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveMessage, setSaveMessage] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [savingTrip, setSavingTrip] = useState(false);
  const [tripSaved, setTripSaved] = useState(false);

  const [selectedCurrency, setSelectedCurrency] = useState("INR");
  const [exchangeRates, setExchangeRates] = useState({
    INR: 1,
    USD: 0.012,
    EUR: 0.011,
    GBP: 0.0094,
    JPY: 1.83,
    SGD: 0.016,
    AED: 0.044
  });

  const currencies = [
    { code: "INR", flag: "🇮🇳", label: "INR (default)" },
    { code: "USD", flag: "🇺🇸", label: "USD" },
    { code: "EUR", flag: "🇪🇺", label: "EUR" },
    { code: "GBP", flag: "🇬🇧", label: "GBP" },
    { code: "JPY", flag: "🇯🇵", label: "JPY" },
    { code: "SGD", flag: "🇸🇬", label: "SGD" },
    { code: "AED", flag: "🇦🇪", label: "AED" }
  ];

  useEffect(() => {
    const fetchRates = async () => {
      try {
        const cached = localStorage.getItem("ainomad_rates");
        const cachedTime = localStorage.getItem("ainomad_rates_time");
        const oneHour = 60 * 60 * 1000;
        
        if (cached && cachedTime && (Date.now() - Number(cachedTime) < oneHour)) {
          setExchangeRates(JSON.parse(cached));
          return;
        }
        
        const res = await fetch("https://open.er-api.com/v6/latest/INR");
        if (!res.ok) throw new Error("API failed");
        const data = await res.json();
        if (data && data.rates) {
          const rates = {
            INR: 1,
            USD: data.rates.USD || 0.012,
            EUR: data.rates.EUR || 0.011,
            GBP: data.rates.GBP || 0.0094,
            JPY: data.rates.JPY || 1.83,
            SGD: data.rates.SGD || 0.016,
            AED: data.rates.AED || 0.044
          };
          setExchangeRates(rates);
          localStorage.setItem("ainomad_rates", JSON.stringify(rates));
          localStorage.setItem("ainomad_rates_time", String(Date.now()));
        }
      } catch (err) {
        console.error("Failed to fetch exchange rates:", err);
      }
    };
    fetchRates();
  }, []);

  const formatINR = (value) => {
    const num = Math.round(Number(value));
    if (isNaN(num)) return `₹0`;
    const str = num.toString();
    const lastThree = str.substring(str.length - 3);
    const otherParts = str.substring(0, str.length - 3);
    if (otherParts !== '') {
      const formatted = otherParts.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + lastThree;
      return `₹${formatted}`;
    }
    return `₹${lastThree}`;
  };

  const convertINRText = (text, targetCurrency, rate) => {
    if (!text || typeof text !== 'string') return text;
    if (targetCurrency === 'INR' || !rate) return text;

    const currencySymbols = {
      USD: '$',
      EUR: '€',
      GBP: '£',
      JPY: '¥',
      SGD: 'S$',
      AED: 'AED '
    };
    const symbol = currencySymbols[targetCurrency] || '';

    const formatConverted = (inrVal) => {
      const converted = inrVal * rate;
      if (targetCurrency === 'JPY') {
        return `${symbol}${Math.round(converted).toLocaleString('ja-JP')} JPY`;
      } else {
        return `${symbol}${converted.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")} ${targetCurrency}`;
      }
    };

    const priceRegex = /(?:₹|INR)\s*([\d,]+(?:\.\d+)?)/gi;
    const matches = [...text.matchAll(priceRegex)];
    if (matches.length > 0) {
      let parts = [];
      let lastIndex = 0;
      
      for (const match of matches) {
        const matchIndex = match.index;
        const rawValue = match[1];
        const inrValue = parseFloat(rawValue.replace(/,/g, ''));
        
        parts.push(text.substring(lastIndex, matchIndex));
        
        if (!isNaN(inrValue)) {
          parts.push(formatConverted(inrValue));
        } else {
          parts.push(match[0]);
        }
        
        lastIndex = matchIndex + match[0].length;
      }
      parts.push(text.substring(lastIndex));
      
      const firstMatch = matches[0];
      const lastMatch = matches[matches.length - 1];
      const startPos = firstMatch.index;
      const endPos = lastMatch.index + lastMatch[0].length;
      
      const originalPriceBlock = text.substring(startPos, endPos);
      const convertedPriceBlock = parts.join('').substring(startPos, parts.join('').length - (text.length - endPos));
      
      const replacement = `${convertedPriceBlock} (${originalPriceBlock} original)`;
      
      return text.substring(0, startPos) + replacement + text.substring(endPos);
    }

    return text;
  };

  const convertPrice = (priceText) => {
    if (selectedCurrency === "INR") return priceText;
    const rate = exchangeRates[selectedCurrency];
    return convertINRText(priceText, selectedCurrency, rate);
  };

  const openFlightBooking = (flight) => {
    const airlineLow = (flight?.airline || "").toLowerCase().trim();
    const airlineMappings = {
      "air india": "https://www.airindia.com",
      "qatar airways": "https://www.qatarairways.com",
      "emirates": "https://www.emirates.com",
      "singapore airlines": "https://www.singaporeair.com",
      "indigo": "https://www.goindigo.in",
      "lufthansa": "https://www.lufthansa.com",
      "etihad": "https://www.etihad.com",
      "british airways": "https://www.britishairways.com",
      "turkish airlines": "https://www.turkishairlines.com"
    };

    let link = "";

    // 1. Map to official airline website if known
    for (const [key, officialUrl] of Object.entries(airlineMappings)) {
      if (airlineLow.includes(key) || key.includes(airlineLow)) {
        link = officialUrl;
        break;
      }
    }

    // 2. Validate booking_url if provided
    if (!link && flight?.booking_url) {
      const urlLow = flight.booking_url.toLowerCase();
      const isBlocked = ["airtrfx.com", "affiliate", "adsystem", "clickserve", "doubleclick", "adroll", "partner", "promo", "redirect", "track", "click", "ad"].some(k => urlLow.includes(k));
      
      const trustedBookingPlatforms = ["google.com/travel/flights", "google.co.in/travel/flights", "skyscanner.co.in", "skyscanner.com", "makemytrip.com", "booking.com/flights", "kayak.com"];
      const isTrustedPlatform = trustedBookingPlatforms.some(p => urlLow.includes(p));
      
      const officialDomains = [
        "singaporeair.com", "qatarairways.com", "emirates.com", "airindia.com", "goindigo.in", 
        "lufthansa.com", "etihad.com", "britishairways.com", "turkishairlines.com", "spicejet.com",
        "jal.co.jp", "ana.co.jp", "cathaypacific.com", "thaiairways.com", "malaysiaairlines.com",
        "gulfair.com", "airasia.com", "flyscoot.com", "vietjetair.com", "srilankan.com", "airfrance.com", "klm.com"
      ];
      const isOfficialDomain = officialDomains.some(d => urlLow.includes(d));

      if (!isBlocked && (isTrustedPlatform || isOfficialDomain)) {
        link = flight.booking_url;
      }
    }

    // 3. Fallback to Google Flights
    if (!link) {
      link = `https://www.google.com/travel/flights?q=${encodeURIComponent(
        `Flights ${flight?.departure?.split(" - ")[0] || ""} to ${flight?.arrival?.split(" - ")[0] || ""}`
      )}`;
    }

    window.open(link, "_blank");
  };

  const openHotelBooking = (hotel) => {
    const url =
      hotel?.official_url ||
      `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(
        `${hotel?.name || ""} ${location || ""}`
      )}`;
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  };

  const fetchItinerary = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch("/api/itinerary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          start_date: startDate, 
          end_date: endDate, 
          location, 
          departure_location: departureLocation, 
          budget 
        })
      });
      
      let data;
      const rawText = await response.text();
      try {
        data = rawText ? JSON.parse(rawText) : {};
      } catch (parseErr) {
        console.error("[itinerary] Response is not valid JSON:", parseErr, rawText?.slice(0, 200));
        throw new Error("Could not read itinerary response. Please try again.");
      }

      if (!response.ok) {
        throw new Error(data?.error || "Failed to generate itinerary");
      }

      if (data?.error) {
        throw new Error(data.error);
      }

      console.log("RAW ITINERARY RESPONSE:", data);
      console.log("DATA KEYS:", Object.keys(data || {}));
      console.log("DAYS:", data?.days);
      console.log("FLIGHTS:", data?.flights);
      console.log("HOTELS:", data?.hotels);
      console.log("VISA:", data?.visa_details);
      console.log("NESTED ITINERARY:", data?.itinerary);

      const normalizedItinerary = data?.itinerary || data;

      console.log("NORMALIZED:", normalizedItinerary);

      setItinerary({
        flights: normalizedItinerary?.flights || [],
        hotels: normalizedItinerary?.hotels || [],
        days: normalizedItinerary?.days || [],
        visa_details: normalizedItinerary?.visa_details || {},
        ...normalizedItinerary
      });
      setFormStep(5);
    } catch (err) {
      console.error("[itinerary] Scrapbook generation error:", err);
      setError(err.message || "An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    fetchItinerary();
  };
  
  const handleNextStep = () => {
    setFormStep(prev => Math.min(prev + 1, 4));
  };
  
  const handlePrevStep = () => {
    setFormStep(prev => Math.max(prev - 1, 0));
  };
  
  const resetForm = () => {
    setFormStep(0);
    setItinerary(null);
    setSaveMessage(null);
    setSaveError(null);
    setTripSaved(false);
  };

  const handleSaveTrip = async () => {
    if (!isAuthenticated || !user?.id) {
      router.push(`/login?next=${encodeURIComponent("/iternary")}`);
      return;
    }
    if (savingTrip || tripSaved) return;

    setSavingTrip(true);
    setSaveMessage(null);
    setSaveError(null);

    try {
      await saveTrip({
        userId: user.id,
        destination: location || itinerary?.destination || "Trip",
        startDate: startDate || null,
        endDate: endDate || null,
        budget: budget ? Number(String(budget).replace(/[^\d.]/g, "")) : null,
        readinessScore: itinerary?.readiness_score ?? null,
        overspendingRisk: itinerary?.overspending_risk ?? null,
      });
      setTripSaved(true);
      setSaveMessage("Trip saved successfully ✈️");
    } catch (err) {
      setSaveError(err.message || "Could not save trip.");
    } finally {
      setSavingTrip(false);
    }
  };
  
  const formContent = [
    {
      title: "Where are we heading?",
      subtitle: "Specify your next destination and where you will embark from",
      icon: "🧭",
      field: (
        <div className="w-full space-y-4">
          <div>
            <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">Target Destination</label>
            <div className="relative">
              <input 
                type="text" 
                value={location} 
                onChange={(e) => setLocation(e.target.value)} 
                className="w-full p-4 pl-12 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none shadow-inner placeholder-[#1E2229]/40 font-sans"
                placeholder="e.g. Kyoto, Japan or Tuscany, Italy"
                required
              />
              <MapPin size={18} className="absolute left-4 top-4.5 text-[#C85A32]" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">Embarkation Point</label>
            <div className="relative">
              <input 
                type="text" 
                value={departureLocation} 
                onChange={(e) => setDepartureLocation(e.target.value)} 
                className="w-full p-4 pl-12 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none shadow-inner placeholder-[#1E2229]/40 font-sans"
                placeholder="e.g. JFK New York or London Heathrow"
                required
              />
              <span className="absolute left-4 top-3.5 text-lg">🏠</span>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Select your dates",
      subtitle: "Determine when this journey takes place",
      icon: "🗓️",
      field: (
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">Departure Date</label>
            <div className="relative">
              <input 
                type="date" 
                value={startDate} 
                onChange={(e) => setStartDate(e.target.value)} 
                className="w-full p-4 pl-12 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none shadow-inner font-sans" 
                required
              />
              <Calendar size={18} className="absolute left-4 top-4.5 text-[#C85A32]" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">Return Date</label>
            <div className="relative">
              <input 
                type="date" 
                value={endDate} 
                onChange={(e) => setEndDate(e.target.value)} 
                className="w-full p-4 pl-12 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none shadow-inner font-sans" 
                required
              />
              <Calendar size={18} className="absolute left-4 top-4.5 text-[#C85A32]" />
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Set your resources",
      subtitle: "Configure your budget threshold for accommodations and transit",
      icon: "🪙",
      field: (
        <div className="w-full mt-2">
          <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-3">Estimated Budget Range</label>
          <div className="relative pt-2">
            <input 
              type="range" 
              min="10000" 
              max="1000000" 
              step="10000" 
              value={budget || 150000} 
              onChange={(e) => setBudget(e.target.value)} 
              className="w-full h-2 bg-[#EAE3D2] rounded-full appearance-none cursor-pointer accent-[#C85A32]"
            />
            <div className="flex justify-between text-xs text-[#1E2229]/60 mt-3 font-mono">
              <span>₹10,000</span>
              <span>₹10,00,000+</span>
            </div>
            <div className="text-center mt-6">
              <span className="text-5xl font-bold font-display text-[#C85A32] flex items-center justify-center gap-1">
                {formatINR(budget || 150000)}
              </span>
              <p className="text-xs text-[#1E2229]/50 mt-1 font-mono">Total Estimated Funds</p>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Verify Logbook Entry",
      subtitle: "Confirm details before generating your travel scrapbook",
      icon: "✍️",
      field: (
        <div className="w-full text-center py-4 bg-[#FBF9F6] rounded-xl border border-[#EAE3D2] p-6 space-y-4">
          <div className="text-[#1E2229]/80 text-sm leading-relaxed max-w-md mx-auto">
            We will compile matching flights, boutique stays, and structured days tailored to your goals.
          </div>
          <div className="inline-flex flex-wrap items-center justify-center gap-3 bg-white px-4 py-2.5 rounded-full border border-[#EAE3D2] text-[#1E2229] shadow-sm text-sm">
            <span className="font-bold text-[#1E3F2E]">📍 {location}</span>
            <span className="text-[#EAE3D2]">|</span>
            <span className="font-mono text-xs">{startDate} to {endDate}</span>
            <span className="text-[#EAE3D2]">|</span>
            <span className="font-bold text-[#C85A32]">{formatINR(budget || 150000)}</span>
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 relative font-sans">
      {/* Background paper layout grids */}
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-60"></div>
      
      <div className="max-w-4xl mx-auto px-6 relative z-10">
        {/* Header */}
        <div className="mb-12 text-center pt-8">
          <h1 className="text-4xl md:text-5xl font-bold text-[#1E2229] font-display">Itinerary Planner</h1>
        </div>
        
        {/* Loading State */}
        {loading && (
          <div className="fixed inset-0 bg-[#FBF9F6]/90 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="text-center p-8 bg-white border border-[#EAE3D2] rounded-2xl max-w-md w-full shadow-xl">
              <div className="relative w-28 h-28 mx-auto mb-6">
                <div className="w-full h-full rounded-full border-4 border-[#C85A32]/25 border-t-[#C85A32] animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center text-4xl">
                  🧭
                </div>
              </div>
              <div className="text-2xl font-bold font-display text-[#1E3F2E] mb-2">Drafting Itinerary...</div>
              <div className="text-sm text-[#1E2229]/75">Retrieving routes, accommodations, and visa guidelines</div>
            </div>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <div className="fixed inset-0 bg-[#FBF9F6]/90 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="text-center p-8 bg-white border border-red-200 rounded-2xl max-w-md w-full shadow-xl">
              <div className="text-5xl mb-4">⚠️</div>
              <div className="text-lg font-bold text-red-600 mb-2">Scrapbook Generation Error</div>
              <div className="text-sm text-[#1E2229]/75 mb-6">{error}</div>
              <button 
                onClick={() => setError(null)}
                className="px-6 py-2.5 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg text-red-600 font-bold transition-all text-sm"
              >
                Revise Form
              </button>
            </div>
          </div>
        )}
        
        {/* Multistep Form or Results */}
        {!itinerary ? (
          <div className="flex justify-center items-center min-h-[50vh]">
            <form onSubmit={handleSubmit} className="w-full max-w-xl">
              {/* Progress Dots */}
              <div className="mb-8 flex justify-center gap-3">
                {[0, 1, 2, 3].map((step) => (
                  <div 
                    key={step} 
                    className={`h-2.5 rounded-full transition-all duration-300 ${
                      formStep === step 
                        ? 'w-10 bg-[#C85A32]' 
                        : formStep > step 
                          ? 'w-2.5 bg-[#1E3F2E]' 
                          : 'w-2.5 bg-[#EAE3D2]'
                    }`}
                  />
                ))}
              </div>
              
              {/* Scrapbook Form Panel */}
              <div className="bg-white border border-[#EAE3D2] rounded-2xl shadow-[0_12px_40px_rgba(30,34,41,0.04)] p-8 relative overflow-hidden">
                {/* Vintage Tape Accent */}
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 w-28 h-6 bg-[#C85A32]/10 border-x border-[#C85A32]/25 rotate-1"></div>
                
                <div className="flex items-center gap-4 mb-6 pb-4 border-b border-[#EAE3D2]/50">
                  <div className="w-12 h-12 flex items-center justify-center bg-[#FBF9F6] border border-[#EAE3D2] rounded-xl text-2xl">
                    {formContent[formStep].icon}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold font-display text-[#1E2229]">{formContent[formStep].title}</h2>
                    <p className="text-xs text-[#1E2229]/50 font-sans mt-0.5">{formContent[formStep].subtitle}</p>
                  </div>
                </div>
                
                <div className="min-h-[160px] flex items-center">
                  {formContent[formStep].field}
                </div>
                
                {/* Form Nav Buttons */}
                <div className="flex justify-between mt-10 pt-4 border-t border-[#EAE3D2]/50">
                  {formStep > 0 ? (
                    <button 
                      type="button"
                      onClick={handlePrevStep}
                      className="px-5 py-2.5 border border-[#EAE3D2] hover:bg-[#FBF9F6] rounded-lg text-xs font-bold text-[#1E2229] transition-all flex items-center gap-2"
                    >
                      <ArrowLeft size={14} /> BACK
                    </button>
                  ) : (
                    <div />
                  )}
                  
                  <div>
                    {formStep < 3 ? (
                      <button 
                        type="button"
                        onClick={handleNextStep}
                        className="px-5 py-2.5 bg-[#1E3F2E] hover:bg-[#2D5A43] text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2 shadow-sm disabled:opacity-50"
                        disabled={
                          (formStep === 0 && (!location || !departureLocation)) ||
                          (formStep === 1 && (!startDate || !endDate)) ||
                          (formStep === 2 && !budget)
                        }
                      >
                        NEXT <ArrowRight size={14} />
                      </button>
                    ) : (
                      <button 
                        type="submit"
                        className="px-6 py-3 bg-[#C85A32] hover:bg-[#A54422] text-white rounded-lg text-sm font-bold transition-all flex items-center gap-2 shadow-md"
                      >
                        <Sparkles size={16} /> GENERATE JOURNAL
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </form>
          </div>
        ) : (
          <div className="space-y-12">
            {/* Scrapbook Header */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-8 text-center relative overflow-hidden shadow-sm">
              <div className="absolute -top-3 left-12 w-20 h-6 bg-[#1E3F2E]/10 border-x border-[#1E3F2E]/25 -rotate-2"></div>
              
              <div className="absolute top-4 right-4 z-20">
                <select
                  value={selectedCurrency}
                  onChange={(e) => setSelectedCurrency(e.target.value)}
                  className="bg-[#FBF9F6] border border-[#EAE3D2] hover:border-[#C85A32] text-xs font-mono font-bold text-[#1E2229] py-1 px-2 rounded outline-none cursor-pointer transition-colors shadow-sm"
                >
                  {currencies.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.flag} {c.label}
                    </option>
                  ))}
                </select>
              </div>

              <span className="text-[10px] font-bold font-mono tracking-widest text-[#C85A32] uppercase block mb-2">OFFICIAL PLANNED ESCAPE</span>
              <h2 className="text-4xl font-extrabold font-display text-[#1E3F2E] leading-tight">{location} Journal</h2>
              
              <div className="mt-6 flex flex-wrap justify-center items-center gap-6 text-sm text-[#1E2229]/80 font-sans border-t border-[#EAE3D2]/50 pt-6">
                <div className="flex items-center gap-2">
                  <span>🛫 Departure:</span>
                  <span className="font-mono text-xs font-bold">{departureLocation}</span>
                </div>
                <span className="hidden sm:inline text-[#EAE3D2]">|</span>
                <div className="flex items-center gap-2">
                  <span>🗓️ Schedule:</span>
                  <span className="font-mono text-xs font-bold">{startDate} to {endDate}</span>
                </div>
                <span className="hidden sm:inline text-[#EAE3D2]">|</span>
                <div className="flex items-center gap-2">
                  <span>💰 Funds:</span>
                  <span className="font-mono text-xs font-bold text-[#C85A32]">{convertPrice(formatINR(budget || 150000))}</span>
                </div>
              </div>
            </div>
            
            {/* Flights Boarding Pass Ticket */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl overflow-hidden shadow-sm">
              <div className="bg-[#1E3F2E] px-6 py-4 text-white flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <Plane size={18} className="rotate-45" />
                  <span className="font-display font-bold tracking-wider">BOARDING DOCKETS</span>
                </div>
                <span className="font-mono text-xs tracking-widest opacity-60">AINOMAD LOGISTICS</span>
              </div>
              
              <div className="divide-y divide-[#EAE3D2]/50">
                {(itinerary?.flights || []).map((flight, i) => (
                  <div
                    key={i}
                    role="button"
                    tabIndex={0}
                    onClick={() => openFlightBooking(flight)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openFlightBooking(flight);
                      }
                    }}
                    className="p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative cursor-pointer hover:bg-[#FBF9F6]/60 transition-colors"
                    title={`Book on ${flight.booking_platform || "partner site"}`}
                  >
                    {/* Visual separation dashed lines on pass stubs */}
                    <div className="hidden md:block absolute right-64 top-0 bottom-0 border-l border-dashed border-[#EAE3D2]"></div>
                    
                    <div className="flex-1 space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[#C85A32] font-mono tracking-wider uppercase">
                          {i === 0 ? "OUTBOUND SECTOR" : "RETURN SECTOR"}
                        </span>
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-[#FBF9F6] border border-[#EAE3D2] text-[#1E3F2E]">
                          {flight.airline}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between md:max-w-md gap-4">
                        <div className="text-left">
                          <div className="text-3xl font-extrabold text-[#1E2229] font-mono tracking-tight">
                            {flight.departure.split(" - ")[0]}
                          </div>
                          <div className="text-xs text-[#1E2229]/50 font-sans mt-0.5">
                            DEPART: {flight.departure.split(" - ")[1]}
                          </div>
                        </div>
                        
                        <div className="flex-1 px-4 text-center">
                          <div className="h-0.5 bg-[#EAE3D2] relative">
                            <div className="absolute left-0 -top-1 w-2.5 h-2.5 rounded-full bg-[#1E3F2E]"></div>
                            <div className="absolute right-0 -top-1 w-2.5 h-2.5 rounded-full bg-[#C85A32]"></div>
                          </div>
                          <span className="text-[10px] font-mono text-[#1E2229]/40 mt-1 block">FLIGHT TRANSIT</span>
                        </div>
                        
                        <div className="text-right">
                          <div className="text-3xl font-extrabold text-[#1E2229] font-mono tracking-tight">
                            {flight.arrival.split(" - ")[0]}
                          </div>
                          <div className="text-xs text-[#1E2229]/50 font-sans mt-0.5">
                            ARRIVE: {flight.arrival.split(" - ")[1]}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Ticket Price Stub */}
                    <div className="md:w-48 text-center flex md:flex-col items-center md:items-end justify-between md:justify-center border-t md:border-t-0 border-[#EAE3D2]/40 pt-4 md:pt-0 gap-1">
                      <span className="text-xs text-[#1E2229]/40 font-sans uppercase">ESTIMATED FARE</span>
                      <span className="text-2xl font-bold font-display text-[#C85A32]">{convertPrice(flight.price)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Hotels Postcards Section */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="text-2xl">🏨</span>
                <h3 className="text-2xl font-bold font-display text-[#1E3F2E]">Lodges & Accommodations</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {(itinerary?.hotels || []).map((hotel, i) => (
                  <div
                    key={i}
                    role="button"
                    tabIndex={0}
                    onClick={() => openHotelBooking(hotel)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openHotelBooking(hotel);
                      }
                    }}
                    className="bg-white rounded-xl overflow-hidden border border-[#EAE3D2] shadow-sm hover:shadow-md transition-all group cursor-pointer"
                    title={`View ${hotel.name} on booking site`}
                  >
                    <div className="relative h-56 bg-gradient-to-br from-[#1E3F2E]/80 via-[#4A6741] to-[#C85A32]/40 group-hover:scale-105 transition-transform duration-500">
                      <div className="absolute top-4 left-4">
                        <div className="px-2.5 py-1 rounded bg-[#FFFFFF] border border-[#EAE3D2] text-[#C85A32] text-xs font-bold font-mono">
                          ★ {hotel.rating}
                        </div>
                      </div>
                      <div className="absolute bottom-4 right-4">
                        <div className="px-3 py-1 rounded bg-[#C85A32] text-white text-xs font-bold font-mono">
                          {convertPrice(hotel.price_per_night)} / night
                        </div>
                      </div>
                    </div>
                    
                    <div className="p-6">
                      <h4 className="text-xl font-bold font-display text-[#1E2229] group-hover:text-[#C85A32] transition-colors">{hotel.name}</h4>
                      <p className="text-xs text-[#1E2229]/60 font-sans mt-2 flex items-center gap-1.5">
                        <MapPin size={12} className="text-[#C85A32]" />
                        {hotel.location}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Daily Schedule Timeline Scrapbook */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 md:p-8 shadow-sm">
              <div className="flex items-center gap-3 mb-10 pb-4 border-b border-[#EAE3D2]/50">
                <span className="text-2xl">📓</span>
                <h3 className="text-2xl font-bold font-display text-[#1E3F2E]">Daily Adventures</h3>
              </div>
              
              <div className="relative pl-6 md:pl-10 space-y-12 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#EAE3D2]">
                {(itinerary?.days || []).map((day, i) => (
                  <div key={i} className="relative">
                    {/* Circle checkpoint index */}
                    <div className="absolute -left-[30px] md:-left-[46px] top-0 w-6 h-6 rounded-full bg-[#1E3F2E] border-2 border-white flex items-center justify-center text-white text-[10px] font-bold font-mono shadow-sm">
                      {i+1}
                    </div>
                    
                    <div className="space-y-4">
                      <h4 className="text-xl font-bold font-display text-[#1E2229] border-b border-[#EAE3D2]/40 pb-2">{day.day}</h4>
                      
                      <div className="bg-[#FBF9F6] border border-[#EAE3D2]/60 rounded-xl divide-y divide-[#EAE3D2]/40">
                        {day.activities.map((activity, j) => (
                          <div 
                            key={j} 
                            className="p-5 flex flex-col sm:flex-row items-start gap-4 hover:bg-[#FFFFFF] transition-colors"
                          >
                            <div className="px-2.5 py-1 rounded bg-white border border-[#EAE3D2] text-[#C85A32] text-xs font-bold font-mono min-w-[76px] text-center">
                              {activity.time}
                            </div>
                            <div className="flex-1 space-y-1">
                              <h5 className="font-bold text-[#1E3F2E] text-base">{activity.place}</h5>
                              {activity.details && (
                                <p className="text-sm text-[#1E2229]/70 leading-relaxed font-sans">{activity.details}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Travel Documents Dossier */}
            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 md:p-8 shadow-sm">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#EAE3D2]/50">
                <span className="text-2xl">🛂</span>
                <h3 className="text-2xl font-bold font-display text-[#1E3F2E]">Travel Dossier</h3>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 bg-[#FBF9F6] border border-[#EAE3D2]/60 rounded-xl p-6">
                <div>
                  <span className="text-[10px] font-bold font-mono text-[#1E2229]/40 uppercase tracking-wider block">Visa Requirement</span>
                  <span className="text-xl font-bold font-display mt-1 block">
                    {itinerary?.visa_details?.required ? 
                      <span className="text-[#C85A32] flex items-center gap-1">Required 🔴</span> : 
                      <span className="text-[#1E3F2E] flex items-center gap-1">Not Required 🟢</span>
                    }
                  </span>
                </div>
                
                <div>
                  <span className="text-[10px] font-bold font-mono text-[#1E2229]/40 uppercase tracking-wider block">Processing Time</span>
                  <span className="text-xl font-bold font-display text-[#1E2229] mt-1 block">
                    {itinerary?.visa_details?.processing_time || "N/A"}
                  </span>
                </div>
                
                <div>
                  <span className="text-[10px] font-bold font-mono text-[#1E2229]/40 uppercase tracking-wider block">Estimated Visa Cost</span>
                  <span className="text-xl font-bold font-display text-[#C85A32] mt-1 block">
                    {convertPrice(itinerary?.visa_details?.cost || "Free")}
                  </span>
                </div>
              </div>
              
              {itinerary?.visa_details?.documents_needed && itinerary?.visa_details?.documents_needed.length > 0 && (
                <div className="mt-6">
                  <span className="text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider block mb-3">Required Documents</span>
                  <div className="flex flex-wrap gap-2">
                    {(itinerary?.visa_details?.documents_needed || []).map((doc, i) => (
                      <span 
                        key={i} 
                        className="px-3 py-1 rounded bg-white border border-[#EAE3D2] text-[#1E2229] text-xs font-medium font-sans shadow-sm"
                      >
                        📁 {doc}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="text-center mt-12 space-y-4">
              {saveMessage && (
                <p className="text-sm text-[#1E3F2E] font-semibold bg-[#1E3F2E]/10 border border-[#1E3F2E]/20 rounded-lg py-2 px-4 inline-block">
                  {saveMessage}
                </p>
              )}
              {saveError && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg py-2 px-4 inline-block">
                  {saveError}
                </p>
              )}
              <button 
                type="button"
                onClick={handleSaveTrip}
                disabled={savingTrip || tripSaved}
                className="px-8 py-3.5 bg-[#C85A32] hover:bg-[#A54422] text-white font-bold rounded-lg text-base transition-all shadow-md transform hover:-translate-y-0.5 disabled:opacity-60 disabled:transform-none"
              >
                {savingTrip ? "Saving…" : tripSaved ? "Trip saved ✈️" : "Stamp Memoir & Save Trip"}
              </button>
              {tripSaved && (
                <p className="text-xs font-mono text-[#1E3F2E]">
                  <button
                    type="button"
                    onClick={() => router.push("/trips")}
                    className="text-[#C85A32] font-bold hover:underline"
                  >
                    View My Trips
                  </button>
                  {" · "}
                  <button
                    type="button"
                    onClick={() => router.push("/journal")}
                    className="text-[#C85A32] font-bold hover:underline"
                  >
                    Open Travel Journal
                  </button>
                </p>
              )}
              <div>
                <button 
                  onClick={resetForm}
                  className="text-xs font-bold font-mono text-[#1E3F2E] hover:text-[#C85A32] transition-colors"
                >
                  REVISE PLANNING JOURNAL
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}