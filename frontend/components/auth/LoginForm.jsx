'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import AuthShell from '@/components/auth/AuthShell';
import AuthAlert from '@/components/auth/AuthAlert';
import PasswordInput from '@/components/auth/PasswordInput';
import { useAuth } from '@/hooks/useAuth';

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signIn, isAuthenticated, loading: authLoading, authError, clearAuthError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const next = searchParams.get('next') || '/';

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace(next.startsWith('/') ? next : '/');
    }
  }, [authLoading, isAuthenticated, router, next]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearAuthError();
    setLoading(true);
    const { error } = await signIn({ email, password });
    setLoading(false);
    if (!error) {
      router.replace(next.startsWith('/') ? next : '/');
      router.refresh();
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to continue your travel journal"
      footer={
        <>
          New explorer?{' '}
          <Link href="/signup" className="font-bold text-[#C85A32] hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <AuthAlert message={authError} />
        {searchParams.get('registered') === '1' && (
          <AuthAlert type="success" message="Account created. Sign in to continue." />
        )}

        <div>
          <label htmlFor="email" className="block text-xs font-mono font-bold uppercase tracking-wider text-[#1E3F2E] mb-2">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            required
            className="w-full p-3.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm focus:border-[#C85A32] focus:ring-2 focus:ring-[#C85A32]/15 outline-none"
          />
        </div>

        <PasswordInput
          id="password"
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Your password"
          autoComplete="current-password"
        />

        <button
          type="submit"
          disabled={loading || authLoading}
          className="w-full py-3.5 bg-[#1E3F2E] text-white rounded-lg font-bold text-sm hover:bg-[#2D5A43] transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Signing in…
            </>
          ) : (
            'Sign in'
          )}
        </button>
      </form>
    </AuthShell>
  );
}
