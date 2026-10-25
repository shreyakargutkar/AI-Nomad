'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { clearStoredUser, setStoredUser } from '@/lib/auth';
import { ensureUserProfile, fetchUserProfile } from '@/lib/authProfile';

const AuthContext = createContext(null);

function mapSessionUser(sessionUser, profile) {
  if (!sessionUser) return null;
  return {
    id: sessionUser.id,
    email: sessionUser.email,
    name:
      profile?.name ||
      sessionUser.user_metadata?.full_name ||
      sessionUser.user_metadata?.name ||
      sessionUser.email?.split('@')[0] ||
      'Explorer',
    travel_style: profile?.travel_style ?? null,
  };
}

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  const applySession = useCallback(async (nextSession) => {
    setSession(nextSession);
    const authUser = nextSession?.user;
    if (!authUser) {
      setUser(null);
      clearStoredUser();
      return;
    }
    let profile = null;
    try {
      profile = await fetchUserProfile(authUser.id);
    } catch {
      profile = null;
    }
    const mapped = mapSessionUser(authUser, profile);
    setUser(mapped);
    setStoredUser(mapped);
  }, []);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    let mounted = true;

    supabase.auth.getSession().then(({ data: { session: initial } }) => {
      if (!mounted) return;
      applySession(initial).finally(() => {
        if (mounted) setLoading(false);
      });
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      applySession(nextSession);
      setLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [applySession]);

  const signUp = useCallback(async ({ name, email, password }) => {
    setAuthError(null);
    if (!supabase) {
      const err = new Error('Supabase is not configured.');
      setAuthError(err.message);
      return { error: err };
    }

    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: { full_name: name.trim(), name: name.trim() },
      },
    });

    if (error) {
      setAuthError(error.message);
      return { error };
    }

    if (data.user) {
      const { error: profileError } = await ensureUserProfile(data.user, { name });
      if (profileError) {
        setAuthError(profileError.message);
        return { error: profileError };
      }
      await applySession(data.session);
    }

    return { error: null, data };
  }, [applySession]);

  const signIn = useCallback(async ({ email, password }) => {
    setAuthError(null);
    if (!supabase) {
      const err = new Error('Supabase is not configured.');
      setAuthError(err.message);
      return { error: err };
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    if (error) {
      setAuthError(error.message);
      return { error };
    }

    if (data.user) {
      await ensureUserProfile(data.user, {
        name: data.user.user_metadata?.full_name || data.user.user_metadata?.name,
      });
      await applySession(data.session);
    }

    return { error: null, data };
  }, [applySession]);

  const signOut = useCallback(async () => {
    setAuthError(null);
    if (supabase) {
      await supabase.auth.signOut();
    }
    setUser(null);
    setSession(null);
    clearStoredUser();
    router.push('/');
    router.refresh();
  }, [router]);

  const value = useMemo(
    () => ({
      user,
      session,
      loading,
      authError,
      isAuthenticated: Boolean(user?.id),
      signUp,
      signIn,
      signOut,
      clearAuthError: () => setAuthError(null),
    }),
    [user, session, loading, authError, signUp, signIn, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return ctx;
}
