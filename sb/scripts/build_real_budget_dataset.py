import pandas as pd
import numpy as np
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "..", "data")

print("="*70)
print("STEP 2: BUILD REAL TRAVEL BUDGET DATASET")
print("="*70)

# Load datasets
print("\nLoading datasets...")
hotel_df = pd.read_csv(os.path.join(data_dir, "hotel_bookings.csv"))
economy_df = pd.read_csv(os.path.join(data_dir, "economy.csv"))
cities_df = pd.read_csv(os.path.join(data_dir, "cities.csv"))
tourism_df = pd.read_csv(os.path.join(data_dir, "Tourism_Hospitality_Industry_Analysis.csv.xls"))

print(f"hotel_bookings.csv: {hotel_df.shape}")
print(f"economy.csv: {economy_df.shape}")
print(f"cities.csv: {cities_df.shape}")
print(f"Tourism_Hospitality_Industry_Analysis.csv.xls: {tourism_df.shape}")

# ============================================================
# STEP 2.1: Clean hotel_bookings.csv (base dataset)
# ============================================================
print("\n" + "="*70)
print("CLEANING hotel_bookings.csv")
print("="*70)

# Select relevant columns from hotel bookings
hotel_clean = hotel_df[[
    'hotel', 'country', 'stays_in_weekend_nights', 'stays_in_week_nights',
    'adults', 'children', 'adr', 'customer_type', 'reserved_room_type'
]].copy()

# Calculate total stay duration
hotel_clean['total_stays'] = hotel_clean['stays_in_weekend_nights'] + hotel_clean['stays_in_week_nights']

# Remove rows with invalid data
hotel_clean = hotel_clean[
    (hotel_clean['total_stays'] > 0) & 
    (hotel_clean['adr'] > 0) & 
    (hotel_clean['adults'] > 0) &
    (hotel_clean['country'].notna())
]

# Remove extreme outliers (adr > 1000 or total_stays > 30)
hotel_clean = hotel_clean[
    (hotel_clean['adr'] < 1000) & 
    (hotel_clean['total_stays'] <= 30)
]

print(f"After cleaning: {hotel_clean.shape}")
print(f"Removed {len(hotel_df) - len(hotel_clean)} rows")

# Calculate target variable: estimated trip cost (hotel cost only)
hotel_clean['estimated_hotel_cost'] = hotel_clean['adr'] * hotel_clean['total_stays']

# Country code to name mapping (ISO 3166-1 alpha-3)
country_code_map = {
    'PRT': 'PORTUGAL', 'GBR': 'UNITED KINGDOM', 'USA': 'UNITED STATES', 'ESP': 'SPAIN',
    'IRL': 'IRELAND', 'FRA': 'FRANCE', 'ROU': 'ROMANIA', 'NOR': 'NORWAY', 'OMN': 'OMAN',
    'ARG': 'ARGENTINA', 'POL': 'POLAND', 'DEU': 'GERMANY', 'BEL': 'BELGIUM', 'CHE': 'SWITZERLAND',
    'CN': 'CHINA', 'GRC': 'GREECE', 'ITA': 'ITALY', 'NLD': 'NETHERLANDS', 'DNK': 'DENMARK',
    'RUS': 'RUSSIA', 'SWE': 'SWEDEN', 'AUT': 'AUSTRIA', 'ISR': 'ISRAEL', 'EST': 'ESTONIA',
    'CZE': 'CZECH REPUBLIC', 'FIN': 'FINLAND', 'BRA': 'BRAZIL', 'BGR': 'BULGARIA', 'SRB': 'SERBIA',
    'AUS': 'AUSTRALIA', 'IND': 'INDIA', 'CHL': 'CHILE', 'MEX': 'MEXICO', 'ZAF': 'SOUTH AFRICA',
    'TUR': 'TURKEY', 'MOZ': 'MOZAMBIQUE', 'URU': 'URUGUAY', 'BEL': 'BELARUS', 'COL': 'COLOMBIA',
    'NGA': 'NIGERIA', 'KOR': 'SOUTH KOREA', 'HUN': 'HUNGARY', 'ARE': 'UNITED ARAB EMIRATES',
    'UKR': 'UKRAINE', 'CPV': 'CAPE VERDE', 'SVN': 'SLOVENIA', 'JPN': 'JAPAN', 'LTU': 'LITHUANIA',
    'LVA': 'LATVIA', 'HRV': 'CROATIA', 'BLR': 'BELARUS', 'IRL': 'IRELAND', 'ALB': 'ALBANIA',
    'ABW': 'ARUBA', 'AGO': 'ANGOLA', 'AFG': 'AFGHANISTAN', 'AND': 'ANDORRA', 'ARE': 'UNITED ARAB EMIRATES',
    'ARG': 'ARGENTINA', 'ARM': 'ARMENIA', 'ASM': 'AMERICAN SAMOA', 'ATA': 'ANTARCTICA', 'ATF': 'FRENCH SOUTHERN TERRITORIES',
    'ATG': 'ANTIGUA AND BARBUDA', 'AUS': 'AUSTRALIA', 'AUT': 'AUSTRIA', 'AZE': 'AZERBAIJAN', 'BDI': 'BURUNDI',
    'BEL': 'BELGIUM', 'BEN': 'BENIN', 'BFA': 'BURKINA FASO', 'BGD': 'BANGLADESH', 'BGR': 'BULGARIA',
    'BHR': 'BAHRAIN', 'BHS': 'BAHAMAS', 'BIH': 'BOSNIA AND HERZEGOVINA', 'BLM': 'SAINT BARTHELEMY',
    'BLR': 'BELARUS', 'BLZ': 'BELIZE', 'BMU': 'BERMUDA', 'BOL': 'BOLIVIA', 'BRA': 'BRAZIL',
    'BRB': 'BARBADOS', 'BRN': 'BRUNEI', 'BTN': 'BHUTAN', 'BWA': 'BOTSWANA', 'CAF': 'CENTRAL AFRICAN REPUBLIC',
    'CAN': 'CANADA', 'CHE': 'SWITZERLAND', 'CHL': 'CHILE', 'CHN': 'CHINA', 'CIV': 'COTE D IVOIRE',
    'CMR': 'CAMEROON', 'COD': 'CONGO', 'COG': 'CONGO', 'COK': 'COOK ISLANDS', 'COL': 'COLOMBIA',
    'COM': 'COMOROS', 'CPV': 'CAPE VERDE', 'CRI': 'COSTA RICA', 'CUB': 'CUBA', 'CUW': 'CURACAO',
    'CXR': 'CHRISTMAS ISLAND', 'CYP': 'CYPRUS', 'CZE': 'CZECH REPUBLIC', 'DEU': 'GERMANY', 'DJI': 'DJIBOUTI',
    'DMA': 'DOMINICA', 'DNK': 'DENMARK', 'DOM': 'DOMINICAN REPUBLIC', 'DZA': 'ALGERIA', 'ECU': 'ECUADOR',
    'EGY': 'EGYPT', 'ERI': 'ERITREA', 'ESP': 'SPAIN', 'EST': 'ESTONIA', 'ETH': 'ETHIOPIA',
    'FIN': 'FINLAND', 'FJI': 'FIJI', 'FRA': 'FRANCE', 'FRO': 'FAROE ISLANDS', 'FSM': 'MICRONESIA',
    'GAB': 'GABON', 'GBR': 'UNITED KINGDOM', 'GEO': 'GEORGIA', 'GGY': 'GUERNSEY', 'GHA': 'GHANA',
    'GIB': 'GIBRALTAR', 'GIN': 'GUINEA', 'GLP': 'GUADELOUPE', 'GMB': 'GAMBIA', 'GNB': 'GUINEA-BISSAU',
    'GNQ': 'EQUATORIAL GUINEA', 'GRC': 'GREECE', 'GRD': 'GRENADA', 'GRL': 'GREENLAND', 'GTM': 'GUATEMALA',
    'GUF': 'FRENCH GUIANA', 'GUM': 'GUAM', 'GUY': 'GUYANA', 'HKG': 'HONG KONG', 'HND': 'HONDURAS',
    'HRV': 'CROATIA', 'HTI': 'HAITI', 'HUN': 'HUNGARY', 'IDN': 'INDONESIA', 'IMN': 'ISLE OF MAN',
    'IND': 'INDIA', 'IOT': 'BRITISH INDIAN OCEAN TERRITORY', 'IRL': 'IRELAND', 'IRN': 'IRAN',
    'IRQ': 'IRAQ', 'ISL': 'ICELAND', 'ISR': 'ISRAEL', 'ITA': 'ITALY', 'JAM': 'JAMAICA',
    'JEY': 'JERSEY', 'JOR': 'JORDAN', 'JPN': 'JAPAN', 'KAZ': 'KAZAKHSTAN', 'KEN': 'KENYA',
    'KGZ': 'KYRGYZSTAN', 'KHM': 'CAMBODIA', 'KIR': 'KIRIBATI', 'KNA': 'SAINT KITTS AND NEVIS',
    'KOR': 'SOUTH KOREA', 'KWT': 'KUWAIT', 'LAO': 'LAOS', 'LBN': 'LEBANON', 'LBR': 'LIBERIA',
    'LBY': 'LIBYA', 'LCA': 'SAINT LUCIA', 'LIE': 'LIECHTENSTEIN', 'LKA': 'SRI LANKA', 'LSO': 'LESOTHO',
    'LTU': 'LITHUANIA', 'LUX': 'LUXEMBOURG', 'LVA': 'LATVIA', 'MAC': 'MACAU', 'MAF': 'SAINT MARTIN',
    'MAR': 'MOROCCO', 'MCO': 'MONACO', 'MDA': 'MOLDOVA', 'MDG': 'MADAGASCAR', 'MDV': 'MALDIVES',
    'MEX': 'MEXICO', 'MHL': 'MARSHALL ISLANDS', 'MKD': 'NORTH MACEDONIA', 'MLI': 'MALI', 'MLT': 'MALTA',
    'MMR': 'MYANMAR', 'MNE': 'MONTENEGRO', 'MNG': 'MONGOLIA', 'MNP': 'NORTHERN MARIANA ISLANDS',
    'MOZ': 'MOZAMBIQUE', 'MRT': 'MAURITANIA', 'MSR': 'MONTSERRAT', 'MTQ': 'MARTINIQUE', 'MUS': 'MAURITIUS',
    'MWI': 'MALAWI', 'MYS': 'MALAYSIA', 'MYT': 'MAYOTTE', 'NAM': 'NAMIBIA', 'NCL': 'NEW CALEDONIA',
    'NER': 'NIGER', 'NFK': 'NORFOLK ISLAND', 'NGA': 'NIGERIA', 'NIC': 'NICARAGUA', 'NIU': 'NIUE',
    'NLD': 'NETHERLANDS', 'NOR': 'NORWAY', 'NPL': 'NEPAL', 'NRU': 'NAURU', 'NZL': 'NEW ZEALAND',
    'OMN': 'OMAN', 'PAK': 'PAKISTAN', 'PAN': 'PANAMA', 'PER': 'PERU', 'PHL': 'PHILIPPINES',
    'PLW': 'PALAU', 'PNG': 'PAPUA NEW GUINEA', 'POL': 'POLAND', 'PRI': 'PUERTO RICO', 'PRK': 'NORTH KOREA',
    'PRT': 'PORTUGAL', 'PRY': 'PARAGUAY', 'PSE': 'PALESTINE', 'PYF': 'FRENCH POLYNESIA', 'QAT': 'QATAR',
    'REU': 'REUNION', 'ROU': 'ROMANIA', 'RUS': 'RUSSIA', 'RWA': 'RWANDA', 'SAU': 'SAUDI ARABIA',
    'SDN': 'SUDAN', 'SEN': 'SENEGAL', 'SGP': 'SINGAPORE', 'SGS': 'SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS',
    'SHN': 'SAINT HELENA', 'SJM': 'SVALBARD AND JAN MAYEN', 'SLB': 'SOLOMON ISLANDS', 'SLE': 'SIERRA LEONE',
    'SLV': 'EL SALVADOR', 'SMR': 'SAN MARINO', 'SOM': 'SOMALIA', 'SPM': 'SAINT PIERRE AND MIQUELON',
    'SRB': 'SERBIA', 'SSD': 'SOUTH SUDAN', 'STP': 'SAO TOME AND PRINCIPE', 'SUR': 'SURINAME', 'SVK': 'SLOVAKIA',
    'SVN': 'SLOVENIA', 'SWE': 'SWEDEN', 'SWZ': 'SWAZILAND', 'SYC': 'SEYCHELLES', 'SYR': 'SYRIA',
    'TCA': 'TURKS AND CAICOS ISLANDS', 'TCD': 'CHAD', 'TGO': 'TOGO', 'THA': 'THAILAND', 'TJK': 'TAJIKISTAN',
    'TKL': 'TOKELAU', 'TKM': 'TURKMENISTAN', 'TLS': 'TIMOR-LESTE', 'TON': 'TONGA', 'TTO': 'TRINIDAD AND TOBAGO',
    'TUN': 'TUNISIA', 'TUR': 'TURKEY', 'TUV': 'TUVALU', 'TWN': 'TAIWAN', 'TZA': 'TANZANIA',
    'UGA': 'UGANDA', 'UKR': 'UKRAINE', 'UMI': 'UNITED STATES MINOR OUTLYING ISLANDS', 'URY': 'URUGUAY',
    'USA': 'UNITED STATES', 'UZB': 'UZBEKISTAN', 'VAT': 'VATICAN CITY', 'VCT': 'SAINT VINCENT AND THE GRENADINES',
    'VEN': 'VENEZUELA', 'VGB': 'VIRGIN ISLANDS BRITISH', 'VIR': 'VIRGIN ISLANDS US', 'VNM': 'VIETNAM',
    'VUT': 'VANUATU', 'WLF': 'WALLIS AND FUTUNA', 'WSM': 'SAMOA', 'YEM': 'YEMEN', 'ZAF': 'SOUTH AFRICA',
    'ZMB': 'ZAMBIA', 'ZWE': 'ZIMBABWE'
}

# Convert country codes to full names
hotel_clean['country'] = hotel_clean['country'].map(country_code_map).fillna(hotel_clean['country'])
hotel_clean['country'] = hotel_clean['country'].str.upper().str.strip()

print(f"\nTarget variable: estimated_hotel_cost")
print(f"Mean: ${hotel_clean['estimated_hotel_cost'].mean():.2f}")
print(f"Median: ${hotel_clean['estimated_hotel_cost'].median():.2f}")
print(f"Max: ${hotel_clean['estimated_hotel_cost'].max():.2f}")

# ============================================================
# STEP 2.2: Clean economy.csv
# ============================================================
print("\n" + "="*70)
print("CLEANING economy.csv")
print("="*70)

# Select relevant columns and get latest year data for each country
economy_clean = economy_df[
    ['country', 'year', 'tourism_expenditures', 'gdp', 'inflation']
].copy()

# Normalize country names
economy_clean['country'] = economy_clean['country'].str.upper().str.strip()

# Get latest year data for each country
economy_clean = economy_clean.sort_values('year').groupby('country').last().reset_index()

# Fill missing values with median
economy_clean['tourism_expenditures'] = economy_clean['tourism_expenditures'].fillna(economy_clean['tourism_expenditures'].median())
economy_clean['gdp'] = economy_clean['gdp'].fillna(economy_clean['gdp'].median())
economy_clean['inflation'] = economy_clean['inflation'].fillna(economy_clean['inflation'].median())

print(f"After cleaning: {economy_clean.shape}")

# ============================================================
# STEP 2.3: Clean cities.csv
# ============================================================
print("\n" + "="*70)
print("CLEANING cities.csv")
print("="*70)

# Select relevant columns
cities_clean = cities_df[['country', 'budget_level']].copy()

# Normalize country names
cities_clean['country'] = cities_clean['country'].str.upper().str.strip()

# Remove duplicates
cities_clean = cities_clean.drop_duplicates()

print(f"After cleaning: {cities_clean.shape}")
print(f"Unique countries: {cities_clean['country'].nunique()}")

# ============================================================
# STEP 2.4: Clean Tourism_Hospitality data
# ============================================================
print("\n" + "="*70)
print("CLEANING Tourism_Hospitality_Industry_Analysis.csv.xls")
print("="*70)

# Select relevant columns and aggregate by country
tourism_clean = tourism_df[[
    'Country', 'Tourist_Spending_USD', 'Average_Room_Price_USD', 
    'Tourism_Revenue_USD', 'Contribution_to_GDP_Percent'
]].copy()

# Normalize country names
tourism_clean['Country'] = tourism_clean['Country'].str.upper().str.strip()

# Aggregate by country (take mean if multiple entries)
tourism_clean = tourism_clean.groupby('Country').mean().reset_index()
tourism_clean.columns = ['country', 'avg_tourist_spending', 'avg_room_price', 'tourism_revenue', 'gdp_contribution']

print(f"After cleaning: {tourism_clean.shape}")

# ============================================================
# STEP 2.5: Merge datasets
# ============================================================
print("\n" + "="*70)
print("MERGING DATASETS")
print("="*70)

# Start with hotel data as base
merged = hotel_clean.copy()

# Merge economy data
print(f"\nMerging economy data...")
merged = merged.merge(
    economy_clean, 
    on='country', 
    how='left'
)
print(f"After economy merge: {merged.shape}")

# Merge cities data
print(f"Merging cities data...")
merged = merged.merge(
    cities_clean, 
    on='country', 
    how='left'
)
print(f"After cities merge: {merged.shape}")

# Merge tourism data
print(f"Merging tourism data...")
merged = merged.merge(
    tourism_clean, 
    on='country', 
    how='left'
)
print(f"After tourism merge: {merged.shape}")

# ============================================================
# STEP 2.6: Handle missing values after merge
# ============================================================
print("\n" + "="*70)
print("HANDLING MISSING VALUES")
print("="*70)

# Check missing values
missing = merged.isnull().sum()
print(f"Missing values per column:")
for col, count in missing.items():
    if count > 0:
        print(f"  {col}: {count} ({round(count/len(merged)*100, 1)}%)")

# Fill missing budget_level with 'Mid-range' (most common)
merged['budget_level'] = merged['budget_level'].fillna('Mid-range')

# Fill missing economic indicators with median
for col in ['tourism_expenditures', 'gdp', 'inflation', 'avg_tourist_spending', 'avg_room_price', 'tourism_revenue', 'gdp_contribution']:
    if col in merged.columns:
        merged[col] = merged[col].fillna(merged[col].median())

# Fill missing children with 0
merged['children'] = merged['children'].fillna(0)

print(f"\nFinal dataset shape: {merged.shape}")

# ============================================================
# STEP 2.7: Create final features
# ============================================================
print("\n" + "="*70)
print("CREATING FINAL FEATURES")
print("="*70)

# Select final features for ML
final_features = [
    'hotel', 'country', 'total_stays', 'adults', 'children',
    'customer_type', 'reserved_room_type', 'budget_level',
    'tourism_expenditures', 'gdp', 'inflation',
    'avg_tourist_spending', 'avg_room_price', 'tourism_revenue',
    'estimated_hotel_cost'  # Target variable
]

final_df = merged[final_features].copy()

# Rename target to match expected name
final_df = final_df.rename(columns={'estimated_hotel_cost': 'actual_trip_cost'})

# Remove any remaining rows with missing target
final_df = final_df[final_df['actual_trip_cost'].notna()]

print(f"Final dataset shape: {final_df.shape}")
print(f"\nFinal columns:")
for col in final_df.columns:
    print(f"  - {col}")

# ============================================================
# STEP 2.8: Save final dataset
# ============================================================
print("\n" + "="*70)
print("SAVING FINAL DATASET")
print("="*70)

output_path = os.path.join(data_dir, "real_budget_dataset.csv")
final_df.to_csv(output_path, index=False)

print(f"Saved to: {output_path}")
print(f"Total rows: {len(final_df)}")
print(f"Total columns: {len(final_df.columns)}")

print("\n" + "="*70)
print("DATASET BUILDING COMPLETE")
print("="*70)
print("\nTarget variable: actual_trip_cost (estimated hotel cost)")
print("Features: Hotel type, country, duration, travelers, economic indicators")
print("No synthetic data - all from real Kaggle datasets")
