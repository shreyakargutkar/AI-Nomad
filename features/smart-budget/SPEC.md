# Feature 1: Smart Overspending Risk Engine

## Product vision

An intelligent budget predictor that forecasts **spending risk** for a traveler’s specific profile—not a spreadsheet that only sums line items. The emotional payoff: *“I’ll run out of money on Day 5 unless I change something today.”*

**Route:** `/features/smart-budget`  
**API:** `POST /api/budget-intelligence` → Flask `5009`

---

## Data inputs

| Input | Type | Required | Purpose |
|-------|------|----------|---------|
| `destination` | string | Yes | Resolve country profile (Japan, France, Thailand, Turkey, …) |
| `total_budget` | number (INR) | Yes | Budget envelope for health score |
| `travel_style` | `budget` \| `mid-range` \| `luxury` | Yes | Daily base rates multiplier |
| `itinerary` | free text | Recommended | Activity matching, alert triggers, activity surcharges |
| `shopping_preferences` | string | Optional | Shopping allowance tier |
| `food_preferences` | string | Optional | Food cost multiplier (street vs fine dining, dietary) |
| `start_date` / `end_date` | ISO date | Optional | Trip length for burn forecast |
| `days` | number | Optional | Override duration |

---

## Core logic / algorithm

### 1. Destination resolution
Map city/country strings → `budget_profiles.json` key (e.g. Tokyo → `japan`).

### 2. Projected spend model

```
projected_total =
  (daily_base[style] × food_multiplier × days)
  + itinerary_activity_costs
  + shopping_allowance(style, prefs, days)
  + sum(hidden_costs)
```

- **Itinerary activity costs:** Keyword match against `activity_costs_inr` (Disney combo, JR Pass, teamLab, etc.) + attraction DB cross-match.
- **Food multiplier:** 0.88 (street/budget) → 1.35 (fine dining).
- **Shopping allowance:** Style base × preference modifiers (luxury +80%, minimal −60%).

### 3. Trip Budget Health Score (0–100)

Weighted penalties:
- Projected/budget ratio (>105%, >115%)
- Hidden costs as % of budget (>15%)
- Count/severity of overspending alerts

### 4. Destination-specific alerts

Template engine in `budget_profiles.json`: triggers on itinerary/neighborhood keywords → human-readable messages with `potential_overage_inr`.

### 5. Smart fixes (3+)

Condition-matched fixes from profile DB, sorted by `savings_inr`, each with implementation steps.

### 6. Day-by-day burn forecast

Per-day spend with variance (arrival/departure/shopping day bump). Track cumulative spend; set `budget_exhaust_day` when `remaining_inr ≤ 0`.

---

## UI components

| Component | Role |
|-----------|------|
| Input form | Destination, budget, style, dates, itinerary, prefs |
| Health score ring | 0–100 with color bands (green/amber/red) |
| Projection bar | Budget vs projected with over/under copy |
| Alert cards | Severity-styled overspending warnings |
| Hidden costs list | Line items travelers forget |
| Smart fixes panel | Top 3 fixes with savings + steps |
| Burn forecast strip | D1–Dn mini chart with OUT/warning states |

---

## Example output (Tokyo demo)

**Inputs:** ₹1,20,000 budget · Mid-range · 7 days · Shinjuku hotel · Disneyland + DisneySea · outlet Day 3

**Sample response highlights:**
- **Health score:** ~52–68 (high risk from Disney combo)
- **Alert:** “Disneyland + DisneySea combo may exceed budget by ₹14,000”
- **Alert:** “Peak-season cafes in Shinjuku push food costs 25% higher”
- **Hidden costs:** Airport transfer ₹3,200 · Suica ₹1,500 · eSIM ₹2,800 · lockers ₹2,200 · accommodation tax ₹800 · add-ons ₹4,500
- **Smart fixes:** Ueno vs Shinjuku (₹18k) · JR Pass (₹7k) · Outlet Day 3 (₹4k)
- **Burn:** “At this rate, budget exhausts by Day 5”

---

## Key differentiators

| Typical budget apps | Smart Overspending Risk Engine |
|---------------------|--------------------------------|
| Static category totals | Itinerary-aware activity surcharges |
| Generic “food $60/day” | Food + shopping preference multipliers |
| No surprise costs | Explicit hidden-cost line items |
| Post-trip reporting | **Predictive** exhaust day + health score |
| Generic tips | Destination alerts with ₹ overage amounts |
| Vague “save money” | Smart fixes with precise ₹ savings + steps |

---

## Demo script (60 seconds)

1. Open **Features → Smart Overspending Risk Engine**
2. Pre-filled Tokyo + Disney itinerary → **Generate**
3. Point to **Health Score** + “exhausts by Day 5”
4. Scroll **Disney alert** + **hidden costs**
5. Show **Smart fixes** panel (₹18k Ueno save)
6. Pan **day-by-day burn** strip

---

## Files

- Spec: `features/smart-budget/SPEC.md`
- Backend: `backend/services/budget_intelligence/app.py`
- Data: `backend/data/budget_profiles.json`
- Frontend: `frontend/app/features/smart-budget/page.jsx`
- Proxy: `frontend/app/api/budget-intelligence/route.js`
