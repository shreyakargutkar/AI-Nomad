'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Luggage, Compass, ArrowRight } from 'lucide-react';

export default function SmartPackingPage() {
  const [form, setForm] = useState({
    destination: '',
    start_date: '',
    end_date: '',
    itinerary: '',
  });
  const [packing, setPacking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [checked, setChecked] = useState({});

  const generate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/readiness', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, prebooked: [] }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to generate packing list');
      setPacking(data.packing_recommendations);
      setChecked({});
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const items = packing
    ? [
        ...(packing.essentials || []),
        ...(packing.by_activity || []),
        ...(packing.duration_extras || []),
      ]
    : [];

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 px-6">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-10 pt-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
            <Luggage size={10} /> Smart Packing
          </span>
          <h1 className="text-4xl font-bold font-display text-[#1E2229]">Packing Assistant</h1>
          <p className="text-sm text-[#1E2229]/60 mt-2">
            Weather- and activity-aware lists for your destination
          </p>
        </div>

        {!packing ? (
          <form onSubmit={generate} className="bg-white border border-[#EAE3D2] rounded-2xl p-8 space-y-4 shadow-sm">
            <input
              required
              placeholder="Destination (e.g. Tokyo, Japan)"
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
              className="w-full p-4 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-sm"
            />
            <div className="grid grid-cols-2 gap-4">
              <input
                required
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="w-full p-4 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] outline-none text-sm"
              />
              <input
                required
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="w-full p-4 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] outline-none text-sm"
              />
            </div>
            <textarea
              required
              rows={3}
              placeholder="Activities: teamLab, temples, hiking..."
              value={form.itinerary}
              onChange={(e) => setForm({ ...form, itinerary: e.target.value })}
              className="w-full p-4 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] outline-none text-sm"
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#1E3F2E] text-white py-4 rounded-lg font-bold text-sm uppercase disabled:opacity-50"
            >
              {loading ? 'Building list…' : 'Generate packing list'}
            </button>
          </form>
        ) : (
          <div className="bg-white border border-[#EAE3D2] rounded-2xl p-8 shadow-sm">
            {packing.weather?.summary && (
              <p className="text-xs text-[#2D6A8F] bg-[#2D6A8F]/5 border border-[#2D6A8F]/15 rounded-lg px-4 py-3 mb-6">
                {packing.weather.summary}
              </p>
            )}
            <ul className="space-y-2 mb-6">
              {items.map((item, i) => (
                <li key={i}>
                  <button
                    type="button"
                    onClick={() => setChecked((c) => ({ ...c, [i]: !c[i] }))}
                    className={`w-full text-left flex items-center gap-3 py-2 px-2 rounded-lg text-sm ${
                      checked[i] ? 'line-through text-[#1E2229]/40' : 'text-[#1E2229]'
                    }`}
                  >
                    <span
                      className={`w-5 h-5 rounded border flex-shrink-0 ${
                        checked[i] ? 'bg-[#1E3F2E] border-[#1E3F2E]' : 'border-[#EAE3D2]'
                      }`}
                    />
                    {item}
                  </button>
                </li>
              ))}
            </ul>
            {packing.contextual_tips?.map((tip, i) => (
              <p key={i} className="text-xs text-[#1E3F2E] border-l-2 border-[#1E3F2E]/30 pl-3 mb-2">
                {tip}
              </p>
            ))}
            <Link
              href="/readiness"
              className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-[#C85A32] hover:text-[#A54422]"
            >
              Full readiness dashboard <ArrowRight size={14} />
            </Link>
            <button
              type="button"
              onClick={() => setPacking(null)}
              className="block mt-4 text-xs font-mono text-[#1E2229]/50 hover:text-[#C85A32]"
            >
              ← New search
            </button>
          </div>
        )}

        <p className="text-center mt-8 text-xs text-[#1E2229]/45 flex items-center justify-center gap-1">
          <Compass size={12} /> Need bookings & visas too? Use the{' '}
          <Link href="/readiness" className="text-[#C85A32] font-bold">
            Trip Readiness Dashboard
          </Link>
        </p>
      </div>
    </div>
  );
}
