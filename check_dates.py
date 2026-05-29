import csv
from collections import Counter

def check_2026_pax_dates():
    file_path = r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    
    unique_dates = Counter()
    unique_months = Counter()
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row['FlightDate'].strip()
            unique_dates[date_str] += 1
            try:
                month = date_str.split('-')[1]
                unique_months[month] += 1
            except:
                pass
                
    sorted_dates = sorted(unique_dates.keys())
    print("\n" + "="*80)
    print("DATE PROFILE OF Passenger_Nat_Age_Seat-2026_Month5_24.csv")
    print("="*80)
    print(f"Total rows: {sum(unique_dates.values())}")
    print(f"Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
    print(f"Number of unique dates: {len(unique_dates)}")
    
    print("\n[1] Distribution by Month:")
    for month, count in sorted(unique_months.items()):
        print(f"  - Month {month}: {count} rows")
        
    print("\n[2] Sample of Date counts (first 10 and last 10 dates):")
    print("  First 10 dates:")
    for d in sorted_dates[:10]:
        print(f"    - {d}: {unique_dates[d]} rows")
    print("  Last 10 dates:")
    for d in sorted_dates[-10:]:
        print(f"    - {d}: {unique_dates[d]} rows")

if __name__ == "__main__":
    check_2026_pax_dates()
