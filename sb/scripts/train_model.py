import pandas as pd
import joblib
import os
import subprocess
import sys

"""
DATA LEAKAGE EXPLANATION:
The previous model achieved R2 = 1.0 because it was using 'Accommodation cost' 
and 'Transportation cost' as features to predict 'actual_trip_cost', which is 
simply the sum of those two columns. This is classic data leakage - the model 
was learning the answer directly from the input features.

FIX: This version explicitly selects ONLY realistic user-input features that 
would be known BEFORE booking a trip (destination, duration, traveler demographics, 
economic indicators). No price information is used as input.
"""

# Try to import sklearn, install if missing
try:
    from sklearn.model_selection import train_test_split
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
    import numpy as np
except ImportError:
    print("scikit-learn not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])
    from sklearn.model_selection import train_test_split
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
    import numpy as np

# Try to import joblib, install if missing
try:
    import joblib
except ImportError:
    print("joblib not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "joblib"])

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to sb/, then into data/
data_dir = os.path.join(script_dir, "..", "data")
# Go up one level to sb/, then into models/
models_dir = os.path.join(script_dir, "..", "models")

# Create models directory if it doesn't exist
os.makedirs(models_dir, exist_ok=True)

# Define file paths
dataset_path = os.path.join(data_dir, "real_budget_dataset.csv")
model_path = os.path.join(models_dir, "budget_model.pkl")

print("Loading dataset...")
df = pd.read_csv(dataset_path)

# Remove duplicates
df = df.drop_duplicates()

print("Dataset shape:", df.shape)
print("\nAvailable columns in dataset:")
print(df.columns.tolist())

# Define feature columns - ONLY realistic user-input features
# These are features known BEFORE booking (no price information)
categorical_features = [
    "hotel",
    "country",
    "customer_type",
    "reserved_room_type",
    "budget_level"
]

numeric_features = [
    "total_stays",
    "adults",
    "children",
    "tourism_expenditures",
    "gdp",
    "inflation",
    "avg_tourist_spending",
    "tourism_revenue"
]

# Combine all features
all_features = categorical_features + numeric_features

# Verify no data leakage - remove any price-related columns
leakage_columns = ["Accommodation cost", "Transportation cost", "actual_trip_cost", "avg_room_price", "adr"]
for col in leakage_columns:
    if col in all_features:
        raise ValueError(f"DATA LEAKAGE DETECTED: '{col}' should not be in features!")

# Explicitly select ONLY the allowed features
X = df[all_features].copy()
y = df["actual_trip_cost"]

print("\n" + "="*50)
print("DATA LEAKAGE VERIFICATION")
print("="*50)
print(f"Target column: actual_trip_cost")
print(f"\nCategorical features ({len(categorical_features)}):")
for feat in categorical_features:
    print(f"  - {feat}")
print(f"\nNumeric features ({len(numeric_features)}):")
for feat in numeric_features:
    print(f"  - {feat}")
print(f"\nTotal features used: {len(all_features)}")
print("="*50)

# Check for any remaining price columns in X
price_keywords = ["cost", "price", "amount", "fee", "rate"]
found_leakage = []
for col in X.columns:
    if any(keyword in col.lower() for keyword in price_keywords):
        found_leakage.append(col)

if found_leakage:
    print(f"\n⚠ WARNING: Potential leakage columns found: {found_leakage}")
    print("Removing these columns...")
    X = X.drop(columns=found_leakage)
else:
    print("\n✓ No price-related columns detected in features")

# Create preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("num", "passthrough", numeric_features)
    ]
)

# Create model pipeline
model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
])

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training model...")
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)

# Calculate metrics
mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
r2 = r2_score(y_test, predictions)

print("\nModel Performance")
print("-------------------")
print(f"MAE: {round(mae, 2)}")
print(f"RMSE: {round(rmse, 2)}")
print(f"R2 Score: {round(r2, 2)}")

# Feature importance
print("\nFeature Importance")
print("-------------------")
# Get feature names after one-hot encoding
preprocessor = model.named_steps['preprocessor']
cat_encoder = preprocessor.named_transformers_['cat']
cat_feature_names = cat_encoder.get_feature_names_out(categorical_features)
all_feature_names = list(cat_feature_names) + numeric_features

# Get feature importances
importances = model.named_steps['regressor'].feature_importances_
feature_importance_df = pd.DataFrame({
    'feature': all_feature_names,
    'importance': importances
}).sort_values('importance', ascending=False)

print("Top 10 most important features:")
print(feature_importance_df.head(10).to_string(index=False))

# Save model
joblib.dump(model, model_path)

print("\nModel saved!")
print(f"Location: {model_path}")
