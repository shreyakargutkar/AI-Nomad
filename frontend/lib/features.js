import {
  ClipboardCheck,
  Map,
  Luggage,
  Globe2,
  Wallet,
  Users,
  MessageCircle,
  TrendingUp,
  ShieldAlert,
  Sparkles,
  Compass,
} from 'lucide-react';

/** All product features — accessed only via Features nav / hub (not top-level nav). */
export const FEATURE_ITEMS = [
  {
    slug: 'trip-readiness',
    title: 'Trip Readiness Dashboard',
    description:
      'Packing lists, booking intel, country requirements, and a readiness score before you fly.',
    href: '/readiness',
    icon: ClipboardCheck,
    color: '#1E3F2E',
  },
  {
    slug: 'itinerary',
    title: 'Itinerary Planner',
    description:
      'Generate structured daily schedules, flights, hotels, and visa notes for your journey.',
    href: '/iternary',
    icon: Map,
    color: '#C85A32',
  },
  {
    slug: 'packing',
    title: 'Smart Packing Assistant',
    description:
      'Destination-aware packing lists tailored to weather, trip length, and activities.',
    href: '/features/packing',
    icon: Luggage,
    color: '#1E3F2E',
  },
  {
    slug: 'cultural-intelligence',
    title: 'Cultural Intelligence',
    description:
      'Discover local festivals, cultural gatherings, and events matched to your destination.',
    href: '/features/cultural-intelligence',
    icon: Globe2,
    color: '#2D6A8F',
  },
  {
    slug: 'budget',
    title: 'Budget Planner',
    description:
      'Estimate trip costs across flights, stays, food, and activities before you book.',
    href: '/features/budget',
    icon: Wallet,
    color: '#C85A32',
  },
  {
    slug: 'smart-budget',
    title: 'Smart Overspending Risk Engine',
    description:
      'Trip Budget Health Score, destination overspend alerts, hidden costs, and smart fixes with day-by-day burn forecast.',
    href: '/features/smart-budget',
    icon: TrendingUp,
    color: '#A54422',
  },
  {
    slug: 'emergency-companion',
    title: 'AI Emergency Travel Companion',
    description:
      'Auto-activated crisis dashboard — hospitals, scam warnings, instant translations, and SOS step-by-step guidance.',
    href: '/features/emergency-companion',
    icon: ShieldAlert,
    color: '#5B1E1E',
  },
  {
    slug: 'contextual-recommendations',
    title: 'Live Context Recommendations',
    description:
      'Moment-aware suggestions that shift with time, weather, location, and activity — not static Top 10 lists.',
    href: '/features/contextual-recommendations',
    icon: Sparkles,
    color: '#2D6A8F',
  },
  {
    slug: 'journal',
    title: 'Collaborative Travel Journal',
    description:
      'Co-author trip timelines with travel partners — entries, photos, and shared history.',
    href: '/journal',
    icon: Users,
    color: '#1E3F2E',
  },
  {
    slug: 'community',
    title: 'Community / Travel Feed',
    description:
      'Browse postcards, stories, and tips from explorers on the road.',
    href: '/livecommu',
    icon: MessageCircle,
    color: '#C85A32',
  },
  {
    slug: 'smart-day-planner',
    title: 'Smart Day Planner',
    description:
      'Plan daily routes with optimized pathing, set anchor events, and simulate live travel disruptions on a map.',
    href: '/features/smart-day-planner',
    icon: Compass,
    color: '#2D6A8F',
  },
];

