import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

export default function FeatureHubCard({ title, description, href, icon: Icon, color = '#1E3F2E' }) {
  return (
    <Link
      href={href}
      className="bg-white p-8 rounded-xl border border-[#EAE3D2] hover:border-[#C85A32] shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between group"
    >
      <div>
        <div
          className="mb-6 w-14 h-14 rounded-xl bg-[#FBF9F6] flex items-center justify-center border border-[#EAE3D2]/40 group-hover:scale-105 transition-all"
          style={{ color }}
        >
          <Icon className="h-10 w-10" style={{ color }} />
        </div>
        <h3 className="text-2xl font-bold font-display mb-3 text-[#1E2229]">{title}</h3>
        <p className="text-sm text-[#1E2229]/75 leading-relaxed font-sans">{description}</p>
      </div>
      <div className="mt-8 flex items-center gap-1 text-xs font-bold text-[#C85A32] group-hover:text-[#A54422] font-mono">
        OPEN UTILITY <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
      </div>
    </Link>
  );
}
