# Event Relevance & Personalization ML Model Methodology

## Overview
The **Cultural Intelligence / Local Culture & Events** recommendation system utilizes a trained **RandomForestRegressor** pipeline to evaluate and rank candidate local events against a traveler's specific destination, travel dates, and personal interests.

Rather than relying on static or outdated festival lists, the architecture uses a **Live Event Discovery Pipeline**:
1. Live Web Search (Tavily Search API) targeted at municipal tourism boards, venue calendars, and local listings.
2. Structured Information Extraction & Strict Date/Locality Filtering.
3. Event Deduplication across sources.
4. **Machine Learning Relevance & Personalization Ranking** via `event_relevance_model.pkl`.
5. Natural Language explanation of top recommendations via Groq LLM (strictly grounded in verified event facts).

---

## Dataset Description (Derived Training Dataset)
- **Dataset Path**: `sb/data/event_relevance_dataset.csv`
- **Total Records**: 32,000 pairing instances.
- **Dataset Nature**: **Derived / Domain-Engineered Training Dataset** based on destination locality, temporal trip overlap, and multi-interest traveler taxonomy.
- **Missing / Null Values**: 0
- **Duplicate Records**: 0

> [!NOTE]
> This training dataset is explicitly documented as a **derived training dataset** engineered to capture domain rules of trip temporal overlap, geographic proximity, and personal interest alignment. It is NOT presented as a real-world user log dataset.

---

## Input Features & Feature Engineering

| Feature Name | Type | Valid Range | Description |
|---|---|---|---|
| `distance_from_destination` | Float | 0.5 – 120.0 km | Distance from destination city center. Events within 15 km have 0 penalty. |
| `date_overlap` | Float | 0.0 – 1.0 | Temporal alignment: 1.0 (completely inside trip), 0.8 (overlapping), 0.4 (adjacent), 0.05 (outside). |
| `days_until_event` | Integer | 1 – 150 days | Lead time from today's reference date to event start date. |
| `interest_match` | Float | 0.0 – 1.0 | Direct keyword / semantic overlap with traveler's selected interest tags. |
| `event_category` | Categorical | 8 categories | `anime`, `tech`, `food`, `culture`, `art`, `music`, `sports`, `community`. |
| `event_popularity` | Integer | 1 – 10 | Authority / attendance score of the event. |
| `event_source_reliability` | Float | 0.65 – 1.0 | Source confidence (1.0 = official tourism/venue, 0.85 = verified board, 0.65 = blog). |
| `event_locality` | Float | 0.0 – 1.0 | 1.0 = In-city, 0.5 = Surrounding metro area, 0.0 = Different city/region. |
| `price_affordability` | Float | 0.4 – 1.0 | Affordability factor: 1.0 (free admission), 0.7 (standard ticket), 0.4 (high-cost). |
| `user_interest_similarity`| Float | 0.0 – 1.0 | Normalized multi-token Jaccard similarity across interest categories. |
| `event_duration` | Integer | 1 – 14 days | Length of event in days. |

---

## Target Variable
- **Target Name**: `event_relevance_score`
- **Type**: Continuous float (0.0 to 100.0)
- **Interpretation**:
  - `80 – 100`: **Top Match** — In-city event occurring during the traveler's dates aligning strongly with their selected interests.
  - `60 – 79`: **Recommended** — Strong local or adjacent event with moderate interest match.
  - `40 – 59`: **Moderate Match** — Marginal temporal or topical alignment.
  - `< 40`: **Low Relevance / Filtered** — Event located in a different city or occurring outside travel dates.

---

## Model Architecture & Evaluation
- **Pipeline Structure**:
  - `ColumnTransformer`:
    - Categorical (`event_category`): `OneHotEncoder(handle_unknown="ignore")`
    - Numerical: `StandardScaler()`
  - Regressor: `RandomForestRegressor(n_estimators=100, max_depth=15, min_samples_split=4, random_state=42)`
- **Train / Test Split**: 80% train (25,600 samples) / 20% test (6,400 samples).
- **Held-Out Test Set Metrics**:
  - **Mean Absolute Error (MAE)**: `1.162` points
  - **Root Mean Squared Error (RMSE)**: `1.507` points
  - **R² Score**: `0.9961` (99.61% variance explained)
- **Serialization Artifact**: `sb/models/event_relevance_model.pkl`
