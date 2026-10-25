"""
Training Script for AI-Nomad Travel Readiness ML Model.

Model: RandomForestRegressor Pipeline
Preprocessor: ColumnTransformer (OneHotEncoder for categoricals + numeric passthrough)
Input Dataset: sb/data/readiness_dataset.csv
Output Artifact: sb/models/readiness_model.pkl
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_PATH = os.path.join(SB_ROOT, "data", "readiness_dataset.csv")
MODELS_DIR = os.path.join(SB_ROOT, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "readiness_model.pkl")

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)


def train_readiness_model():
    print("=" * 65)
    print("AI-NOMAD TRAVEL READINESS ML TRAINING PIPELINE")
    print("Model: Scikit-Learn RandomForestRegressor Pipeline")
    print("=" * 65)

    if not os.path.isfile(DATA_PATH):
        print(f"Error: Dataset not found at {DATA_PATH}")
        print("Run sb/scripts/generate_readiness_dataset.py first.")
        sys.exit(1)

    print(f"1. Loading dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"   Loaded {len(df):,} records, {len(df.columns)} columns.")

    # Define categorical and numeric features
    categorical_features = [
        "destination_country",
        "season",
        "weather_risk",
    ]

    numeric_features = [
        "trip_duration_days",
        "previous_trips",
        "flight_booked",
        "hotel_booked",
        "passport_valid",
        "visa_required",
        "visa_ready",
        "documents_completed",
        "travel_insurance",
        "emergency_prepared",
        "country_preparation",
        "packing_completed",
    ]

    target = "preparedness_score"
    feature_columns = categorical_features + numeric_features

    X = df[feature_columns]
    y = df[target]

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
            ("num", "passthrough", numeric_features),
        ]
    )

    # Full ML pipeline
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=100,
                    max_depth=18,
                    min_samples_split=4,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    # 80/20 train/test split on held-out test set
    print("\n2. Splitting data into 80% train and 20% held-out test set...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"   Training samples:  {len(X_train):,}")
    print(f"   Test samples:      {len(X_test):,}")

    # Training
    print("\n3. Training RandomForestRegressor with ColumnTransformer...")
    pipeline.fit(X_train, y_train)
    print("   ✓ Training complete!")

    # Evaluation on held-out test set
    print("\n4. Evaluating model on held-out test set...")
    y_pred = pipeline.predict(X_test)
    y_pred_clamped = np.clip(y_pred, 0.0, 100.0)

    mae = mean_absolute_error(y_test, y_pred_clamped)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_clamped))
    r2 = r2_score(y_test, y_pred_clamped)

    print("\n" + "=" * 65)
    print("MODEL PERFORMANCE METRICS (Held-Out Test Set)")
    print("=" * 65)
    print(f"  Mean Absolute Error (MAE):    {mae:.3f} points")
    print(f"  Root Mean Squared Error (RMSE):{rmse:.3f} points")
    print(f"  R² Score (Variance Explained): {r2:.4f} ({r2 * 100:.2f}%)")
    print("=" * 65)

    # Actual vs Predicted Examples
    print("\n5. Actual vs Predicted Sample Comparison:")
    comparison_df = X_test.head(10).copy()
    comparison_df["Actual_Score"] = y_test.head(10).values
    comparison_df["Predicted_Score"] = np.round(y_pred_clamped[:10], 1)
    comparison_df["Abs_Error"] = np.round(np.abs(comparison_df["Actual_Score"] - comparison_df["Predicted_Score"]), 2)

    sample_view = comparison_df[
        [
            "destination_country",
            "passport_valid",
            "visa_required",
            "visa_ready",
            "flight_booked",
            "packing_completed",
            "Actual_Score",
            "Predicted_Score",
            "Abs_Error",
        ]
    ]
    print(sample_view.to_string(index=False))

    # Feature Importance Extraction
    print("\n6. Feature Importance Analysis:")
    preproc = pipeline.named_steps["preprocessor"]
    cat_encoder = preproc.named_transformers_["cat"]
    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_features))
    all_feature_names = cat_feature_names + numeric_features

    regressor = pipeline.named_steps["regressor"]
    importances = regressor.feature_importances_

    importance_df = pd.DataFrame(
        {"Feature": all_feature_names, "Importance": importances}
    ).sort_values("Importance", ascending=False)

    print("   Top 15 Most Influential Features:")
    print(importance_df.head(15).to_string(index=False))

    # Save trained artifact
    print(f"\n7. Saving complete pipeline to: {MODEL_PATH}")
    joblib.dump(pipeline, MODEL_PATH)
    print("   ✓ Saved model successfully.")

    return pipeline, mae, rmse, r2


if __name__ == "__main__":
    train_readiness_model()
