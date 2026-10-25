"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Check,
  Calendar,
  MapPin,
  Package,
  FileText,
  Ticket,
  ArrowLeft,
  Compass,
  Sparkles,
  AlertCircle,
  Clock,
  Shield,
  Luggage,
  Plane,
  Hotel,
  ChevronDown,
  Info,
  ShieldAlert,
} from "lucide-react";

const BREAKDOWN_META = [
  { key: "packing", label: "Packing", icon: Luggage, color: "#1E3F2E" },
  { key: "tickets", label: "Tickets", icon: Ticket, color: "#C85A32" },
  { key: "documents", label: "Documents", icon: Shield, color: "#5B4FCF" },
  { key: "country_requirements", label: "Country Prep", icon: FileText, color: "#2D6A8F" },
];

export default function TripReadinessDashboard() {
  // Step in user journey: "form" | "prep_check" | "dashboard"
  const [step, setStep] = useState("form");

  // Step 1: Trip Details
  const [formData, setFormData] = useState({
    destination: "",
    cities: "",
    start_date: "",
    end_date: "",
    itinerary: "",
    prebooked: "",
  });

  // Step 2: Travel Preparation Check
  const [prepData, setPrepData] = useState({
    flight_booked: 1,
    hotel_booked: 1,
    passport_valid: 1,
    visa_status: "not_required", // "yes" | "not_required" | "not_yet"
    travel_insurance: 0,
    packing_completed: 0,
    emergency_prepared: 0,
    documents_completed: 1,
    previous_trips: 3,
  });

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [packedItems, setPackedItems] = useState({});
  const [showCalculationDetails, setShowCalculationDetails] = useState(false);

  // Automatically infer sensible defaults from trip input
  const inferPrepDefaults = (currentForm) => {
    const preText = (currentForm.prebooked || "").toLowerCase();
    const destText = (currentForm.destination || "").toLowerCase();

    const hasFlight = /flight|airline|air\s|ana|jal|ticket\s+to|boarding|plane/.test(preText);
    const hasHotel = /hotel|hostel|inn|ryokan|airbnb|resort|stay|lodging|room|apartment/.test(preText);
    const hasInsurance = /insurance|policy|allianz|coverage/.test(preText);
    const hasVisa = /visa|permit|entry\s+pass/.test(preText);
    const isExempt = /japan|france|greece|thailand|indonesia|italy|spain|germany|portugal|singapore/.test(destText);

    return {
      flight_booked: hasFlight ? 1 : (preText ? 1 : 0),
      hotel_booked: hasHotel ? 1 : (preText ? 1 : 0),
      passport_valid: 1,
      visa_status: hasVisa ? "yes" : (isExempt ? "not_required" : "yes"),
      travel_insurance: hasInsurance ? 1 : 0,
      packing_completed: 0,
      emergency_prepared: 0,
      documents_completed: 1,
      previous_trips: 3,
    };
  };

  const handleProceedToPrepCheck = (e) => {
    e.preventDefault();
    setError(null);
    if (!formData.destination || !formData.start_date || !formData.end_date || !formData.itinerary) {
      setError("Please fill in all required trip details.");
      return;
    }
    const defaults = inferPrepDefaults(formData);
    setPrepData(defaults);
    setStep("prep_check");
  };

  const fetchReadiness = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/readiness", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          ...prepData,
          prebooked: formData.prebooked.split("\n").filter((t) => t.trim()),
        }),
      });
      if (!response.ok) throw new Error("Failed to generate readiness assessment");
      const data = await response.json();
      setDashboardData(data);
      setPackedItems({});
      setStep("dashboard");
    } catch (err) {
      setError(err.message || "Could not reach readiness service. Is the backend running?");
    }
    setLoading(false);
  };

  const allPackingItems = useMemo(() => {
    if (!dashboardData?.packing_recommendations) return [];
    const p = dashboardData.packing_recommendations;
    return [
      ...(p.essentials || []).map((item) => ({ item, group: "Essentials" })),
      ...(p.by_activity || []).map((item) => ({ item, group: "Activity-specific" })),
      ...(p.duration_extras || []).map((item) => ({ item, group: "Trip length" })),
    ];
  }, [dashboardData]);

  const packingChecked = allPackingItems.filter((_, i) => packedItems[i]).length;
  const packingProgress =
    allPackingItems.length > 0
      ? Math.round((packingChecked / allPackingItems.length) * 100)
      : 0;

  const togglePacked = (index) => {
    setPackedItems((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const scoreColor =
    dashboardData?.readiness_score >= 80
      ? "#1E3F2E"
      : dashboardData?.readiness_score >= 50
        ? "#C85A32"
        : "#A54422";

  // ==========================================
  // STEP 1: INITIAL TRIP INFORMATION FORM
  // ==========================================
  if (step === "form") {
    return (
      <div className="min-h-screen bg-[#FBF9F6] py-24 relative font-sans">
        <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-60" />

        <div className="max-w-xl mx-auto px-6 relative z-10">
          <div className="text-center mb-10 pt-8">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
              <Compass size={10} /> Smart Trip Readiness
            </span>
            <h1 className="text-4xl font-bold text-[#1E2229] font-display">
              Readiness Dashboard
            </h1>
            <p className="text-sm text-[#1E2229]/60 mt-2 max-w-md mx-auto">
              Step 1 of 2 · Enter your trip destination and dates. We will automatically infer local weather, season, and country requirements.
            </p>
            <div className="h-0.5 w-12 bg-[#C85A32] mx-auto mt-4" />
          </div>

          <form
            onSubmit={handleProceedToPrepCheck}
            className="bg-white border border-[#EAE3D2] rounded-2xl shadow-[0_12px_40px_rgba(30,34,41,0.04)] p-8 space-y-5 relative overflow-hidden"
          >
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-28 h-6 bg-[#C85A32]/10 border-x border-[#C85A32]/25 rotate-1" />

            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">
                Destination Country / City
              </label>
              <input
                type="text"
                required
                value={formData.destination}
                onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                placeholder="e.g. Japan, Tokyo, Paris, Bali, Thailand"
                className="w-full p-4 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none placeholder-[#1E2229]/40"
              />
            </div>

            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">
                Cities (optional)
              </label>
              <input
                type="text"
                value={formData.cities}
                onChange={(e) => setFormData({ ...formData, cities: e.target.value })}
                placeholder="e.g. Tokyo, Kyoto"
                className="w-full p-4 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none placeholder-[#1E2229]/40"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  required
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full p-4 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  required
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full p-4 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">
                Itinerary — activities & attractions
              </label>
              <textarea
                required
                value={formData.itinerary}
                onChange={(e) => setFormData({ ...formData, itinerary: e.target.value })}
                placeholder="teamLab Planets, Senso-ji, Shibuya Crossing, Universal Studios Japan"
                rows={4}
                className="w-full p-4 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none placeholder-[#1E2229]/40"
              />
              <p className="text-[10px] text-[#1E2229]/45 mt-1">Separate with commas or new lines</p>
            </div>

            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase tracking-wider mb-2">
                Already Booked (one per line)
              </label>
              <textarea
                value={formData.prebooked}
                onChange={(e) => setFormData({ ...formData, prebooked: e.target.value })}
                placeholder="teamLab Planets&#10;Tokyo Skytree ticket"
                rows={3}
                className="w-full p-4 rounded-lg text-[#1E2229] bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none placeholder-[#1E2229]/40"
              />
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="w-full bg-[#1E3F2E] hover:bg-[#2D5A43] text-white py-4 rounded-lg font-bold text-sm tracking-wide uppercase transition-all shadow-md flex items-center justify-center gap-2"
            >
              Generate Readiness Dashboard →
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ==========================================
  // STEP 2: TRAVEL PREPARATION CHECK
  // ==========================================
  if (step === "prep_check") {
    return (
      <div className="min-h-screen bg-[#FBF9F6] py-24 relative font-sans">
        <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-60" />

        <div className="max-w-2xl mx-auto px-6 relative z-10">
          <button
            type="button"
            onClick={() => setStep("form")}
            className="mb-6 inline-flex items-center text-xs font-bold font-mono text-[#1E3F2E] hover:text-[#C85A32] gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to trip details
          </button>

          <div className="text-center mb-8">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#C85A32]/10 text-[#C85A32] text-[10px] font-bold uppercase tracking-widest border border-[#C85A32]/20 mb-3">
              <Sparkles size={11} /> Step 2 of 2 · AI-Nomad Verification
            </span>
            <h1 className="text-3xl md:text-4xl font-bold text-[#1E2229] font-display">
              Travel Preparation Check
            </h1>
            <p className="text-xs text-[#1E2229]/65 mt-2 max-w-lg mx-auto leading-relaxed">
              We&apos;ve derived climate, season, and route details for <strong className="text-[#1E3F2E]">{formData.destination}</strong>. Please confirm these 8 preparation factors to run your ML readiness prediction.
            </p>
            <div className="h-0.5 w-12 bg-[#C85A32] mx-auto mt-4" />
          </div>

          <div className="bg-white border border-[#EAE3D2] rounded-2xl shadow-[0_12px_40px_rgba(30,34,41,0.04)] p-6 md:p-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Factor 1: Flight */}
              <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">✈️</span>
                  <label className="text-xs font-bold text-[#1E2229] font-sans">Flight booked?</label>
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, flight_booked: 1 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.flight_booked === 1
                        ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✓ Yes
                  </button>
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, flight_booked: 0 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.flight_booked === 0
                        ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✕ No
                  </button>
                </div>
              </div>

              {/* Factor 2: Hotel */}
              <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🏨</span>
                  <label className="text-xs font-bold text-[#1E2229] font-sans">Hotel / Stays booked?</label>
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, hotel_booked: 1 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.hotel_booked === 1
                        ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✓ Yes
                  </button>
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, hotel_booked: 0 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.hotel_booked === 0
                        ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✕ No
                  </button>
                </div>
              </div>

              {/* Factor 3: Passport */}
              <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🛂</span>
                  <label className="text-xs font-bold text-[#1E2229] font-sans">Passport valid (6+ mos)?</label>
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, passport_valid: 1 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.passport_valid === 1
                        ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✓ Yes
                  </button>
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, passport_valid: 0 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.passport_valid === 0
                        ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✕ No
                  </button>
                </div>
              </div>

              {/* Factor 4: Travel Insurance */}
              <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🛡️</span>
                  <label className="text-xs font-bold text-[#1E2229] font-sans">Travel insurance?</label>
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, travel_insurance: 1 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.travel_insurance === 1
                        ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✓ Yes
                  </button>
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, travel_insurance: 0 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.travel_insurance === 0
                        ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✕ No
                  </button>
                </div>
              </div>

              {/* Factor 5: Packing */}
              <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎒</span>
                  <label className="text-xs font-bold text-[#1E2229] font-sans">Packing completed?</label>
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, packing_completed: 1 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.packing_completed === 1
                        ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✓ Yes
                  </button>
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, packing_completed: 0 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.packing_completed === 0
                        ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✕ No
                  </button>
                </div>
              </div>

              {/* Factor 6: Emergency Prep */}
              <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🚨</span>
                  <label className="text-xs font-bold text-[#1E2229] font-sans">Emergency contacts saved?</label>
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, emergency_prepared: 1 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.emergency_prepared === 1
                        ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✓ Yes
                  </button>
                  <button
                    type="button"
                    onClick={() => setPrepData({ ...prepData, emergency_prepared: 0 })}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                      prepData.emergency_prepared === 0
                        ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    ✕ No
                  </button>
                </div>
              </div>
            </div>

            {/* Factor 7: Visa 3-way radio */}
            <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">📄</span>
                  <label className="text-xs font-bold text-[#1E2229] font-sans">Visa status for {formData.destination}?</label>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setPrepData({ ...prepData, visa_status: "yes" })}
                  className={`py-2 text-xs font-bold rounded-lg border transition-all ${
                    prepData.visa_status === "yes"
                      ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                      : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                  }`}
                >
                  ✓ Yes, ready
                </button>
                <button
                  type="button"
                  onClick={() => setPrepData({ ...prepData, visa_status: "not_required" })}
                  className={`py-2 text-xs font-bold rounded-lg border transition-all ${
                    prepData.visa_status === "not_required"
                      ? "bg-[#2D6A8F] text-white border-[#2D6A8F] shadow-sm"
                      : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                  }`}
                >
                  ⚡ Not required
                </button>
                <button
                  type="button"
                  onClick={() => setPrepData({ ...prepData, visa_status: "not_yet" })}
                  className={`py-2 text-xs font-bold rounded-lg border transition-all ${
                    prepData.visa_status === "not_yet"
                      ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                      : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                  }`}
                >
                  ✕ Not yet
                </button>
              </div>
            </div>

            {/* Factor 8: Important Documents */}
            <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">📑</span>
                <label className="text-xs font-bold text-[#1E2229] font-sans">Important documents saved offline (tickets, IDs, reservations)?</label>
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setPrepData({ ...prepData, documents_completed: 1 })}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                    prepData.documents_completed === 1
                      ? "bg-[#1E3F2E] text-white border-[#1E3F2E] shadow-sm"
                      : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                  }`}
                >
                  ✓ Yes, prepared
                </button>
                <button
                  type="button"
                  onClick={() => setPrepData({ ...prepData, documents_completed: 0 })}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                    prepData.documents_completed === 0
                      ? "bg-[#C85A32] text-white border-[#C85A32] shadow-sm"
                      : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                  }`}
                >
                  ✕ Pending
                </button>
              </div>
            </div>

            {/* Experience: Previous international trips */}
            <div className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/60 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">🌍</span>
                <label className="text-xs font-bold text-[#1E2229] font-sans">Have you travelled internationally before?</label>
              </div>
              <div className="grid grid-cols-4 gap-2 pt-1">
                {[
                  { label: "First trip (0)", val: 0 },
                  { label: "1–3 trips", val: 2 },
                  { label: "4–10 trips", val: 6 },
                  { label: "10+ trips", val: 12 },
                ].map((tier) => (
                  <button
                    key={tier.val}
                    type="button"
                    onClick={() => setPrepData({ ...prepData, previous_trips: tier.val })}
                    className={`py-2 text-[11px] font-bold rounded-lg border transition-all ${
                      prepData.previous_trips === tier.val
                        ? "bg-[#1E3F2E] text-white border-[#1E3F2E]"
                        : "bg-white text-[#1E2229]/70 border-[#EAE3D2] hover:bg-[#FBF9F6]"
                    }`}
                  >
                    {tier.label}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
                {error}
              </p>
            )}

            <div className="pt-2 flex flex-col sm:flex-row gap-3">
              <button
                type="button"
                onClick={() => setStep("form")}
                className="w-full sm:w-1/3 py-4 border border-[#EAE3D2] hover:bg-[#FBF9F6] text-[#1E2229] rounded-lg font-bold text-sm tracking-wide transition-all uppercase"
              >
                ← Back
              </button>
              <button
                type="button"
                onClick={fetchReadiness}
                disabled={loading}
                className="w-full sm:w-2/3 bg-[#1E3F2E] hover:bg-[#2D5A43] text-white py-4 rounded-lg font-bold text-sm tracking-wide uppercase transition-all shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                )}
                {loading ? "Running ML Prediction…" : "Submit & Calculate Readiness Score →"}
              </button>
            </div>

            <p className="text-center text-[11px] text-[#1E2229]/45 font-mono">
              ✨ Powered by AI-Nomad ML Readiness Engine
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // STEP 3: DASHBOARD DISPLAY
  // ==========================================
  const { packing_recommendations: packing, country_requirements: country, booking_intelligence: booking } =
    dashboardData;

  const score = dashboardData.readiness_score ?? dashboardData.preparedness_score ?? 0;
  const riskLevel = dashboardData.risk_level || "LOW";
  const isML = dashboardData.score_source === "ml";

  // Derive "What you're doing well" and "Needs attention"
  const doingWellList = dashboardData.doing_well && dashboardData.doing_well.length > 0
    ? dashboardData.doing_well
    : [
        prepData.flight_booked ? "Flight booked and confirmed" : null,
        prepData.hotel_booked ? "Hotel / accommodation booked" : null,
        prepData.passport_valid ? "Passport verified valid (6+ months)" : null,
        prepData.visa_status === "not_required" ? "Destination is visa-exempt" : (prepData.visa_status === "yes" ? "Visa ready & approved" : null),
        prepData.travel_insurance ? "Travel insurance policy active" : null,
        prepData.packing_completed ? "Packing checklist completed" : null,
      ].filter(Boolean);

  const needsAttentionList = dashboardData.needs_attention && dashboardData.needs_attention.length > 0
    ? dashboardData.needs_attention
    : [
        !prepData.flight_booked ? "Flight transit is not yet booked" : null,
        !prepData.hotel_booked ? "Accommodations are not yet reserved" : null,
        !prepData.passport_valid ? "CRITICAL: Passport validity requires attention" : null,
        prepData.visa_status === "not_yet" ? "CRITICAL: Travel visa has not been obtained" : null,
        !prepData.travel_insurance ? "Travel insurance not arranged" : null,
        !prepData.packing_completed ? "Packing is incomplete" : null,
        !prepData.emergency_prepared ? "Emergency numbers and local clinics not documented" : null,
      ].filter(Boolean);

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-20 md:py-24 relative font-sans">
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-60" />

      <div className="max-w-6xl mx-auto px-4 md:px-6 relative z-10">
        <button
          type="button"
          onClick={() => setStep("form")}
          className="mb-6 inline-flex items-center text-xs font-bold font-mono text-[#1E3F2E] hover:text-[#C85A32] gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Edit trip details
        </button>

        <header className="text-center mb-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
            <Sparkles size={10} /> AI-Nomad Readiness
          </span>
          <h1 className="text-3xl md:text-4xl font-bold text-[#1E2229] font-display">
            Smart Trip Readiness Dashboard
          </h1>
          <p className="text-xs text-[#1E2229]/50 mt-2 font-mono uppercase tracking-wider flex flex-wrap justify-center gap-x-2 gap-y-1">
            <span className="inline-flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {dashboardData.destination?.display || formData.destination}
            </span>
            <span>·</span>
            <span>{dashboardData.duration_days} days</span>
            <span>·</span>
            <span>{dashboardData.season}</span>
            {packing?.weather?.summary && (
              <>
                <span>·</span>
                <span className="normal-case tracking-normal">{packing.weather.summary}</span>
              </>
            )}
          </p>
        </header>

        {/* ==========================================
            SECTION: YOUR TRAVEL READINESS (SCORE HERO)
            ========================================== */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white border border-[#EAE3D2] rounded-2xl shadow-sm p-6 md:p-8 mb-8"
        >
          <div className="flex flex-col lg:flex-row gap-8 items-center">
            {/* Score Radial Ring */}
            <div className="flex-shrink-0 text-center">
              <div className="relative inline-block">
                <svg className="w-44 h-44 -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" stroke="#FBF9F6" strokeWidth="7" fill="none" />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    stroke={scoreColor}
                    strokeWidth="7"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray="264"
                    strokeDashoffset={264 - (264 * score) / 100}
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-[10px] font-mono tracking-widest text-[#1E2229]/40 uppercase mb-0.5">
                    YOUR TRAVEL READINESS
                  </span>
                  <span className="text-4xl font-extrabold font-mono" style={{ color: scoreColor }}>
                    {score} <span className="text-xl font-normal text-[#1E2229]/40">/ 100</span>
                  </span>
                  <span
                    className={`mt-1 text-[10px] font-bold font-mono tracking-wider px-2 py-0.5 rounded-full uppercase border ${
                      riskLevel === "LOW"
                        ? "bg-[#1E3F2E]/10 text-[#1E3F2E] border-[#1E3F2E]/20"
                        : riskLevel === "MEDIUM"
                        ? "bg-[#2D6A8F]/10 text-[#2D6A8F] border-[#2D6A8F]/20"
                        : "bg-[#C85A32]/10 text-[#C85A32] border-[#C85A32]/20"
                    }`}
                  >
                    {riskLevel} RISK
                  </span>
                </div>
              </div>
            </div>

            {/* Score Breakdown Bars & Label */}
            <div className="flex-1 w-full space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#EAE3D2]/50 pb-3">
                <div>
                  <h2 className="text-xl font-bold font-display text-[#1E2229]">
                    Readiness Breakdown
                  </h2>
                  <p className="text-xs text-[#1E2229]/50 mt-0.5">
                    Multi-factor evaluation across international preparation categories
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono px-3 py-1 rounded-full font-bold uppercase tracking-wider bg-[#1E3F2E]/10 text-[#1E3F2E] border border-[#1E3F2E]/20 inline-flex items-center gap-1.5">
                    <Sparkles size={12} className="text-[#C85A32]" />
                    {isML ? "ML-Powered Readiness Prediction" : "Rule-Based Readiness Fallback"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                {BREAKDOWN_META.map(({ key, label, icon: Icon, color }) => {
                  const val = dashboardData.score_breakdown?.[key] ?? 0;
                  return (
                    <div key={key} className="space-y-1.5 p-2 rounded-lg bg-[#FBF9F6]/50 border border-[#EAE3D2]/40">
                      <div className="flex justify-between items-center text-xs">
                        <span className="flex items-center gap-1.5 font-medium text-[#1E2229]">
                          <Icon className="w-3.5 h-3.5" style={{ color }} />
                          {label}
                        </span>
                        <span className="font-mono font-bold" style={{ color }}>
                          {val}%
                        </span>
                      </div>
                      <div className="h-2 bg-white rounded-full overflow-hidden border border-[#EAE3D2]/50">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${val}%` }}
                          transition={{ duration: 0.8, delay: 0.1 }}
                          className="h-full rounded-full"
                          style={{ backgroundColor: color }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Expandable "How was my score calculated?" toggle */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setShowCalculationDetails(!showCalculationDetails)}
                  className="text-xs text-[#1E3F2E] hover:text-[#C85A32] font-semibold flex items-center gap-1 transition-colors"
                >
                  <Info size={13} />
                  <span>How was my score calculated?</span>
                  <ChevronDown size={14} className={`transition-transform ${showCalculationDetails ? "rotate-180" : ""}`} />
                </button>

                <AnimatePresence>
                  {showCalculationDetails && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-3 p-4 bg-[#FBF9F6] border border-[#EAE3D2] rounded-xl text-xs text-[#1E2229]/80 leading-relaxed space-y-2 overflow-hidden"
                    >
                      <p>
                        Your readiness score is predicted by AI-Nomad&apos;s machine learning model, evaluating 15 combined features across legal validity, transit bookings, climate adaptation, and emergency coverage.
                      </p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1 font-mono text-[10px]">
                        <span className="p-1.5 bg-white rounded border border-[#EAE3D2]">Destination: {dashboardData.destination?.display || formData.destination}</span>
                        <span className="p-1.5 bg-white rounded border border-[#EAE3D2]">Duration: {dashboardData.duration_days} days</span>
                        <span className="p-1.5 bg-white rounded border border-[#EAE3D2]">Season: {dashboardData.season}</span>
                        <span className="p-1.5 bg-white rounded border border-[#EAE3D2]">Flights: {prepData.flight_booked ? "Booked" : "Pending"}</span>
                        <span className="p-1.5 bg-white rounded border border-[#EAE3D2]">Lodging: {prepData.hotel_booked ? "Booked" : "Pending"}</span>
                        <span className="p-1.5 bg-white rounded border border-[#EAE3D2]">Insurance: {prepData.travel_insurance ? "Active" : "None"}</span>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* ==========================================
              WHAT YOU'RE DOING WELL & NEEDS ATTENTION
              ========================================== */}
          <div className="mt-8 pt-6 border-t border-[#EAE3D2] grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Doing Well */}
            <div className="p-5 rounded-xl bg-[#1E3F2E]/5 border border-[#1E3F2E]/20 space-y-3">
              <h3 className="text-sm font-bold font-display text-[#1E3F2E] flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#1E3F2E] text-white text-xs flex items-center justify-center font-bold">✓</span>
                WHAT YOU&apos;RE DOING WELL
              </h3>
              <ul className="space-y-2">
                {doingWellList.length > 0 ? (
                  doingWellList.map((item, i) => (
                    <li key={i} className="text-xs text-[#1E2229] flex items-start gap-2">
                      <span className="text-[#1E3F2E] font-bold">✓</span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-xs text-[#1E2229]/60 italic">No verified preparation steps completed yet.</li>
                )}
              </ul>
            </div>

            {/* Needs Attention */}
            <div className="p-5 rounded-xl bg-[#C85A32]/5 border border-[#C85A32]/20 space-y-3">
              <h3 className="text-sm font-bold font-display text-[#A54422] flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#C85A32] text-white text-xs flex items-center justify-center font-bold">⚠️</span>
                NEEDS ATTENTION
              </h3>
              <ul className="space-y-2">
                {needsAttentionList.length > 0 ? (
                  needsAttentionList.map((item, i) => (
                    <li key={i} className="text-xs text-[#1E2229] flex items-start gap-2">
                      <span className="text-[#C85A32] font-bold">⚠️</span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-xs text-[#1E3F2E] font-semibold">Outstanding preparation! No critical risk factors identified.</li>
                )}
              </ul>
            </div>
          </div>

          {/* ==========================================
              AI-NOMAD RECOMMENDATIONS (BEFORE YOU FLY)
              ========================================== */}
          <div className="mt-8 pt-6 border-t border-[#EAE3D2]">
            <h3 className="text-sm font-bold font-display text-[#C85A32] mb-4 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              AI-NOMAD RECOMMENDATIONS
            </h3>
            <ul className="space-y-2">
              {(dashboardData.before_you_fly || []).map((action, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-xl bg-[#C85A32]/5 border border-[#C85A32]/15 text-sm text-[#1E2229]"
                >
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#C85A32] text-white text-xs font-bold flex items-center justify-center">
                    {i + 1}
                  </span>
                  <span>{action.text || action}</span>
                </li>
              ))}
            </ul>
          </div>
        </motion.section>

        {/* ==========================================
            SECTIONS: SMART PACKING & COUNTRY REQUIREMENTS
            ========================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Section 1: Smart Packing */}
          <SectionCard title="Smart Packing Checklist" icon={Package} accent="#1E3F2E">
            <div className="flex justify-between items-center mb-4 text-xs">
              <span className="text-[#1E2229]/60">Your packing progress</span>
              <span className="font-mono font-bold text-[#1E3F2E]">{packingProgress}%</span>
            </div>
            <div className="h-1.5 bg-[#FBF9F6] rounded-full mb-4 overflow-hidden">
              <div
                className="h-full bg-[#1E3F2E] transition-all duration-300 rounded-full"
                style={{ width: `${packingProgress}%` }}
              />
            </div>
            <div className="max-h-64 overflow-y-auto pr-1 space-y-0.5">
              {allPackingItems.map(({ item, group }, i) => (
                <ChecklistRow
                  key={`${item}-${i}`}
                  label={item}
                  sub={group}
                  checked={!!packedItems[i]}
                  onToggle={() => togglePacked(i)}
                />
              ))}
            </div>
            {packing?.contextual_tips?.length > 0 && (
              <div className="mt-5 pt-4 border-t border-[#EAE3D2] space-y-2">
                <p className="text-[10px] font-bold font-mono text-[#C85A32] uppercase tracking-wider">
                  Destination tips
                </p>
                {packing.contextual_tips.map((tip, i) => (
                  <p key={i} className="text-xs text-[#1E3F2E] leading-relaxed pl-3 border-l-2 border-[#1E3F2E]/30">
                    {tip}
                  </p>
                ))}
              </div>
            )}
          </SectionCard>

          {/* Section 2: Country Requirements */}
          <SectionCard title="Country-Specific Travel Requirements" icon={FileText} accent="#5B4FCF">
            {!country?.found && country?.message ? (
              <p className="text-sm text-[#1E2229]/70">{country.message}</p>
            ) : (
              <>
                {country?.visa && (
                  <div className="mb-5 p-4 bg-purple-50/60 rounded-xl border border-purple-100">
                    <p className="text-[10px] font-bold font-mono text-purple-700 uppercase mb-1">
                      Visa & entry
                    </p>
                    <p className="text-sm leading-relaxed">{country.visa.summary}</p>
                    {country.visa.documents && (
                      <ul className="mt-2 space-y-1">
                        {country.visa.documents.map((d, i) => (
                          <li key={i} className="text-xs text-[#1E2229]/75 flex items-center gap-1.5">
                            <Check className="w-3 h-3 text-purple-600" /> {d}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
                {country?.transportation?.map((t, i) => (
                  <div key={i} className="mb-4 pb-4 border-b border-[#EAE3D2]/50 last:border-0">
                    <p className="font-semibold text-sm text-[#1E2229]">{t.name}</p>
                    <p className="text-xs text-[#1E2229]/70 mt-1">{t.description}</p>
                    {t.where_to_get && (
                      <p className="text-[10px] font-mono text-[#C85A32] mt-2">
                        Get it: {t.where_to_get}
                      </p>
                    )}
                  </div>
                ))}
                {country?.document_checklist && (
                  <div className="mt-4">
                    <p className="text-[10px] font-bold font-mono uppercase text-[#1E3F2E] mb-2">
                      Document checklist
                    </p>
                    {country.document_checklist.map((doc, i) => (
                      <p key={i} className="text-xs py-1 flex gap-2">
                        <FileText className="w-3.5 h-3.5 text-[#5B4FCF] flex-shrink-0 mt-0.5" />
                        {doc}
                      </p>
                    ))}
                  </div>
                )}
                {country?.cultural_notes && (
                  <div className="mt-4 pt-3 border-t border-[#EAE3D2]">
                    <p className="text-[10px] font-bold font-mono uppercase mb-2">Cultural notes</p>
                    {country.cultural_notes.map((n, i) => (
                      <p key={i} className="text-xs text-[#1E2229]/80 mb-1.5">
                        {n}
                      </p>
                    ))}
                  </div>
                )}
              </>
            )}
          </SectionCard>
        </div>

        {/* Section 3: Booking Intelligence */}
        <SectionCard title="Itinerary Booking Intelligence" icon={Ticket} accent="#C85A32">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {booking?.booked?.map((item, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/80 flex justify-between items-start"
              >
                <div>
                  <p className="font-bold text-sm text-[#1E2229]">{item.name}</p>
                  <p className="text-xs text-[#1E2229]/60 mt-0.5">
                    {item.status === "prebooked" ? "Pre-booked by you" : "No reservation needed"}
                  </p>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#1E3F2E] bg-[#1E3F2E]/10 px-2 py-0.5 rounded">
                  Confirmed
                </span>
              </div>
            ))}
            {booking?.pending?.map((item, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-[#EAE3D2] bg-[#FBF9F6]/80 hover:border-[#2D6A8F]/40 transition-colors"
              >
                <p className="font-bold text-sm text-[#1E2229]">{item.name}</p>
                {item.booking_required ? (
                  <span className="inline-block mt-1 text-[9px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                    Advance booking
                  </span>
                ) : (
                  <span className="inline-block mt-1 text-[9px] font-bold uppercase tracking-wider text-[#1E3F2E] bg-[#1E3F2E]/10 px-2 py-0.5 rounded">
                    Walk-in OK
                  </span>
                )}
                <dl className="mt-3 space-y-1.5 text-[11px]">
                  <div>
                    <dt className="font-mono text-[#1E2229]/45 uppercase">Booking window</dt>
                    <dd className="text-[#1E2229]">{item.optimal_window}</dd>
                  </div>
                  {item.avoid_times && item.avoid_times !== "None" && (
                    <div>
                      <dt className="font-mono text-red-500/80 uppercase">Avoid</dt>
                      <dd className="text-red-700/90">{item.avoid_times}</dd>
                    </div>
                  )}
                  <div>
                    <dt className="font-mono text-[#1E2229]/45 uppercase">Best visit</dt>
                    <dd className="text-[#2D6A8F] font-medium">{item.best_time}</dd>
                  </div>
                  {item.guidance && (
                    <p className="text-[#1E2229]/65 pt-1 border-t border-[#EAE3D2]/50 leading-relaxed">
                      {item.guidance}
                    </p>
                  )}
                </dl>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

function SectionCard({ title, icon: Icon, children, accent = "#1E2229", className = "" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white rounded-xl border border-[#EAE3D2] p-6 shadow-sm ${className}`}
    >
      <div className="flex items-center mb-5 pb-3 border-b border-[#EAE3D2]/50">
        <div
          className="p-2.5 rounded-lg mr-3"
          style={{ backgroundColor: `${accent}15`, color: accent }}
        >
          <Icon className="w-5 h-5" />
        </div>
        <h3 className="text-lg font-bold font-display text-[#1E2229]">{title}</h3>
      </div>
      {children}
    </motion.div>
  );
}

function ChecklistRow({ label, sub, checked, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="w-full flex items-start py-2.5 text-left hover:bg-[#FBF9F6] rounded-lg px-1 -mx-1 transition-colors"
    >
      <div
        className={`flex-shrink-0 w-5 h-5 rounded mr-3 mt-0.5 flex items-center justify-center border transition-colors ${
          checked ? "bg-[#1E3F2E] border-[#1E3F2E] text-white" : "bg-white border-[#EAE3D2]"
        }`}
      >
        {checked && <Check className="w-3 h-3 stroke-[3]" />}
      </div>
      <div>
        <span className={`text-sm block ${checked ? "line-through text-[#1E2229]/45" : "text-[#1E2229]"}`}>
          {label}
        </span>
        {sub && <span className="text-[10px] text-[#1E2229]/40 font-mono">{sub}</span>}
      </div>
    </button>
  );
}
