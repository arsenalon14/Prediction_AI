import csv
import os

def check_may_dates():
    pax_file = r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    sales_file = r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month5_24.csv"
    wastage_file = r"C:\Users\Chaiwatwannawit\Desktop\AI\Wastage-2026_Month5_24.csv"
    
    # 1. Passenger dates in May
    pax_dates = set()
    with open(pax_file, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if not row: continue
            date = row[0].strip()
            if date.startswith('2026-05'):
                pax_dates.add(date)
                
    # 2. Sales dates in May
    sales_dates = set()
    if os.path.exists(sales_file):
        with open(sales_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row['flight_date'].strip()
                if date.startswith('2026-05'):
                    sales_dates.add(date)
                    
    # 3. Wastage dates in May
    wastage_dates = set()
    if os.path.exists(wastage_file):
        with open(wastage_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row['flightdate'].strip()
                if date.startswith('2026-05'):
                    wastage_dates.add(date)
                    
    print("="*80)
    print("MAY 2026 UNIQUE DATES COMPARISON")
    print("="*80)
    print(f"Passenger Manifest unique May dates ({len(pax_dates)}): {sorted(list(pax_dates))}")
    print(f"Sales Data unique May dates ({len(sales_dates)}): {sorted(list(sales_dates))}")
    print(f"Wastage Data unique May dates ({len(wastage_dates)}): {sorted(list(wastage_dates))}")
    
    # Missing calendar dates in May (1-24)
    all_may_calendar = [f"2026-05-{d:02d}" for d in range(1, 25)]
    missing_in_pax = set(all_may_calendar) - pax_dates
    print(f"\nMissing dates in Passenger Manifest for May 1-24: {sorted(list(missing_in_pax))}")
    
    missing_in_sales = set(all_may_calendar) - sales_dates
    print(f"Missing dates in Sales for May 1-24: {sorted(list(missing_in_sales))}")

if __name__ == "__main__":
    check_may_dates()
