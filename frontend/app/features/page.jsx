import { FEATURE_ITEMS } from '@/lib/features';
import FeatureHubCard from '@/components/FeatureHubCard';

export default function FeaturesSection() {
  return (
    <section className="py-24 bg-[#FBF9F6] min-h-screen">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-16 pt-12">
          <span className="text-xs uppercase tracking-widest text-[#C85A32] font-extrabold">
            The Wanderer&apos;s Toolkit
          </span>
          <h2 className="text-4xl font-bold font-display text-[#1E3F2E] mt-3 mb-4">Features</h2>
          <p className="text-md text-[#1E2229]/70 max-w-xl mx-auto font-sans leading-relaxed">
            Every Ainomad utility lives here — readiness, planning, culture, budget, journals, and
            community. Alfred, your chat assistant, is available from the compass on any page.
          </p>
          <div className="h-0.5 w-16 bg-[#EAE3D2] mx-auto mt-6" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
          {FEATURE_ITEMS.map((feature) => (
            <FeatureHubCard
              key={feature.slug}
              title={feature.title}
              description={feature.description}
              href={feature.href}
              icon={feature.icon}
              color={feature.color}
            />
          ))}
        </div>

        <p className="text-center text-xs text-[#1E2229]/50 mt-12 font-mono max-w-lg mx-auto">
          Need quick guidance? Open Alfred via the floating compass — no separate voice app required.
        </p>
      </div>
    </section>
  );
}
