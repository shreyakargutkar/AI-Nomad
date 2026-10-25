import { Suspense } from 'react';
import CulturalIntelligence from '@/components/CulturalIntelligence';

function Fallback() {
  return (
    <div className="min-h-screen bg-[#FBF9F6] flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function CulturalIntelligencePage() {
  return (
    <Suspense fallback={<Fallback />}>
      <CulturalIntelligence />
    </Suspense>
  );
}
