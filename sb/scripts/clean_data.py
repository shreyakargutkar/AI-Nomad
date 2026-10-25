import pandas as pd

print("Loading datasets...")

travel = pd.read_csv("data/travel.csv")
economy = pd.read_csv("data/economy.csv")
cities = pd.read_csv("data/cities.csv")

print("Datasets loaded successfully")


travel = travel.dropna()

travel["Accommodation cost"] = pd.to_numeric(
    travel["Accommodation cost"], errors="coerce"
)

travel["Transportation cost"] = pd.to_numeric(
    travel["Transportation cost"], errors="coerce"
)

travel = travel.dropna()


travel["actual_trip_cost"] = (
    travel["Accommodation cost"]
    + travel["Transportation cost"]
)


travel["destination_country"] = (
    travel["Destination"]
    .str.split(",")
    .str[-1]
    .str.strip()
)


economy = economy[
    [
        "country",
        "tourism_expenditures",
        "gdp",
        "inflation"
    ]
]

economy = economy.dropna()

latest_year = 2023

economy = economy[economy["country"].notna()]


merged_data = travel.merge(
    economy,
    left_on="destination_country",
    right_on="country",
    how="left"
)


cities = cities[
    [
        "country",
        "budget_level"
    ]
]

merged_data = merged_data.merge(
    cities,
    left_on="destination_country",
    right_on="country",
    how="left"
)


final_data = merged_data[
    [
        "Duration (days)",
        "Traveler age",
        "Traveler gender",
        "Traveler nationality",
        "Accommodation type",
        "Transportation type",
        "destination_country",
        "tourism_expenditures",
        "gdp",
        "inflation",
        "budget_level",
        "actual_trip_cost"
    ]
]

final_data = final_data.dropna()


final_data.to_csv(
    "data/final_budget_dataset.csv",
    index=False
)

print("\nCleaning complete!")
print("Final dataset shape:", final_data.shape)
print("\nFirst 5 rows:")
print(final_data.head())

print("\nSaved file:")
print("data/final_budget_dataset.csv")