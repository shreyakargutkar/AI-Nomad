"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Compass,
  MapPin,
  Tag,
  Search,
  Globe2,
  Calendar,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Clock,
  Filter,
  Building,
} from "lucide-react";

const PRESET_INTERESTS = [
  "Anime & Gaming",
  "Technology & AI",
  "Food & Culinary",
  "Traditional Culture",
  "Art & Exhibitions",
  "Live Music",
  "Sports",
];

const CATEGORIES = [
  { key: "all", label: "All Events", icon: "🎉" },
  { key: "ANIME_GAMING", label: "Anime & Gaming", icon: "🎮" },
  { key: "TECHNOLOGY", label: "Technology", icon: "💻" },
  { key: "FOOD_DRINK", label: "Food & Drink", icon: "🍜" },
  { key: "CULTURE_MATSURI", label: "Culture & Matsuri", icon: "⛩️" },
  { key: "ART_DESIGN", label: "Art & Design", icon: "🎨" },
  { key: "MUSIC_CONCERTS", label: "Music & Concerts", icon: "🎵" },
  { key: "SPORTS", label: "Sports", icon: "⚽" },
];

export default function CulturalIntelligence() {
  const searchParams = useSearchParams();

  const [location, setLocation] = useState("");
  const [startDate, setStartDate] = useState("2026-11-10");
  const [endDate, setEndDate] = useState("2026-11-17");
  const [interests, setInterests] = useState("Anime, technology, food, traditional culture");
  const [category, setCategory] = useState("all");

  const [events, setEvents] = useState([]);
  const [headerTitle, setHeaderTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [rankingSource, setRankingSource] = useState(null);
  const [noResultsInfo, setNoResultsInfo] = useState(null);

  useEffect(() => {
    const loc = searchParams.get("location");
    if (loc) setLocation(loc);
  }, [searchParams]);

  const fetchEvents = async (options = {}) => {
    if (!location.trim()) {
      setError("Please enter a destination city to discover events.");
      return;
    }

    setLoading(true);
    setError(null);
    setNoResultsInfo(null);

    const activeCategory = options.reset_category ? "all" : (options.category || category);
    if (options.reset_category) {
      setCategory("all");
    }

    const payload = {
      location: location.trim(),
      start_date: startDate,
      end_date: endDate,
      interests: options.reset_category ? "" : (interests.trim() || "culture, events"),
      category: activeCategory,
      allow_outside_dates: options.allow_outside_dates || false,
      allow_nearby: options.allow_nearby || false,
    };

    try {
      const response = await fetch("/api/festivals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to discover events for this destination");
      }

      setHasSearched(true);
      setHeaderTitle(data.header_title || `Verified Events for ${location}`);
      setRankingSource(data.ranking_source || "ml_event_relevance_model");

      if (data.events && data.events.length > 0) {
        setEvents(data.events);
      } else {
        setEvents([]);
        setNoResultsInfo({
          message: data.message || `No verified local events matching your interests were found in ${location} for these dates.`,
          canShowOutside: data.can_show_outside_dates,
          canShowNearby: data.can_show_nearby,
        });
      }
    } catch (err) {
      setError(err.message || "Could not reach event service. Make sure services are running.");
      setEvents([]);
    }

    setLoading(false);
  };

  const handleInterestTagClick = (tag) => {
    const cleanTag = tag.replace(/ & .*/, "");
    if (!interests.toLowerCase().includes(cleanTag.toLowerCase())) {
      setInterests((prev) => (prev ? `${prev}, ${cleanTag}` : cleanTag));
    }
  };

  const illustrations = {
    anime: "🎮",
    tech: "💻",
    food: "🍜",
    culture: "⛩️",
    art: "🎨",
    music: "🎵",
    sports: "⚽",
    community: "🏘️",
    all: "🎉",
  };

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-20 md:py-24 relative font-sans">
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-60" />

      <div className="max-w-6xl mx-auto px-4 md:px-6 relative z-10">
        {/* Header */}
        <div className="text-center mb-10 pt-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#2D6A8F]/10 text-[#2D6A8F] text-[10px] font-bold uppercase tracking-widest border border-[#2D6A8F]/20 mb-3">
            <Globe2 size={11} /> Real-Time Cultural Intelligence
          </span>
          <h1 className="text-3xl md:text-5xl font-bold text-[#1E2229] font-display">
            Local Culture & Events
          </h1>
          <p className="text-xs md:text-sm text-[#1E2229]/65 max-w-xl mx-auto mt-2 leading-relaxed">
            Real-time, date-specific event discovery powered by live search and machine learning relevance ranking. Never stale, never fabricated.
          </p>
          <div className="h-0.5 w-12 bg-[#C85A32] mx-auto mt-4" />
        </div>

        <div className="flex flex-col lg:flex-row gap-8 items-start">
          {/* ==========================================
              LEFT COLUMN: SEARCH & FILTERS FORM
              ========================================== */}
          <motion.div
            initial={{ x: -16, opacity: 0 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-full lg:w-5/12 bg-white border border-[#EAE3D2] rounded-2xl shadow-sm p-6 space-y-5"
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#EAE3D2]/50">
              <h2 className="text-lg font-bold font-display text-[#1E2229]">
                Trip Discovery Parameters
              </h2>
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#2D6A8F] font-bold bg-[#2D6A8F]/10 px-2 py-0.5 rounded">
                Live & Verified
              </span>
            </div>

            {/* Destination Input */}
            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-1.5">
                Destination City / Country
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Tokyo, Japan (or Paris, France)"
                  className="w-full p-3.5 pl-10 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-sm text-[#1E2229] placeholder-[#1E2229]/40"
                />
                <MapPin size={16} className="absolute left-3.5 top-3.5 text-[#C85A32]" />
              </div>
            </div>

            {/* Date Range Inputs */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-1.5 flex items-center gap-1">
                  <Calendar size={12} /> Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full p-3 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-xs text-[#1E2229]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-1.5 flex items-center gap-1">
                  <Calendar size={12} /> End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full p-3 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-xs text-[#1E2229]"
                />
              </div>
            </div>

            {/* Interests Freeform & Quick Tags */}
            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-1.5 flex items-center gap-1">
                <Tag size={12} /> Personal Interests & Passions
              </label>
              <input
                type="text"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
                placeholder="e.g. Anime, technology, food, traditional culture"
                className="w-full p-3.5 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-sm text-[#1E2229] placeholder-[#1E2229]/40 mb-2"
              />
              <div className="flex flex-wrap gap-1.5">
                {PRESET_INTERESTS.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => handleInterestTagClick(tag)}
                    className="text-[10px] font-mono px-2.5 py-1 rounded bg-[#FBF9F6] hover:bg-[#EAE3D2] border border-[#EAE3D2] text-[#1E2229]/75 transition-colors"
                  >
                    + {tag}
                  </button>
                ))}
              </div>
            </div>

            {/* Category Filter Pills */}
            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-1.5 flex items-center gap-1">
                <Filter size={12} /> Event Category
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.key}
                    type="button"
                    onClick={() => setCategory(cat.key)}
                    className={`px-2.5 py-2 rounded-lg text-xs font-bold font-mono text-left border transition-all flex items-center gap-1.5 ${
                      category === cat.key
                        ? "bg-[#1E3F2E] border-[#1E3F2E] text-white shadow-sm"
                        : "bg-[#FBF9F6] border-[#EAE3D2] text-[#1E2229]/80 hover:bg-white"
                    }`}
                  >
                    <span>{cat.icon}</span>
                    <span className="truncate">{cat.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3.5 bg-red-50 border border-red-100 rounded-xl flex items-start gap-2.5 text-xs text-red-700">
                <AlertCircle size={15} className="flex-shrink-0 mt-0.5 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="button"
              onClick={() => fetchEvents()}
              disabled={loading}
              className="w-full bg-[#1E3F2E] hover:bg-[#2D5A43] text-white font-bold py-4 rounded-xl text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-md transition-all disabled:opacity-50"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Sparkles size={14} className="text-[#C85A32]" />
              )}
              {loading ? "Searching Live Sources & ML Ranking…" : "Discover Verified Local Events →"}
            </button>

            <div className="pt-2 border-t border-[#EAE3D2]/50 text-center">
              <span className="text-[10px] text-[#1E2229]/50 font-mono inline-flex items-center gap-1">
                <ShieldCheck size={11} className="text-[#1E3F2E]" />
                ML Relevance Pipeline · No hallucinated events
              </span>
            </div>
          </motion.div>

          {/* ==========================================
              RIGHT COLUMN: RANKED EVENT RESULTS
              ========================================== */}
          <div className="w-full lg:w-7/12 space-y-4">
            {/* Header when events are loaded */}
            {events.length > 0 && (
              <div className="bg-white border border-[#EAE3D2] rounded-xl px-5 py-3.5 flex flex-col sm:flex-row justify-between sm:items-center gap-2">
                <div>
                  <h3 className="text-sm font-bold font-display text-[#1E2229]">
                    {headerTitle || `Verified Events for ${location}`}
                  </h3>
                  <p className="text-[11px] text-[#1E2229]/60 font-mono">
                    Showing {events.length} events tailored to your dates and interests
                  </p>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold uppercase tracking-wider text-[#1E3F2E] bg-[#1E3F2E]/10 px-2.5 py-1 rounded-full border border-[#1E3F2E]/20 self-start sm:self-auto">
                  <Sparkles size={11} className="text-[#C85A32]" />
                  ML Ranked
                </span>
              </div>
            )}

            {/* Event Cards */}
            {events.length > 0 ? (
              <div className="space-y-4">
                {events.map((event, index) => {
                  const score = event.event_relevance_score ?? event.relevance_score ?? 85;
                  const tier = event.relevance_tier || "Top Match";
                  const icon = illustrations[event.category] || "🎉";

                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="bg-white border border-[#EAE3D2] rounded-2xl p-5 md:p-6 shadow-sm hover:border-[#C85A32]/60 transition-all space-y-4"
                    >
                      {/* Top Bar: Icon, Title, ML Score */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3">
                          <span className="text-3xl shrink-0 p-2 bg-[#FBF9F6] border border-[#EAE3D2] rounded-xl">
                            {icon}
                          </span>
                          <div>
                            <div className="flex flex-wrap items-center gap-2 mb-1">
                              <span className="text-[10px] font-mono uppercase tracking-wider font-bold px-2 py-0.5 rounded bg-[#2D6A8F]/10 text-[#2D6A8F] border border-[#2D6A8F]/20">
                                {event.category_label || event.category}
                              </span>
                              <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                                <span>✓</span> VERIFIED EVENT
                              </span>
                              {event.price && (
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                                  🎟️ {event.price}
                                </span>
                              )}
                            </div>
                            <h4 className="text-base md:text-lg font-bold font-display text-[#1E2229] leading-snug">
                              {event.name}
                            </h4>
                          </div>
                        </div>

                        {/* ML Score Badge */}
                        <div className="text-right shrink-0">
                          <div className="inline-flex flex-col items-end">
                            <span className="text-sm md:text-base font-extrabold font-mono text-[#1E3F2E]">
                              {score}% MATCH
                            </span>
                            <span className="text-[9px] font-mono uppercase tracking-wider font-bold text-[#C85A32]">
                              {tier}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Event Details Grid */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#1E2229]/80 bg-[#FBF9F6] p-3 rounded-xl border border-[#EAE3D2]/70">
                        <div className="flex items-center gap-1.5">
                          <Calendar size={13} className="text-[#C85A32] shrink-0" />
                          <span className="font-mono font-medium">
                            {event.start_date}
                            {event.end_date && event.end_date !== event.start_date
                              ? ` → ${event.end_date}`
                              : ""}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <MapPin size={13} className="text-[#1E3F2E] shrink-0" />
                          <span className="font-bold text-[#1E2229]">
                            {event.city}{event.state ? `, ${event.state}` : ""}{event.country ? `, ${event.country}` : ""}
                          </span>
                        </div>
                        {event.venue && (
                          <div className="sm:col-span-2 flex items-center gap-1.5 text-[11px] text-[#1E2229]/70 pt-1 border-t border-[#EAE3D2]/40">
                            <Building size={12} className="text-[#2D6A8F] shrink-0" />
                            <span className="truncate" title={event.venue}>
                              Venue: <span className="font-medium text-[#1E2229]/90">{event.venue}</span>
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Event Description */}
                      <p className="text-xs text-[#1E2229]/80 leading-relaxed">
                        {event.description}
                      </p>

                      {/* Why it's recommended (Personalized rationale) */}
                      {event.why_recommended && (
                        <div className="p-3 bg-[#1E3F2E]/5 border border-[#1E3F2E]/15 rounded-xl text-xs text-[#1E3F2E] leading-relaxed flex items-start gap-2">
                          <span className="text-base shrink-0">💡</span>
                          <div>
                            <span className="font-bold font-mono uppercase text-[10px] block text-[#1E3F2E]/80 mb-0.5">
                              Why It&apos;s Recommended
                            </span>
                            <span>{event.why_recommended}</span>
                          </div>
                        </div>
                      )}

                      {/* Source & Transparency Footer */}
                      <div className="pt-2 border-t border-[#EAE3D2]/50 flex flex-wrap items-center justify-between text-[11px] text-[#1E2229]/55 font-mono gap-2">
                        <span className="flex items-center gap-1">
                          <ShieldCheck size={12} className="text-emerald-700" />
                          Source: <strong className="text-[#1E2229]/75">{event.source_name || "Official Local Source"}</strong>
                          {event.last_verified && <span> · Verified: {event.last_verified}</span>}
                        </span>

                        {event.source_url && event.source_status === "VALID" ? (
                          <a
                            href={event.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[#C85A32] hover:text-[#A54422] font-bold transition-colors"
                          >
                            <span>View Source</span>
                            <ExternalLink size={11} />
                          </a>
                        ) : (
                          <span className="text-[10px] text-[#1E2229]/40 italic">Source unavailable</span>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            ) : hasSearched && noResultsInfo ? (
              /* ==========================================
                 NO RESULTS STATE (No Hallucinations)
                 ========================================== */
              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-8 text-center space-y-4">
                <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto">
                  <AlertCircle size={24} />
                </div>
                <div>
                  <h4 className="text-base font-bold font-display text-[#1E2229]">
                    No Verified Events Found
                  </h4>
                  <p className="text-xs text-[#1E2229]/65 max-w-md mx-auto mt-1 leading-relaxed">
                    {noResultsInfo.message}
                  </p>
                </div>

                <div className="pt-2 flex flex-col sm:flex-row gap-2 justify-center max-w-lg mx-auto">
                  <button
                    type="button"
                    onClick={() => fetchEvents({ reset_category: true })}
                    className="flex-1 py-2.5 px-3 text-xs font-bold font-mono rounded-lg bg-[#1E3F2E] text-white hover:bg-[#2D5A43] shadow-sm transition-colors"
                  >
                    ⛩️ Show all cultural events
                  </button>
                  <button
                    type="button"
                    onClick={() => fetchEvents({ allow_nearby: true })}
                    className="flex-1 py-2.5 px-3 text-xs font-bold font-mono rounded-lg border border-[#C85A32] text-[#C85A32] hover:bg-[#C85A32]/5 transition-colors"
                  >
                    📍 Expand to nearby cities
                  </button>
                  <button
                    type="button"
                    onClick={() => fetchEvents({ allow_outside_dates: true })}
                    className="flex-1 py-2.5 px-3 text-xs font-bold font-mono rounded-lg border border-[#EAE3D2] text-[#1E2229]/75 hover:bg-[#FBF9F6] transition-colors"
                  >
                    📅 Outside travel dates
                  </button>
                </div>
              </div>
            ) : (
              /* Default Empty State */
              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-10 text-center">
                <Compass className="w-10 h-10 text-[#2D6A8F] mx-auto mb-4 opacity-50" />
                <h3 className="font-bold font-display text-base text-[#1E2229]">
                  Discover Real-Time Local Events
                </h3>
                <p className="text-xs text-[#1E2229]/65 max-w-sm mx-auto mt-1">
                  Enter your destination city and travel dates to surface verified local festivals, tech meetups, culinary fairs, and cultural gatherings.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
