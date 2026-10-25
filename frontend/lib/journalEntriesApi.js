import { supabase } from '@/lib/supabase';
import { listUserTrips } from '@/lib/tripsApi';

export async function listEntriesForTrip(tripId) {
  if (!supabase || !tripId) return [];
  const { data, error } = await supabase
    .from('journal_entries')
    .select('*')
    .eq('trip_id', tripId)
    .order('created_at', { ascending: false });
  if (error) throw error;
  return data || [];
}

/** Trips for user with their journal entries (for grouped history). */
export async function listJournalGroupedByTrip(userId) {
  const trips = await listUserTrips(userId);
  if (!trips.length) return [];

  const tripIds = trips.map((t) => t.trip_id);
  const { data: entries, error } = await supabase
    .from('journal_entries')
    .select('*')
    .in('trip_id', tripIds)
    .order('created_at', { ascending: false });

  if (error) throw error;

  return trips.map((trip) => ({
    trip,
    entries: (entries || []).filter((e) => e.trip_id === trip.trip_id),
  }));
}

export async function createJournalEntry({ tripId, title, content, imageUrl }) {
  if (!supabase || !tripId) throw new Error('Select a saved trip first.');
  const { data, error } = await supabase
    .from('journal_entries')
    .insert({
      trip_id: tripId,
      title: title?.trim() || null,
      content: content?.trim() || '',
      image_url: imageUrl || null,
    })
    .select()
    .single();
  if (error) throw error;
  return data;
}

export async function updateJournalEntry(entryId, { title, content, imageUrl }) {
  if (!supabase || !entryId) throw new Error('Entry not found.');
  const payload = {};
  if (title !== undefined) payload.title = title?.trim() || null;
  if (content !== undefined) payload.content = content?.trim() || '';
  if (imageUrl !== undefined) payload.image_url = imageUrl || null;

  const { data, error } = await supabase
    .from('journal_entries')
    .update(payload)
    .eq('entry_id', entryId)
    .select()
    .single();
  if (error) throw error;
  return data;
}

export async function deleteJournalEntry(entryId) {
  if (!supabase || !entryId) throw new Error('Entry not found.');
  const { error } = await supabase.from('journal_entries').delete().eq('entry_id', entryId);
  if (error) throw error;
}

/** Read image file as data URL for image_url (no storage bucket required). */
export function readImageAsDataUrl(file, maxBytes = 800_000) {
  return new Promise((resolve, reject) => {
    if (!file) {
      resolve(null);
      return;
    }
    if (file.size > maxBytes) {
      reject(new Error('Image must be under 800KB. Try a smaller photo.'));
      return;
    }
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Could not read image.'));
    reader.readAsDataURL(file);
  });
}
