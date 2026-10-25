#!/usr/bin/env python3
"""
Training Pipeline for Cultural Intelligence Event Relevance & Personalization Model.

Uses a scikit-learn Pipeline with:
  - ColumnTransformer (OneHotEncoder for event_category, StandardScaler for numericals)
  - RandomForestRegressor predicting continuous event_relevance_score (0.0 - 100.0)

Artifact:
  Saved to `sb/models/event_relevance_model.pkl`
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_PATH = os.path.join(SB_ROOT, "data", "event_relevance_dataset.csv")
MODEL_DIR = os.path.join(SB_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "event_relevance_model.pkl")

CATEGORICAL_FEATURES = ["event_category"]
NUMERICAL_FEATURES = [
    "category_match",
    "distance_from_destination",
    "date_overlap",
    "days_until_event",
    "interest_match",
    "event_popularity",
    "event_source_reliability",
    "event_locality",
    "price_affordability",
    "user_interest_similarity",
    "event_duration",
]
TARGET_COL = "event_relevance_score"


def train_model():
    print(f"Loading event relevance dataset from {DATA_PATH}...")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Run generate_event_relevance_dataset.py first.")

    df = pd.read_csv(DATA_PATH)
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    X = df[CATEGORICAL_FEATURES + NUMERICAL_FEATURES]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"Train set: {X_train.shape[0]} samples | Test set: {X_test.shape[0]} samples")

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERICAL_FEATURES),
        ]
    )

    regressor = RandomForestRegressor(
        n_estimators=100,
        max_depth=16,
        min_samples_split=4,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", regressor),
    ])

    print("Fitting RandomForestRegressor pipeline...")
    pipeline.fit(X_train, y_train)

    print("Evaluating model performance on held-out test split...")
    y_pred = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print("=" * 55)
    print("EVENT RELEVANCE ML MODEL EVALUATION METRICS:")
    print(f"  • Mean Absolute Error (MAE):     {mae:.3f} points")
    print(f"  • Root Mean Squared Error (RMSE): {rmse:.3f} points")
    print(f"  • R² Determination Score:         {r2:.4f} ({r2*100:.2f}% variance explained)")
    print("=" * 55)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Trained model serialized successfully to: {MODEL_PATH}")

    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2": round(r2, 4),
        "test_samples": len(y_test),
    }


if __name__ == "__main__":
    train_model()
