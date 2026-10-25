'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ChevronDown, LogOut, Map, BookOpen, User } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

function initials(name, email) {
  const base = name || email || 'E';
  const parts = base.trim().split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return base.slice(0, 2).toUpperCase();
}

export default function UserMenu() {
  const { user, signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  if (!user) return null;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-lg border border-[#EAE3D2] bg-white hover:border-[#C85A32]/40 transition-colors"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span className="w-8 h-8 rounded-full bg-[#1E3F2E] text-white text-xs font-bold flex items-center justify-center">
          {initials(user.name, user.email)}
        </span>
        <span className="hidden lg:block text-sm font-semibold text-[#1E2229] max-w-[100px] truncate">
          {user.name}
        </span>
        <ChevronDown size={14} className={`text-[#1E2229]/50 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full mt-2 w-52 bg-white border border-[#EAE3D2] rounded-xl shadow-lg py-2 z-50"
        >
          <p className="px-4 py-2 text-[10px] font-mono text-[#1E2229]/45 truncate border-b border-[#EAE3D2]/60 mb-1">
            {user.email}
          </p>
          <Link
            href="/trips"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-4 py-2.5 text-sm text-[#1E2229]/85 hover:bg-[#FBF9F6] hover:text-[#C85A32]"
          >
            <Map size={16} /> My Trips
          </Link>
          <Link
            href="/journal"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-4 py-2.5 text-sm text-[#1E2229]/85 hover:bg-[#FBF9F6] hover:text-[#C85A32]"
          >
            <BookOpen size={16} /> Travel Journal
          </Link>
          <Link
            href="/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-4 py-2.5 text-sm text-[#1E2229]/85 hover:bg-[#FBF9F6] hover:text-[#C85A32]"
          >
            <User size={16} /> Profile
          </Link>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              signOut();
            }}
            className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 border-t border-[#EAE3D2]/60 mt-1"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      )}
    </div>
  );
}
