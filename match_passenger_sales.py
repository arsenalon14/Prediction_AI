import os
import csv
import sys
from collections import Counter, defaultdict

# Reconfigure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

def match_sales_demographics(sales_file, passenger_file):
    print(f"\nMatching Sales data with Passenger manifest:")
    print(f"  - Sales: {sales_file}")
    print(f"  - Passengers: {passenger_file}")
    
    # 1. Load Passenger Manifest into a fast lookup table
    # Key: (Date, FlightNumber, Seat) -> (Age, Gender, Nationality)
    passenger_lookup = {}
    total_manifest_records = 0
    duplicate_seats = 0
    
    with open(passenger_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_manifest_records += 1
            date = row['FlightDate'].strip()
            flight = row['FlightNumber'].strip()
            seat = row['UnitDesignator'].strip()
            
            if not seat or seat == "":
                continue
                
            age_str = row['PaxAge'].strip()
            age = int(age_str) if age_str.isdigit() else None
            gender = row['gender'].strip()
            nationality = row['Country_name'].strip()
            
            # Unique lookup key for the seat on that specific flight date
            key = (date, flight, seat)
            if key in passenger_lookup:
                duplicate_seats += 1
            passenger_lookup[key] = {
                'age': age,
                'gender': gender,
                'nationality': nationality
            }
            
    print(f"  * Loaded {len(passenger_lookup)} unique passengers from manifest (Total lines: {total_manifest_records}, Duplicate seats: {duplicate_seats})")
    
    # 2. Iterate through Sales and Match
    total_sales = 0
    matched_sales = 0
    unmatched_sales_no_seat = 0
    unmatched_sales_not_found = 0
    
    # Aggregate statistics for matches
    buyer_nationalities = Counter()
    buyer_ages = []
    
    # Product sales per nationality
    # Nationality -> Product -> Qty
    nat_product_sales = defaultdict(lambda: Counter())
    
    # Product sales per age group
    # Age Group -> Product -> Qty
    age_product_sales = defaultdict(lambda: Counter())
    
    # Revenue stats by nationality
    nat_revenue = defaultdict(float)
    
    with open(sales_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_sales += 1
            
            date = row['flight_date'].strip()
            flight = row['flightnum'].strip()
            seat = row['seat_number'].strip()
            product = row['product'].strip()
            
            qty_str = row['quantity'].strip()
            qty = int(qty_str) if qty_str.isdigit() else 1
            
            rev_str = row['net_sales_base'].strip()
            rev = float(rev_str) if rev_str else 0.0
            
            if not seat or seat == "" or seat.upper() in {"CREW", "NONE"}:
                unmatched_sales_no_seat += 1
                continue
                
            key = (date, flight, seat)
            if key in passenger_lookup:
                matched_sales += 1
                pax_info = passenger_lookup[key]
                age = pax_info['age']
                nationality = pax_info['nationality']
                
                # Record metrics
                buyer_nationalities[nationality] += qty
                nat_revenue[nationality] += rev
                nat_product_sales[nationality][product] += qty
                
                if age is not None:
                    buyer_ages.append(age)
                    # Categorize age group
                    if age <= 12:
                        group = 'Kids (0-12)'
                    elif 13 <= age <= 25:
                        group = 'Youths (13-25)'
                    elif 26 <= age <= 50:
                        group = 'Adults (26-50)'
                    else:
                        group = 'Seniors (51+)'
                        
                    age_product_sales[group][product] += qty
            else:
                unmatched_sales_not_found += 1

    print("\n" + "="*80)
    print(f"PASSENGER MATCHING & DEMOGRAPHIC SALES REPORT")
    print(f"  Source File: {os.path.basename(sales_file)}")
    print("="*80)
    print(f"  * Total Sales Transactions: {total_sales}")
    print(f"  * Successfully Matched: {matched_sales} ({matched_sales/total_sales*100:.1f}%)")
    print(f"  * Unmatched (No Seat Info): {unmatched_sales_no_seat} ({unmatched_sales_no_seat/total_sales*100:.1f}%)")
    print(f"  * Unmatched (Seat not in manifest): {unmatched_sales_not_found} ({unmatched_sales_not_found/total_sales*100:.1f}%)")
    
    # A. Top Buying Nationalities (by Quantity and Revenue)
    print("\n[A] TOP 10 BUYING NATIONALITIES (BY QUANTITY & REVENUE):")
    sorted_nats = sorted(buyer_nationalities.items(), key=lambda x: x[1], reverse=True)
    for i, (nat, qty) in enumerate(sorted_nats[:10], 1):
        rev = nat_revenue[nat]
        print(f"  {i:2d}. {nat:<30} | Qty Bought: {qty:<5} | Total Net Spend: {rev:,.2f} THB")
        
    # B. Buyer Age Distribution
    print("\n[B] BUYER AGE DISTRIBUTION PROFILE:")
    if buyer_ages:
        avg_age = sum(buyer_ages) / len(buyer_ages)
        median_age = sorted(buyer_ages)[len(buyer_ages)//2]
        
        kids = sum(1 for a in buyer_ages if a <= 12)
        youths = sum(1 for a in buyer_ages if 13 <= a <= 25)
        adults = sum(1 for a in buyer_ages if 26 <= a <= 50)
        seniors = sum(1 for a in buyer_ages if a >= 51)
        
        total_pax_age = len(buyer_ages)
        print(f"  * Average Age of Buyer: {avg_age:.1f} years | Median Age of Buyer: {median_age} years")
        print(f"  * Age Groups:")
        print(f"    - Kids (0-12): {kids} ({kids/total_pax_age*100:.1f}%)")
        print(f"    - Youths (13-25): {youths} ({youths/total_pax_age*100:.1f}%)")
        print(f"    - Adults (26-50): {adults} ({adults/total_pax_age*100:.1f}%)")
        print(f"    - Seniors (51+): {seniors} ({seniors/total_pax_age*100:.1f}%)")
        
    # C. Product Preferences of Top 3 Nationalities
    print("\n[C] PRODUCT PREFERENCES FOR TOP 3 NATIONALITIES:")
    for i, (nat, _) in enumerate(sorted_nats[:3], 1):
        print(f"  * Top 5 Products Purchased by {nat.upper()}:")
        top_p = nat_product_sales[nat].most_common(5)
        for rank, (prod, qty) in enumerate(top_p, 1):
            safe_prod = prod.encode('ascii', errors='replace').decode('ascii')
            print(f"    - {rank}. {safe_prod:<50} | Qty: {qty}")
            
    # D. Product Preferences by Age Group
    print("\n[D] PRODUCT PREFERENCES BY AGE GROUP:")
    for group in sorted(age_product_sales.keys()):
        print(f"  * Top 5 Products Purchased by {group}:")
        top_p = age_product_sales[group].most_common(5)
        for rank, (prod, qty) in enumerate(top_p, 1):
            safe_prod = prod.encode('ascii', errors='replace').decode('ascii')
            print(f"    - {rank}. {safe_prod:<50} | Qty: {qty}")

if __name__ == "__main__":
    # Run for 2025
    match_sales_demographics(
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2025.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2025.csv"
    )
