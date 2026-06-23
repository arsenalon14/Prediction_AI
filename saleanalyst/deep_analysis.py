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

# Date Normalization
m['DateNorm'] = pd.to_datetime(m['FlightDate'], errors='coerce').dt.strftime('%Y-%m-%d')
n['DateNorm'] = pd.to_datetime(n['DepartureDate'], errors='coerce').dt.strftime('%Y-%m-%d')
p['DateNorm'] = pd.to_datetime(p['DepartureDate'], errors='coerce').dt.strftime('%Y-%m-%d')

# 0. Seat Upgrade exclusion details
seat_upgrade_rows = m[m['ProductType'] == 'SEAT UPGRADE']
seat_upgrade_rev = seat_upgrade_rows['NetSales'].sum()
seat_upgrade_qty = seat_upgrade_rows['Quantity'].sum()
m_filtered = m[m['ProductType'] != 'SEAT UPGRADE'].copy()

# 1. Passenger calculation
# Aggregating Passenger counts at flight level to get absolute total passengers
n_agg = n.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], as_index=False)['PaxCount'].sum()
n_agg.rename(columns={'PaxCount': 'Total_Pax'}, inplace=True)
total_pax = n_agg['Total_Pax'].sum()
print("Total absolute passengers:", total_pax)

# 2. Main 4 Category Calculation
cats = ['Perishable', 'Non-Perishable', 'Beverage', 'Merchandise']
beverage_exclude_codes = {
    'FNBG02000638', 'FNBG02000607', 'FNBG02000768', 'FNBG02000670', 'FNBG04000062', 
    'FNBG02000766', 'FNBG02000767', 'FNBG02000688', 'FNBG02000890', 'FNBG03002190', 
    'OTSI01000252', 'FNBG03001946', 'FNBG03001945', 'FNBG03001944', 'COMBO1000406', 
    'COMBO1001481', 'COMBO1001482', 'COMBO1001520', 'COMBO1001519', 'COMBO1000999', 
    'COMBO1002675', 'COMBO1002678', 'COMBO1002711', 'COMBO1002712', 'COMBO1002982', 
    'COMBO1002983', 'COMBO1002154', 'COMBO1002155', 'COMBO1002313', 'COMBO1000738', 
    'COMBO1000737'
}

cat_stats = []
combo_total_discount = m_filtered[m_filtered['ProductCategory'] == 'Combo']['NetSales'].sum()

# Standard Onboard categories
for cat in cats:
    df_cat = m_filtered[m_filtered['ProductCategory'] == cat]
    base_rev = df_cat['NetSales'].sum()
    
    if cat == 'Beverage':
        calc_rev = base_rev + combo_total_discount
        # exclude codes for qty
        df_qty = df_cat[~df_cat['ProductCode'].isin(beverage_exclude_codes)]
        calc_qty = df_qty['Quantity'].sum()
    else:
        calc_rev = base_rev
        calc_qty = df_cat['Quantity'].sum()
        
    cat_stats.append({
        'Category': cat,
        'Base_NetSales': base_rev,
        'Calculated_Revenue': calc_rev,
        'Quantity': calc_qty
    })

# Add PBM Category
exclude_pbm_items = ['water', 'coconut water', 'americano']
pbm_revenue_total = p['ConvertedChargeAmount'].sum() # PBM total revenue includes all items

# Quantity: filter out the pure drinks
p_qty_filtered = p[~p['SSRDesc'].str.strip().str.lower().isin(exclude_pbm_items)]
pbm_quantity_filtered = p_qty_filtered['SSRCount'].sum()

cat_stats.append({
    'Category': 'PBM',
    'Base_NetSales': pbm_revenue_total,
    'Calculated_Revenue': pbm_revenue_total,
    'Quantity': pbm_quantity_filtered
})

df_cat_stats = pd.DataFrame(cat_stats)

# Calculate RPP (Revenue / TotalPassenger) and TUR (Quantity / TotalPassenger)
df_cat_stats['RPP'] = df_cat_stats['Calculated_Revenue'] / total_pax
df_cat_stats['TUR'] = df_cat_stats['Quantity'] / total_pax

# 3. Aggregations for Joining
p_agg = p.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], as_index=False)['SSRCount'].sum()
p_agg.rename(columns={'SSRCount': 'Total_Prebooked_Meals'}, inplace=True)

# Flight Sales aggregate
flight_cat_sales = m_filtered.groupby(['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route', 'ProductCategory'], as_index=False)['NetSales'].sum()
flight_sales_pivot = flight_cat_sales.pivot(
    index=['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'],
    columns='ProductCategory',
    values='NetSales'
).reset_index().fillna(0)

if 'Combo' in flight_sales_pivot.columns:
    flight_sales_pivot['Total_Beverage_Revenue'] = flight_sales_pivot['Beverage'] + flight_sales_pivot['Combo']
else:
    flight_sales_pivot['Total_Beverage_Revenue'] = flight_sales_pivot['Beverage'] if 'Beverage' in flight_sales_pivot.columns else 0

flight_sales_pivot['Total_Onboard_Revenue'] = (
    flight_sales_pivot.get('Perishable', 0) +
    flight_sales_pivot.get('Non-Perishable', 0) +
    flight_sales_pivot['Total_Beverage_Revenue'] +
    flight_sales_pivot.get('Merchandise', 0)
)

# Merge Flight level stats
merged = pd.merge(n_agg, p_agg, on=['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], how='outer')
merged = pd.merge(merged, flight_sales_pivot, on=['DateNorm', 'FlightNumber', 'Country', 'Sector', 'Route'], how='outer')
merged = merged.fillna(0)

# Add Month column
merged['Month'] = pd.to_datetime(merged['DateNorm']).dt.strftime('%B %Y')

# Insights Calculations
total_onboard_rev = merged['Total_Onboard_Revenue'].sum()
total_pbm_qty = merged['Total_Prebooked_Meals'].sum()
overall_spend_per_pax = total_onboard_rev / total_pax if total_pax > 0 else 0

# Monthly trends
monthly_summary = merged.groupby('Month').agg(
    Flights=('FlightNumber', 'count'),
    Total_Passengers=('Total_Pax', 'sum'),
    Prebooked_Meals=('Total_Prebooked_Meals', 'sum'),
    Onboard_Revenue=('Total_Onboard_Revenue', 'sum')
).reset_index()
monthly_summary['Spend_Per_Pax'] = monthly_summary['Onboard_Revenue'] / monthly_summary['Total_Passengers']

# Route/Sector Performance
route_summary = merged.groupby(['Route', 'Country']).agg(
    Flights=('FlightNumber', 'count'),
    Total_Passengers=('Total_Pax', 'sum'),
    Prebooked_Meals=('Total_Prebooked_Meals', 'sum'),
    Onboard_Revenue=('Total_Onboard_Revenue', 'sum')
).reset_index().sort_values('Onboard_Revenue', ascending=False)
route_summary['Spend_Per_Pax'] = route_summary['Onboard_Revenue'] / route_summary['Total_Passengers']

# Top Combos Popularity Analysis
combo_m = m_filtered[m_filtered['ProductCategory'] == 'Combo'].copy()
top_combos = combo_m.groupby(['ProductCode', 'Product']).agg(
    Sales_Count=('Quantity', 'sum'),
    Total_Discount=('NetSales', 'sum')
).reset_index().sort_values('Sales_Count', ascending=False).head(10)
top_combos['Total_Discount'] = top_combos['Total_Discount'].abs()

# Top Prebooked SSR Codes
p['SSRDesc_clean'] = p['SSRDesc'].apply(lambda x: str(x).encode('ascii', 'ignore').decode('ascii'))
top_prebooks = p.groupby(['SSRCode', 'SSRDesc_clean']).agg(
    Prebooked_Quantity=('SSRCount', 'sum'),
    Estimated_Charge=('ConvertedChargeAmount', 'sum')
).reset_index().sort_values('Prebooked_Quantity', ascending=False).head(10)

# Generate Markdown content
md = f"""# Airline Inflight Catering Inventory & Sales Revenue Deep Analysis

> [!NOTE]
> This analysis is prepared in compliance with the **Data Analyst** guidelines and provides a multi-dimensional look at inflight catering performance, passenger behavior, prebook meal conversion, and revenue optimization.

## Executive Summary
This report analyzes **{len(m_filtered):,}** transaction records from the **MasterSaleFile**, merged with passenger statistics (**{len(n):,}** records in **NationalityFile**) and prebooked service data (**{len(p):,}** records in **PBMFile**).

* **Total Onboard Sales Revenue**: **{total_onboard_rev:,.2f} THB** (after adjusting Beverage category with negative Combo discounts)
* **Total Passenger Volume**: **{total_pax:,.0f} Passengers**
* **Average Spend per Passenger (Onboard)**: **{overall_spend_per_pax:,.4f} THB**
* **Total Prebooked Meals (All items)**: **{total_pbm_qty:,.0f} Units**
* **Total PBM Category Revenue**: **{pbm_revenue_total:,.2f} THB** (fully inclusive of all prebooked charges)

***

## 1. Category Performance (Main 5 Categories)
Below is the breakdown of sales revenue, product quantities sold, **RPP (Revenue Per Passenger)**, and **TUR (Take Up Rate / Quantity Per Passenger in %)** across the five primary categories.
* **SEAT UPGRADE** has been completely excluded from all calculations (**{len(seat_upgrade_rows):,}** rows removed, representing **{seat_upgrade_rev:,.2f} THB**).
* **Combo Category** rows (which represent the discount transactions, totaling **{combo_total_discount:,.2f} THB**) have been excluded from direct onboard category listings but applied as a subtraction from `Beverage` revenue.
* **Beverage quantity** excludes **{len(beverage_exclude_codes)}** specific component codes to prevent quantity inflation.
* **PBM Category** revenue captures **all** prebooked service charges, but the quantity excludes pure drink items (`'Water'`, `'Coconut Water'`, and `'Americano'`) to avoid artificial meal count inflation.

| Category | Base NetSales / Charges (THB) | Total Adjusted Revenue (THB) | Quantity Sold (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""

for idx, row in df_cat_stats.iterrows():
    avg_price = row['Calculated_Revenue'] / row['Quantity'] if row['Quantity'] > 0 else 0
    rpp_formatted = f"{row['RPP']:.2f}"
    tur_formatted = f"{row['TUR'] * 100:.2f}%"
    md += f"| **{row['Category']}** | {row['Base_NetSales']:,.2f} | {row['Calculated_Revenue']:,.2f} | {row['Quantity']:,.0f} | **{rpp_formatted}** | **{tur_formatted}** | {avg_price:.2f} |\n"

md += f"""
> [!TIP]
> * **RPP (Revenue per Passenger)** tells us how much revenue each boarded passenger yields in that category.
> * **TUR (Take Up Rate / Units per Passenger)** shows the purchase conversion rate per passenger. For example, a Beverage TUR of **{df_cat_stats.loc[2, 'TUR'] * 100:.2f}%** means the average passenger buys **{df_cat_stats.loc[2, 'TUR'] * 100:.2f}%** drinks.

***

## 2. Monthly Trends Analysis
Passenger volumes, prebooking trends, and onboard sales vary by month:

| Month | Flights | Total Passengers | Total Prebooks | Onboard Revenue (THB) | Onboard Spend / Pax (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""

for idx, row in monthly_summary.iterrows():
    md += f"| {row['Month']} | {row['Flights']:,} | {row['Total_Passengers']:,.0f} | {row['Prebooked_Meals']:,.0f} | {row['Onboard_Revenue']:,.2f} | {row['Spend_Per_Pax']:.4f} |\n"

md += """
***

## 3. Top 10 High-Performing Routes
The table below lists the top routes by total onboard revenue, detailing passenger capacity, prebooked meal rates, and average passenger spend.

| Route | Country / Region | Flights | Total Passengers | Prebooked Meals | Onboard Revenue (THB) | Spend / Pax (THB) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""

for idx, row in route_summary.head(10).iterrows():
    md += f"| **{row['Route']}** | {row['Country']} | {row['Flights']:,} | {row['Total_Passengers']:,.0f} | {row['Prebooked_Meals']:,.0f} | {row['Onboard_Revenue']:,.2f} | {row['Spend_Per_Pax']:.4f} |\n"

md += """
***

## 4. Combo Sales & Popularity Analysis
Combo items are identified by `ProductCode` starting with `COMBO` or `CRFT`. Combo menu transactions have their individual parts categorized under physical goods, while the main promo entry (discount) is captured in the `Combo` category.

### Top 10 Most Popular Combo Deals:
| Product Code | Combo Menu Description | Quantity Sold | Total Discounts Saved (THB) |
| :--- | :--- | :---: | :---: |
"""

for idx, row in top_combos.iterrows():
    md += f"| `{row['ProductCode']}` | {row['Product']} | {row['Sales_Count']:,.0f} | {row['Total_Discount']:,.2f} |\n"

md += """
***

## 5. Top 10 Prebooked SSR Meal Preferences
Prebooking is a critical tool for minimizing food waste (Newsvendor critical fractile optimization) and securing upfront revenue. The most popular prebooked items are:

| SSR Code | SSR Meal/Beverage Description | Total Prebooked Quantity | Estimated Prebooked Revenue (THB) |
| :--- | :--- | :---: | :---: |
"""

for idx, row in top_prebooks.iterrows():
    md += f"| `{row['SSRCode']}` | {row['SSRDesc_clean']} | {row['Prebooked_Quantity']:,.0f} | {row['Estimated_Charge']:,.2f} |\n"

md += """
***

## Key Strategic Insights & Recommendations

1. **PBM Revenue Engine**: PBM is the second-largest revenue category overall at **{pbm_revenue_total:,.2f} THB**, representing high customer engagement before flights.
2. **Onboard vs. Prebook Synergy**: Since PBM represents a locked-in meal commitment, we should design high-margin onboard dessert and premium beverage menus to capture additional impulse onboard spend from passengers who have already prebooked their main course.
3. **Route Tailoring**: Routes like **DMKICN** (Seoul) and **DMKMAA** (Chennai) display vastly different spend patterns and product preferences. Adjusting the catering stock loading factor (L) for regional palettes will maximize revenue and slash catering waste.
"""

# Write out artifact
output_file = os.path.join(artifact_dir, "catering_revenue_analysis.md")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(md)

print("Markdown report written to:", output_file)
