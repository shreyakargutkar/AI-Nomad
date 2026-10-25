# Feature 2: AI Emergency Travel Companion

## Product vision

**“A travel assistant for when things go wrong.”** Auto-activates when the traveler reaches a destination—hyper-local essentials, scam intelligence, one-tap phrases, and an SOS assistant that turns panic into a checklist.

**Route:** `/features/emergency-companion`  
**APIs:**
- `POST /api/emergency/detect` → country profile + essentials
- `POST /api/emergency/sos` → natural-language crisis workflows  
**Backend:** Flask `5010`

---

## Data inputs

| Input | Endpoint | Purpose |
|-------|----------|---------|
| `destination` | detect, sos | Country auto-detection |
| `query` | sos | Natural language crisis description |

Future: GPS coordinates, user nationality for embassy lookup, live hospital APIs.

---

## Core logic

### 1. Auto-detect country
`destination` string → `emergency_profiles.json` (Japan, France, Thailand, Turkey).

On page load / **Activate**, return full profile with `auto_activated: true`.

### 2. Emergency Essentials Card
Structured payload:
- Nearest hospital (name, distance, English note)
- Nearby pharmacy
- Safe taxi apps + transport guidance
- Emergency numbers (police, ambulance, tourist hotline)
- Embassy example (demo: Embassy of India)

### 3. Scam warnings
Country-specific array with `severity` (Japan: last train, cash; Paris: pickpockets; Thailand: tuk-tuk; Turkey: FX scams).

### 4. One-tap translations (4 categories)

| Category | Example (Japan) |
|----------|-----------------|
| Medical | 医者に診てもらいたいです |
| Food | 私はベジタリアンです |
| Transport | この住所まで連れて行ってください |
| Emergency | 警察を呼んでください |

Tap → copy phrase to clipboard (TTS hook-ready).

### 5. SOS Smart Assistant

Keyword router on `query`:
- `lost_passport` → embassy + police report + emergency docs workflow
- `missed_train` → next train + hotel + taxi guidance
- `medical_emergency` → 119 + hospital + insurance steps
- Fallback → general calm guidance + hotlines

Each response includes:
- **Reassurance** (“Stay calm…”)
- **Numbered steps**
- **Local contacts**

Optional: plug `GROQ_API_KEY` for LLM expansion (structure preserved).

---

## UI components

| Component | Role |
|-----------|------|
| Dark crisis theme | Visual distinction from planning features |
| Destination + Activate | Manual override / demo country switch |
| Auto-detected banner | Flag + “Companion active” |
| Essentials card | Hospital, pharmacy, taxis, tel: links |
| Scam warning stack | Severity-colored cards |
| Translation grid 2×2 | Copy-on-tap phrase cards |
| SOS input + chips | Quick prompts + NL query |
| SOS result panel | Reassurance + steps + contacts |

---

## Example scenario (Tokyo)

**User arrives → auto-detect Japan**

Essentials:
- St. Luke’s International Hospital · 2.4 km
- Matsumoto Kiyoshi · 450 m
- Apps: JapanTaxi, GO Taxi

Scams:
- Last train timing trap (¥5,000+ taxi risk)
- Cash dependency at shrines/ramen shops

**SOS query:** “I lost my passport at Shinjuku”

Response:
- Reassurance + 4 steps (police report → embassy → EC → airline)
- Contacts: Police 110, Tourist hotline 050-3816-2787

---

## Key differentiators

| Generic travel safety pages | AI Emergency Companion |
|----------------------------|-------------------------|
| Static country PDFs | Auto-activate on destination |
| Long articles | Scannable cards + one-tap actions |
| No local scams | **Hyper-local** scam warnings |
| Google Translate separately | 4 crisis categories pre-loaded |
| Search forums for help | **SOS workflows** with steps + reassurance |
| Feels like insurance docs | Feels like **AI protecting you** |

---

## Demo script (60 seconds)

1. Open **Features → AI Emergency Travel Companion**
2. Show **Japan auto-detected** banner
3. Tap **Emergency** translation → copied phrase
4. Highlight **last train** scam warning
5. Tap chip **“I lost my passport”**
6. Read **Stay calm** + step 1–4 workflow

---

## Files

- Spec: `features/emergency-companion/SPEC.md`
- Backend: `backend/services/emergency/app.py`
- Data: `backend/data/emergency_profiles.json`
- Frontend: `frontend/app/features/emergency-companion/page.jsx`
- Proxies: `frontend/app/api/emergency/detect/route.js`, `.../sos/route.js`
