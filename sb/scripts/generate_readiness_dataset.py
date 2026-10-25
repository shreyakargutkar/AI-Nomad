"""
Dataset Generation Script for Travel Readiness ML Model.

Generates a realistic, domain-grounded training dataset (readiness_dataset.csv)
derived from AI-Nomad's readiness methodology.

Target file: sb/data/readiness_dataset.csv
Target count: ~30,000 unique records
"""

import os
import random
import numpy as np
import pandas as pd

# Set fixed seed for reproducibility
random.seed(42)
np.random.seed(42)

DESTINATIONS = [
    # Core AI-Nomad destinations
    "Japan", "France", "Greece", "Thailand", "Indonesia",
    # Global top travel destinations
    "Italy", "Spain", "Switzerland", "United Kingdom", "Germany",
    "United States", "Canada", "Australia", "Singapore", "United Arab Emirates",
    "Vietnam", "Portugal", "Mexico", "Turkey", "India"
]

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
WEATHER_RISKS = ["LOW", "MEDIUM", "HIGH"]

# Visa requirement likelihood by destination (for general international traveler mix)
# (1 = usually requires visa/e-visa for standard international travelers, 0 = often visa-free or visa-on-arrival)
VISA_PROBABILITY = {
    "Japan": 0.40,
    "France": 0.45,
    "Greece": 0.45,
    "Thailand": 0.35,
    "Indonesia": 0.30,
    "Italy": 0.45,
    "Spain": 0.45,
    "Switzerland": 0.45,
    "United Kingdom": 0.50,
    "Germany": 0.45,
    "United States": 0.65,
    "Canada": 0.55,
    "Australia": 0.60,
    "Singapore": 0.25,
    "United Arab Emirates": 0.35,
    "Vietnam": 0.55,
    "Portugal": 0.45,
    "Mexico": 0.40,
    "Turkey": 0.50,
    "India": 0.60,
}


def calculate_domain_preparedness_score(row, add_noise=True):
    """
    Calculates the domain-based preparedness score (0 - 100) based on AI-Nomad methodology.
    
    Component Breakdown (100 pts max):
    - Passport Validity: 15 pts (Critical legal necessity)
    - Visa Compliance: 12 pts (Exempt if not required; 0 if required & missing)
    - General Documents: 8 pts (IDs, tickets, permits, boarding passes)
    - Flight Booking: 12 pts (Transit locked in)
    - Hotel Booking: 8 pts (Lodging confirmed)
    - Packing Execution: 14 pts (Gear, clothing, essentials prepared)
    - Weather Preparedness: 6 pts (Adapted to local weather conditions)
    - Travel Insurance: 8 pts (Medical & cancellation safety net)
    - Emergency Preparedness: 7 pts (Embassies, local SOS numbers, offline maps)
    - Country Preparation: 8 pts (eSIM, transit IC card, local currency, customs)
    - Experience Factor: 2 pts (Bonus based on previous trips count)
    
    Hard Logical Dependencies & Caps:
    - Missing Passport -> Hard Cap at 38
    - Missing Required Visa -> Hard Cap at 45
    - Both Passport & Visa Missing -> Hard Cap at 25
    - Unbooked Flights & Hotel -> -5 penalty
    - High Weather Risk + Incomplete Packing + No Emergency Prep -> -4 penalty
    - Long Trip (>=21 days) without Insurance -> -3 penalty
    """
    score = 0.0

    # 1. Documentation & Legality (35 pts max)
    score += 15.0 * row["passport_valid"]

    if row["visa_required"] == 0:
        score += 12.0  # Exempt from visa requirements
    else:
        score += 12.0 * row["visa_ready"]

    score += 8.0 * row["documents_completed"]

    # 2. Bookings (20 pts max)
    score += 12.0 * row["flight_booked"]
    score += 8.0 * row["hotel_booked"]

    # 3. Packing & Weather (20 pts max)
    score += 14.0 * row["packing_completed"]

    w_risk = row["weather_risk"]
    packing = row["packing_completed"]
    if w_risk == "LOW":
        score += 6.0
    elif w_risk == "MEDIUM":
        score += 4.0 if packing == 1 else 1.0
    else:  # HIGH
        score += 6.0 if packing == 1 else 0.0

    # 4. Safety & Insurance (15 pts max)
    score += 8.0 * row["travel_insurance"]
    score += 7.0 * row["emergency_prepared"]

    # 5. Destination & Logistics (10 pts max)
    score += 8.0 * row["country_preparation"]
    score += min(2.0, row["previous_trips"] * 0.5)

    # --- Domain Hard Caps & Penalties ---
    # Cannot travel abroad legally with an invalid passport
    if row["passport_valid"] == 0:
        score = min(score, 38.0)

    # Cannot pass immigration if visa is mandatory and not issued
    if row["visa_required"] == 1 and row["visa_ready"] == 0:
        score = min(score, 45.0)

    # Dual critical blocker
    if row["passport_valid"] == 0 and (row["visa_required"] == 1 and row["visa_ready"] == 0):
        score = min(score, 25.0)

    # Severe unmitigated weather hazard
    if w_risk == "HIGH" and packing == 0 and row["emergency_prepared"] == 0:
        score = max(0.0, score - 4.0)

    # Completely unbooked transit and stay
    if row["flight_booked"] == 0 and row["hotel_booked"] == 0:
        score = max(0.0, score - 5.0)

    # Long stay without medical/cancellation buffer
    if row["trip_duration_days"] >= 21 and row["travel_insurance"] == 0:
        score = max(0.0, score - 3.0)

    # Realistic domain noise (subtle variance reflecting unobserved human factors)
    if add_noise:
        noise = random.gauss(0, 1.2)
        score += noise

    # Final clamp to 0.0 - 100.0 range
    return round(float(np.clip(score, 0.0, 100.0)), 1)


def generate_persona_record(persona_type):
    """Generate a realistic traveler profile based on behavioral personas."""
    country = random.choice(DESTINATIONS)
    season = random.choice(SEASONS)

    # Seasonal weather risks
    if season in ["Winter", "Summer"]:
        weather_risk = random.choices(["LOW", "MEDIUM", "HIGH"], weights=[0.40, 0.35, 0.25])[0]
    else:
        weather_risk = random.choices(["LOW", "MEDIUM", "HIGH"], weights=[0.60, 0.30, 0.10])[0]

    # Visa requirement based on destination
    visa_req_prob = VISA_PROBABILITY.get(country, 0.45)
    visa_required = 1 if random.random() < visa_req_prob else 0

    if persona_type == "expert_nomad":
        # Experienced, well-traveled, solid documentation, varied duration
        previous_trips = random.randint(8, 28)
        trip_duration_days = random.choices([7, 14, 21, 30, 45, 60], weights=[0.2, 0.3, 0.2, 0.15, 0.1, 0.05])[0]
        passport_valid = 1 if random.random() < 0.99 else 0
        visa_ready = 1 if visa_required == 0 else (1 if random.random() < 0.94 else 0)
        flight_booked = 1 if random.random() < 0.92 else 0
        hotel_booked = 1 if random.random() < 0.85 else 0
        documents_completed = 1 if random.random() < 0.90 else 0
        travel_insurance = 1 if random.random() < 0.82 else 0
        emergency_prepared = 1 if random.random() < 0.85 else 0
        country_preparation = 1 if random.random() < 0.88 else 0
        packing_completed = 1 if random.random() < 0.88 else 0

    elif persona_type == "organized_planner":
        # Ultra-prepared family or leisure planner
        previous_trips = random.randint(2, 10)
        trip_duration_days = random.randint(5, 18)
        passport_valid = 1 if random.random() < 0.99 else 0
        visa_ready = 1 if visa_required == 0 else (1 if random.random() < 0.96 else 0)
        flight_booked = 1 if random.random() < 0.98 else 0
        hotel_booked = 1 if random.random() < 0.96 else 0
        documents_completed = 1 if random.random() < 0.95 else 0
        travel_insurance = 1 if random.random() < 0.92 else 0
        emergency_prepared = 1 if random.random() < 0.90 else 0
        country_preparation = 1 if random.random() < 0.92 else 0
        packing_completed = 1 if random.random() < 0.90 else 0

    elif persona_type == "last_minute_adventurer":
        # High spontaneous energy, bookings done but paperwork/packing lagging
        previous_trips = random.randint(1, 8)
        trip_duration_days = random.randint(3, 12)
        passport_valid = 1 if random.random() < 0.95 else 0
        visa_ready = 1 if visa_required == 0 else (1 if random.random() < 0.70 else 0)
        flight_booked = 1 if random.random() < 0.88 else 0
        hotel_booked = 1 if random.random() < 0.55 else 0
        documents_completed = 1 if random.random() < 0.55 else 0
        travel_insurance = 1 if random.random() < 0.45 else 0
        emergency_prepared = 1 if random.random() < 0.40 else 0
        country_preparation = 1 if random.random() < 0.50 else 0
        packing_completed = 1 if random.random() < 0.40 else 0

    elif persona_type == "first_time_traveler":
        # Beginner, low experience, some knowledge gaps
        previous_trips = random.choices([0, 1], weights=[0.75, 0.25])[0]
        trip_duration_days = random.randint(4, 14)
        passport_valid = 1 if random.random() < 0.90 else 0
        visa_ready = 1 if visa_required == 0 else (1 if random.random() < 0.65 else 0)
        flight_booked = 1 if random.random() < 0.90 else 0
        hotel_booked = 1 if random.random() < 0.85 else 0
        documents_completed = 1 if random.random() < 0.60 else 0
        travel_insurance = 1 if random.random() < 0.55 else 0
        emergency_prepared = 1 if random.random() < 0.45 else 0
        country_preparation = 1 if random.random() < 0.40 else 0
        packing_completed = 1 if random.random() < 0.60 else 0

    elif persona_type == "business_traveler":
        # Short stay, corporate logistics, high documentation
        previous_trips = random.randint(5, 25)
        trip_duration_days = random.randint(2, 6)
        passport_valid = 1 if random.random() < 0.99 else 0
        visa_ready = 1 if visa_required == 0 else (1 if random.random() < 0.98 else 0)
        flight_booked = 1 if random.random() < 0.98 else 0
        hotel_booked = 1 if random.random() < 0.96 else 0
        documents_completed = 1 if random.random() < 0.95 else 0
        travel_insurance = 1 if random.random() < 0.90 else 0
        emergency_prepared = 1 if random.random() < 0.75 else 0
        country_preparation = 1 if random.random() < 0.85 else 0
        packing_completed = 1 if random.random() < 0.80 else 0

    elif persona_type == "unprepared_procrastinator":
        # Severe gaps across multiple categories
        previous_trips = random.randint(0, 5)
        trip_duration_days = random.randint(3, 15)
        passport_valid = 1 if random.random() < 0.75 else 0
        visa_ready = 1 if visa_required == 0 else (1 if random.random() < 0.30 else 0)
        flight_booked = 1 if random.random() < 0.50 else 0
        hotel_booked = 1 if random.random() < 0.35 else 0
        documents_completed = 1 if random.random() < 0.25 else 0
        travel_insurance = 1 if random.random() < 0.20 else 0
        emergency_prepared = 1 if random.random() < 0.15 else 0
        country_preparation = 1 if random.random() < 0.20 else 0
        packing_completed = 1 if random.random() < 0.20 else 0

    else:
        # Uniform balanced mix across intermediate preparation stages
        previous_trips = random.randint(0, 15)
        trip_duration_days = random.randint(1, 30)
        passport_valid = 1 if random.random() < 0.92 else 0
        visa_ready = 1 if visa_required == 0 else (1 if random.random() < 0.75 else 0)
        flight_booked = 1 if random.random() < 0.80 else 0
        hotel_booked = 1 if random.random() < 0.75 else 0
        documents_completed = 1 if random.random() < 0.70 else 0
        travel_insurance = 1 if random.random() < 0.65 else 0
        emergency_prepared = 1 if random.random() < 0.60 else 0
        country_preparation = 1 if random.random() < 0.65 else 0
        packing_completed = 1 if random.random() < 0.65 else 0

    # Ensure consistency: if visa is not required, visa_ready defaults to 1
    if visa_required == 0:
        visa_ready = 1

    row = {
        "destination_country": country,
        "trip_duration_days": int(trip_duration_days),
        "season": season,
        "previous_trips": int(previous_trips),
        "flight_booked": int(flight_booked),
        "hotel_booked": int(hotel_booked),
        "passport_valid": int(passport_valid),
        "visa_required": int(visa_required),
        "visa_ready": int(visa_ready),
        "documents_completed": int(documents_completed),
        "travel_insurance": int(travel_insurance),
        "emergency_prepared": int(emergency_prepared),
        "country_preparation": int(country_preparation),
        "packing_completed": int(packing_completed),
        "weather_risk": weather_risk,
    }

    row["preparedness_score"] = calculate_domain_preparedness_score(row, add_noise=True)
    return row


def generate_dataset(num_records=35000):
    """Generate target number of unique, realistic records."""
    persona_pool = [
        ("expert_nomad", 0.18),
        ("organized_planner", 0.22),
        ("last_minute_adventurer", 0.16),
        ("first_time_traveler", 0.14),
        ("business_traveler", 0.10),
        ("unprepared_procrastinator", 0.08),
        ("general_balanced", 0.12),
    ]

    personas, weights = zip(*persona_pool)

    records = []
    seen = set()

    # Generate records
    attempts = 0
    max_attempts = num_records * 3

    while len(records) < num_records and attempts < max_attempts:
        attempts += 1
        persona = random.choices(personas, weights=weights)[0]
        rec = generate_persona_record(persona)

        # Create signature for deduplication
        sig = (
            rec["destination_country"],
            rec["trip_duration_days"],
            rec["season"],
            rec["previous_trips"],
            rec["flight_booked"],
            rec["hotel_booked"],
            rec["passport_valid"],
            rec["visa_required"],
            rec["visa_ready"],
            rec["documents_completed"],
            rec["travel_insurance"],
            rec["emergency_prepared"],
            rec["country_preparation"],
            rec["packing_completed"],
            rec["weather_risk"],
            rec["preparedness_score"],
        )

        if sig not in seen:
            seen.add(sig)
            records.append(rec)

    df = pd.DataFrame(records)
    return df


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "readiness_dataset.csv")

    print("=" * 60)
    print("AI-NOMAD TRAVEL READINESS DATASET GENERATOR")
    print("Methodology: Domain-based synthetic derivation")
    print("=" * 60)
    print("Generating ~35,000 realistic traveler records...")

    df = generate_dataset(num_records=35000)

    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f"\n✓ Saved dataset to: {output_csv}")

    # Step 3 reporting requirements
    print("\n" + "=" * 60)
    print("DATASET VERIFICATION & DIAGNOSTICS")
    print("=" * 60)
    print(f"Number of rows:              {len(df):,}")
    print(f"Number of features:          {len(df.columns) - 1} (+1 target 'preparedness_score')")
    print(f"Missing values count:        {df.isnull().sum().sum()}")
    print(f"Exact duplicate rows:        {df.duplicated().sum()}")

    print("\nFeature List:")
    for col in df.columns:
        dt = df[col].dtype
        print(f"  - {col:25} ({dt})")

    print("\nScore Distribution:")
    score = df["preparedness_score"]
    print(f"  Min:       {score.min():.1f}")
    print(f"  25th %ile: {score.quantile(0.25):.1f}")
    print(f"  Median:    {score.median():.1f}")
    print(f"  75th %ile: {score.quantile(0.75):.1f}")
    print(f"  Max:       {score.max():.1f}")
    print(f"  Mean:      {score.mean():.1f}")
    print(f"  Std Dev:   {score.std():.1f}")

    print("\nScore Bands:")
    print(f"  Critical Risk (<40):       {(score < 40).mean() * 100:.1f}%")
    print(f"  Moderate Readiness (40-69):{((score >= 40) & (score < 70)).mean() * 100:.1f}%")
    print(f"  High Readiness (70-89):    {((score >= 70) & (score < 90)).mean() * 100:.1f}%")
    print(f"  Departure Ready (90-100):  {(score >= 90).mean() * 100:.1f}%")

    print("\nSample Records (first 5):")
    print(df.head(5).to_string(index=False))
    print("=" * 60)


if __name__ == "__main__":
    main()
