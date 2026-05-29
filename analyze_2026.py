import os
import csv
import sys
from collections import Counter, defaultdict

# Configure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

# Price catalog for Perishable products
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

def load_passenger_manifest():
    pax_file = r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    passenger_lookup = {}
    
    # Track monthly demographics
    monthly_pax = defaultdict(lambda: {
        'total': 0,
        'f175': 0,
        'f176': 0,
        'ages': [],
        'nationalities': []
    })
    
    with open(pax_file, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return passenger_lookup, monthly_pax
            
        headers = [h.strip() for h in headers]
        
        # Determine indexes of columns dynamically
        date_idx, flight_idx, age_idx, seat_idx, gender_idx, nat_idx = -1, -1, -1, -1, -1, -1
        
        for idx, h in enumerate(headers):
            h_clean = h.lower()
            if h_clean in ('flightdate', 'date', 'flight_date'):
                date_idx = idx
            elif h_clean in ('flightnumber', 'flight', 'flightnum', 'flightno'):
                flight_idx = idx
            elif h_clean in ('paxage', 'age'):
                age_idx = idx
            elif h_clean in ('unitdesignator', 'seat', 'seat_number'):
                seat_idx = idx
            elif h_clean == 'gender':
                gender_idx = idx
            elif h_clean in ('country_name', 'nationality', 'country'):
                nat_idx = idx
                
        # Robust fallbacks in case headers are completely custom or column names are not matched
        if date_idx == -1: date_idx = 0  # In column A is DATE Field
        if flight_idx == -1: flight_idx = 1
        if age_idx == -1: age_idx = 2
        if seat_idx == -1: seat_idx = 3
        if gender_idx == -1: gender_idx = 4
        if nat_idx == -1: nat_idx = 5
        
        for row_num, row in enumerate(reader, start=2):
            if not row:
                continue
            # Ensure the row has enough elements for all matched indexes
            max_idx = max(date_idx, flight_idx, age_idx, seat_idx, gender_idx, nat_idx)
            if len(row) <= max_idx:
                continue
                
            try:
                date = row[date_idx].strip()
                flight = row[flight_idx].strip()
                seat = row[seat_idx].strip()
                
                # Parse month robustly from DATE Field
                parts = date.split('-')
                if len(parts) >= 2:
                    # e.g., YYYY-MM-DD
                    if len(parts[0]) == 4:
                        month = int(parts[1])
                    else:
                        # e.g., DD-MM-YYYY
                        month = int(parts[1])
                else:
                    parts = date.split('/')
                    if len(parts) >= 2:
                        # e.g., DD/MM/YYYY or YYYY/MM/DD
                        if len(parts[0]) == 4:
                            month = int(parts[1])
                        else:
                            month = int(parts[1])
                    else:
                        continue
                
                age_str = row[age_idx].strip()
                age = int(age_str) if age_str.isdigit() else None
                
                gender = row[gender_idx].strip()
                nationality = row[nat_idx].strip()
                
                # Monthly aggregation
                monthly_pax[month]['total'] += 1
                if flight == '175':
                    monthly_pax[month]['f175'] += 1
                elif flight == '176':
                    monthly_pax[month]['f176'] += 1
                    
                if age is not None:
                    monthly_pax[month]['ages'].append(age)
                if nationality:
                    monthly_pax[month]['nationalities'].append(nationality)
                
                # Lookup key
                if seat:
                    key = (date, flight, seat)
                    passenger_lookup[key] = {
                        'age': age,
                        'gender': gender,
                        'nationality': nationality
                    }
            except Exception as e:
                continue
                
    return passenger_lookup, monthly_pax


def analyze_2026_demographics():
    print("\n" + "="*80)
    print("PART 1: MONTHLY 2026 PASSENGER DEMOGRAPHICS (JAN - MAY 24)")
    print("="*80)
    
    passenger_lookup, monthly_pax = load_passenger_manifest()
    
    for month in sorted(monthly_pax.keys()):
        data = monthly_pax[month]
        total = data['total']
        f175 = data['f175']
        f176 = data['f176']
        ages = data['ages']
        nats = data['nationalities']
        
        avg_age = sum(ages) / len(ages) if ages else 0
        median_age = sorted(ages)[len(ages)//2] if ages else 0
        
        kids = sum(1 for a in ages if a <= 12)
        youths = sum(1 for a in ages if 13 <= a <= 25)
        adults = sum(1 for a in ages if 26 <= a <= 50)
        seniors = sum(1 for a in ages if a >= 51)
        
        nat_counts = Counter(nats)
        top_nats = nat_counts.most_common(5)
        top_nats_str = ", ".join([f"{nat}: {count} ({count/len(nats)*100:.1f}%)" for nat, count in top_nats])
        
        month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May (1-24)'}
        name = month_names.get(month, f"Month {month:02d}")
        
        print(f"\n* {name} 2026 Boarded Passengers:")
        print(f"  - Total Boarded Pax: {total} (FD175: {f175}, FD176: {f176})")
        print(f"  - Age Profile: Mean = {avg_age:.1f} years | Median = {median_age} years")
        print(f"    - Kids (0-12): {kids} ({kids/len(ages)*100:.1f}%) | Youths (13-25): {youths} ({youths/len(ages)*100:.1f}%)")
        print(f"    - Adults (26-50): {adults} ({adults/len(ages)*100:.1f}%) | Seniors (51+): {seniors} ({seniors/len(ages)*100:.1f}%)")
        print(f"  - Top Nationalities: {top_nats_str}")
        
    return passenger_lookup

def analyze_2026_pbm():
    print("\n" + "="*80)
    print("PART 2: PRE-BOOKED MEAL (PBM) DEVELOPMENT (JAN - MAY 24)")
    print("  *(EXCLUDING WATER BOTTLES: BWFD, BWAK, BWHL, WBHL)*")
    print("="*80)
    
    exclude_ssrs = {'BWFD', 'BWAK', 'BWHL', 'WBHL'}
    pbm_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2026_Month5_24.csv"
    ]
    
    monthly_data = defaultdict(lambda: {
        'total_pbm': 0,
        'f175_pbm': 0,
        'f176_pbm': 0,
        'ssrs': [],
        'nationalities': []
    })
    
    for file_path in pbm_files:
        if not os.path.exists(file_path):
            continue
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ssr = row['SSRCode'].strip()
                    if ssr in exclude_ssrs:
                        continue
                        
                    date_str = row['FlightDate'].strip()
                    month = int(date_str.split('-')[1])
                    flight = row['Flight'].strip()
                    nationality = row['Country_name'].strip()
                    
                    monthly_data[month]['total_pbm'] += 1
                    if flight == '175':
                        monthly_data[month]['f175_pbm'] += 1
                    elif flight == '176':
                        monthly_data[month]['f176_pbm'] += 1
                        
                    monthly_data[month]['ssrs'].append(ssr)
                    if nationality:
                        monthly_data[month]['nationalities'].append(nationality)
                except Exception as e:
                    continue
                    
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        total = data['total_pbm']
        f175 = data['f175_pbm']
        f176 = data['f176_pbm']
        ssrs = data['ssrs']
        nats = data['nationalities']
        
        ssr_counts = Counter(ssrs)
        top_ssrs = ssr_counts.most_common(3)
        top_ssrs_str = ", ".join([f"{code}: {count} ({count/total*100:.1f}%)" for code, count in top_ssrs])
        
        nat_counts = Counter(nats)
        top_nats = nat_counts.most_common(3)
        top_nats_str = ", ".join([f"{nat}: {count} ({count/total*100:.1f}%)" for nat, count in top_nats])
        
        month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May (1-24)'}
        name = month_names.get(month, f"Month {month:02d}")
        
        print(f"\n* {name} 2026 Perishable PBM:")
        print(f"  - Total Perishable Orders: {total} (FD175: {f175}, FD176: {f176})")
        print(f"  - Top SSR Meal Codes: {top_ssrs_str}")
        print(f"  - Top Nationalities Ordering PBM: {top_nats_str}")

def analyze_2026_sales_demographics(passenger_lookup):
    print("\n" + "="*80)
    print("PART 3: IN-FLIGHT BOB SALES DEMOGRAPHIC MATCHING (JAN - MAY 24)")
    print("="*80)
    
    sales_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month5_24.csv"
    ]
    
    total_sales = 0
    matched_sales = 0
    
    buyer_nationalities = Counter()
    buyer_ages = []
    
    # Product sales per nationality and category
    nat_product_sales = defaultdict(lambda: Counter())
    category_revenue = defaultdict(float)
    product_revenue = defaultdict(float)
    products = Counter()
    categories = Counter()
    
    # Perishable-specific trackers
    perishables = Counter()
    perishable_revenue = defaultdict(float)
    product_code_to_name = {}
    
    for file_path in sales_files:
        if not os.path.exists(file_path):
            continue
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    total_sales += 1
                    
                    date = row['flight_date'].strip()
                    flight = row['flightnum'].strip()
                    seat = row['seat_number'].strip()
                    product = row['product'].strip()
                    prod_code = row['product_code'].strip()
                    cat = row['product_category'].strip()
                    
                    qty_str = row['quantity'].strip()
                    qty = int(qty_str) if qty_str.isdigit() else 1
                    
                    rev_str = row['net_sales_base'].strip()
                    rev = float(rev_str) if rev_str else 0.0
                    
                    products[product] += qty
                    categories[cat] += qty
                    product_revenue[product] += rev
                    category_revenue[cat] += rev
                    
                    # Track code to name mapping and perishables
                    if prod_code:
                        product_code_to_name[prod_code] = product
                        if prod_code in PRICES:
                            perishables[prod_code] += qty
                            perishable_revenue[prod_code] += rev
                    
                    if not seat or seat == "":
                        continue
                        
                    key = (date, flight, seat)
                    if key in passenger_lookup:
                        matched_sales += 1
                        pax = passenger_lookup[key]
                        age = pax['age']
                        nationality = pax['nationality']
                        
                        buyer_nationalities[nationality] += qty
                        nat_product_sales[nationality][product] += qty
                        if age is not None:
                            buyer_ages.append(age)
                except Exception as e:
                    continue

    print(f"  * Total Sales Transactions Processed: {total_sales}")
    print(f"  * Successfully Matched to Manifest: {matched_sales} ({matched_sales/total_sales*100:.1f}%)")
    
    print("\n[A] GLOBAL SALES QUANTITY & NET REVENUE BY CATEGORY:")
    for cat, count in categories.most_common():
        rev = category_revenue[cat]
        print(f"  - {cat if cat else 'Empty':<18}: Qty: {count:<5} | Net Sales: {rev:,.2f} THB ({rev/sum(category_revenue.values())*100:.1f}%)")
        
    print("\n[B] TOP 10 BEST-SELLING PERISHABLES IN 2026 (JAN - MAY 24):")
    for i, (code, qty) in enumerate(perishables.most_common(10), 1):
        rev = perishable_revenue[code]
        prod_name = product_code_to_name.get(code, code)
        safe_prod = prod_name.encode('ascii', errors='replace').decode('ascii')
        print(f"  {i:2d}. {safe_prod:<50} | Qty: {qty:<5} | Net Sales: {rev:,.2f} THB")

    print("\n[C] TOP 5 BUYING NATIONALITIES IN-FLIGHT (FROM MANIFEST MATCHES):")
    sorted_nats = sorted(buyer_nationalities.items(), key=lambda x: x[1], reverse=True)
    for i, (nat, count) in enumerate(sorted_nats[:5], 1):
        safe_nat = nat.encode('ascii', errors='replace').decode('ascii')
        print(f"  {i:2d}. {safe_nat:<25} | Qty Purchased: {count:<5}")
        
    print("\n[D] DEMOGRAPHIC BUYING PREFERENCES FOR TOP 3 NATIONALITIES:")
    for i, (nat, _) in enumerate(sorted_nats[:3], 1):
        print(f"  * Top 3 Products Purchased by {nat.upper()}:")
        top_p = nat_product_sales[nat].most_common(3)
        for rank, (prod, qty) in enumerate(top_p, 1):
            safe_prod = prod.encode('ascii', errors='replace').decode('ascii')
            print(f"    - {rank}. {safe_prod:<50} | Qty: {qty}")

    print("\n[E] BUYER AGE PROFILE IN 2026:")
    if buyer_ages:
        avg_age = sum(buyer_ages) / len(buyer_ages)
        median_age = sorted(buyer_ages)[len(buyer_ages)//2]
        
        kids = sum(1 for a in buyer_ages if a <= 12)
        youths = sum(1 for a in buyer_ages if 13 <= a <= 25)
        adults = sum(1 for a in buyer_ages if 26 <= a <= 50)
        seniors = sum(1 for a in buyer_ages if a >= 51)
        
        total_matched_pax = len(buyer_ages)
        print(f"  - Average Age of In-Flight Buyer: {avg_age:.1f} years | Median: {median_age} years")
        print(f"  - Age Group Distribution of Purchases:")
        print(f"    - Kids (0-12): {kids} ({kids/total_matched_pax*100:.1f}%) | Youths (13-25): {youths} ({youths/total_matched_pax*100:.1f}%)")
        print(f"    - Adults (26-50): {adults} ({adults/total_matched_pax*100:.1f}%) | Seniors (51+): {seniors} ({seniors/total_pax_age*100:.1f}%)" if 'total_pax_age' in locals() else f"    - Adults (26-50): {adults} ({adults/total_matched_pax*100:.1f}%) | Seniors (51+): {seniors} ({seniors/total_matched_pax*100:.1f}%)")

if __name__ == "__main__":
    passenger_lookup = analyze_2026_demographics()
    analyze_2026_pbm()
    analyze_2026_sales_demographics(passenger_lookup)
