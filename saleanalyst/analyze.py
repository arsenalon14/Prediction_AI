import pandas as pd
import numpy as np

# Load files
print("Loading files...")
master_path = r"C:\Users\Chaiwatwannawit\Desktop\MasterSaleFileDate2026-06-01_Time14.08.41.csv"
nat_path = r"C:\Users\Chaiwatwannawit\Desktop\NationalityFileDate2026-06-01_Time14.15.32.csv"
pbm_path = r"C:\Users\Chaiwatwannawit\Desktop\PBMDate2026-06-01_Time14.22.38.csv"

m = pd.read_csv(master_path, encoding='latin1')
n = pd.read_csv(nat_path, encoding='latin1')
p = pd.read_csv(pbm_path, encoding='latin1')

print("Loaded shapes:")
print("Master:", m.shape)
print("Nationality:", n.shape)
print("PBM:", p.shape)

# Normalize flight number and dates
def normalize_date(df, col):
    df[col] = pd.to_datetime(df[col], errors='coerce')
    # Convert to yyyy-mm-dd string
    return df[col].dt.strftime('%Y-%m-%d')

m['DateNorm'] = normalize_date(m, 'FlightDate')
n['DateNorm'] = normalize_date(n, 'DepartureDate')
p['DateNorm'] = normalize_date(p, 'DepartureDate')

# Check SEAT UPGRADE filter
print("Total rows before SEAT UPGRADE filter:", len(m))
m = m[m['ProductType'] != 'SEAT UPGRADE']
print("Total rows after SEAT UPGRADE filter:", len(m))

# Aggregating Nationality data
# Join keys: DateNorm, FlightNumber, Country, Sector, Route
n_agg = n.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], as_index=False)['PaxCount'].sum()
n_agg.rename(columns={'PaxCount': 'Total_Pax'}, inplace=True)

# Aggregating PBM data
p_agg = p.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], as_index=False)['SSRCount'].sum()
p_agg.rename(columns={'SSRCount': 'Total_Prebooked_Meals'}, inplace=True)

print("Aggregated Nationality shape:", n_agg.shape)
print("Aggregated PBM shape:", p_agg.shape)

# Main 4 category Revenue & Quantity Calculation (excluding Combo category)
cats = ['Perishable', 'Non-Perishable', 'Beverage', 'Merchandise']
m_cats = m[m['ProductCategory'].isin(cats)].copy()

# For Beverage quantity, we exclude a list of specific codes
beverage_exclude_codes = {
    'FNBG02000638', 'FNBG02000607', 'FNBG02000768', 'FNBG02000670', 'FNBG04000062', 
    'FNBG02000766', 'FNBG02000767', 'FNBG02000688', 'FNBG02000890', 'FNBG03002190', 
    'OTSI01000252', 'FNBG03001946', 'FNBG03001945', 'FNBG03001944', 'COMBO1000406', 
    'COMBO1001481', 'COMBO1001482', 'COMBO1001520', 'COMBO1001519', 'COMBO1000999', 
    'COMBO1002675', 'COMBO1002678', 'COMBO1002711', 'COMBO1002712', 'COMBO1002982', 
    'COMBO1002983', 'COMBO1002154', 'COMBO1002155', 'COMBO1002313', 'COMBO1000738', 
    'COMBO1000737'
}

# Calculate basic category sales and quantities
cat_stats = []
for cat in cats:
    df_cat = m_cats[m_cats['ProductCategory'] == cat]
    rev = df_cat['NetSales'].sum()
    
    if cat == 'Beverage':
        # Apply special trick for Beverage: Revenue = NetSales(Beverage) + NetSales(Combo)
        combo_rev = m[m['ProductCategory'] == 'Combo']['NetSales'].sum()
        total_rev = rev + combo_rev
        
        # Quantity calculation: exclude specific codes
        df_qty = df_cat[~df_cat['ProductCode'].isin(beverage_exclude_codes)]
        total_qty = df_qty['Quantity'].sum()
    else:
        total_rev = rev
        total_qty = df_cat['Quantity'].sum()
        
    cat_stats.append({
        'Category': cat,
        'Base_NetSales': rev,
        'Calculated_Revenue': total_rev,
        'Quantity': total_qty
    })

df_cat_stats = pd.DataFrame(cat_stats)
print("\n=== Main 4 Categories Summary ===")
print(df_cat_stats)

# Combo Analysis
print("\n=== Combo Analysis ===")
# Look at ProductCodes starting with COMBO or CRFT
combo_codes = m[m['ProductCode'].str.startswith(('COMBO', 'CRFT'), na=False)]
print("Total rows starting with COMBO or CRFT:", len(combo_codes))
print("ProductCategories represented in COMBO/CRFT codes:")
print(combo_codes.groupby('ProductCategory').size())

# Join Flight-level data
print("\n=== Joining Flight-level data ===")
# Let's get flight-level sales
flight_sales = m.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], as_index=False).agg(
    Total_NetSales=('NetSales', 'sum'),
    Total_Quantity=('Quantity', 'sum')
)
print("Unique flights in Sales:", len(flight_sales))

# Merge
merged = pd.merge(flight_sales, n_agg, on=['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], how='outer')
merged = pd.merge(merged, p_agg, on=['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], how='outer')

print("Merged shape:", merged.shape)
print("Missing Passenger count:", merged['Total_Pax'].isna().sum())
print("Missing Prebooked Meals:", merged['Total_Prebooked_Meals'].isna().sum())
print("Missing Sales:", merged['Total_NetSales'].isna().sum())

# Export summaries
print("\nWriting out temp file...")
merged.to_csv(r"C:\Users\Chaiwatwannawit\Desktop\Sale\merged_insights.csv", index=False)
print("Done!")
