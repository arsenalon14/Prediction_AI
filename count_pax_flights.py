import csv
from collections import defaultdict

def count_flights():
    file_path = r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    
    # Track unique dates and count rows per flight pairing
    # Month -> FlightNumber -> Set of unique dates
    flight_dates = defaultdict(lambda: defaultdict(set))
    # Month -> FlightNumber -> Passenger count
    pax_counts = defaultdict(lambda: defaultdict(int))
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['FlightDate'].strip()
            flight = row['FlightNumber'].strip()
            month = int(date.split('-')[1])
            
            flight_dates[month][flight].add(date)
            pax_counts[month][flight] += 1
            
    print("="*80)
    print("FLIGHT OPERATIONS & LOAD DIAGNOSTICS FOR 2026 PASSENGER MANIFEST")
    print("="*80)
    
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May (1-24)'}
    
    for month in sorted(pax_counts.keys()):
        name = month_names.get(month, f"Month {month:02d}")
        print(f"\n* {name} 2026:")
        for flight in sorted(pax_counts[month].keys()):
            dates_count = len(flight_dates[month][flight])
            total_pax = pax_counts[month][flight]
            avg_pax = total_pax / dates_count if dates_count > 0 else 0.0
            print(f"  - Flight {flight}: Unique Dates: {dates_count} | Total Pax: {total_pax} | Avg Pax/Flight: {avg_pax:.1f}")

if __name__ == "__main__":
    count_flights()
