# AI-Nomad Travel Readiness ML Prediction System

This document outlines the architecture, training dataset derivation, domain scoring methodology, evaluation metrics, and explainability mechanisms for the **AI-Nomad Travel Readiness ML Predictor**.

---

## 1. Overview & Objective

The goal of this system is to upgrade AI-Nomad's travel readiness capability from a purely static, weighted rule formula to an **explainable Machine Learning Regression Pipeline** using `scikit-learn`.

- **Target Variable**: `preparedness_score` (Continuous float/integer normalized to `0 – 100`)
- **Model Architecture**: `RandomForestRegressor` embedded in a `ColumnTransformer` + `Pipeline`
- **Trained Artifact**: `sb/models/readiness_model.pkl`
- **Training Dataset**: `sb/data/readiness_dataset.csv` (35,000 unique records)
- **Synthetic/Derived Disclosure**: As specified in project requirements, this dataset is a **derived/synthetic domain training dataset** grounded in AI-Nomad's established readiness methodology and international travel compliance rules.

---

## 2. Feature Schema

The model evaluates **15 distinct travel preparation features** spanning trip parameters, logistics, legal documentation, safety, and packing readiness:

| Feature Name | Type | Allowed Values / Representation | Description |
|---|---|---|---|
| `destination_country` | Categorical | 20 global destinations (Japan, France, Greece, Thailand, etc.) | Target travel country |
| `trip_duration_days` | Numeric | Integer $\ge 1$ (typical 2–60 days) | Total trip length in calendar days |
| `season` | Categorical | `Spring`, `Summer`, `Autumn`, `Winter` | Season of departure |
| `previous_trips` | Numeric | Integer $\ge 0$ (typical 0–28) | Traveler's prior international trips (experience) |
| `flight_booked` | Binary | `0` or `1` | Whether departure/return flights are confirmed |
| `hotel_booked` | Binary | `0` or `1` | Whether lodging/accommodations are reserved |
| `passport_valid` | Binary | `0` or `1` | Passport valid for 6+ months beyond return date |
| `visa_required` | Binary | `0` or `1` | Whether destination mandates an entry visa / eVisa |
| `visa_ready` | Binary | `0` or `1` | Entry visa / permit obtained and confirmed |
| `documents_completed` | Binary | `0` or `1` | Boarding passes, ID copies, itinerary offline |
| `travel_insurance` | Binary | `0` or `1` | Active travel medical & cancellation coverage |
| `emergency_prepared` | Binary | `0` or `1` | Embassy info, local SOS numbers, offline maps |
| `country_preparation` | Binary | `0` or `1` | Destination prep (eSIM, transit card, currency) |
| `packing_completed` | Binary | `0` or `1` | Weather-aligned clothing & essentials packed |
| `weather_risk` | Categorical | `LOW`, `MEDIUM`, `HIGH` | Extreme weather hazard (storm, heatwave, blizzard) |
| **`preparedness_score`** | **Target** | **`0.0 – 100.0`** | **Overall traveler readiness score** |

---

## 3. Domain Scoring Methodology

The synthetic target labels in `readiness_dataset.csv` are derived through a multi-tier domain scoring model reflecting the physical realities of international travel:

### A. Point Breakdown (100 Points Total)

1. **Documentation & Border Clearance (35 Points)**
   - `passport_valid`: **15 pts** (Fundamental legal pre-requisite)
   - `visa_compliance`: **12 pts**
     - If `visa_required == 0`: **12 pts** (Exempt)
     - If `visa_required == 1`: **12 pts** if `visa_ready == 1`, else **0 pts**
   - `documents_completed`: **8 pts** (Health forms, vouchers, driving licenses)

2. **Booking Readiness (20 Points)**
   - `flight_booked`: **12 pts** (Confirmed transit)
   - `hotel_booked`: **8 pts** (Secured accommodation)

3. **Packing & Climate Adaptation (20 Points)**
   - `packing_completed`: **14 pts** (Essential gear and apparel)
   - `weather_preparedness`: **6 pts**
     - `weather_risk == "LOW"`: **6 pts**
     - `weather_risk == "MEDIUM"`: **4 pts** if packed, else **1 pt**
     - `weather_risk == "HIGH"`: **6 pts** if packed, else **0 pts**

4. **Safety & Crisis Preparation (15 Points)**
   - `travel_insurance`: **8 pts** (Medical emergency and delay buffer)
   - `emergency_prepared`: **7 pts** (Local emergency numbers, offline navigation)

5. **Destination Logistics & Experience (10 Points)**
   - `country_preparation`: **8 pts** (Local SIM/eSIM, transit card like Suica, currency)
   - `experience_factor`: **2 pts** ($\min(2.0, \text{previous\_trips} \times 0.5)$)

---

### B. Logical Dependencies & Critical Hard Caps

In real-world travel, certain gaps are catastrophic regardless of how well other areas are prepared. The methodology implements non-linear constraints:

1. **Passport Invalidation Hard Cap**:
   - If `passport_valid == 0`, a traveler cannot board international flights.
   - **Constraint**: $\text{score} = \min(\text{score}, 38.0)$
2. **Missing Visa Hard Cap**:
   - If `visa_required == 1` and `visa_ready == 0`, the traveler will be rejected at border control.
   - **Constraint**: $\text{score} = \min(\text{score}, 45.0)$
   - *Note*: If `visa_required == 0`, `visa_ready` does not penalize the traveler.
3. **Compound Critical Blocker**:
   - If both `passport_valid == 0` and `visa_ready == 0` (when required):
   - **Constraint**: $\text{score} = \min(\text{score}, 25.0)$
4. **Severe Unmitigated Weather Exposure**:
   - If `weather_risk == "HIGH"` and `packing_completed == 0` and `emergency_prepared == 0`:
   - Penalty: $-4.0\text{ pts}$
5. **Completely Unbooked Transit & Stay**:
   - If `flight_booked == 0` and `hotel_booked == 0`:
   - Penalty: $-5.0\text{ pts}$
6. **Extended Duration Vulnerability**:
   - If `trip_duration_days >= 21` and `travel_insurance == 0`:
   - Penalty: $-3.0\text{ pts}$
7. **Controlled Stochastic Variance (Domain Noise)**:
   - Subtle Gaussian noise ($\mu = 0, \sigma = 1.2$) added to reflect unmeasured personal factors, rounded to 1 decimal place and strictly clamped within $[0.0, 100.0]$.

---

## 4. Model Training & Evaluation Metrics

The model was trained on **28,000 samples** and evaluated on a **7,000 held-out test set** (80/20 train/test split).

### Evaluation Results (Held-Out Test Set)

| Metric | Result | Interpretation |
|---|---|---|
| **MAE (Mean Absolute Error)** | **0.997 points** | On average, predictions deviate by less than 1 point on a 100-point scale. |
| **RMSE (Root Mean Squared Error)** | **1.307 points** | Penalizes larger outliers; shows extremely tight residuals. |
| **R² Score** | **0.9966 (99.66%)** | The model explains 99.66% of the variance across test cases. |

### Top 10 Influential Features (Random Forest Importance)

1. `packing_completed` (33.30%)
2. `visa_ready` (22.56%)
3. `passport_valid` (17.05%)
4. `flight_booked` (6.85%)
5. `travel_insurance` (6.18%)
6. `country_preparation` (4.44%)
7. `documents_completed` (3.28%)
8. `hotel_booked` (2.69%)
9. `emergency_prepared` (2.67%)
10. `weather_risk_LOW` (0.48%)

---

## 5. Inference & Explainability

The prediction interface is exposed via:
```python
from predict_readiness import predict_readiness

result = predict_readiness({
    "destination_country": "Japan",
    "trip_duration_days": 8,
    "season": "Spring",
    "previous_trips": 4,
    "flight_booked": 1,
    "hotel_booked": 1,
    "passport_valid": 1,
    "visa_required": 1,
    "visa_ready": 1,
    "documents_completed": 1,
    "travel_insurance": 1,
    "emergency_prepared": 1,
    "country_preparation": 1,
    "packing_completed": 0,
    "weather_risk": "LOW"
})
```

### Response Format:
```json
{
  "preparedness_score": 86,
  "readiness_band": "High Readiness",
  "top_factors": [
    "Passport is verified valid",
    "Visa is approved and ready",
    "Flight is booked and confirmed",
    "Packing is incomplete"
  ]
}
```

The explainability engine breaks down the prediction into:
1. **Strengths (Positive Drivers)**: Completed critical steps boosting the score.
2. **Bottlenecks (Risk Factors)**: Incomplete or hazardous gaps dragging down the score (e.g. missing visa, invalid passport, high weather risk with uncompleted packing).

---

## 6. Comparison: Rule-Based vs ML Regression

| Dimension | Old Rule-Based System (`readiness/app.py`) | New ML Readiness Predictor (`predict_readiness.py`) |
|---|---|---|
| **Mechanism** | Static linear weighting of 4 sub-scores | Scikit-Learn `RandomForestRegressor` Pipeline |
| **Non-Linear Interactions** | Limited (if/else thresholding) | Automatically captures complex combinations (e.g. high weather risk $\times$ incomplete packing) |
| **Explainability** | Hardcoded category percentages | Dynamic feature-importance factor ranking & gap analysis |
| **Adaptability** | Formula must be rewritten for new variables | Pipeline easily retrained on expanded datasets |
| **Generalization** | Brittle to missing or partial inputs | Trained with robust imputations & out-of-vocabulary handling via `OneHotEncoder(handle_unknown='ignore')` |
