import { supabase } from '@/lib/supabase';

/** Insert profile row using Supabase Auth user id (never a random UUID). */
export async function ensureUserProfile(authUser, { name } = {}) {
  if (!supabase || !authUser?.id) return { error: new Error('Supabase not configured') };

  const { data: existing, error: selectError } = await supabase
    .from('users')
    .select('id')
    .eq('id', authUser.id)
    .maybeSingle();

  if (selectError) return { error: selectError };
  if (existing) return { error: null };

  const profileName =
    name?.trim() ||
    authUser.user_metadata?.full_name ||
    authUser.user_metadata?.name ||
    authUser.email?.split('@')[0] ||
    'Explorer';

  const { error: insertError } = await supabase.from('users').insert({
    id: authUser.id,
    name: profileName,
    email: authUser.email,
  });

  return { error: insertError };
}

export async function fetchUserProfile(userId) {
  if (!supabase || !userId) return null;
  const { data, error } = await supabase
    .from('users')
    .select('id, name, email, travel_style, created_at')
    .eq('id', userId)
    .maybeSingle();
  if (error) throw error;
  return data;
}
