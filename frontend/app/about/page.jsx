import Link from 'next/link';
import { Compass, ArrowRight } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#FBF9F6] py-28 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-4">
          <Compass size={10} /> Our Philosophy
        </span>
        <h1 className="text-4xl font-bold font-display text-[#1E2229] mb-6">About Ainomad</h1>
        <p className="text-[#1E2229]/75 leading-relaxed mb-6 text-left">
          Ainomad is a travel preparation platform built for hackathon explorers who want plans that feel like
          stories—not spreadsheets. We combine structured itineraries, festival discovery, community scrapbooks,
          and a smart readiness dashboard so you arrive prepared, not overwhelmed.
        </p>
        <p className="text-[#1E2229]/75 leading-relaxed mb-10 text-left">
          Our design language draws from physical travel journals: warm paper tones, editorial typography, and
          tools that respect the nuance of each destination—from JR Pass logistics in Japan to temple dress codes
          in Thailand.
        </p>
        <Link
          href="/features"
          className="inline-flex items-center gap-2 px-6 py-3 bg-[#1E3F2E] text-white rounded-lg font-bold text-sm hover:bg-[#2D5A43] transition-colors"
        >
          View features <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
