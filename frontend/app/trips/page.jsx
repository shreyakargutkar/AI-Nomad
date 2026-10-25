'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { BookOpen, Map, Plus, Trash2 } from 'lucide-react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { deleteTrip, formatTripDates, listUserTrips } from '@/lib/tripsApi';

function TripsContent() {
  const { user } = useAuth();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const load = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listUserTrips(user.id);
      setTrips(data);
    } catch (e) {
      setError(e.message || 'Failed to load trips');
    }
    setLoading(false);
  }, [user?.id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (trip) => {
    const label = trip.destination || 'this trip';
    if (!window.confirm(`Delete "${label}" and all its journal entries? This cannot be undone.`)) {
      return;
    }
    setDeletingId(trip.trip_id);
    setError(null);
    try {
      await deleteTrip(user.id, trip.trip_id);
      setTrips((prev) => prev.filter((t) => t.trip_id !== trip.trip_id));
    } catch (e) {
      setError(e.message || 'Failed to delete trip');
    }
    setDeletingId(null);
  };

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-28 px-6">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
            <Map size={10} /> Saved journeys
          </span>
          <h1 className="text-4xl font-bold font-display text-[#1E2229]">My Trips</h1>
          <p className="text-sm text-[#1E2229]/60 mt-2">Itineraries you stamped to your memoir</p>
        </div>

        {error && (
          <p className="text-sm text-red-600 text-center mb-4 bg-red-50 border border-red-200 rounded-lg py-2 px-4">
            {error}
          </p>
        )}

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="w-10 h-10 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : trips.length === 0 ? (
          <div className="bg-white border border-[#EAE3D2] rounded-2xl p-12 text-center shadow-sm">
            <p className="text-base text-[#1E2229]/70 mb-2 font-display font-semibold">
              Your travel memories start here ✈️
            </p>
            <p className="text-sm text-[#1E2229]/55 mb-8">Save your first trip.</p>
            <Link
              href="/iternary"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#1E3F2E] text-white rounded-lg font-bold text-sm hover:bg-[#2D5A43] transition-colors"
            >
              <Plus size={16} /> Plan a trip
            </Link>
          </div>
        ) : (
          <ul className="space-y-5">
            {trips.map((trip) => (
              <li
                key={trip.trip_id}
                className="bg-white border border-[#EAE3D2] rounded-2xl p-6 shadow-[0_10px_30px_-10px_rgba(30,34,41,0.06)] hover:border-[#C85A32]/30 transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-bold font-display text-[#1E2229]">
                      {trip.destination || 'Untitled trip'}
                    </h3>
                    <p className="text-xs text-[#1E2229]/55 mt-2 font-mono">
                      {formatTripDates(trip.start_date, trip.end_date)}
                    </p>
                    <div className="flex flex-wrap gap-3 mt-3 text-xs font-semibold">
                      {trip.budget != null && (
                        <span className="px-2.5 py-1 rounded-full bg-[#FBF9F6] border border-[#EAE3D2] text-[#1E2229]">
                          Budget ₹{Number(trip.budget).toLocaleString('en-IN')}
                        </span>
                      )}
                      {trip.readiness_score != null && (
                        <span className="px-2.5 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E]">
                          Readiness {trip.readiness_score}%
                        </span>
                      )}
                      {trip.overspending_risk && (
                        <span className="px-2.5 py-1 rounded-full bg-[#C85A32]/10 text-[#C85A32]">
                          Risk: {trip.overspending_risk}
                        </span>
                      )}
                    </div>
                    {trip.created_at && (
                      <p className="text-[10px] font-mono text-[#1E2229]/40 mt-3">
                        Saved {new Date(trip.created_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <div className="flex sm:flex-col gap-2 shrink-0">
                    <Link
                      href={`/journal?trip=${trip.trip_id}`}
                      className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 bg-[#1E3F2E] text-white rounded-lg text-xs font-bold hover:bg-[#2D5A43]"
                    >
                      <BookOpen size={14} /> Journal
                    </Link>
                    <button
                      type="button"
                      onClick={() => handleDelete(trip)}
                      disabled={deletingId === trip.trip_id}
                      className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 border border-red-200 text-red-600 rounded-lg text-xs font-bold hover:bg-red-50 disabled:opacity-50"
                    >
                      <Trash2 size={14} />
                      {deletingId === trip.trip_id ? 'Deleting…' : 'Delete'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function TripsPage() {
  return (
    <ProtectedRoute>
      <TripsContent />
    </ProtectedRoute>
  );
}
