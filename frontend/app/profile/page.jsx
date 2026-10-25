'use client';

import { useEffect, useState } from 'react';
import { User } from 'lucide-react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AuthAlert from '@/components/auth/AuthAlert';
import { useAuth } from '@/hooks/useAuth';
import { fetchUserProfile } from '@/lib/authProfile';
import { supabase } from '@/lib/supabase';

function ProfileContent() {
  const { user } = useAuth();
  const [name, setName] = useState('');
  const [travelStyle, setTravelStyle] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user?.id) return;
    fetchUserProfile(user.id)
      .then((profile) => {
        setName(profile?.name || user.name || '');
        setTravelStyle(profile?.travel_style || '');
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [user?.id, user?.name]);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!supabase || !user?.id) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    const { error: updateError } = await supabase
      .from('users')
      .update({ name: name.trim(), travel_style: travelStyle.trim() || null })
      .eq('id', user.id);
    setSaving(false);
    if (updateError) {
      setError(updateError.message);
      return;
    }
    setMessage('Profile updated.');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FBF9F6] flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-28 px-6">
      <div className="max-w-lg mx-auto">
        <div className="text-center mb-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
            <User size={10} /> Explorer profile
          </span>
          <h1 className="text-4xl font-bold font-display text-[#1E2229]">Profile</h1>
        </div>

        <form onSubmit={handleSave} className="bg-white border border-[#EAE3D2] rounded-2xl p-8 shadow-sm space-y-5">
          <AuthAlert message={error} />
          <AuthAlert type="success" message={message} />

          <div>
            <label className="block text-xs font-mono font-bold uppercase text-[#1E3F2E] mb-2">Email</label>
            <p className="text-sm text-[#1E2229]/70 p-3 bg-[#FBF9F6] rounded-lg border border-[#EAE3D2]">{user?.email}</p>
          </div>

          <div>
            <label htmlFor="name" className="block text-xs font-mono font-bold uppercase text-[#1E3F2E] mb-2">
              Name
            </label>
            <input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full p-3.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm outline-none focus:border-[#C85A32]"
            />
          </div>

          <div>
            <label htmlFor="travel_style" className="block text-xs font-mono font-bold uppercase text-[#1E3F2E] mb-2">
              Travel style
            </label>
            <input
              id="travel_style"
              value={travelStyle}
              onChange={(e) => setTravelStyle(e.target.value)}
              placeholder="e.g. slow travel, adventure, luxury"
              className="w-full p-3.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm outline-none focus:border-[#C85A32]"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full py-3 bg-[#1E3F2E] text-white rounded-lg font-bold text-sm disabled:opacity-60"
          >
            {saving ? 'Saving…' : 'Save profile'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
