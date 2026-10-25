import pandas as pd
import joblib
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to sb/, then into models/
models_dir = os.path.join(script_dir, "..", "models")

# Load the trained model
model_path = os.path.join(models_dir, "budget_model.pkl")
print(f"Loading model from: {model_path}")
model = joblib.load(model_path)

# Create sample user input for Japan trip
# These are realistic values based on the training data
sample_input = pd.DataFrame({
    'hotel': ['Resort Hotel'],
    'country': ['JAPAN'],
    'total_stays': [8],
    'adults': [2],
    'children': [0],
    'customer_type': ['Transient'],
    'reserved_room_type': ['A'],
    'budget_level': ['Luxury'],
    'tourism_expenditures': [4.5e10],  # Japan's tourism expenditure in USD
    'gdp': [4.9e12],  # Japan's GDP in USD
    'inflation': [2.5],  # Japan's inflation rate
    'avg_tourist_spending': [2000],  # Average tourist spending in USD
    'tourism_revenue': [3.5e10]  # Japan's tourism revenue in USD
})

print("\n" + "="*50)
print("SAMPLE INPUT FOR PREDICTION")
print("="*50)
print("Destination: Japan")
print("Duration: 8 days")
print("Adults: 2")
print("Children: 0")
print("Hotel Type: Resort Hotel")
print("Room Type: A")
print("Budget Level: Luxury")
print("="*50)

# Make prediction
prediction = model.predict(sample_input)
predicted_cost = prediction[0]

# Convert to Indian Rupees (approximate exchange rate: 1 USD = 83 INR)
exchange_rate = 83
predicted_cost_inr = predicted_cost * exchange_rate

print("\nEstimated Trip Cost:")
print(f"₹ {predicted_cost_inr:,.2f}")
print(f"(USD ${predicted_cost:,.2f})")

print("\nPrediction completed successfully.")
