import os
import csv
import sys
from collections import Counter, defaultdict
import numpy as np

# Configure stdout to handle UTF-8 printing
sys.stdout.reconfigure(encoding='utf-8')

def parse_month(date_str):
    """Robustly extracts MM as int from YYYY-MM-DD or other standard date strings."""
    try:
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts[0]) == 4:
                return int(parts[1])
            else:
                return int(parts[1])
        elif '/' in date_str:
            parts = date_str.split('/')
            if len(parts[0]) == 4:
                return int(parts[1])
            else:
                return int(parts[1])
    except:
        pass
    return None

def load_passenger_data(file_path):
    """Loads passenger manifest with dynamic header index mapping."""
    # Key: (Date, Flight, Seat) -> (Age, Gender, Nationality)
    lookup = {}
    # Month -> { 'total': 0, 'nationalities': Counter(), 'ages': [] }
    monthly_stats = defaultdict(lambda: {'total': 0, 'nationalities': Counter(), 'ages': []})
    
    if not os.path.exists(file_path):
        return lookup, monthly_stats
        
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return lookup, monthly_stats
            
        headers = [h.strip() for h in headers]
        
        # Dynamic index mapping
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
                
        # Robust fallbacks
        if date_idx == -1: date_idx = 0
        if flight_idx == -1: flight_idx = 1
        if age_idx == -1: age_idx = 2
        if seat_idx == -1: seat_idx = 3
        if gender_idx == -1: gender_idx = 4
        if nat_idx == -1: nat_idx = 5
        
        for row in reader:
            if not row or len(row) <= max(date_idx, flight_idx, age_idx, seat_idx, gender_idx, nat_idx):
                continue
            try:
                date = row[date_idx].strip()
                flight = row[flight_idx].strip()
                seat = row[seat_idx].strip()
                
                month = parse_month(date)
                if month is None or not (1 <= month <= 12):
                    continue
                    
                age_str = row[age_idx].strip()
                age = int(age_str) if age_str.isdigit() else None
                gender = row[gender_idx].strip()
                nationality = row[nat_idx].strip()
                
                # Update monthly stats
                monthly_stats[month]['total'] += 1
                if nationality:
                    monthly_stats[month]['nationalities'][nationality] += 1
                if age is not None:
                    monthly_stats[month]['ages'].append(age)
                    
                if seat:
                    key = (date, flight, seat)
                    lookup[key] = {
                        'age': age,
                        'gender': gender,
                        'nationality': nationality
                    }
            except Exception as e:
                continue
                
    return lookup, monthly_stats

def load_pbm_data(file_paths):
    """Loads PBM bookings across files (2026 has two files)."""
    # Month -> { 'total': 0, 'ssrs': Counter(), 'nationalities': Counter() }
    monthly_stats = defaultdict(lambda: {'total': 0, 'ssrs': Counter(), 'nationalities': Counter()})
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            continue
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = row['FlightDate'].strip()
                    month = parse_month(date)
                    if month is None or not (1 <= month <= 12):
                        continue
                        
                    ssr = row['SSRCode'].strip()
                    # Exclude water bottles SSRs to focus on true booked meals if required,
                    # but keep it general since they want all booked PBMs
                    nationality = row['Country_name'].strip()
                    
                    monthly_stats[month]['total'] += 1
                    if ssr:
                        monthly_stats[month]['ssrs'][ssr] += 1
                    if nationality:
                        monthly_stats[month]['nationalities'][nationality] += 1
                except Exception as e:
                    continue
    return monthly_stats

def load_sales_data(file_paths, passenger_lookup):
    """Loads sales data across files and matches to passenger manifest."""
    # Month -> {
    #   'total_transactions': 0,
    #   'matched_transactions': 0,
    #   'revenue_by_cat': defaultdict(float),
    #   'qty_by_cat': Counter(),
    #   'buyer_nationalities': Counter(),
    #   'buyer_ages': []
    # }
    monthly_stats = defaultdict(lambda: {
        'total_transactions': 0,
        'matched_transactions': 0,
        'revenue_by_cat': defaultdict(float),
        'qty_by_cat': Counter(),
        'buyer_nationalities': Counter(),
        'buyer_ages': []
    })
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            continue
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = row['flight_date'].strip()
                    month = parse_month(date)
                    if month is None or not (1 <= month <= 12):
                        continue
                        
                    flight = row['flightnum'].strip()
                    seat = row['seat_number'].strip()
                    cat = row.get('product_category', row.get('new_product_category', '')).strip()
                    
                    qty_str = row['quantity'].strip()
                    qty = int(qty_str) if qty_str.isdigit() else 1
                    
                    rev_str = row['net_sales_base'].strip()
                    rev = float(rev_str) if rev_str else 0.0
                    
                    stats = monthly_stats[month]
                    stats['total_transactions'] += 1
                    stats['revenue_by_cat'][cat] += rev
                    stats['qty_by_cat'][cat] += qty
                    
                    if not seat or seat == "":
                        continue
                        
                    key = (date, flight, seat)
                    if key in passenger_lookup:
                        stats['matched_transactions'] += 1
                        pax = passenger_lookup[key]
                        age = pax['age']
                        nationality = pax['nationality']
                        
                        if nationality:
                            stats['buyer_nationalities'][nationality] += qty
                        if age is not None:
                            stats['buyer_ages'].append(age)
                except Exception as e:
                    continue
    return monthly_stats

def generate_report():
    print("Step 1: Processing 2024 Database...")
    pax_lookup_24, pax_stats_24 = load_passenger_data(
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2024.csv"
    )
    pbm_stats_24 = load_pbm_data(
        [r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2024.csv"]
    )
    sales_stats_24 = load_sales_data(
        [r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2024.csv"],
        pax_lookup_24
    )
    
    print("Step 2: Processing 2025 Database...")
    pax_lookup_25, pax_stats_25 = load_passenger_data(
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2025.csv"
    )
    pbm_stats_25 = load_pbm_data(
        [r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2025.csv"]
    )
    sales_stats_25 = load_sales_data(
        [r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2025.csv"],
        pax_lookup_25
    )
    
    print("Step 3: Processing 2026 Database...")
    pax_lookup_26, pax_stats_26 = load_passenger_data(
        r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    )
    pbm_stats_26 = load_pbm_data([
        r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\PBM-DATA_2026_Month5_24.csv"
    ])
    sales_stats_26 = load_sales_data([
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month5_24.csv"
    ], pax_lookup_26)
    
    output_file = r"C:\Users\Chaiwatwannawit\Desktop\AGY\unified_3year_report.txt"
    print(f"Step 4: Compiling report to: {output_file}...")
    
    month_names = {
        1: 'January', 2: 'February (CNY)', 3: 'March', 4: 'April (Songk)', 5: 'May (Cut-off)', 6: 'June',
        7: 'July (Peak)', 8: 'August (Peak)', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    with open(output_file, mode='w', encoding='utf-8') as out:
        def write_and_print(text):
            out.write(text + "\n")
            print(text)
            
        write_and_print("="*110)
        write_and_print("      THAI AIRASIA (TAA) BUY-ON-BOARD 3-YEAR UNIFIED COMPARATIVE REPORT (2024 - 2026)")
        write_and_print("           Routes: DMK-MLE-DMK | Data Range: Jan 2024 - May 24, 2026")
        write_and_print("="*110)
        
        # -------------------------------------------------------------
        # PART 1: TOTAL PASSENGER VOLUME COMPARISON
        # -------------------------------------------------------------
        write_and_print("\n" + "#"*110)
        write_and_print("PART 1: MONTHLY BOARDED PASSENGER COMPARISON")
        write_and_print("#"*110)
        write_and_print(f"   {'Month':<18} | {'2024 Pax':<12} | {'2025 Pax':<12} | {'2026 Pax':<12} | {'Growth 24->25':<14} | {'Growth 25->26':<14}")
        write_and_print("-"*110)
        
        total_pax_24 = 0
        total_pax_25 = 0
        total_pax_26 = 0
        
        for m in range(1, 13):
            p24 = pax_stats_24[m]['total']
            p25 = pax_stats_25[m]['total']
            p26 = pax_stats_26[m]['total']
            
            total_pax_24 += p24
            total_pax_25 += p25
            total_pax_26 += p26
            
            g24_25 = f"{(p25-p24)/p24*100:+.1f}%" if p24 > 0 else "N/A"
            g25_26 = f"{(p26-p25)/p25*100:+.1f}%" if p25 > 0 and p26 > 0 else "N/A"
            
            m_name = month_names[m]
            p26_str = f"{p26:,}" if p26 > 0 else "-"
            write_and_print(f"   {m_name:<18} | {p24:<12,} | {p25:<12,} | {p26_str:<12} | {g24_25:<14} | {g25_26:<14}")
            
        write_and_print("-"*110)
        write_and_print(f"   {'TOTAL':<18} | {total_pax_24:<12,} | {total_pax_25:<12,} | {total_pax_26:<12,} | {(total_pax_25-total_pax_24)/total_pax_24*100:+.2f}% | N/A")
        
        # -------------------------------------------------------------
        # PART 1.1: MONTHLY PASSENGER NATIONALITY DISTRIBUTION
        # -------------------------------------------------------------
        write_and_print("\n" + "="*80)
        write_and_print("PART 1.1: MONTHLY PASSENGER NATIONALITY DISTRIBUTION TRENDS")
        write_and_print("="*80)
        for m in range(1, 13):
            m_name = month_names[m]
            write_and_print(f"\n* MONTH: {m_name.upper()}")
            for year, stats_dict in [('2024', pax_stats_24), ('2025', pax_stats_25), ('2026', pax_stats_26)]:
                st = stats_dict[m]
                if st['total'] == 0:
                    continue
                top_nats = st['nationalities'].most_common(3)
                top_nats_str = ", ".join([f"{nat}: {count:,} ({count/st['total']*100:.1f}%)" for nat, count in top_nats])
                write_and_print(f"  - {year}: Boarded: {st['total']:,} | Top Nationalities: {top_nats_str}")

        # -------------------------------------------------------------
        # PART 2: PRE-BOOKED MEAL (PBM) COMPARISON
        # -------------------------------------------------------------
        write_and_print("\n" + "#"*110)
        write_and_print("PART 2: MONTHLY PRE-BOOKED MEAL (PBM) VOLUME COMPARISON")
        write_and_print("#"*110)
        write_and_print(f"   {'Month':<18} | {'2024 PBMs':<12} | {'2025 PBMs':<12} | {'2026 PBMs':<12} | {'Growth 24->25':<14} | {'Growth 25->26':<14}")
        write_and_print("-"*110)
        
        total_pbm_24 = 0
        total_pbm_25 = 0
        total_pbm_26 = 0
        
        for m in range(1, 13):
            pbm24 = pbm_stats_24[m]['total']
            pbm25 = pbm_stats_25[m]['total']
            pbm26 = pbm_stats_26[m]['total']
            
            total_pbm_24 += pbm24
            total_pbm_25 += pbm25
            total_pbm_26 += pbm26
            
            g24_25 = f"{(pbm25-pbm24)/pbm24*100:+.1f}%" if pbm24 > 0 else "N/A"
            g25_26 = f"{(pbm26-pbm25)/pbm25*100:+.1f}%" if pbm25 > 0 and pbm26 > 0 else "N/A"
            
            m_name = month_names[m]
            pbm26_str = f"{pbm26:,}" if pbm26 > 0 else "-"
            write_and_print(f"   {m_name:<18} | {pbm24:<12,} | {pbm25:<12,} | {pbm26_str:<12} | {g24_25:<14} | {g25_26:<14}")
            
        write_and_print("-"*110)
        write_and_print(f"   {'TOTAL':<18} | {total_pbm_24:<12,} | {total_pbm_25:<12,} | {total_pbm_26:<12,} | {(total_pbm_25-total_pbm_24)/total_pbm_24*100:+.2f}% | N/A")

        # -------------------------------------------------------------
        # PART 2.1: PBM TOP SSR CODES & BOOKING NATIONALITIES
        # -------------------------------------------------------------
        write_and_print("\n" + "="*80)
        write_and_print("PART 2.1: MONTHLY PBM TOP MEALS & BOOKING NATIONALITIES")
        write_and_print("="*80)
        for m in range(1, 13):
            m_name = month_names[m]
            write_and_print(f"\n* MONTH: {m_name.upper()}")
            for year, stats_dict in [('2024', pbm_stats_24), ('2025', pbm_stats_25), ('2026', pbm_stats_26)]:
                st = stats_dict[m]
                if st['total'] == 0:
                    continue
                top_ssrs = st['ssrs'].most_common(3)
                top_ssrs_str = ", ".join([f"{ssr}: {count:,} ({count/st['total']*100:.1f}%)" for ssr, count in top_ssrs])
                
                top_nats = st['nationalities'].most_common(2)
                top_nats_str = ", ".join([f"{nat}: {count:,} ({count/st['total']*100:.1f}%)" for nat, count in top_nats])
                
                write_and_print(f"  - {year}: Booked PBM: {st['total']:,} | Top Meal SSRs: {top_ssrs_str} | Top Nationalities: {top_nats_str}")

        # -------------------------------------------------------------
        # PART 3: IN-FLIGHT BOB SALES & REVENUE COMPARISON BY CATEGORY
        # -------------------------------------------------------------
        write_and_print("\n" + "#"*110)
        write_and_print("PART 3: MONTHLY IN-FLIGHT BOB SALES BY CATEGORY")
        write_and_print("#"*110)
        
        # Get all unique categories across all years
        all_categories = set()
        for month_data in sales_stats_24.values():
            all_categories.update(month_data['qty_by_cat'].keys())
        for month_data in sales_stats_25.values():
            all_categories.update(month_data['qty_by_cat'].keys())
        for month_data in sales_stats_26.values():
            all_categories.update(month_data['qty_by_cat'].keys())
            
        all_categories = sorted(list(all_categories))
        
        for m in range(1, 13):
            m_name = month_names[m]
            write_and_print(f"\n--- MONTH: {m_name.upper()} ---")
            write_and_print(f"   {'Category':<18} | {'24 Qty':<6} | {'24 Rev (THB)':<13} | {'25 Qty':<6} | {'25 Rev (THB)':<13} | {'26 Qty':<6} | {'26 Rev (THB)':<13}")
            write_and_print("-"*110)
            
            for cat in all_categories:
                q24 = sales_stats_24[m]['qty_by_cat'][cat]
                r24 = sales_stats_24[m]['revenue_by_cat'][cat]
                
                q25 = sales_stats_25[m]['qty_by_cat'][cat]
                r25 = sales_stats_25[m]['revenue_by_cat'][cat]
                
                q26 = sales_stats_26[m]['qty_by_cat'][cat]
                r26 = sales_stats_26[m]['revenue_by_cat'][cat]
                
                cat_display = cat if cat else 'Empty/Misc'
                q26_str = f"{q26:<6d}" if q26 > 0 else "-"
                r26_str = f"{r26:<13,.0f}" if r26 > 0 else "-"
                
                write_and_print(f"   {cat_display:<18} | {q24:<6d} | {r24:<13,.0f} | {q25:<6d} | {r25:<13,.0f} | {q26_str} | {r26_str}")
            write_and_print("-"*110)

        # -------------------------------------------------------------
        # PART 4: BUYER DEMOGRAPHICS (NATIONALITY & AGE PROFILE)
        # -------------------------------------------------------------
        write_and_print("\n" + "#"*110)
        write_and_print("PART 4: IN-FLIGHT BOB BUYER DEMOGRAPHICS & MATCHING PERFORMANCE")
        write_and_print("#"*110)
        
        for m in range(1, 13):
            m_name = month_names[m]
            write_and_print(f"\n--- MONTH: {m_name.upper()} ---")
            
            for year, stats_dict in [('2024', sales_stats_24), ('2025', sales_stats_25), ('2026', sales_stats_26)]:
                st = stats_dict[m]
                if st['total_transactions'] == 0:
                    continue
                match_rate = st['matched_transactions'] / st['total_transactions'] * 100 if st['total_transactions'] > 0 else 0.0
                
                top_buyer_nats = st['buyer_nationalities'].most_common(3)
                top_buyer_nats_str = ", ".join([f"{nat}: {qty:,} ({qty/sum(st['buyer_nationalities'].values())*100:.1f}%)" for nat, qty in top_buyer_nats]) if st['buyer_nationalities'] else "N/A"
                
                ages = st['buyer_ages']
                avg_age = np.mean(ages) if ages else 0.0
                median_age = np.median(ages) if ages else 0.0
                
                kids = sum(1 for a in ages if a <= 12)
                youths = sum(1 for a in ages if 13 <= a <= 25)
                adults = sum(1 for a in ages if 26 <= a <= 50)
                seniors = sum(1 for a in ages if a >= 51)
                
                age_group_str = f"Kids: {kids/len(ages)*100:.1f}%, Youth: {youths/len(ages)*100:.1f}%, Adult: {adults/len(ages)*100:.1f}%, Senior: {seniors/len(ages)*100:.1f}%" if ages else "N/A"
                
                write_and_print(f"  * {year} In-Flight Sales:")
                write_and_print(f"    - Transactions: {st['total_transactions']:,} | Matched: {st['matched_transactions']:,} ({match_rate:.1f}%)")
                write_and_print(f"    - Top Buying Nationalities (BoB): {top_buyer_nats_str}")
                if ages:
                    write_and_print(f"    - Buyer Age Profile: Mean = {avg_age:.1f} yrs | Median = {median_age:.0f} yrs")
                    write_and_print(f"    - Age Distribution: {age_group_str}")
                write_and_print("    " + "-"*80)

if __name__ == "__main__":
    generate_report()
