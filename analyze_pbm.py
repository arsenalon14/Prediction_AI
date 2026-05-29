import os
import csv
from collections import Counter, defaultdict

def analyze_pbm(file_path):
    print(f"Loading and analyzing Pre-Booked Meal data (excluding Water Bottles): {file_path}")
    
    # Water bottle SSR codes to exclude (non-perishables)
    exclude_ssrs = {'BWFD', 'BWAK', 'BWHL', 'WBHL'}
    
    # Structure to hold monthly PBM data
    monthly_data = defaultdict(lambda: {
        'total_pbm': 0,
        'f175_pbm': 0,
        'f176_pbm': 0,
        'ssrs': [],
        'nationalities': [],
        'ages': [],
        'seat_count': set()
    })
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ssr = row['SSRCode'].strip()
                if ssr in exclude_ssrs:
                    continue  # Exclude bottle of water
                
                date_str = row['FlightDate']
                month = int(date_str.split('-')[1])
                
                flight = row['Flight'].strip()
                seat = row['Seat'].strip()
                nationality = row['Country_name'].strip()
                
                age_str = row['PaxAge'].strip()
                age = int(age_str) if age_str.isdigit() else None
                
                pax_key = f"{date_str}_{flight}_{seat}"
                
                monthly_data[month]['total_pbm'] += 1
                if flight == '175':
                    monthly_data[month]['f175_pbm'] += 1
                elif flight == '176':
                    monthly_data[month]['f176_pbm'] += 1
                
                monthly_data[month]['ssrs'].append(ssr)
                if nationality:
                    monthly_data[month]['nationalities'].append(nationality)
                if age is not None:
                    monthly_data[month]['ages'].append(age)
                if seat:
                    monthly_data[month]['seat_count'].add(pax_key)
                    
            except Exception as e:
                continue

    print("\n" + "="*80)
    print(f"MONTHLY PRE-BOOKED MEAL (PBM) REPORT FOR {os.path.basename(file_path)}")
    print("  *(EXCLUDING WATER BOTTLES: BWFD, BWAK, BWHL, WBHL)*")
    print("="*80)
    
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        total = data['total_pbm']
        f175 = data['f175_pbm']
        f176 = data['f176_pbm']
        ssrs = data['ssrs']
        nats = data['nationalities']
        pax_count = len(data['seat_count'])
        
        if total == 0:
            print(f"\n--- MONTH {month:02d} --- No perishable PBMs found.")
            continue
            
        avg_pbm_per_pax = total / pax_count if pax_count > 0 else 0
        
        # Popular SSR codes (top 5)
        ssr_counts = Counter(ssrs)
        top_ssrs = ssr_counts.most_common(5)
        top_ssrs_str = ", ".join([f"{code}: {count} ({count/total*100:.1f}%)" for code, count in top_ssrs])
        
        # Popular Nationalities buying PBMs (top 5)
        nat_counts = Counter(nats)
        top_nats = nat_counts.most_common(5)
        top_nats_str = ", ".join([f"{nat}: {count} ({count/total*100:.1f}%)" for nat, count in top_nats])
        
        print(f"\n--- MONTH {month:02d} ---")
        print(f"  * Total Perishable PBM Orders: {total} (FD175: {f175}, FD176: {f176})")
        print(f"  * Unique Passengers Ordering: {pax_count} (Average = {avg_pbm_per_pax:.2f} meals/pax)")
        print(f"  * Top SSR Meal Codes: {top_ssrs_str}")
        print(f"  * Top Nationalities Ordering: {top_nats_str}")

if __name__ == "__main__":
    # Test 2025
    analyze_pbm(r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2025.csv")
