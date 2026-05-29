import os
import csv
import sys
from collections import defaultdict

# Configure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

# Price catalog previously resolved
PRICES = {
    'FNBG03002004': 180.0, # 8 TREASURE RICE BOWL
    'FNBG03001774': 150.0, # MALA HOTPOT NOODLES
    'FNBG03000041': 150.0, # ML NOI FRIED CHICKEN WITH BASIL ON RICE
    'FNBG03000025': 150.0, # UNCLE CHIN CHICKEN RICE
    'FNBG03002061': 150.0, # PALMYRA GRILLED CHICKEN, STICKY RICE AND SOMTAM
    'FNBG03000027': 150.0, # Chicken Teriyaki with Rice
    'FNBG03001857': 150.0, # FRIED FISH FILLET WITH SWEET CHILLI SAUCE AND RICE
    'FNBG03001880': 150.0, # GRILLED MACKEREL WITH JAPANESE SAUCE AND RICE
    'FNBG03002154': 150.0, # KHAO SOI GAI
    'FNBG03002153': 150.0, # LANNA KHAN TOK
    'FNBG03000085': 150.0, # Nasi Lemak
    'FNBG03001956': 149.0, # GREEN CURRY CHICKEN WITH RICE AND SALTED EGG
    'FNBG03000077': 120.0, # THAI MANGO STICKY RICE.
    'FNBG03001926': 120.0, # AMERICAN FRIED RICE & KIDS' FRIED RICE
    'FNBG03002005': 120.0, # BAKED MAC DOUBLE CHEESE
    'FNBG03001931': 120.0, # BASIL CHICKEN FRIED RICE
    'FNBG03001959': 120.0, # CHICKEN CHEESE HAMBURG SANDWICH
    'FNBG02000820': 120.0, # JAPANESE MATCHA LATTE
    'FNBG03002102': 120.0, # KUA KLING KAI WITH SUNNY SALTED EGG
    'FNBG03001928': 120.0, # NAPOLETANA STYLE MUSHROOM TRUFFLE PIZZA
    'FNBG03002006': 120.0, # PIZZA OVAL CHICKEN SLICE & MUSHROOM
    'FNBG03001397': 120.0, # SHOKUPAN CHICKEN & CHEESE SANDWICH
    'FNBG02000276': 100.0, # Boba Thai Milk Tea
    'FNBG02000218': 100.0, # BOBA MILK TEA
    'FNBG02000579': 100.0, # FRESH CALAMANSI JUICE
    'FNBG02000605': 100.0, # FRESH LONGAN JUICE
    'FNBG02000860': 100.0, # O-AEW FRESH LONGAN JUICE
    'FNBG03002010': 100.0, # THE OG BURNT CHEESECAKE
    'FNBG03002180': 100.0, # TUNA CORN & EBIKO KANIKAMA SANDWICH
    'FNBG02000888': 100.0, # PINEAPPLE PRIK KLUA JUICE
    'FNBG02000665': 100.0, # YUZU LEMON ROOIBOS TEA
    'FNBG03002158': 90.0,  # PHULAE PINEAPPLE CHEESECAKE
    'FNBG03001925': 80.0,  # KAO TOM MUD (BANANA NUTELLA STICKY RICE)
    'FNBG03001775': 60.0,  # BOBA MILK TEA PUDDING
    'FNBG03001776': 60.0,  # BOBA THAI MILK TEA PUDDING
    'FNBG03000519': 180.0, # Pad Thai with Egg Wrap
    'FNBG03002104': 180.0, # SOUTHERN YELLOW CURRY SEAFOOD
    'FNBG03002108': 100.0, # DIT SNACK BOX
}

def load_cogs():
    """Loads COGS from Cost Perishable.csv for different years."""
    cogs = defaultdict(lambda: {'2024': None, '2025': None, '2026': None})
    cost_file = r"C:\Users\Chaiwatwannawit\Desktop\AI\Cost Perishable.csv"
    
    if not os.path.exists(cost_file):
        print("Error: Cost file not found.")
        return cogs
        
    with open(cost_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['Code'].strip()
            
            c24 = row['2024'].strip()
            c25 = row['2025'].strip()
            c26 = row['2026'].strip()
            
            cogs[code]['2024'] = float(c24) if c24 else None
            cogs[code]['2025'] = float(c25) if c25 else None
            cogs[code]['2026'] = float(c26) if c26 else None
            
    return cogs

def process_historical_perishables():
    print("Step 1: Loading COGS lookup table...")
    cogs_lookup = load_cogs()
    
    # Files to process
    wastage_files = [
        # 2024
        (r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2024.csv", "2024"),
        # 2025
        (r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2025.csv", "2025"),
        # 2026 Months 1-4
        (r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2026_Month1_4.csv", "2026"),
        # 2026 Month 5 (to May 24)
        (r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2026_Month5_24.csv", "2026")
    ]
    
    output_rows = []
    
    print("\nStep 2: Processing and merging wastage logs with financial lookup...")
    
    # 2026 statistics tracker
    monthly_2026_stats = defaultdict(lambda: {
        'loaded': 0,
        'sold': 0,
        'wasted': 0,
        'stockouts': 0,
        'records': 0
    })
    
    for file_path, year in wastage_files:
        if not os.path.exists(file_path):
            print(f"Warning: File not found {file_path}")
            continue
            
        print(f"Processing: {os.path.basename(file_path)}...")
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = row['flightdate'].strip()
                    flight = row['flightno'].strip()
                    code = row['prtnum'].strip()
                    name = row['product_name'].strip()
                    
                    open_q = int(row['open_quantity'].strip())
                    sale_q = int(row['sale_quantity'].strip())
                    waste = int(row['wastage'].strip())
                    
                    if open_q <= 0:
                        continue
                        
                    # Financial lookup
                    price = PRICES.get(code, 150.0) # default hot meal price if not found
                    cogs_years = cogs_lookup.get(code, {'2024': None, '2025': None, '2026': None})
                    cost = cogs_years.get(year, None)
                    
                    # Fallback cost if missing for that specific year (use another year's cost)
                    if cost is None:
                        cost = cogs_years['2025'] or cogs_years['2024'] or cogs_years['2026'] or (price * 0.4) # default to 40% margin
                        
                    is_stockout = 1 if sale_q >= open_q else 0
                    
                    # Store row
                    output_rows.append({
                        'FlightDate': date,
                        'Year': year,
                        'FlightNumber': flight,
                        'ProductCode': code,
                        'ProductName': name,
                        'LoadedQty': open_q,
                        'SoldQty': sale_q,
                        'WastedQty': waste,
                        'StockoutFlag': is_stockout,
                        'Price': price,
                        'Cost': cost,
                        'NetSales': sale_q * price,
                        'COGS': open_q * cost,
                        'CriticalRatio': (price - cost) / price if price > 0 else 0.0
                    })
                    
                    # Track 2026 specifically
                    if year == "2026":
                        month = int(date.split('-')[1])
                        monthly_2026_stats[month]['loaded'] += open_q
                        monthly_2026_stats[month]['sold'] += sale_q
                        monthly_2026_stats[month]['wasted'] += waste
                        monthly_2026_stats[month]['stockouts'] += is_stockout
                        monthly_2026_stats[month]['records'] += 1
                        
                except Exception as e:
                    continue

    # Write merged dataset to a single file in the AGY folder
    output_file = r"C:\Users\Chaiwatwannawit\Desktop\AGY\perishable_historical_data.csv"
    print(f"\nStep 3: Exporting combined Perishable database to: {output_file}...")
    
    headers = [
        'FlightDate', 'Year', 'FlightNumber', 'ProductCode', 'ProductName',
        'LoadedQty', 'SoldQty', 'WastedQty', 'StockoutFlag', 'Price', 'Cost',
        'NetSales', 'COGS', 'CriticalRatio'
    ]
    
    with open(output_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output_rows)
        
    print(f"Successfully exported {len(output_rows)} records.")
    
    # 4. Print 2026 Injected Performance Summary
    print("\n" + "="*80)
    print("INJECTED 2026 PERISHABLES PERFORMANCE REPORT (JAN - MAY 24)")
    print("="*80)
    for month in sorted(monthly_2026_stats.keys()):
        stats = monthly_2026_stats[month]
        loaded = stats['loaded']
        sold = stats['sold']
        waste = stats['wasted']
        stockouts = stats['stockouts']
        records = stats['records']
        
        sell_through = (sold / loaded * 100) if loaded > 0 else 0.0
        stockout_rate = (stockouts / records * 100) if records > 0 else 0.0
        
        month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May (1-24)'}
        name = month_names.get(month, f"Month {month:02d}")
        
        print(f"  * {name:<12}: Loaded: {loaded:<5} | Sold: {sold:<5} | Wasted: {waste:<5} | Sell-Through: {sell_through:.1f}% | Stockout Rate: {stockout_rate:.1f}%")

if __name__ == "__main__":
    process_historical_perishables()
