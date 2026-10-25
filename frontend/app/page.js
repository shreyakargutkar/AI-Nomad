'use client';

import { useRouter } from 'next/navigation';
import { ArrowRight, BookOpen, Compass, Palmtree } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen text-[#1E2229] overflow-hidden relative font-sans">
      {/* Editorial Hero Banner */}
      <div className="relative h-[85vh] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0 bg-gradient-to-br from-[#1E3F2E] via-[#2D5A43] to-[#1E2229]">
          <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_30%_20%,#C85A32_0%,transparent_50%)]" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#1E2229]/20 via-[#1E2229]/40 to-[#FBF9F6]" />
        </div>

        {/* Hero Text */}
        <div className="relative z-10 text-center max-w-4xl mx-auto px-6 mt-16">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FFFFFF]/25 backdrop-blur-md text-[#FBF9F6] text-xs font-bold uppercase tracking-widest border border-white/20 mb-6">
            <Compass size={14} className="animate-spin-slow" /> The Conscious Explorer
          </span>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white font-display drop-shadow-sm leading-[1.1]">
            Document Your <br/>Next Pilgrimage
          </h1>
          <p className="mt-6 text-lg md:text-xl text-[#FBF9F6]/90 max-w-2xl mx-auto font-sans leading-relaxed">
            Create structured itineraries, trace local events, and measure pre-departure readiness with Ainomad, your organic digital travel logbook.
          </p>
          
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push('/features')}
              className="px-8 py-4 bg-[#C85A32] text-white rounded-lg font-bold text-lg flex items-center justify-center gap-2 shadow-lg hover:bg-[#A54422] transition-all transform hover:-translate-y-0.5"
            >
              Begin Journaling
              <ArrowRight size={18} />
            </button>
            
            <button
              onClick={() => router.push('/about')}
              className="px-8 py-4 bg-white/10 text-white border border-[#EAE3D2]/40 rounded-lg font-bold text-lg hover:bg-white/20 backdrop-blur-sm transition-all"
            >
              Our Philosophy
            </button>
          </div>
        </div>
      </div>

      {/* Narrative Intro Section */}
      <section className="relative z-10 bg-[#FBF9F6] py-20 px-6 md:px-16 lg:px-24">
        <div className="max-w-4xl mx-auto text-center">
          <span className="text-xs uppercase tracking-widest text-[#C85A32] font-extrabold">A New Perspective</span>
          <h2 className="text-3xl md:text-4xl font-bold font-display text-[#1E3F2E] mt-3 mb-6">Built for those who travel intentionally</h2>
          <p className="text-lg text-[#1E2229]/80 leading-relaxed font-sans max-w-3xl mx-auto">
            Traditional travel planners look like spreadsheets. We believe plans should look like stories. Ainomad combines natural intelligence with beautiful typography to produce itineraries that feel like visual journals of your future travels.
          </p>
        </div>
      </section>

      {/* Feature Highlight Grid */}
      <section id="features" className="relative z-10 bg-white py-20 px-6 md:px-16 lg:px-24 border-y border-[#EAE3D2]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs uppercase tracking-widest text-[#C85A32] font-extrabold">Digital Tools</span>
            <h2 className="text-3xl md:text-4xl font-bold font-display text-[#1E3F2E] mt-3">Logbook Features</h2>
            <div className="h-1 w-12 bg-[#C85A32] mx-auto mt-4"></div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <button type="button" onClick={() => router.push('/iternary')} className="text-left bg-[#FBF9F6] p-8 rounded-xl border border-[#EAE3D2]/60 hover:shadow-md hover:border-[#C85A32]/40 transition-all group w-full">
              <div className="w-12 h-12 bg-[#1E3F2E]/10 rounded-full flex items-center justify-center text-[#1E3F2E] mb-6 group-hover:bg-[#1E3F2E] group-hover:text-white transition-all">
                <BookOpen size={22} />
              </div>
              <h3 className="text-xl font-bold font-display text-[#1E2229] mb-3">Custom Itineraries</h3>
              <p className="text-sm text-[#1E2229]/75 leading-relaxed">
                Describe your dream escape and generate interactive daily plans, complete with accommodation ideas, flights, and travel documents.
              </p>
            </button>

            <button type="button" onClick={() => router.push('/readiness')} className="text-left bg-[#FBF9F6] p-8 rounded-xl border border-[#EAE3D2]/60 hover:shadow-md hover:border-[#C85A32]/40 transition-all group w-full">
              <div className="w-12 h-12 bg-[#1E3F2E]/10 rounded-full flex items-center justify-center text-[#1E3F2E] mb-6 group-hover:bg-[#1E3F2E] group-hover:text-white transition-all">
                <Compass size={22} />
              </div>
              <h3 className="text-xl font-bold font-display text-[#1E2229] mb-3">Pre-Departure Readiness</h3>
              <p className="text-sm text-[#1E2229]/75 leading-relaxed">
                Log what you have booked and receive a visual preparedness briefing. We compile packing, visa, and local transport essentials dynamically.
              </p>
            </button>

            <button type="button" onClick={() => router.push('/features/cultural-intelligence')} className="text-left bg-[#FBF9F6] p-8 rounded-xl border border-[#EAE3D2]/60 hover:shadow-md hover:border-[#C85A32]/40 transition-all group w-full">
              <div className="w-12 h-12 bg-[#1E3F2E]/10 rounded-full flex items-center justify-center text-[#1E3F2E] mb-6 group-hover:bg-[#1E3F2E] group-hover:text-white transition-all">
                <Palmtree size={22} />
              </div>
              <h3 className="text-xl font-bold font-display text-[#1E2229] mb-3">Explorer&apos;s Bulletins</h3>
              <p className="text-sm text-[#1E2229]/75 leading-relaxed">
                Locate local events, music, art festivals, and regional gatherings tailored directly to your calendar dates and personal interests.
              </p>
            </button>
          </div>
        </div>
      </section>

      {/* Destinations Section - Polaroid Scrapbook Grid */}
      <section id="destinations" className="relative z-10 bg-[#FBF9F6] py-24 px-6 md:px-16 lg:px-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <span className="text-xs uppercase tracking-widest text-[#C85A32] font-extrabold">Travel Inspiration</span>
            <h2 className="text-3xl md:text-5xl font-bold font-display text-[#1E3F2E] mt-3">From the Travel Log</h2>
            <p className="mt-4 text-[#1E2229]/70 font-sans max-w-xl mx-auto">
              Visual snapshots and design stories compiled by our traveling community
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* Polaroid 1 */}
            <div className="bg-white p-5 pb-9 border border-[#EAE3D2] shadow-lg hover:shadow-xl transition-all transform hover:-rotate-2 hover:-translate-y-2 duration-300 group rotate-1">
              <div className="relative h-64 w-full overflow-hidden bg-gradient-to-br from-[#1E3F2E] via-[#4A6741] to-[#8B9A6B] group-hover:scale-105 transition-transform duration-500" aria-label="Kyoto, Japan" />
              <div className="mt-5 text-left">
                <span className="text-[10px] font-bold tracking-widest text-[#C85A32] font-mono block mb-1">MAY 2026 · JOURNAL ENTRY</span>
                <h3 className="text-2xl font-bold font-display text-[#1E2229]">Kyoto, Japan</h3>
                <p className="text-sm text-[#1E2229]/70 mt-2 leading-relaxed">
                  Tranquil temples, wooden teahouses, and morning coffee by the Kamogawa River.
                </p>
                <div className="mt-5 pt-4 border-t border-[#EAE3D2]/50 flex justify-between items-center">
                  <span className="text-xs font-mono text-[#1E3F2E]">4.9 ★ Kyoto Prefecture</span>
                  <button 
                    onClick={() => router.push('/features/cultural-intelligence?location=Kyoto')} 
                    className="text-[#C85A32] hover:text-[#A54422] text-sm font-bold flex items-center gap-1 transition-colors"
                  >
                    Read log →
                  </button>
                </div>
              </div>
            </div>
            
            {/* Polaroid 2 */}
            <div className="bg-white p-5 pb-9 border border-[#EAE3D2] shadow-lg hover:shadow-xl transition-all transform hover:rotate-2 hover:-translate-y-2 duration-300 group -rotate-2">
              <div className="relative h-64 w-full overflow-hidden bg-gradient-to-br from-[#4A90A4] via-[#87CEEB] to-[#F5F0E8] group-hover:scale-105 transition-transform duration-500" aria-label="Santorini, Greece" />
              <div className="mt-5 text-left">
                <span className="text-[10px] font-bold tracking-widest text-[#C85A32] font-mono block mb-1">JUN 2026 · JOURNAL ENTRY</span>
                <h3 className="text-2xl font-bold font-display text-[#1E2229]">Santorini, Greece</h3>
                <p className="text-sm text-[#1E2229]/70 mt-2 leading-relaxed">
                  Steep volcanic cliffs, whitewashed alleys, and sunset views over the Aegean Sea.
                </p>
                <div className="mt-5 pt-4 border-t border-[#EAE3D2]/50 flex justify-between items-center">
                  <span className="text-xs font-mono text-[#1E3F2E]">4.8 ★ Cyclades Islands</span>
                  <button 
                    onClick={() => router.push('/features/cultural-intelligence?location=Santorini')}
                    className="text-[#C85A32] hover:text-[#A54422] text-sm font-bold flex items-center gap-1 transition-colors"
                  >
                    Read log →
                  </button>
                </div>
              </div>
            </div>
            
            {/* Polaroid 3 */}
            <div className="bg-white p-5 pb-9 border border-[#EAE3D2] shadow-lg hover:shadow-xl transition-all transform hover:-rotate-1 hover:-translate-y-2 duration-300 group rotate-2">
              <div className="relative h-64 w-full overflow-hidden bg-gradient-to-br from-[#2D6A4F] via-[#52B788] to-[#D8F3DC] group-hover:scale-105 transition-transform duration-500" aria-label="Bali, Indonesia" />
              <div className="mt-5 text-left">
                <span className="text-[10px] font-bold tracking-widest text-[#C85A32] font-mono block mb-1">AUG 2026 · JOURNAL ENTRY</span>
                <h3 className="text-2xl font-bold font-display text-[#1E2229]">Bali, Indonesia</h3>
                <p className="text-sm text-[#1E2229]/70 mt-2 leading-relaxed">
                  Terraced emerald rice fields, ocean mist, and temple ceremonies in Ubud.
                </p>
                <div className="mt-5 pt-4 border-t border-[#EAE3D2]/50 flex justify-between items-center">
                  <span className="text-xs font-mono text-[#1E3F2E]">4.7 ★ Lesser Sundas</span>
                  <button 
                    onClick={() => router.push('/features/cultural-intelligence?location=Bali')}
                    className="text-[#C85A32] hover:text-[#A54422] text-sm font-bold flex items-center gap-1 transition-colors"
                  >
                    Read log →
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-center mt-16">
            <button 
              onClick={() => router.push('/features/cultural-intelligence')}
              className="px-6 py-3 border border-[#EAE3D2] bg-white rounded-lg text-sm font-bold hover:bg-[#FBF9F6] transition-all inline-flex items-center gap-2 text-[#1E2229] shadow-sm"
            >
              Browse All Memoirs
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </section>

      {/* Editorial Footer */}
      <footer className="relative z-10 bg-white border-t border-[#EAE3D2] px-6 md:px-16 lg:px-24 py-16 text-[#1E2229]/80">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex flex-col items-center md:items-start">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🧭</span>
              <p className="text-2xl font-bold font-display text-[#1E3F2E] tracking-wider">AINOMAD</p>
            </div>
            <p className="text-xs text-[#1E2229]/65 max-w-xs text-center md:text-left">
              An organic digital logbook for curious wanderers and conscious travelers. Tracing journeys, stories, and readiness.
            </p>
          </div>
          
          <div className="flex gap-16 text-center md:text-left">
            <div>
              <h4 className="font-display font-bold text-sm text-[#1E2229] mb-3">Navigation</h4>
              <ul className="text-xs space-y-2">
                <li><a href="/features" className="hover:text-[#C85A32] transition-colors">Features</a></li>
                <li><a href="/features" className="hover:text-[#C85A32] transition-colors">All Features</a></li>
                <li><a href="/readiness" className="hover:text-[#C85A32] transition-colors">Trip Readiness</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-display font-bold text-sm text-[#1E2229] mb-3">Philosophy</h4>
              <ul className="text-xs space-y-2">
                <li><a href="/about" className="hover:text-[#C85A32] transition-colors">About Us</a></li>
                <li><a href="/contact" className="hover:text-[#C85A32] transition-colors">Contact Log</a></li>
                <li><a href="#" className="hover:text-[#C85A32] transition-colors">Privacy Note</a></li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="max-w-6xl mx-auto border-t border-[#EAE3D2]/50 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-[#1E2229]/50">
            © {new Date().getFullYear()} Ainomad. Crafted for intentional exploration.
          </p>
          <div className="flex gap-6 text-xs text-[#1E2229]/60">
            <a href="#" className="hover:text-[#C85A32] transition-colors">Notebook</a>
            <a href="#" className="hover:text-[#C85A32] transition-colors">Postcards</a>
            <a href="#" className="hover:text-[#C85A32] transition-colors">Telegrams</a>
          </div>
        </div>
      </footer>
    </div>
  );
}