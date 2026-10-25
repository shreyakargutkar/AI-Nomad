'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import AuthShell from '@/components/auth/AuthShell';
import AuthAlert from '@/components/auth/AuthAlert';
import PasswordInput from '@/components/auth/PasswordInput';
import { useAuth } from '@/hooks/useAuth';

function validatePassword(password) {
  if (password.length < 8) return 'Password must be at least 8 characters.';
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    return 'Use letters and numbers for a stronger password.';
  }
  return null;
}

export default function SignupPage() {
  const router = useRouter();
  const { signUp, isAuthenticated, loading: authLoading, authError, clearAuthError } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace('/');
    }
  }, [authLoading, isAuthenticated, router]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearAuthError();
    setLocalError(null);
    setSuccess(null);

    if (!name.trim()) {
      setLocalError('Please enter your name.');
      return;
    }
    const pwErr = validatePassword(password);
    if (pwErr) {
      setLocalError(pwErr);
      return;
    }
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }

    setLoading(true);
    const { error, data } = await signUp({ name: name.trim(), email, password });
    setLoading(false);

    if (error) return;

    if (data?.session) {
      router.replace('/');
      router.refresh();
      return;
    }

    setSuccess('Check your email to confirm your account, then sign in.');
    setTimeout(() => router.push('/login?registered=1'), 2000);
  };

  const displayError = localError || authError;

  return (
    <AuthShell
      title="Join Ainomad"
      subtitle="Create your explorer account"
      footer={
        <>
          Already have an account?{' '}
          <Link href="/login" className="font-bold text-[#C85A32] hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <AuthAlert message={displayError} />
        <AuthAlert type="success" message={success} />

        <div>
          <label htmlFor="name" className="block text-xs font-mono font-bold uppercase tracking-wider text-[#1E3F2E] mb-2">
            Full name
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Alex Explorer"
            autoComplete="name"
            required
            className="w-full p-3.5 rounded-lg border border-[#EAE3D2] bg-[#FBF9F6] text-sm focus:border-[#C85A32] focus:ring-2 focus:ring-[#C85A32]/15 outline-none"
          />
        </div>

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
          placeholder="Min. 8 characters"
          autoComplete="new-password"
          minLength={8}
        />

        <PasswordInput
          id="confirmPassword"
          label="Confirm password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Repeat password"
          autoComplete="new-password"
          minLength={8}
        />

        <button
          type="submit"
          disabled={loading || authLoading}
          className="w-full py-3.5 bg-[#C85A32] text-white rounded-lg font-bold text-sm hover:bg-[#A54422] transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Creating account…
            </>
          ) : (
            'Create account'
          )}
        </button>
      </form>
    </AuthShell>
  );
}
