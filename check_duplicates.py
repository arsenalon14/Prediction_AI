import csv
from collections import Counter

def check_duplicates():
    file_path = r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2026_Month5_24.csv"
    
    seat_counts = Counter()
    total_rows = 0
    empty_seats = 0
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            total_rows += 1
            date = row['FlightDate'].strip()
            flight = row['FlightNumber'].strip()
            seat = row['UnitDesignator'].strip()
            
            if not seat:
                empty_seats += 1
                continue
                
            key = (date, flight, seat)
            seat_counts[key] += 1
            
    duplicates = {k: v for k, v in seat_counts.items() if v > 1}
    
    print(f"Total Rows: {total_rows}")
    print(f"Empty Seats: {empty_seats}")
    print(f"Unique (Date, Flight, Seat) Keys: {len(seat_counts)}")
    print(f"Number of seat keys with duplicates: {len(duplicates)}")
    if duplicates:
        print("First 10 duplicates:")
        for k, v in list(duplicates.items())[:10]:
            print(f"  - Key: {k} | Count: {v}")
            
if __name__ == "__main__":
    check_duplicates()
