import pandas as pd
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to sb/, then into data/
data_dir = os.path.join(script_dir, "..", "data")

# List all CSV files
csv_files = [
    "travel.csv",
    "economy.csv", 
    "cities.csv",
    "hotel_bookings.csv",
    "structured_UNWTO_tourism_data.csv",
    "Tourism_Hospitality_Industry_Analysis.csv.xls"
]

print("="*70)
print("STEP 1: INSPECT ALL DATASETS FOR TRAVEL BUDGET PREDICTION")
print("="*70)

for csv_file in csv_files:
    file_path = os.path.join(data_dir, csv_file)
    
    if not os.path.exists(file_path):
        print(f"\n✗ {csv_file} - FILE NOT FOUND")
        continue
    
    print(f"\n{'='*70}")
    print(f"DATASET: {csv_file}")
    print(f"{'='*70}")
    
    try:
        df = pd.read_csv(file_path)
        
        print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")
        
        print(f"\nColumn names:")
        for col in df.columns:
            print(f"  - {col}")
        
        print(f"\nMissing values:")
        missing = df.isnull().sum()
        for col, count in missing.items():
            if count > 0:
                print(f"  - {col}: {count} ({round(count/len(df)*100, 1)}%)")
        
        if missing.sum() == 0:
            print("  ✓ No missing values")
        
        print(f"\nFirst 3 rows:")
        print(df.head(3))
        
        # Analyze usefulness for travel budget prediction
        print(f"\nUSEFULNESS FOR TRAVEL BUDGET PREDICTION:")
        
        # Check for cost/price columns
        cost_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['cost', 'price', 'rate', 'spending', 'revenue', 'adr'])]
        if cost_cols:
            print(f"  ✓ Cost/Price columns found: {cost_cols}")
        
        # Check for country/location columns
        location_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['country', 'city', 'destination', 'hotel'])]
        if location_cols:
            print(f"  ✓ Location columns found: {location_cols}")
        
        # Check for duration/time columns
        duration_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['duration', 'stay', 'length', 'time'])]
        if duration_cols:
            print(f"  ✓ Duration/Time columns found: {duration_cols}")
        
        # Check for economic indicators
        economic_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['gdp', 'inflation', 'expenditure'])]
        if economic_cols:
            print(f"  ✓ Economic columns found: {economic_cols}")
        
        # Check for traveler demographics
        traveler_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['age', 'gender', 'nationality', 'adult', 'guest'])]
        if traveler_cols:
            print(f"  ✓ Traveler demographic columns found: {traveler_cols}")
        
        # Provide recommendation
        print(f"\nRECOMMENDATION:")
        if csv_file == "travel.csv":
            print("  ✓ HIGHLY USEFUL - Contains actual trip costs, traveler demographics, destinations")
            print("  KEEP: Destination, Duration, Traveler age/gender/nationality, Accommodation/Transportation type")
            print("  REMOVE: Trip ID, Traveler name (identifiers)")
        elif csv_file == "economy.csv":
            print("  ✓ USEFUL - Contains country-level economic indicators")
            print("  KEEP: country, tourism_expenditures, gdp, inflation")
            print("  REMOVE: country_code, year (use latest), tourism_arrivals (not cost-related)")
        elif csv_file == "cities.csv":
            print("  ✓ USEFUL - Contains city-level attributes and budget levels")
            print("  KEEP: country, budget_level, region")
            print("  REMOVE: id, latitude/longitude (not needed for cost prediction)")
        elif csv_file == "hotel_bookings.csv":
            print("  ✓ VERY USEFUL - Large real hotel booking dataset with actual prices (adr)")
            print("  KEEP: country, stays_in_weekend_nights, stays_in_week_nights, adults, adr, hotel")
            print("  REMOVE: is_canceled, lead_time, booking_changes (not cost-related)")
        elif csv_file == "structured_UNWTO_tourism_data.csv":
            print("  ⚠ LIMITED USE - Time series data, mostly empty values")
            print("  SKIP: Too sparse, not directly useful for individual trip cost prediction")
        elif csv_file == "Tourism_Hospitality_Industry_Analysis.csv.xls":
            print("  ✓ USEFUL - Contains tourism spending and revenue data")
            print("  KEEP: Country, Tourist_Spending_USD, Average_Room_Price_USD, Tourism_Revenue_USD")
            print("  REMOVE: City, Month (aggregate to country level)")
        
    except Exception as e:
        print(f"\n✗ Error reading {csv_file}: {e}")

print(f"\n{'='*70}")
print("SUMMARY OF RECOMMENDED DATASETS")
print(f"{'='*70}")
print("\nPRIMARY DATASETS TO USE:")
print("1. hotel_bookings.csv - Large real hotel pricing data (adr = average daily rate)")
print("2. travel.csv - Small but complete trip cost data")
print("3. economy.csv - Country economic indicators")
print("4. cities.csv - City budget levels")
print("5. Tourism_Hospitality_Industry_Analysis.csv.xls - Tourism spending data")

print("\nDATASETS TO SKIP:")
print("- structured_UNWTO_tourism_data.csv - Too sparse, time series format not suitable")

print("\nMERGING STRATEGY:")
print("- Use hotel_bookings.csv as base (largest real pricing dataset)")
print("- Merge economy.csv by country for economic context")
print("- Merge cities.csv by country for budget level")
print("- Use travel.csv to validate feature relationships")
print("- Calculate trip cost from hotel_bookings: adr * (stays_in_weekend_nights + stays_in_week_nights)")
