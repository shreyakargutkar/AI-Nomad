'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Hospital,
  Pill,
  Car,
  Phone,
  AlertTriangle,
  Languages,
  Siren,
  MapPin,
  Copy,
  Check,
  Send,
  HeartPulse,
  Utensils,
  Navigation,
  BadgeAlert,
} from 'lucide-react';

const TRANSLATION_CATEGORIES = [
  { key: 'medical', label: 'Medical', icon: HeartPulse, color: '#A54422' },
  { key: 'food', label: 'Food', icon: Utensils, color: '#1E3F2E' },
  { key: 'transport', label: 'Transport', icon: Navigation, color: '#2D6A8F' },
  { key: 'emergency', label: 'Emergency', icon: BadgeAlert, color: '#C85A32' },
];

const SOS_SUGGESTIONS = [
  'I lost my passport',
  'I missed my train',
  'I need a doctor urgently',
  'I was pickpocketed near the metro',
];

const QUICK_DESTINATIONS = [
  { label: 'Tokyo', value: 'Tokyo, Japan', flag: '🇯🇵' },
  { label: 'Paris', value: 'Paris, France', flag: '🇫🇷' },
  { label: 'Bangkok', value: 'Bangkok, Thailand', flag: '🇹🇭' },
  { label: 'Istanbul', value: 'Istanbul, Turkey', flag: '🇹🇷' },
  { label: 'Santorini', value: 'Santorini, Greece', flag: '🇬🇷' },
  { label: 'Bali', value: 'Bali, Indonesia', flag: '🇮🇩' },
  { label: 'Barcelona', value: 'Barcelona, Spain', flag: '🇪🇸' },
  { label: 'Rome', value: 'Rome, Italy', flag: '🇮🇹' },
  { label: 'Dubai', value: 'Dubai, UAE', flag: '🇦🇪' },
  { label: 'London', value: 'London, UK', flag: '🇬🇧' },
  { label: 'New York', value: 'New York, USA', flag: '🇺🇸' },
  { label: 'Seoul', value: 'Seoul, South Korea', flag: '🇰🇷' },
  { label: 'Sydney', value: 'Sydney, Australia', flag: '🇦🇺' },
  { label: 'Delhi', value: 'Delhi, India', flag: '🇮🇳' },
  { label: 'Kyoto', value: 'Kyoto, Japan', flag: '🇯🇵' },
  { label: 'Phuket', value: 'Phuket, Thailand', flag: '🇹🇭' },
];

export default function EmergencyCompanionPage() {
  const [destination, setDestination] = useState('Tokyo, Japan');
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);
  const [sosQuery, setSosQuery] = useState('');
  const [sosResult, setSosResult] = useState(null);
  const [sosLoading, setSosLoading] = useState(false);

  const activate = useCallback(async (dest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/emergency/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination: dest }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Could not activate companion');
      setProfile(data);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    activate(destination);
  }, []);

  const pickDestination = (value) => {
    setDestination(value);
    setSosResult(null);
    activate(value);
  };

  const handleDetect = (e) => {
    e.preventDefault();
    activate(destination);
    setSosResult(null);
  };

  const copyPhrase = (key, text) => {
    navigator.clipboard?.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const askSos = async (query) => {
    const q = query || sosQuery;
    if (!q.trim()) return;
    setSosLoading(true);
    setSosQuery(q);
    try {
      const res = await fetch('/api/emergency/sos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination, query: q }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'SOS failed');
      setSosResult(data);
    } catch (err) {
      setError(err.message);
    }
    setSosLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0f1419] text-white py-24 relative font-sans">
      <div className="absolute inset-0 bg-[radial-gradient(rgba(200,90,50,0.15)_1px,transparent_1px)] [background-size:20px_20px] opacity-40" />

      <div className="max-w-3xl mx-auto px-6 relative z-10">
        <div className="text-center mb-8 pt-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/20 text-red-300 text-[10px] font-bold uppercase tracking-widest border border-red-500/30 mb-3">
            <Siren size={10} className="animate-pulse" /> AI Emergency Travel Companion
          </span>
          <h1 className="text-4xl font-bold font-display">When things go wrong</h1>
          <p className="text-sm text-white/55 mt-2 max-w-md mx-auto">
            Auto-activates at your destination — 15+ countries, city-specific hospitals, scams, and
            translations.
          </p>
        </div>

        <form onSubmit={handleDetect} className="flex gap-2 mb-4 max-w-lg mx-auto">
          <div className="relative flex-1">
            <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
            <input
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="w-full pl-9 pr-4 py-3 rounded-xl bg-white/10 border border-white/15 text-sm placeholder-white/35 focus:border-red-400/50 outline-none"
              placeholder="Paris, Santorini, Bali, Dubai, London…"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-3 rounded-xl bg-red-600 hover:bg-red-500 text-sm font-bold shrink-0"
          >
            Activate
          </button>
        </form>

        <div className="mb-8 max-w-2xl mx-auto">
          <p className="text-[10px] font-mono uppercase tracking-widest text-white/35 text-center mb-3">
            Quick destinations
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {QUICK_DESTINATIONS.map((d) => (
              <button
                key={d.value}
                type="button"
                onClick={() => pickDestination(d.value)}
                className={`text-xs px-3 py-1.5 rounded-full border transition ${
                  destination === d.value
                    ? 'bg-red-600/30 border-red-400/50 text-white'
                    : 'bg-white/5 border-white/10 text-white/70 hover:border-white/25 hover:text-white'
                }`}
              >
                {d.flag} {d.label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-center text-red-300 text-sm mb-6 flex items-center justify-center gap-2">
            <AlertTriangle size={14} /> {error}
          </p>
        )}

        {loading && (
          <p className="text-center text-white/50 text-sm animate-pulse">Detecting country…</p>
        )}

        {!loading && profile && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <div className="flex items-center justify-between bg-gradient-to-r from-red-950/80 to-[#1E2229] border border-red-500/25 rounded-2xl p-5">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-red-300/80">
                  Auto-detected · Companion active
                </p>
                <h2 className="text-2xl font-bold font-display mt-1">
                  {profile.flag}{' '}
                  {profile.location_label || profile.display_name}
                </h2>
                {profile.city_display && profile.city_display !== profile.display_name && (
                  <p className="text-xs text-white/45 mt-1 font-mono">
                    City-specific essentials · {profile.country_key?.replace('_', ' ')}
                  </p>
                )}
              </div>
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center border border-red-400/40">
                <Shield size={22} className="text-red-400" />
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <h3 className="text-xs font-mono uppercase tracking-widest text-white/45 mb-4">
                Emergency essentials card
              </h3>
              <div className="grid sm:grid-cols-2 gap-4">
                <EssentialRow
                  icon={Hospital}
                  label="Nearest hospital"
                  name={profile.emergency_essentials.hospital.name}
                  meta={`${profile.emergency_essentials.hospital.distance} · ${profile.emergency_essentials.hospital.note}`}
                />
                <EssentialRow
                  icon={Pill}
                  label="Nearby pharmacy"
                  name={profile.emergency_essentials.pharmacy.name}
                  meta={`${profile.emergency_essentials.pharmacy.distance} · ${profile.emergency_essentials.pharmacy.note}`}
                />
                <div className="sm:col-span-2 p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="flex items-center gap-2 text-white/50 text-[10px] font-mono uppercase mb-2">
                    <Car size={12} /> Safe taxi apps
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {profile.emergency_essentials.taxi_apps.map((app) => (
                      <span
                        key={app}
                        className="px-3 py-1 rounded-full bg-[#1E3F2E]/40 border border-[#1E3F2E] text-xs font-medium"
                      >
                        {app}
                      </span>
                    ))}
                  </div>
                  <p className="text-[11px] text-white/45 mt-2">
                    {profile.emergency_essentials.safe_transport}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(profile.emergency_numbers).map(([k, v]) => (
                  <a
                    key={k}
                    href={`tel:${v}`}
                    className="text-center p-3 rounded-xl bg-red-600/20 border border-red-500/30 hover:bg-red-600/30 transition"
                  >
                    <Phone size={14} className="mx-auto text-red-300 mb-1" />
                    <p className="text-[9px] uppercase font-mono text-white/50">{k.replace('_', ' ')}</p>
                    <p className="font-bold text-sm">{v}</p>
                  </a>
                ))}
              </div>

              {profile.embassy && (
                <div className="mt-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/25 text-sm">
                  <p className="font-bold text-amber-200">{profile.embassy.label}</p>
                  <p className="text-white/60 text-xs mt-1">{profile.embassy.address}</p>
                  <a href={`tel:${profile.embassy.phone}`} className="text-amber-300 font-mono text-xs mt-2 inline-block">
                    {profile.embassy.phone}
                  </a>
                </div>
              )}
            </div>

            <div>
              <h3 className="text-xs font-mono uppercase tracking-widest text-white/45 mb-3 flex items-center gap-2">
                <AlertTriangle size={12} className="text-amber-400" />
                Country-specific scam warnings
              </h3>
              <div className="space-y-2">
                {profile.scam_warnings.map((w, i) => (
                  <div
                    key={i}
                    className={`p-4 rounded-xl border ${
                      w.severity === 'high'
                        ? 'bg-amber-500/10 border-amber-500/30'
                        : 'bg-white/5 border-white/10'
                    }`}
                  >
                    <p className="font-bold text-sm">{w.title}</p>
                    <p className="text-xs text-white/60 mt-1">{w.body}</p>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-xs font-mono uppercase tracking-widest text-white/45 mb-3 flex items-center gap-2">
                <Languages size={12} /> One-tap critical phrases
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {TRANSLATION_CATEGORIES.map(({ key, label, icon: Icon, color }) => {
                  const t = profile.translations[key];
                  if (!t) return null;
                  const copyId = `tr-${key}`;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => copyPhrase(copyId, t.phrase)}
                      className="text-left p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/25 transition group"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span
                          className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase"
                          style={{ color }}
                        >
                          <Icon size={12} /> {label}
                        </span>
                        {copiedKey === copyId ? (
                          <Check size={14} className="text-green-400" />
                        ) : (
                          <Copy size={14} className="text-white/30 group-hover:text-white/60" />
                        )}
                      </div>
                      <p className="text-lg font-display leading-tight">{t.phrase}</p>
                      <p className="text-[10px] text-white/45 mt-1 font-mono">{t.romanization}</p>
                      <p className="text-[10px] text-white/55 mt-0.5">{t.english}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="bg-gradient-to-b from-[#1E2229] to-black border border-white/10 rounded-2xl p-6">
              <h3 className="text-sm font-bold flex items-center gap-2 text-red-300">
                <Siren size={16} /> SOS Smart Assistant
              </h3>
              <p className="text-xs text-white/50 mt-1 mb-4">
                Describe what happened — get step-by-step guidance and local contacts.
              </p>

              <div className="flex flex-wrap gap-2 mb-4">
                {SOS_SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => askSos(s)}
                    className="text-[10px] px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/15 border border-white/10"
                  >
                    {s}
                  </button>
                ))}
              </div>

              <div className="flex gap-2">
                <input
                  value={sosQuery}
                  onChange={(e) => setSosQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && askSos()}
                  placeholder="e.g. Lost passport at Shinjuku station"
                  className="flex-1 px-4 py-3 rounded-xl bg-black/40 border border-white/15 text-sm outline-none focus:border-red-400/40"
                />
                <button
                  type="button"
                  onClick={() => askSos()}
                  disabled={sosLoading}
                  className="px-4 py-3 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50"
                >
                  <Send size={18} />
                </button>
              </div>

              <AnimatePresence>
                {sosResult && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-5 p-5 rounded-xl bg-red-950/40 border border-red-500/25"
                  >
                    <p className="text-xs font-mono text-red-300/80 uppercase">
                      {sosResult.matched ? 'Matched workflow' : 'General guidance'}
                    </p>
                    <h4 className="text-lg font-bold mt-1">{sosResult.title}</h4>
                    <p className="text-sm text-amber-200/90 mt-2 italic border-l-2 border-amber-400/50 pl-3">
                      {sosResult.reassurance}
                    </p>
                    <ol className="mt-4 space-y-2">
                      {sosResult.steps.map((step, i) => (
                        <li key={i} className="text-sm flex gap-3 text-white/85">
                          <span className="w-6 h-6 rounded-full bg-red-600/30 flex items-center justify-center text-xs font-bold shrink-0">
                            {i + 1}
                          </span>
                          {step}
                        </li>
                      ))}
                    </ol>
                    {sosResult.contacts?.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-white/10">
                        <p className="text-[10px] font-mono uppercase text-white/40 mb-2">Contacts</p>
                        {sosResult.contacts.map((c, i) => (
                          <p key={i} className="text-xs font-mono text-red-200/90">
                            {c}
                          </p>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function EssentialRow({ icon: Icon, label, name, meta }) {
  return (
    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
      <div className="flex items-center gap-2 text-white/45 text-[10px] font-mono uppercase mb-1">
        <Icon size={12} /> {label}
      </div>
      <p className="font-bold text-sm">{name}</p>
      <p className="text-[11px] text-white/50 mt-1">{meta}</p>
    </div>
  );
}
