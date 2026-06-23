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

# Unique Routes
routes = n['Route'].dropna().unique()
print(f"Analyzing {len(routes)} routes...")

route_reports = []

for route in routes:
    # 1. Route specific passenger count
    n_route = n[n['Route'] == route]
    n_agg_r = n_route.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], as_index=False)['PaxCount'].sum()
    route_pax = n_agg_r['PaxCount'].sum()
    
    if route_pax == 0:
        continue
        
    # Get country/region for this route
    route_countries = n_route['Country'].dropna().unique()
    country_label = route_countries[0] if len(route_countries) > 0 else "Unknown"
    
    # 2. Onboard sales
    m_r = m_filtered[m_filtered['Route'] == route]
    
    # 3. PBM sales
    p_r = p[p['Route'] == route]
    
    # Standard Categories stats
    cats = ['Perishable', 'Non-Perishable', 'Beverage', 'Merchandise']
    combo_total_discount = m_r[m_r['ProductCategory'] == 'Combo']['NetSales'].sum()
    
    cat_rows = []
    for cat in cats:
        df_cat = m_r[m_r['ProductCategory'] == cat]
        base_rev = df_cat['NetSales'].sum()
        
        if cat == 'Beverage':
            calc_rev = base_rev + combo_total_discount
            df_qty = df_cat[~df_cat['ProductCode'].isin(beverage_exclude_codes)]
            calc_qty = df_qty['Quantity'].sum()
        else:
            calc_rev = base_rev
            calc_qty = df_cat['Quantity'].sum()
            
        rpp = calc_rev / route_pax
        tur = calc_qty / route_pax
        
        cat_rows.append({
            'Route': route,
            'Country': country_label,
            'Category': cat,
            'Revenue': calc_rev,
            'Quantity': calc_qty,
            'RPP': rpp,
            'TUR': tur
        })
        
    # PBM Category for this route
    pbm_rev = p_r['ConvertedChargeAmount'].sum()
    p_qty_filtered = p_r[~p_r['SSRDesc'].str.strip().str.lower().isin(exclude_pbm_items)]
    pbm_qty = p_qty_filtered['SSRCount'].sum()
    
    pbm_rpp = pbm_rev / route_pax
    pbm_tur = pbm_qty / route_pax
    
    cat_rows.append({
        'Route': route,
        'Country': country_label,
        'Category': 'PBM',
        'Revenue': pbm_rev,
        'Quantity': pbm_qty,
        'RPP': pbm_rpp,
        'TUR': pbm_tur
    })
    
    route_reports.extend(cat_rows)

df_route_all = pd.DataFrame(route_reports)

# Export all 81 routes to CSV
csv_out_path = r"C:\Users\Chaiwatwannawit\Desktop\Sale\Route_Level_Performance.csv"
df_route_all.to_csv(csv_out_path, index=False)
print("Complete route performance database written to:", csv_out_path)

# Let's find Top 15 routes by Total Adjusted Revenue to present in the report
route_total_revs = df_route_all.groupby(['Route', 'Country'])['Revenue'].sum().reset_index()
top_15_routes = route_total_revs.sort_values('Revenue', ascending=False).head(15)['Route'].tolist()

# Let's generate a stunning Route-level breakdown in markdown
md_route = """
***

## 7. Route-Level Performance Analysis (Top 15 Routes)
The table below details the performance of our Top 15 highest-revenue flight routes. The complete performance database for all 81 routes has been successfully calculated and exported to:
👉 [Route_Level_Performance.csv](file:///C:/Users/Chaiwatwannawit/Desktop/Sale/Route_Level_Performance.csv)
"""

for route in top_15_routes:
    df_r = df_route_all[df_route_all['Route'] == route]
    c_pax = n[n['Route'] == route].groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'])['PaxCount'].sum().sum()
    country_lbl = df_r.iloc[0]['Country']
    
    md_route += f"""
### ✈️ Route {route} ({country_lbl} | Total Passengers: {c_pax:,.0f})
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for idx, row in df_r.iterrows():
        avg_price = row['Revenue'] / row['Quantity'] if row['Quantity'] > 0 else 0
        rpp_formatted = f"{row['RPP']:.2f}"
        tur_formatted = f"{row['TUR'] * 100:.2f}%"
        md_route += f"| **{row['Category']}** | {row['Revenue']:,.2f} | {row['Quantity']:,.0f} | **{rpp_formatted}** | **{tur_formatted}** | {avg_price:.2f} |\n"

# Append Route-level analysis to catering_revenue_analysis.md
report_file = os.path.join(artifact_dir, "catering_revenue_analysis.md")
with open(report_file, 'r', encoding='utf-8') as f:
    orig_md = f.read()

# Find the end of Key Strategic Insights & Recommendations or just append
if "## 7. Route-Level Performance Analysis (Top 15 Routes)" in orig_md:
    # already there, let's truncate to clean it up first
    orig_md = orig_md.split("## 7. Route-Level Performance Analysis (Top 15 Routes)")[0]

updated_md = orig_md.strip() + "\n" + md_route

with open(report_file, 'w', encoding='utf-8') as f:
    f.write(updated_md)

print("Route analysis calculated and successfully appended to catering_revenue_analysis.md")
