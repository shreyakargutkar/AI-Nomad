'use client';

import { useState, useMemo } from 'react';
import { Wallet } from 'lucide-react';

const DEFAULTS = {
  flights: 800,
  hotelPerNight: 150,
  foodPerDay: 60,
  activitiesPerDay: 40,
  transport: 100,
  misc: 150,
};

export default function BudgetPlannerPage() {
  const [nights, setNights] = useState(7);
  const [travelers, setTravelers] = useState(2);
  const [costs, setCosts] = useState(DEFAULTS);

  const total = useMemo(() => {
    const perPerson =
      costs.flights +
      costs.hotelPerNight * nights +
      costs.foodPerDay * nights +
      costs.activitiesPerDay * nights +
      costs.transport +
      costs.misc;
    return Math.round(perPerson * travelers);
  }, [costs, nights, travelers]);

  const update = (key, value) => setCosts((c) => ({ ...c, [key]: Number(value) || 0 }));

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 px-6">
      <div className="max-w-xl mx-auto">
        <div className="text-center mb-10 pt-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#C85A32]/10 text-[#C85A32] text-[10px] font-bold uppercase tracking-widest border border-[#C85A32]/20 mb-3">
            <Wallet size={10} /> Budget Planner
          </span>
          <h1 className="text-4xl font-bold font-display text-[#1E2229]">Trip Budget Estimate</h1>
          <p className="text-sm text-[#1E2229]/60 mt-2">Rough per-person costs × travelers</p>
        </div>

        <div className="bg-white border border-[#EAE3D2] rounded-2xl p-8 shadow-sm space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">Nights</label>
              <input
                type="number"
                min={1}
                value={nights}
                onChange={(e) => setNights(Number(e.target.value))}
                className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">Travelers</label>
              <input
                type="number"
                min={1}
                value={travelers}
                onChange={(e) => setTravelers(Number(e.target.value))}
                className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
            </div>
          </div>

          {[
            ['flights', 'Flights (per person)'],
            ['hotelPerNight', 'Hotel per night'],
            ['foodPerDay', 'Food per day'],
            ['activitiesPerDay', 'Activities per day'],
            ['transport', 'Local transport (flat)'],
            ['misc', 'Misc / insurance (flat)'],
          ].map(([key, label]) => (
            <div key={key}>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">{label}</label>
              <input
                type="number"
                min={0}
                value={costs[key]}
                onChange={(e) => update(key, e.target.value)}
                className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
            </div>
          ))}

          <div className="pt-6 border-t border-[#EAE3D2] text-center">
            <p className="text-xs font-mono uppercase text-[#1E2229]/50">Estimated total</p>
            <p className="text-4xl font-bold font-display text-[#C85A32] mt-1">
              ${total.toLocaleString()}
            </p>
            <p className="text-[10px] text-[#1E2229]/45 mt-2 font-mono">
              ${Math.round(total / travelers).toLocaleString()} per traveler · {nights} nights
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
