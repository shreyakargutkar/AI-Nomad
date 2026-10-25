'use client';

import { useState } from 'react';
import { Compass } from 'lucide-react';

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-28 px-6">
      <div className="max-w-lg mx-auto">
        <div className="text-center mb-10">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
            <Compass size={10} /> Contact Log
          </span>
          <h1 className="text-4xl font-bold font-display text-[#1E2229]">Get in Touch</h1>
          <p className="text-sm text-[#1E2229]/60 mt-2">Questions, feedback, or collaboration for AI-Nomad</p>
        </div>

        {submitted ? (
          <div className="bg-white border border-[#EAE3D2] rounded-2xl p-8 text-center">
            <p className="text-[#1E3F2E] font-semibold">Message received — thank you!</p>
            <p className="text-sm text-[#1E2229]/60 mt-2">We&apos;ll get back to you soon.</p>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="bg-white border border-[#EAE3D2] rounded-2xl p-8 space-y-4 shadow-sm"
          >
            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-2">Name</label>
              <input
                required
                type="text"
                className="w-full p-3 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-2">Email</label>
              <input
                required
                type="email"
                className="w-full p-3 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-bold font-mono text-[#1E3F2E] uppercase mb-2">Message</label>
              <textarea
                required
                rows={4}
                className="w-full p-3 rounded-lg bg-[#FBF9F6] border border-[#EAE3D2] focus:border-[#C85A32] outline-none text-sm"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-[#C85A32] hover:bg-[#A54422] text-white font-bold py-3 rounded-lg text-sm uppercase tracking-wider"
            >
              Send Message
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
