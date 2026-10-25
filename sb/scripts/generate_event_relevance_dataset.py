#!/usr/bin/env python3
"""
Synthetic / Derived Dataset Generator for Event Relevance & Personalization Ranking.

Methodology:
Generates 35,000 realistic event-traveler pairing records based on:
  - Controlled Event Taxonomy (ANIME_GAMING, TECHNOLOGY, FOOD_DRINK, CULTURE_MATSURI, ART_DESIGN, MUSIC_CONCERTS, SPORTS)
  - Category Match (Hard Constraint Indicator: 1.0 vs 0.0)
  - Destination City & Geographic Locality (distance in km, in-city vs distant)
  - Date Overlap with Traveler Trip (during trip, overlapping, adjacent, outside)
  - Multi-interest Personalization (Anime, Tech, Food, Art, Culture, Music, Sports)
  - Source Credibility & Event Characteristics (popularity, duration, price)

The target `event_relevance_score` (0.0 to 100.0) represents the predicted
suitability of an event for a specific traveler's itinerary and profile.
"""

import os
import random
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_CSV = os.path.join(SB_ROOT, "data", "event_relevance_dataset.csv")

RANDOM_SEED = 42
NUM_SAMPLES = 35000

TAXONOMY_CATEGORIES = [
    "ANIME_GAMING",
    "TECHNOLOGY",
    "FOOD_DRINK",
    "CULTURE_MATSURI",
    "ART_DESIGN",
    "MUSIC_CONCERTS",
    "SPORTS",
]


def generate_dataset(num_samples=NUM_SAMPLES, seed=RANDOM_SEED):
    np.random.seed(seed)
    random.seed(seed)

    records = []

    for _ in range(num_samples):
        # 1. Category from controlled taxonomy
        category = random.choice(TAXONOMY_CATEGORIES)

        # 2. Category Match (80% matching category in ML stage, 20% non-matching for negative sampling)
        cat_match_roll = random.random()
        category_match = 1.0 if cat_match_roll < 0.80 else 0.0

        # 3. Locality & Distance (km from destination center)
        # 65% in-city (0-15km), 20% metro area (15-35km), 15% distant/wrong city (35-120km)
        loc_roll = random.random()
        if loc_roll < 0.65:
            distance = round(float(np.random.uniform(0.5, 14.0)), 1)
            locality = 1.0  # in-city
        elif loc_roll < 0.85:
            distance = round(float(np.random.uniform(15.0, 35.0)), 1)
            locality = 0.5  # surrounding metro
        else:
            distance = round(float(np.random.uniform(36.0, 120.0)), 1)
            locality = 0.0  # distant / wrong city

        # 4. Date Overlap with traveler trip (0.0 to 1.0)
        date_roll = random.random()
        if date_roll < 0.50:
            date_overlap = 1.0
        elif date_roll < 0.70:
            date_overlap = round(float(np.random.uniform(0.70, 0.90)), 2)
        elif date_roll < 0.85:
            date_overlap = round(float(np.random.uniform(0.30, 0.50)), 2)
        else:
            date_overlap = round(float(np.random.uniform(0.0, 0.10)), 2)

        # 5. Days until event
        days_until = int(np.random.randint(1, 150))

        # 6. Interest Match & Similarity (Personalization)
        if category_match == 1.0:
            match_roll = random.random()
            if match_roll < 0.60:
                interest_match = round(float(np.random.uniform(0.75, 1.0)), 2)
                user_interest_similarity = round(float(np.random.uniform(0.70, 1.0)), 2)
            else:
                interest_match = round(float(np.random.uniform(0.40, 0.74)), 2)
                user_interest_similarity = round(float(np.random.uniform(0.35, 0.69)), 2)
        else:
            # Category mismatch: low interest overlap
            interest_match = round(float(np.random.uniform(0.0, 0.25)), 2)
            user_interest_similarity = round(float(np.random.uniform(0.0, 0.20)), 2)

        # 7. Event Popularity & Credibility
        popularity = int(np.random.randint(1, 11))
        source_reliability = round(float(random.choice([0.65, 0.80, 0.90, 1.0])), 2)

        # 8. Price Affordability
        price_affordability = round(float(random.choice([0.4, 0.6, 0.75, 0.9, 1.0])), 2)

        # 9. Event Duration (days)
        duration = int(np.random.choice([1, 1, 2, 2, 3, 4, 7, 10, 14]))

        # ==========================================
        # GROUND TRUTH RELEVANCE SCORE CALCULATION
        # ==========================================
        if category_match == 0.0:
            # Hard mismatch: score is strictly capped <= 22 points
            base_score = float(np.random.uniform(5.0, 22.0))
        else:
            # Valid category: full multi-factor score
            base_score = 100.0 * (
                0.35 * interest_match
                + 0.30 * date_overlap
                + 0.20 * locality
                + 0.07 * user_interest_similarity
                + 0.04 * source_reliability
                + 0.04 * price_affordability
            )

            # Popularity bonus
            base_score += (popularity / 10.0) * 3.0

            # Distance penalty
            if distance > 30.0:
                dist_penalty = min(35.0, (distance - 30.0) * 0.4)
                base_score -= dist_penalty

            # Date overlap cap
            if date_overlap <= 0.15:
                base_score = min(base_score, 35.0)

            # Locality cap
            if locality == 0.0 and distance > 45.0:
                base_score = min(base_score, 30.0)

        # Add slight Gaussian noise
        noise = np.random.normal(0.0, 1.0)
        final_score = float(np.clip(base_score + noise, 0.0, 100.0))

        records.append({
            "category_match": category_match,
            "distance_from_destination": distance,
            "date_overlap": date_overlap,
            "days_until_event": days_until,
            "interest_match": interest_match,
            "event_category": category,
            "event_popularity": popularity,
            "event_source_reliability": source_reliability,
            "event_locality": locality,
            "price_affordability": price_affordability,
            "user_interest_similarity": user_interest_similarity,
            "event_duration": duration,
            "event_relevance_score": round(final_score, 2),
        })

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Dataset successfully created at: {OUTPUT_CSV}")
    print(f"Total rows: {len(df)}")
    print(df.describe().T[["min", "mean", "max"]])
    return df


if __name__ == "__main__":
    generate_dataset()
