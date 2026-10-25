# AI-Nomad

Travel planning platform with itinerary generation, festival search, trip readiness dashboard, community scrapbook, and voice assistant.

## Quick start

```bash
# From project root (requires Python 3.13 venv at .venv/)
./start_services.sh
```

Open **http://localhost:3000**

Stop everything:

```bash
./stop_services.sh
```

## Services

| Service    | Port | Frontend route   |
|-----------|------|------------------|
| Frontend  | 3000 | All pages        |
| Festivals | 5004 | `/search`        |
| Itinerary | 5005 | `/iternary`      |
| Chatbot   | 5006 | Floating widget + `/chatbot` |
| Readiness | 5007 | Features → Trip Readiness (`/readiness`) |
| Journal   | 5008 | Features → Collaborative Journal (`/journal`) |
| Budget Intelligence | 5009 | Features → Smart Overspending Risk Engine (`/features/smart-budget`) |
| Emergency Companion | 5010 | Features → AI Emergency Travel Companion (`/features/emergency-companion`) |
| Contextual Recommendations | 5011 | Features → Live Context Recommendations (`/features/contextual-recommendations`) |

Optional API keys in `.env` at project root (see `.env.example`):

| Key | Service | Purpose |
|-----|---------|---------|
| `WEATHER_API_KEY` | OpenWeatherMap | Live weather + city-local time for recommendations |
| `GOOGLE_PLACES_API_KEY` | Google Places | Real nearby venues (falls back to OpenStreetMap) |
| `GROQ_API_KEY` | Groq | AI contextual explanations (chatbot + recommendations) |
| `GEMINI_API_KEY` | Google Gemini | AI explanations (used before Groq when set) |

Without keys, recommendations still work using OpenStreetMap places, timezone-based local time, and template explanations.

## Navigation

Top navbar: **Features** (dropdown), **About**, **Contact**, **Sign In**.

All tools live under **Features** — no standalone Readiness or Explore links.

**Alfred** (chat assistant) opens from the floating compass on every page.

## Feature routes

| Feature | Route |
|---------|--------|
| Trip Readiness Dashboard | `/readiness` |
| Itinerary Planner | `/iternary` |
| Smart Packing Assistant | `/features/packing` |
| Cultural Intelligence | `/features/cultural-intelligence` |
| Budget Planner | `/features/budget` |
| Smart Overspending Risk Engine | `/features/smart-budget` |
| AI Emergency Travel Companion | `/features/emergency-companion` |
| Live Context Recommendations | `/features/contextual-recommendations` |
| Collaborative Travel Journal | `/journal` (sign in required) |
| Community / Travel Feed | `/livecommu` |

Redirects: `/search` → Cultural Intelligence · `/chatbot` → home (use Alfred widget)

## Pages

- `/` — Home
- `/features` — Feature hub
- `/about`, `/contact` — Info pages

## Production build

```bash
npm run build --prefix frontend
npm run start --prefix frontend   # still needs Flask backends running
```
