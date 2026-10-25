import pandas as pd
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to sb/, then into data/
data_dir = os.path.join(script_dir, "..", "data")

# Define file paths
travel_path = os.path.join(data_dir, "travel.csv")
economy_path = os.path.join(data_dir, "economy.csv")
cities_path = os.path.join(data_dir, "cities.csv")

# Load datasets with error handling
travel = None
economy = None
cities = None

try:
    travel = pd.read_csv(travel_path)
    print(f"✓ Loaded travel.csv")
except FileNotFoundError:
    print(f"✗ Error: {travel_path} not found")

try:
    economy = pd.read_csv(economy_path)
    print(f"✓ Loaded economy.csv")
except FileNotFoundError:
    print(f"✗ Error: {economy_path} not found")

try:
    cities = pd.read_csv(cities_path)
    print(f"✓ Loaded cities.csv")
except FileNotFoundError:
    print(f"✗ Error: {cities_path} not found")

def explore_dataset(df, name):
    """Helper function to print dataset info"""
    if df is None:
        print(f"\n{'='*50}")
        print(f"{name} DATASET - NOT LOADED")
        print(f"{'='*50}")
        return
    
    print(f"\n{'='*50}")
    print(f"{name} DATASET")
    print(f"{'='*50}")
    
    print("\nFirst 5 rows:")
    print(df.head())
    
    print("\nColumns:")
    print(df.columns.tolist())
    
    print("\nShape (rows, columns):")
    print(df.shape)
    
    print("\nData types:")
    print(df.dtypes)
    
    print("\nMissing values:")
    print(df.isnull().sum())

# Explore each dataset
explore_dataset(travel, "TRAVEL")
explore_dataset(economy, "ECONOMY")
explore_dataset(cities, "CITIES")