import { supabase } from '@/lib/supabase';

export async function listUserTrips(userId) {
  if (!supabase || !userId) return [];
  const { data, error } = await supabase
    .from('trips')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });
  if (error) throw error;
  return data || [];
}

export async function saveTrip({ userId, destination, startDate, endDate, budget, readinessScore, overspendingRisk }) {
  if (!supabase || !userId) throw new Error('Sign in to save trips.');
  const { data, error } = await supabase
    .from('trips')
    .insert({
      user_id: userId,
      destination,
      start_date: startDate || null,
      end_date: endDate || null,
      budget: budget != null ? Math.round(Number(budget)) : null,
      readiness_score: readinessScore != null ? Math.round(Number(readinessScore)) : null,
      overspending_risk: overspendingRisk || null,
    })
    .select()
    .single();
  if (error) throw error;
  return data;
}

export async function deleteTrip(userId, tripId) {
  if (!supabase || !userId || !tripId) throw new Error('Unable to delete trip.');

  const { error: entriesError } = await supabase
    .from('journal_entries')
    .delete()
    .eq('trip_id', tripId);
  if (entriesError) throw entriesError;

  const { error } = await supabase
    .from('trips')
    .delete()
    .eq('trip_id', tripId)
    .eq('user_id', userId);
  if (error) throw error;
}

export function formatTripDates(start, end) {
  if (start && end) return `${formatDate(start)} → ${formatDate(end)}`;
  if (start) return `From ${formatDate(start)}`;
  if (end) return `Until ${formatDate(end)}`;
  return 'Dates not set';
}

export function formatDate(value) {
  if (!value) return '';
  try {
    return new Date(value).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return String(value);
  }
}
