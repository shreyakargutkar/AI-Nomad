'use client';

import Link from 'next/link';
import { Compass } from 'lucide-react';

export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="min-h-screen bg-[#FBF9F6] flex items-center justify-center px-6 py-28 relative">
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-50 pointer-events-none" />

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 text-2xl font-extrabold tracking-widest font-display text-[#1E3F2E] hover:opacity-85">
            <Compass size={22} className="text-[#C85A32]" />
            AINOMAD
          </Link>
          <h1 className="text-3xl font-bold font-display text-[#1E2229] mt-6">{title}</h1>
          {subtitle && <p className="text-sm text-[#1E2229]/60 mt-2">{subtitle}</p>}
          <div className="h-0.5 w-12 bg-[#C85A32] mx-auto mt-4" />
        </div>

        <div className="bg-white border border-[#EAE3D2] rounded-2xl p-8 shadow-[0_10px_30px_-10px_rgba(30,34,41,0.08)]">
          {children}
        </div>

        {footer && <div className="text-center mt-6 text-sm text-[#1E2229]/65">{footer}</div>}
      </div>
    </div>
  );
}
