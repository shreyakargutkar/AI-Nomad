'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  CloudRain,
  Sun,
  Clock,
  MapPin,
  RefreshCw,
  Footprints,
  Armchair,
  Users,
  Zap,
} from 'lucide-react';

const PRESETS = [
  {
    label: 'Couple · explorer',
    desc: 'Kyoto · live weather & time',
    payload: {
      city: 'kyoto',
      activity_state: 'stationary',
      group_size: 'couple',
      preferences: ['food', 'culture'],
      archetype: 'explorer',
    },
  },
  {
    label: 'Solo · moving',
    desc: 'Tokyo · live weather & time',
    payload: {
      city: 'tokyo',
      activity_state: 'moving',
      group_size: 'solo',
      preferences: ['outdoor', 'culture', 'nature'],
      archetype: 'explorer',
    },
  },
];

const WEATHER_OPTIONS = [
  { w: 'clear', icon: Sun, label: 'Clear' },
  { w: 'cloudy', icon: CloudRain, label: 'Cloudy' },
  { w: 'rain', icon: CloudRain, label: 'Rain' },
  { w: 'snow', icon: CloudRain, label: 'Snow' },
  { w: 'extreme_heat', icon: Sun, label: 'Heat' },
];

function buildPayload(form) {
  return {
    city: form.city,
    activity_state: form.activity_state,
    group_size: form.group_size,
    archetype: form.archetype,
    budget_tier: form.budget_tier,
    preferences: form.preferences,
    crowd_averse: form.crowd_averse,
  };
}

export default function ContextualRecommendationsPage() {
  const [form, setForm] = useState({
    city: 'kyoto',
    hour: 12,
    weather: 'clear',
    day_type: 'weekday',
    activity_state: 'stationary',
    budget_tier: 'mid',
    group_size: 'couple',
    archetype: 'explorer',
    preferences: ['food', 'culture'],
    crowd_averse: false,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const syncLiveContext = (data) => {
    const live = data?.live_context || data?.context;
    if (!live) return;
    setForm((f) => ({
      ...f,
      hour: live.hour ?? f.hour,
      weather: live.weather ?? f.weather,
      day_type: live.day_type ?? f.day_type,
    }));
  };

  const fetchRecs = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/recommendations/contextual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load recommendations');
      syncLiveContext(data);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err.message);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const initial = { ...form, ...PRESETS[0].payload };
    setForm(initial);
    fetchRecs(buildPayload(initial));
  }, []);

  const applyPreset = (preset) => {
    const next = { ...form, ...preset.payload };
    setForm(next);
    fetchRecs(buildPayload(next));
  };

  const update = (key, value) => {
    const next = { ...form, [key]: value };
    setForm(next);
    fetchRecs(buildPayload(next));
  };

  const timeLabel = (h) => {
    if (h >= 21 || h < 6) return 'Late night';
    if (h >= 17) return 'Evening';
    if (h >= 11) return 'Afternoon';
    return 'Morning';
  };

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 relative font-sans">
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-50" />

      <div className="max-w-3xl mx-auto px-6 relative z-10">
        <div className="text-center mb-8 pt-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#2D6A8F]/10 text-[#2D6A8F] text-[10px] font-bold uppercase tracking-widest border border-[#2D6A8F]/20 mb-3">
            <Sparkles size={10} /> Live Context Engine
          </span>
          <h1 className="text-4xl font-bold font-display text-[#1E2229]">Right now, for you</h1>
          <p className="text-sm text-[#1E2229]/60 mt-2 max-w-lg mx-auto">
            Not a static Top 10 — suggestions regenerate when time, weather, or your moment
            changes.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-3 mb-6">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-left p-4 rounded-xl border border-[#EAE3D2] bg-white hover:border-[#2D6A8F]/40 transition shadow-sm"
            >
              <p className="font-bold text-sm text-[#1E2229]">{p.label}</p>
              <p className="text-[10px] text-[#1E2229]/50 mt-1 font-mono">{p.desc}</p>
            </button>
          ))}
        </div>

        <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6 mb-6 shadow-sm space-y-5">
          <p className="text-[10px] font-mono uppercase tracking-widest text-[#1E2229]/45">
            Adjust traveler context — weather & time sync live from the selected city
          </p>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-1">
                <MapPin size={10} /> City
              </label>
              <select
                value={form.city}
                onChange={(e) => update('city', e.target.value)}
                className="w-full mt-1 p-2.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              >
                <option value="kyoto">Kyoto</option>
                <option value="tokyo">Tokyo</option>
                <option value="paris">Paris</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-1">
                <Clock size={10} /> Local hour ({timeLabel(form.hour)})
              </label>
              <input
                type="range"
                min={0}
                max={23}
                value={form.hour}
                readOnly
                tabIndex={-1}
                className="w-full mt-2 pointer-events-none opacity-80"
              />
              <p className="text-[10px] font-mono text-[#1E2229]/50">
                {result?.live_context?.local_time || `${form.hour}:00`} · {form.day_type}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {WEATHER_OPTIONS.map(({ w, icon: Icon, label }) => (
              <span
                key={w}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold border ${
                  form.weather === w
                    ? 'bg-[#2D6A8F] text-white border-[#2D6A8F]'
                    : 'bg-[#FBF9F6] border-[#EAE3D2] text-[#1E2229]/70'
                }`}
              >
                <Icon size={12} /> {label}
              </span>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { k: 'activity_state', v: 'moving', icon: Footprints, label: 'Moving' },
              { k: 'activity_state', v: 'stationary', icon: Armchair, label: 'Stationary' },
            ].map(({ k, v, icon: Icon, label }) => (
              <button
                key={v}
                type="button"
                onClick={() => update(k, v)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold border ${
                  form[k] === v
                    ? 'bg-[#1E3F2E] text-white border-[#1E3F2E]'
                    : 'bg-[#FBF9F6] border-[#EAE3D2]'
                }`}
              >
                <Icon size={12} /> {label}
              </button>
            ))}
            {[
              { k: 'archetype', v: 'explorer', label: 'Explorer' },
              { k: 'archetype', v: 'family', label: 'Family' },
              { k: 'archetype', v: 'budget', label: 'Budget' },
            ].map(({ k, v, label }) => (
              <button
                key={v}
                type="button"
                onClick={() => update(k, v)}
                className={`px-3 py-2 rounded-lg text-xs font-bold border ${
                  form[k] === v
                    ? 'bg-[#C85A32] text-white border-[#C85A32]'
                    : 'bg-[#FBF9F6] border-[#EAE3D2]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

        {loading && (
          <p className="text-center text-[#1E2229]/50 text-sm animate-pulse flex items-center justify-center gap-2">
            <RefreshCw size={14} className="animate-spin" /> Regenerating for this moment…
          </p>
        )}

        <AnimatePresence mode="wait">
          {result && !loading && (
            <motion.div
              key={result.context_fingerprint}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="p-5 rounded-2xl bg-gradient-to-r from-[#2D6A8F]/15 to-[#1E3F2E]/10 border border-[#2D6A8F]/25">
                <p className="text-[10px] font-mono uppercase tracking-widest text-[#2D6A8F]">
                  Moment detected
                </p>
                <h2 className="text-xl font-bold font-display text-[#1E2229] mt-1">
                  {result.moment_summary}
                </h2>
                <p className="text-xs text-[#1E2229]/55 mt-2">{result.contrast_note}</p>
                <div className="flex flex-wrap gap-2 mt-3">
                  {result.primary_categories.map((c) => (
                    <span
                      key={c}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-white/80 border border-[#EAE3D2] font-mono uppercase"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              {result.recommendations.map((rec, i) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="bg-white border border-[#EAE3D2] rounded-xl p-5 shadow-sm"
                >
                  <div className="flex justify-between items-start gap-3">
                    <div>
                      <span className="text-[10px] font-mono text-[#C85A32] font-bold">
                        #{i + 1} · {Math.round(rec.score * 100)}% match
                      </span>
                      <h3 className="font-bold text-[#1E2229] mt-0.5">{rec.name}</h3>
                    </div>
                    <span className="text-[10px] font-mono text-[#1E2229]/45 shrink-0">
                      {rec.distance_km} km · {rec.duration_min} min
                    </span>
                  </div>
                  <p className="text-sm text-[#1E3F2E] mt-2 italic border-l-2 border-[#2D6A8F]/40 pl-3">
                    {rec.why_now}
                  </p>
                  {rec.conflict_note && (
                    <p className="text-[10px] text-[#C85A32] mt-2 flex items-center gap-1">
                      <Zap size={10} /> {rec.conflict_note}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {rec.categories.map((c) => (
                      <span
                        key={c}
                        className="text-[9px] px-2 py-0.5 rounded bg-[#FBF9F6] border border-[#EAE3D2] font-mono"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </motion.div>
              ))}

              <p className="text-center text-[10px] font-mono text-[#1E2229]/40 pt-4">
                <Users size={10} className="inline mr-1" />
                {result.next_refresh_hint} · fingerprint {result.context_fingerprint}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
