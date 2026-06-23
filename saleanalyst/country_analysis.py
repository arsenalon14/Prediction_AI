import pandas as pd
import numpy as np
import os

# Paths
master_path = r"C:\Users\Chaiwatwannawit\Desktop\MasterSaleFileDate2026-06-01_Time14.08.41.csv"
nat_path = r"C:\Users\Chaiwatwannawit\Desktop\NationalityFileDate2026-06-01_Time14.15.32.csv"
pbm_path = r"C:\Users\Chaiwatwannawit\Desktop\PBMDate2026-06-01_Time14.22.38.csv"
artifact_dir = r"C:\Users\Chaiwatwannawit\.gemini\antigravity-cli\brain\494b943c-78ad-4f88-b258-a17c823b8f5b"

# Load Data
print("Loading data...")
m = pd.read_csv(master_path, encoding='latin1')
n = pd.read_csv(nat_path, encoding='latin1')
p = pd.read_csv(pbm_path, encoding='latin1')

# Normalize Date strings
m['DateNorm'] = pd.to_datetime(m['FlightDate'], errors='coerce').dt.strftime('%Y-%m-%d')
n['DateNorm'] = pd.to_datetime(n['DepartureDate'], errors='coerce').dt.strftime('%Y-%m-%d')
p['DateNorm'] = pd.to_datetime(p['DepartureDate'], errors='coerce').dt.strftime('%Y-%m-%d')

# Filter out SEAT UPGRADE
m_filtered = m[m['ProductType'] != 'SEAT UPGRADE'].copy()

# Exclusions
beverage_exclude_codes = {
    'FNBG02000638', 'FNBG02000607', 'FNBG02000768', 'FNBG02000670', 'FNBG04000062', 
    'FNBG02000766', 'FNBG02000767', 'FNBG02000688', 'FNBG02000890', 'FNBG03002190', 
    'OTSI01000252', 'FNBG03001946', 'FNBG03001945', 'FNBG03001944', 'COMBO1000406', 
    'COMBO1001481', 'COMBO1001482', 'COMBO1001520', 'COMBO1001519', 'COMBO1000999', 
    'COMBO1002675', 'COMBO1002678', 'COMBO1002711', 'COMBO1002712', 'COMBO1002982', 
    'COMBO1002983', 'COMBO1002154', 'COMBO1002155', 'COMBO1002313', 'COMBO1000738', 
    'COMBO1000737'
}
exclude_pbm_items = ['water', 'coconut water', 'americano']

# Unique Countries from Nationality File (the primary passenger driver)
countries = n['Country'].dropna().unique()
print(f"Analyzing {len(countries)} countries: {countries}")

country_reports = []

for country in countries:
    # 1. Country specific passenger count
    n_country = n[n['Country'] == country]
    n_agg_c = n_country.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], as_index=False)['PaxCount'].sum()
    country_pax = n_agg_c['PaxCount'].sum()
    
    if country_pax == 0:
        continue # skip countries with zero passenger data
        
    # 2. Onboard sales for this country
    m_c = m_filtered[m_filtered['Country'] == country]
    
    # 3. PBM sales for this country
    p_c = p[p['Country'] == country]
    
    # Standard Categories stats
    cats = ['Perishable', 'Non-Perishable', 'Beverage', 'Merchandise']
    combo_total_discount = m_c[m_c['ProductCategory'] == 'Combo']['NetSales'].sum()
    
    cat_rows = []
    for cat in cats:
        df_cat = m_c[m_c['ProductCategory'] == cat]
        base_rev = df_cat['NetSales'].sum()
        
        if cat == 'Beverage':
            calc_rev = base_rev + combo_total_discount
            df_qty = df_cat[~df_cat['ProductCode'].isin(beverage_exclude_codes)]
            calc_qty = df_qty['Quantity'].sum()
        else:
            calc_rev = base_rev
            calc_qty = df_cat['Quantity'].sum()
            
        rpp = calc_rev / country_pax
        tur = calc_qty / country_pax
        
        cat_rows.append({
            'Country': country,
            'Category': cat,
            'Revenue': calc_rev,
            'Quantity': calc_qty,
            'RPP': rpp,
            'TUR': tur
        })
        
    # PBM Category for this country
    pbm_rev = p_c['ConvertedChargeAmount'].sum()
    p_qty_filtered = p_c[~p_c['SSRDesc'].str.strip().str.lower().isin(exclude_pbm_items)]
    pbm_qty = p_qty_filtered['SSRCount'].sum()
    
    pbm_rpp = pbm_rev / country_pax
    pbm_tur = pbm_qty / country_pax
    
    cat_rows.append({
        'Country': country,
        'Category': 'PBM',
        'Revenue': pbm_rev,
        'Quantity': pbm_qty,
        'RPP': pbm_rpp,
        'TUR': pbm_tur
    })
    
    country_reports.extend(cat_rows)

df_country_all = pd.DataFrame(country_reports)

# Let's generate a stunning country-level breakdown in markdown
md_country = """
***

## 6. Country-Level Performance Analysis
The table below details category performance grouped by target Country. This helps identify regional taste profiles, prebooking behaviors, and onboard spend variances.
"""

for country in sorted(countries):
    df_c = df_country_all[df_country_all['Country'] == country]
    if len(df_c) == 0:
        continue
    
    # Let's calculate total country passenger count from Nationality file
    c_pax = n[n['Country'] == country].groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'])['PaxCount'].sum().sum()
    
    md_country += f"""
### 📍 {country} (Total Passengers: {c_pax:,.0f})
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for idx, row in df_c.iterrows():
        avg_price = row['Revenue'] / row['Quantity'] if row['Quantity'] > 0 else 0
        rpp_formatted = f"{row['RPP']:.2f}"
        tur_formatted = f"{row['TUR'] * 100:.2f}%"
        md_country += f"| **{row['Category']}** | {row['Revenue']:,.2f} | {row['Quantity']:,.0f} | **{rpp_formatted}** | **{tur_formatted}** | {avg_price:.2f} |\n"

# Append country-level analysis to catering_revenue_analysis.md
report_file = os.path.join(artifact_dir, "catering_revenue_analysis.md")
with open(report_file, 'r', encoding='utf-8') as f:
    orig_md = f.read()

# Find the end of Key Strategic Insights & Recommendations or just append
if "## 6. Country-Level Performance Analysis" in orig_md:
    # already there, let's truncate to clean it up first
    orig_md = orig_md.split("## 6. Country-Level Performance Analysis")[0]

updated_md = orig_md.strip() + "\n" + md_country

with open(report_file, 'w', encoding='utf-8') as f:
    f.write(updated_md)

print("Country analysis calculated and successfully appended to catering_revenue_analysis.md")
