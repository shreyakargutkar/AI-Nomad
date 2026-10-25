'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function ProtectedRoute({ children, redirectTo = '/login' }) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      const next = encodeURIComponent(pathname || '/');
      router.replace(`${redirectTo}?next=${next}`);
    }
  }, [loading, isAuthenticated, router, redirectTo, pathname]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FBF9F6] flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-[#1E2229]/55 mt-4 font-mono">Loading your session…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return children;
}
