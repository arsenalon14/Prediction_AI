import os
import csv
from collections import defaultdict
import numpy as np

def load_costs(filepath):
    costs = defaultdict(dict)
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['Code'].strip()
            if not code: continue
            
            for year in ['2024', '2025', '2026']:
                val = row.get(year, '').strip()
                if val:
                    try:
                        costs[code][year] = float(val)
                    except ValueError:
                        pass
    return costs

def parse_month(date_str):
    try:
        if '-' in date_str:
            return int(date_str.split('-')[1])
        elif '/' in date_str:
            return int(date_str.split('/')[1])
    except:
        pass
    return None

def process_year(year, wastage_files, sales_files, costs_dict):
    # month -> {'revenue': 0, 'cogs': 0, 'wastage_cost': 0, 'total_cost': 0}
    stats = defaultdict(lambda: {'revenue': 0, 'cogs': 0, 'wastage_cost': 0, 'total_cost': 0})
    
    # Process Wastage (for Total Loaded Cost)
    for wf in wastage_files:
        if not os.path.exists(wf): continue
        with open(wf, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    month = parse_month(row['flightdate'])
                    if not month: continue
                    code = row['prtnum'].strip()
                    
                    cost = costs_dict.get(code, {}).get(str(year))
                    if cost is None:
                        cost = costs_dict.get(code, {}).get('2025' if year==2026 else '2024')
                        
                    if cost is not None:
                        open_qty = float(row['open_quantity'])
                        stats[month]['total_cost'] += open_qty * cost
                except Exception as e:
                    continue
                    
    # Process Sales (for Revenue and COGS)
    for sf in sales_files:
        if not os.path.exists(sf): continue
        with open(sf, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    month = parse_month(row['flight_date'])
                    if not month: continue
                    code = row['product_code'].strip()
                    cat = row.get('product_category', row.get('new_product_category', '')).strip()
                    
                    cost = costs_dict.get(code, {}).get(str(year))
                    if cost is None:
                        cost = costs_dict.get(code, {}).get('2025' if year==2026 else '2024')
                        
                    if cost is not None or cat.lower() == 'perishable':
                        qty = float(row['quantity']) if row['quantity'] else 1.0
                        rev = float(row['net_sales_base']) if row['net_sales_base'] else 0.0
                        
                        stats[month]['revenue'] += rev
                        if cost is not None:
                            stats[month]['cogs'] += qty * cost
                except Exception as e:
                    continue
                    
    # Calculate True Wastage Cost for each month
    for month in stats:
        # True wastage is the food we loaded minus the food we sold
        true_wastage = stats[month]['total_cost'] - stats[month]['cogs']
        # Floor at 0 in case of minor accounting discrepancies
        stats[month]['wastage_cost'] = max(0, true_wastage)
        
    return stats

def main():
    base_dir = r"C:\Users\Chaiwatwannawit\Desktop\AI"
    costs_path = os.path.join(base_dir, "Cost Perishable.csv")
    costs_dict = load_costs(costs_path)
    
    # 2024
    w_24 = [os.path.join(base_dir, "Wastage-2024.csv")]
    s_24 = [os.path.join(base_dir, "SaleALL2024.csv")]
    stats_24 = process_year(2024, w_24, s_24, costs_dict)
    
    # 2025
    w_25 = [os.path.join(base_dir, "Wastage-2025.csv")]
    s_25 = [os.path.join(base_dir, "SaleALL2025.csv")]
    stats_25 = process_year(2025, w_25, s_25, costs_dict)
    
    # 2026
    w_26 = [
        os.path.join(base_dir, "Wastage-2026_Month1_4.csv"),
        os.path.join(base_dir, "Wastage-2026_Month5_24.csv")
    ]
    s_26 = [
        os.path.join(base_dir, "SaleALL2026_Month1_4.csv"),
        os.path.join(base_dir, "SaleALL2026_Month5_24.csv")
    ]
    stats_26 = process_year(2026, w_26, s_26, costs_dict)
    
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    print("=======================================================================================================")
    print("                      PERISHABLE FINANCIAL SUMMARY (2024 - 2026)                               ")
    print("=======================================================================================================")
    print(f"| Month | Metric | 2024 | 2025 | 2026 | YoY 24->25 | YoY 25->26 |")
    print(f"|-------|--------|------|------|------|------------|------------|")
    
    for m in range(1, 13):
        m_name = month_names[m][:3] # Short month name
        
        r24 = stats_24[m]['revenue']; c24 = stats_24[m]['cogs']; tc24 = stats_24[m]['total_cost']
        r25 = stats_25[m]['revenue']; c25 = stats_25[m]['cogs']; tc25 = stats_25[m]['total_cost']
        r26 = stats_26[m]['revenue']; c26 = stats_26[m]['cogs']; tc26 = stats_26[m]['total_cost']
        
        m24 = r24 - tc24
        m25 = r25 - tc25
        m26 = r26 - tc26
        
        if r24 == 0 and r25 == 0 and r26 == 0:
            continue
            
        def format_val(v): return f"{v:,.0f}" if v else "-"
        def format_pct(old, new): 
            if old == 0 and new == 0: return "-"
            if old == 0: return "N/A"
            return f"{(new-old)/old*100:+.1f}%"
            
        print(f"| **{m_name}** | **Total Revenue** | {format_val(r24)} | {format_val(r25)} | {format_val(r26)} | {format_pct(r24, r25)} | {format_pct(r25, r26)} |")
        print(f"| | **Total Cost** | {format_val(tc24)} | {format_val(tc25)} | {format_val(tc26)} | {format_pct(tc24, tc25)} | {format_pct(tc25, tc26)} |")
        print(f"| | **Net Margin** | {format_val(m24)} | {format_val(m25)} | {format_val(m26)} | {format_pct(m24, m25)} | {format_pct(m25, m26)} |")


if __name__ == '__main__':
    main()
