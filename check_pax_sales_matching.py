import csv
import os

def check_mismatches():
    pax_file = r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    sales_files = [
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month1_4.csv",
        r"C:\Users\Chaiwatwannawit\Desktop\AI\SaleALL2026_Month5_24.csv"
    ]
    
    # 1. Load all unique (Date, Flight) from Passenger manifest
    pax_flights = set()
    with open(pax_file, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # skip headers
        for row in reader:
            if not row: continue
            date = row[0].strip()
            flight = row[1].strip()
            pax_flights.add((date, flight))
            
    print(f"Total Unique Flights in Passenger Manifest: {len(pax_flights)}")
    
    # 2. Load all unique (Date, Flight) from Sales files
    sales_flights = set()
    for s_file in sales_files:
        if not os.path.exists(s_file):
            continue
        with open(s_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row['flight_date'].strip()
                flight = row['flightnum'].strip()
                sales_flights.add((date, flight))
                
    print(f"Total Unique Flights in Sales Data: {len(sales_flights)}")
    
    # Check mismatches
    sales_not_in_pax = sales_flights - pax_flights
    pax_not_in_sales = pax_flights - sales_flights
    
    print(f"\nNumber of flights in Sales but MISSING in Passenger Manifest: {len(sales_not_in_pax)}")
    if sales_not_in_pax:
        print("First 15 missing flights (Sales but not in Passenger):")
        for date, flight in sorted(list(sales_not_in_pax))[:15]:
            print(f"  - Date: {date} | Flight: {flight}")
            
    print(f"\nNumber of flights in Passenger Manifest but MISSING in Sales: {len(pax_not_in_sales)}")
    if pax_not_in_sales:
        print("First 15 missing flights (Passenger but not in Sales):")
        for date, flight in sorted(list(pax_not_in_sales))[:15]:
            print(f"  - Date: {date} | Flight: {flight}")

if __name__ == "__main__":
    check_mismatches()
