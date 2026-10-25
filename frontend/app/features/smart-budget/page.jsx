'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Wallet,
  AlertTriangle,
  TrendingDown,
  Sparkles,
  Calendar,
  IndianRupee,
  ChevronRight,
  ShieldAlert,
  Lightbulb,
  Plane,
  Users,
  Building,
} from 'lucide-react';

const DEMO_ITINERARY = `Day 1: Arrive Haneda, Shinjuku hotel
Day 2: teamLab Planets, Ginza dinner
Day 3: Shopping Shinjuku + outlet
Day 4: Disneyland
Day 5: DisneySea
Day 6: Asakusa, Skytree
Day 7: Kyoto day trip Shinkansen`;

export default function SmartBudgetPage() {
  const [mode, setMode] = useState('ml'); // 'ml' or 'detailed'
  const [form, setForm] = useState({
    destination: 'Tokyo, Japan',
    total_budget: 120000,
    travel_style: 'mid-range',
    start_date: '',
    end_date: '',
    itinerary: DEMO_ITINERARY,
    shopping_preferences: 'Souvenirs + outlet shopping on Day 3',
    food_preferences: 'Mix of street food and one splurge dinner',
  });
  const [mlForm, setMlForm] = useState({
    destination_country: 'Japan',
    total_stays: 8,
    adults: 2,
    children: 0,
    hotel: 'Resort Hotel',
    reserved_room_type: 'A',
    budget: 70000,
  });
  const [result, setResult] = useState(null);
  const [mlResult, setMlResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/budget-intelligence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          total_budget: Number(form.total_budget),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Analysis failed');
      setResult(data);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const validateMlForm = () => {
    if (!mlForm.destination_country?.trim()) {
      return 'Destination country is required';
    }
    if (!mlForm.total_stays || Number(mlForm.total_stays) <= 0) {
      return 'Trip days must be at least 1';
    }
    if (!mlForm.adults || Number(mlForm.adults) <= 0) {
      return 'At least 1 adult is required';
    }
    if (Number(mlForm.children) < 0) {
      return 'Children count cannot be negative';
    }
    if (!mlForm.budget || Number(mlForm.budget) <= 0) {
      return 'Budget must be greater than 0';
    }
    return null;
  };

  const predictBudget = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);

    const validationError = validateMlForm();
    if (validationError) {
      setError(validationError);
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/predict-budget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...mlForm,
          total_stays: Number(mlForm.total_stays),
          adults: Number(mlForm.adults),
          children: Number(mlForm.children),
          budget: Number(mlForm.budget),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Prediction failed');
      setMlResult(data);
    } catch (err) {
      setError(err.message || 'Could not reach the budget predictor. Is the backend running?');
    }
    setLoading(false);
  };

  const score = result?.trip_budget_health_score ?? 0;
  const scoreColor =
    score >= 75 ? '#1E3F2E' : score >= 50 ? '#C85A32' : '#A54422';

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 relative font-sans">
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-50" />

      <div className="max-w-4xl mx-auto px-6 relative z-10">
        <div className="text-center mb-10 pt-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#C85A32]/10 text-[#C85A32] text-[10px] font-bold uppercase tracking-widest border border-[#C85A32]/20 mb-3">
            <Wallet size={10} /> Smart Budget Predictor
          </span>
          <h1 className="text-4xl font-bold text-[#1E2229] font-display">Trip Budget Prediction</h1>
          <p className="text-sm text-[#1E2229]/60 mt-2 max-w-lg mx-auto">
            ML-powered travel cost prediction with risk assessment and smart recommendations.
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="flex justify-center mb-8">
          <div className="bg-white border border-[#EAE3D2] rounded-full p-1 flex gap-1">
            <button
              onClick={() => { setMode('ml'); setResult(null); setMlResult(null); }}
              className={`px-4 py-2 rounded-full text-xs font-bold transition ${
                mode === 'ml' ? 'bg-[#1E3F2E] text-white' : 'text-[#1E2229]/60 hover:text-[#1E2229]'
              }`}
            >
              <Plane size={12} className="inline mr-1" /> ML Prediction
            </button>
            <button
              onClick={() => { setMode('detailed'); setResult(null); setMlResult(null); }}
              className={`px-4 py-2 rounded-full text-xs font-bold transition ${
                mode === 'detailed' ? 'bg-[#1E3F2E] text-white' : 'text-[#1E2229]/60 hover:text-[#1E2229]'
              }`}
            >
              <Calendar size={12} className="inline mr-1" /> Detailed Analysis
            </button>
          </div>
        </div>

        {mode === 'ml' ? (
          !mlResult ? (
            <form
              onSubmit={predictBudget}
              className="bg-white border border-[#EAE3D2] rounded-2xl p-8 shadow-sm space-y-5 max-w-xl mx-auto"
            >
              <div>
                <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-2">
                  <Plane size={12} /> Destination Country
                </label>
                <input
                  required
                  value={mlForm.destination_country}
                  onChange={(e) => setMlForm({ ...mlForm, destination_country: e.target.value })}
                  className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                  placeholder="Japan"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">
                    Trip Duration (days)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={mlForm.total_stays}
                    onChange={(e) => setMlForm({ ...mlForm, total_stays: e.target.value })}
                    className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-2">
                    <Users size={12} /> Adults
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={mlForm.adults}
                    onChange={(e) => setMlForm({ ...mlForm, adults: e.target.value })}
                    className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">Children</label>
                  <input
                    type="number"
                    min="0"
                    value={mlForm.children}
                    onChange={(e) => setMlForm({ ...mlForm, children: e.target.value })}
                    className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase flex items-center gap-2">
                    <Building size={12} /> Hotel Type
                  </label>
                  <select
                    value={mlForm.hotel}
                    onChange={(e) => setMlForm({ ...mlForm, hotel: e.target.value })}
                    className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                  >
                    <option value="Resort Hotel">Resort Hotel</option>
                    <option value="City Hotel">City Hotel</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">Room Type</label>
                  <select
                    value={mlForm.reserved_room_type}
                    onChange={(e) => setMlForm({ ...mlForm, reserved_room_type: e.target.value })}
                    className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                  >
                    <option value="A">Type A</option>
                    <option value="B">Type B</option>
                    <option value="C">Type C</option>
                    <option value="D">Type D</option>
                    <option value="E">Type E</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">
                    Budget (₹)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={mlForm.budget}
                    onChange={(e) => setMlForm({ ...mlForm, budget: e.target.value })}
                    className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                  />
                </div>
              </div>
              {error && (
                <p className="text-sm text-red-600 flex items-center gap-2">
                  <AlertTriangle size={14} /> {error}
                </p>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 rounded-xl bg-[#1E3F2E] text-white font-bold text-sm hover:bg-[#2a5240] transition disabled:opacity-60 flex items-center justify-center gap-2"
              >
                <Sparkles size={16} />
                {loading ? 'Predicting Budget...' : 'Predict Budget'}
              </button>
            </form>
          ) : (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <button
                type="button"
                onClick={() => setMlResult(null)}
                className="text-xs font-mono text-[#C85A32] hover:underline"
              >
                ← Edit inputs
              </button>

              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-8 shadow-sm">
                <h2 className="text-lg font-bold text-[#1E2229] font-display mb-6 text-center">
                  Trip Budget Analysis
                </h2>

                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-[#FBF9F6] border border-[#EAE3D2] text-center">
                    <p className="text-[10px] font-mono uppercase tracking-widest text-[#1E2229]/50">
                      Your Budget
                    </p>
                    <p className="text-2xl font-bold font-display mt-2 text-[#1E2229]">
                      ₹{(mlResult.budget ?? mlForm.budget)?.toLocaleString('en-IN')}
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-[#FBF9F6] border border-[#EAE3D2] text-center">
                    <p className="text-[10px] font-mono uppercase tracking-widest text-[#1E2229]/50">
                      Predicted Spend
                    </p>
                    <p className="text-2xl font-bold font-display mt-2 text-[#1E3F2E]">
                      ₹{mlResult.predicted_spend?.toLocaleString('en-IN')}
                    </p>
                    {mlResult.predicted_spend_usd != null && (
                      <p className="text-[10px] mt-1 text-[#1E2229]/50">
                        ≈ ${mlResult.predicted_spend_usd?.toLocaleString('en-US')} USD
                      </p>
                    )}
                  </div>

                  <div className="p-4 rounded-xl bg-[#FBF9F6] border border-[#EAE3D2] text-center sm:col-span-2 lg:col-span-1">
                    <p className="text-[10px] font-mono uppercase tracking-widest text-[#1E2229]/50">
                      Risk Level
                    </p>
                    <p
                      className={`text-2xl font-bold font-display mt-2 ${
                        mlResult.risk_level === 'LOW'
                          ? 'text-[#1E3F2E]'
                          : mlResult.risk_level === 'MEDIUM'
                            ? 'text-[#C85A32]'
                            : 'text-[#A54422]'
                      }`}
                    >
                      {mlResult.risk_level}
                    </p>
                  </div>
                </div>

                <div className="mt-4 grid sm:grid-cols-2 gap-4">
                  <div
                    className={`p-4 rounded-xl border text-center ${
                      mlResult.status === 'Over Budget'
                        ? 'bg-red-50 border-red-200'
                        : mlResult.status === 'Near Budget'
                          ? 'bg-amber-50 border-amber-200'
                          : 'bg-emerald-50 border-emerald-200'
                    }`}
                  >
                    <p className="text-[10px] font-mono uppercase tracking-widest text-[#1E2229]/50">
                      Budget Status
                    </p>
                    <p className="text-lg font-bold mt-2">{mlResult.status}</p>
                  </div>

                  <div className="p-4 rounded-xl bg-[#FBF9F6] border border-[#EAE3D2] text-center">
                    <p className="text-[10px] font-mono uppercase tracking-widest text-[#1E2229]/50">
                      Overspending Amount
                    </p>
                    <p
                      className={`text-lg font-bold mt-2 ${
                        mlResult.overspending_amount > 0 ? 'text-[#A54422]' : 'text-[#1E3F2E]'
                      }`}
                    >
                      {mlResult.overspending_amount > 0
                        ? `₹${mlResult.overspending_amount?.toLocaleString('en-IN')}`
                        : '₹0 — on track'}
                    </p>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-[#1E3F2E] text-white rounded-xl">
                  <p className="text-sm font-bold flex items-center gap-2 mb-2">
                    <Lightbulb size={14} /> Recommendation
                  </p>
                  <p className="text-sm opacity-90 leading-relaxed">{mlResult.recommendation}</p>
                </div>
              </div>
            </motion.div>
          )
        ) : (
          !result ? (
            <form
              onSubmit={analyze}
              className="bg-white border border-[#EAE3D2] rounded-2xl p-8 shadow-sm space-y-5 max-w-xl mx-auto"
            >
              <div>
                <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">Destination</label>
                <input
                  required
                  value={form.destination}
                onChange={(e) => setForm({ ...form, destination: e.target.value })}
                className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                placeholder="Tokyo, Japan"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">
                  Total budget (₹)
                </label>
                <input
                  type="number"
                  required
                  value={form.total_budget}
                  onChange={(e) => setForm({ ...form, total_budget: e.target.value })}
                  className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                />
              </div>
              <div>
                <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">
                  Travel style
                </label>
                <select
                  value={form.travel_style}
                  onChange={(e) => setForm({ ...form, travel_style: e.target.value })}
                  className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                >
                  <option value="budget">Budget</option>
                  <option value="mid-range">Mid-range</option>
                  <option value="luxury">Luxury</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">Start</label>
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                  className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                />
              </div>
              <div>
                <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">End</label>
                <input
                  type="date"
                  value={form.end_date}
                  onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                  className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">Itinerary</label>
              <textarea
                rows={5}
                value={form.itinerary}
                onChange={(e) => setForm({ ...form, itinerary: e.target.value })}
                className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">
                Shopping preferences
              </label>
              <input
                value={form.shopping_preferences}
                onChange={(e) => setForm({ ...form, shopping_preferences: e.target.value })}
                className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase">
                Food preferences
              </label>
              <input
                value={form.food_preferences}
                onChange={(e) => setForm({ ...form, food_preferences: e.target.value })}
                className="w-full mt-1 p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
            </div>
            {error && (
              <p className="text-sm text-red-600 flex items-center gap-2">
                <AlertTriangle size={14} /> {error}
              </p>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 rounded-xl bg-[#1E3F2E] text-white font-bold text-sm hover:bg-[#2a5240] transition disabled:opacity-60 flex items-center justify-center gap-2"
            >
              <Sparkles size={16} />
              {loading ? 'Analyzing spend risk…' : 'Generate Budget Health Score'}
            </button>
          </form>
        ) : (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <button
              type="button"
              onClick={() => setResult(null)}
              className="text-xs font-mono text-[#C85A32] hover:underline"
            >
              ← Edit inputs
            </button>

            <div className="grid md:grid-cols-3 gap-6">
              <div className="md:col-span-1 bg-white border border-[#EAE3D2] rounded-2xl p-6 text-center shadow-sm">
                <p className="text-[10px] font-mono uppercase tracking-widest text-[#1E2229]/50">
                  Trip Budget Health Score
                </p>
                <div
                  className="text-6xl font-bold font-display mt-2"
                  style={{ color: scoreColor }}
                >
                  {score}
                </div>
                <p className="text-xs mt-2 text-[#1E2229]/60">{result.risk_label}</p>
                <p className="text-[10px] font-mono mt-4 text-[#C85A32]">
                  {result.budget_exhaust_message}
                </p>
              </div>

              <div className="md:col-span-2 bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-bold text-[#1E3F2E] flex items-center gap-2">
                  <IndianRupee size={14} /> Projection vs budget
                </h3>
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-[10px] font-mono uppercase text-[#1E2229]/45">Your budget</p>
                    <p className="text-xl font-bold">
                      ₹{result.inputs_summary.total_budget_inr.toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] font-mono uppercase text-[#1E2229]/45">Projected spend</p>
                    <p className="text-xl font-bold text-[#C85A32]">
                      ₹{result.projection.projected_total_inr.toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
                <div className="mt-4 h-3 rounded-full bg-[#EAE3D2] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, (result.projection.projected_total_inr / result.inputs_summary.total_budget_inr) * 100)}%`,
                      backgroundColor: scoreColor,
                    }}
                  />
                </div>
                <p className="text-xs mt-2 text-[#1E2229]/55">
                  {result.projection.vs_budget_inr > 0
                    ? `₹${result.projection.vs_budget_inr.toLocaleString('en-IN')} over budget at current pace`
                    : `₹${Math.abs(result.projection.vs_budget_inr).toLocaleString('en-IN')} buffer remaining`}
                </p>
              </div>
            </div>

            {result.overspending_alerts?.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-[#1E2229] flex items-center gap-2">
                  <ShieldAlert size={16} className="text-[#C85A32]" />
                  Destination-specific overspending alerts
                </h3>
                {result.overspending_alerts.map((a, i) => (
                  <div
                    key={i}
                    className={`p-4 rounded-xl border ${
                      a.severity === 'high'
                        ? 'bg-red-50 border-red-200'
                        : 'bg-amber-50 border-amber-200'
                    }`}
                  >
                    <p className="font-bold text-sm">{a.title}</p>
                    <p className="text-xs mt-1 text-[#1E2229]/75">{a.message}</p>
                    {a.potential_overage_inr > 0 && (
                      <p className="text-[10px] font-mono mt-2 text-[#C85A32]">
                        Potential overage: ₹{a.potential_overage_inr.toLocaleString('en-IN')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6">
                <h3 className="text-sm font-bold text-[#1E3F2E] flex items-center gap-2 mb-4">
                  <Lightbulb size={14} /> Hidden costs travelers miss
                </h3>
                <ul className="space-y-2">
                  {result.hidden_costs.map((h) => (
                    <li key={h.id} className="flex justify-between text-xs border-b border-[#EAE3D2]/60 pb-2">
                      <span>
                        <span className="font-medium">{h.label}</span>
                        {h.note && (
                          <span className="block text-[#1E2229]/50 mt-0.5">{h.note}</span>
                        )}
                      </span>
                      <span className="font-mono font-bold shrink-0 ml-2">
                        ₹{h.amount_inr.toLocaleString('en-IN')}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-[#1E3F2E] text-white rounded-2xl p-6">
                <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
                  <TrendingDown size={14} /> Smart fixes
                  <span className="text-[10px] font-mono opacity-70 ml-auto">
                    Top 3 save ₹{result.potential_savings_top3_inr?.toLocaleString('en-IN')}
                  </span>
                </h3>
                <div className="space-y-4">
                  {result.smart_fixes.slice(0, 3).map((fix) => (
                    <div key={fix.id} className="border-t border-white/15 pt-3 first:border-0 first:pt-0">
                      <p className="font-bold text-sm">{fix.title}</p>
                      <p className="text-[#C85A32] text-xs font-mono mt-0.5">
                        Save ₹{fix.savings_inr.toLocaleString('en-IN')}
                      </p>
                      <ol className="mt-2 space-y-1">
                        {fix.steps.map((s, j) => (
                          <li key={j} className="text-[11px] opacity-85 flex gap-2">
                            <ChevronRight size={12} className="shrink-0 mt-0.5" />
                            {s}
                          </li>
                        ))}
                      </ol>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-white border border-[#EAE3D2] rounded-2xl p-6">
              <h3 className="text-sm font-bold text-[#1E2229] flex items-center gap-2 mb-4">
                <Calendar size={14} /> Day-by-day budget burn forecast
              </h3>
              <div className="flex gap-1 overflow-x-auto pb-2">
                {result.day_by_day_forecast.map((d) => (
                  <div
                    key={d.day}
                    className={`min-w-[72px] flex-1 rounded-lg p-2 text-center text-[10px] font-mono border ${
                      d.status === 'depleted'
                        ? 'bg-red-100 border-red-300'
                        : d.status === 'warning'
                          ? 'bg-amber-50 border-amber-200'
                          : 'bg-[#FBF9F6] border-[#EAE3D2]'
                    }`}
                  >
                    <p className="font-bold">D{d.day}</p>
                    <p className="mt-1 opacity-70">-₹{(d.spend_inr / 1000).toFixed(1)}k</p>
                    <p
                      className={`mt-1 font-bold ${
                        d.remaining_inr < 0 ? 'text-red-600' : 'text-[#1E3F2E]'
                      }`}
                    >
                      {d.remaining_inr < 0 ? 'OUT' : `₹${(d.remaining_inr / 1000).toFixed(0)}k`}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
