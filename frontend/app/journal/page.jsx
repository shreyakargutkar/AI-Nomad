'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, BookOpen, Compass, Plus } from 'lucide-react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import JournalEntryCard from '@/components/journal/JournalEntryCard';
import { useAuth } from '@/hooks/useAuth';
import {
  createJournalEntry,
  deleteJournalEntry,
  listEntriesForTrip,
  listJournalGroupedByTrip,
  readImageAsDataUrl,
  updateJournalEntry,
} from '@/lib/journalEntriesApi';
import { formatTripDates, listUserTrips } from '@/lib/tripsApi';

function JournalContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tripParam = searchParams.get('trip');
  const { user } = useAuth();

  const [trips, setTrips] = useState([]);
  const [grouped, setGrouped] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState(tripParam || null);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [entriesLoading, setEntriesLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [entryForm, setEntryForm] = useState({ title: '', content: '' });
  const [imagePreview, setImagePreview] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [editingEntry, setEditingEntry] = useState(null);
  const [editForm, setEditForm] = useState({ title: '', content: '' });
  const [editImagePreview, setEditImagePreview] = useState(null);
  const [editImageUrl, setEditImageUrl] = useState(null);

  const selectedTrip = trips.find((t) => t.trip_id === selectedTripId) || null;

  const loadTripsAndHistory = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    setError(null);
    try {
      const [tripList, groupedList] = await Promise.all([
        listUserTrips(user.id),
        listJournalGroupedByTrip(user.id),
      ]);
      setTrips(tripList);
      setGrouped(groupedList);
      if (tripParam && tripList.some((t) => t.trip_id === tripParam)) {
        setSelectedTripId(tripParam);
      }
    } catch (e) {
      setError(e.message || 'Failed to load journal');
    }
    setLoading(false);
  }, [user?.id, tripParam]);

  const loadEntries = useCallback(async (tripId) => {
    if (!tripId) {
      setEntries([]);
      return;
    }
    setEntriesLoading(true);
    try {
      const list = await listEntriesForTrip(tripId);
      setEntries(list);
    } catch (e) {
      setError(e.message || 'Failed to load entries');
    }
    setEntriesLoading(false);
  }, []);

  useEffect(() => {
    loadTripsAndHistory();
  }, [loadTripsAndHistory]);

  useEffect(() => {
    if (selectedTripId) loadEntries(selectedTripId);
  }, [selectedTripId, loadEntries]);

  useEffect(() => {
    if (tripParam) setSelectedTripId(tripParam);
  }, [tripParam]);

  const onImagePick = async (e, isEdit = false) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const dataUrl = await readImageAsDataUrl(file);
      if (isEdit) {
        setEditImageUrl(dataUrl);
        setEditImagePreview(dataUrl);
      } else {
        setImageUrl(dataUrl);
        setImagePreview(dataUrl);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAddEntry = async (e) => {
    e.preventDefault();
    if (!selectedTripId) {
      setError('Select a saved trip first.');
      return;
    }
    if (!entryForm.content.trim()) {
      setError('Write something for your journal entry.');
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      await createJournalEntry({
        tripId: selectedTripId,
        title: entryForm.title,
        content: entryForm.content,
        imageUrl,
      });
      setEntryForm({ title: '', content: '' });
      setImageUrl(null);
      setImagePreview(null);
      setSuccess('Entry saved to your travel diary.');
      await loadEntries(selectedTripId);
      await loadTripsAndHistory();
    } catch (err) {
      setError(err.message || 'Could not save entry');
    }
    setSubmitting(false);
  };

  const startEdit = (entry) => {
    setEditingEntry(entry);
    setEditForm({ title: entry.title || '', content: entry.content || '' });
    setEditImageUrl(entry.image_url || null);
    setEditImagePreview(entry.image_url || null);
    setError(null);
    setSuccess(null);
  };

  const handleUpdateEntry = async (e) => {
    e.preventDefault();
    if (!editingEntry) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      await updateJournalEntry(editingEntry.entry_id, {
        title: editForm.title,
        content: editForm.content,
        imageUrl: editImageUrl,
      });
      setEditingEntry(null);
      setSuccess('Entry updated.');
      await loadEntries(selectedTripId);
      await loadTripsAndHistory();
    } catch (err) {
      setError(err.message || 'Could not update entry');
    }
    setSubmitting(false);
  };

  const handleDeleteEntry = async (entry) => {
    if (!window.confirm('Delete this journal entry?')) return;
    setError(null);
    try {
      await deleteJournalEntry(entry.entry_id);
      setSuccess('Entry deleted.');
      if (editingEntry?.entry_id === entry.entry_id) setEditingEntry(null);
      await loadEntries(selectedTripId);
      await loadTripsAndHistory();
    } catch (err) {
      setError(err.message || 'Could not delete entry');
    }
  };

  const openTrip = (tripId) => {
    setSelectedTripId(tripId);
    router.replace(`/journal?trip=${tripId}`, { scroll: false });
  };

  const backToHub = () => {
    setSelectedTripId(null);
    setEditingEntry(null);
    router.replace('/journal', { scroll: false });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FBF9F6] flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!trips.length) {
    return (
      <div className="min-h-screen bg-[#FBF9F6] py-28 px-6">
        <div className="max-w-md mx-auto text-center bg-white border border-[#EAE3D2] rounded-2xl p-10 shadow-sm">
          <BookOpen className="w-12 h-12 text-[#1E3F2E] mx-auto mb-4" />
          <h1 className="text-2xl font-bold font-display text-[#1E2229] mb-2">Travel Journal</h1>
          <p className="text-sm text-[#1E2229]/65 mb-6">
            Save a trip from the itinerary planner first, then write day-by-day memories linked to that journey.
          </p>
          <Link
            href="/iternary"
            className="inline-block px-6 py-3 bg-[#1E3F2E] text-white rounded-lg font-bold text-sm hover:bg-[#2D5A43]"
          >
            Plan & save a trip
          </Link>
        </div>
      </div>
    );
  }

  if (selectedTripId && selectedTrip) {
    return (
      <div className="min-h-screen bg-[#FBF9F6] py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <button
            type="button"
            onClick={backToHub}
            className="text-xs font-mono font-bold text-[#1E3F2E] hover:text-[#C85A32] flex items-center gap-1 mb-6"
          >
            <ArrowLeft size={14} /> All trips
          </button>

          <header className="mb-8 border-l-4 border-[#C85A32] pl-5">
            <span className="text-[10px] font-mono font-bold text-[#C85A32] uppercase tracking-widest">
              Travel diary
            </span>
            <h1 className="text-3xl font-bold font-display text-[#1E2229] mt-1">
              {selectedTrip.destination}
            </h1>
            <p className="text-sm text-[#1E2229]/60 mt-1 font-mono">
              {formatTripDates(selectedTrip.start_date, selectedTrip.end_date)}
            </p>
          </header>

          {error && (
            <p className="text-sm text-red-600 mb-4 bg-red-50 border border-red-200 rounded-lg py-2 px-4">{error}</p>
          )}
          {success && (
            <p className="text-sm text-[#1E3F2E] mb-4 bg-[#1E3F2E]/10 border border-[#1E3F2E]/20 rounded-lg py-2 px-4">
              {success}
            </p>
          )}

          {entriesLoading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="relative space-y-6 mb-10 pl-6 border-l-2 border-[#EAE3D2]/80 ml-2">
              {entries.length === 0 ? (
                <p className="text-sm text-[#1E2229]/50 italic -ml-6 pl-6 py-4">
                  No entries yet — add your first memory below.
                </p>
              ) : (
                entries.map((entry) => (
                  <div key={entry.entry_id} className="relative -ml-[1.6rem]">
                    <span className="absolute -left-[0.55rem] top-6 w-3 h-3 rounded-full bg-[#C85A32] border-2 border-[#FBF9F6]" />
                    <JournalEntryCard
                      entry={entry}
                      onEdit={startEdit}
                      onDelete={handleDeleteEntry}
                    />
                  </div>
                ))
              )}
            </div>
          )}

          {editingEntry ? (
            <form onSubmit={handleUpdateEntry} className="bg-white border-2 border-[#1E3F2E]/30 rounded-2xl p-6 mb-6 space-y-4">
              <h2 className="font-bold font-display text-[#1E3F2E]">Edit entry</h2>
              <input
                placeholder="Entry title"
                value={editForm.title}
                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                className="w-full p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
              <textarea
                required
                rows={4}
                value={editForm.content}
                onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                className="w-full p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
              <input type="file" accept="image/*" onChange={(e) => onImagePick(e, true)} className="text-xs" />
              {editImagePreview && (
                <img src={editImagePreview} alt="" className="h-24 rounded-lg object-cover border border-[#EAE3D2]" />
              )}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 bg-[#1E3F2E] text-white py-3 rounded-lg font-bold text-sm disabled:opacity-60"
                >
                  {submitting ? 'Saving…' : 'Update entry'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditingEntry(null)}
                  className="px-4 py-3 border border-[#EAE3D2] rounded-lg text-sm font-bold text-[#1E2229]/70"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleAddEntry} className="bg-white border border-[#EAE3D2] rounded-2xl p-6 space-y-4 shadow-sm">
              <h2 className="font-bold font-display text-[#1E3F2E] flex items-center gap-2">
                <Plus size={16} /> New journal entry
              </h2>
              <input
                placeholder="Entry title (e.g. Day 1 in Tokyo)"
                value={entryForm.title}
                onChange={(e) => setEntryForm({ ...entryForm, title: e.target.value })}
                className="w-full p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
              <textarea
                required
                rows={4}
                placeholder="What happened today?"
                value={entryForm.content}
                onChange={(e) => setEntryForm({ ...entryForm, content: e.target.value })}
                className="w-full p-3 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm"
              />
              <input type="file" accept="image/*" onChange={(e) => onImagePick(e, false)} className="text-xs" />
              {imagePreview && (
                <img src={imagePreview} alt="" className="h-24 rounded-lg object-cover border border-[#EAE3D2]" />
              )}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-[#C85A32] text-white py-3 rounded-lg font-bold text-sm hover:bg-[#A54422] disabled:opacity-60"
              >
                {submitting ? 'Saving…' : 'Save to journal'}
              </button>
            </form>
          )}

          <div className="mt-6">
            <label className="text-xs font-mono font-bold text-[#1E3F2E] uppercase block mb-2">
              Switch trip
            </label>
            <select
              value={selectedTripId}
              onChange={(e) => openTrip(e.target.value)}
              className="w-full p-3 rounded-lg border border-[#EAE3D2] bg-white text-sm"
            >
              {trips.map((t) => (
                <option key={t.trip_id} value={t.trip_id}>
                  {t.destination || 'Trip'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    );
  }

  const tripsWithEntries = grouped.filter((g) => g.entries.length > 0);

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10 pt-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
            <Compass size={10} /> Travel Journal
          </span>
          <h1 className="text-4xl font-bold font-display text-[#1E2229]">Your travel diary</h1>
          <p className="text-sm text-[#1E2229]/60 mt-2">Memories grouped by saved trip</p>
        </div>

        {error && (
          <p className="text-sm text-red-600 text-center mb-4 bg-red-50 border border-red-200 rounded-lg py-2 px-4">
            {error}
          </p>
        )}
        {success && (
          <p className="text-sm text-[#1E3F2E] text-center mb-4 bg-[#1E3F2E]/10 border border-[#1E3F2E]/20 rounded-lg py-2 px-4">
            {success}
          </p>
        )}

        <section className="mb-12">
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1E3F2E] mb-4">
            Choose a trip to write
          </h2>
          <ul className="space-y-3">
            {trips.map((trip) => {
              const count = grouped.find((g) => g.trip.trip_id === trip.trip_id)?.entries.length || 0;
              return (
                <li key={trip.trip_id}>
                  <button
                    type="button"
                    onClick={() => openTrip(trip.trip_id)}
                    className="w-full text-left bg-white border border-[#EAE3D2] rounded-xl p-5 hover:border-[#C85A32] transition-colors shadow-sm flex justify-between items-center gap-4"
                  >
                    <div>
                      <h3 className="font-bold font-display text-[#1E2229]">{trip.destination}</h3>
                      <p className="text-xs text-[#1E2229]/55 mt-1 font-mono">
                        {formatTripDates(trip.start_date, trip.end_date)}
                      </p>
                    </div>
                    <span className="text-[10px] font-mono font-bold text-[#C85A32] shrink-0">
                      {count} {count === 1 ? 'entry' : 'entries'} →
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>

        {tripsWithEntries.length > 0 && (
          <section>
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#1E3F2E] mb-6">
              Journal history
            </h2>
            <div className="space-y-10">
              {tripsWithEntries.map(({ trip, entries: tripEntries }) => (
                <div key={trip.trip_id}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold font-display text-[#1E2229]">{trip.destination}</h3>
                    <button
                      type="button"
                      onClick={() => openTrip(trip.trip_id)}
                      className="text-xs font-bold text-[#C85A32] hover:underline"
                    >
                      View all
                    </button>
                  </div>
                  <ul className="space-y-3">
                    {tripEntries.slice(0, 5).map((entry) => (
                      <li key={entry.entry_id}>
                        <JournalEntryCard
                          entry={entry}
                          compact
                          onEdit={() => openTrip(trip.trip_id)}
                          onDelete={handleDeleteEntry}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        )}

        <p className="text-center mt-10">
          <Link href="/trips" className="text-xs font-mono text-[#C85A32] hover:underline">
            ← My Trips
          </Link>
        </p>
      </div>
    </div>
  );
}

function JournalFallback() {
  return (
    <div className="min-h-screen bg-[#FBF9F6] flex items-center justify-center">
      <div className="w-10 h-10 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function JournalPageInner() {
  return (
    <ProtectedRoute>
      <JournalContent />
    </ProtectedRoute>
  );
}

export default function JournalPage() {
  return (
    <Suspense fallback={<JournalFallback />}>
      <JournalPageInner />
    </Suspense>
  );
}
