import csv
from collections import Counter

def check_historical_dates():
    file_path = r"C:\Users\Chaiwatwannawit\Desktop\AGY\perishable_historical_data.csv"
    
    unique_dates = Counter()
    years = Counter()
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['FlightDate']
            year = row['Year']
            unique_dates[date] += 1
            years[year] += 1
            
    print(f"Total Rows in perishable_historical_data.csv: {sum(unique_dates.values())}")
    print(f"Distribution by Year: {dict(years)}")
    
    # Check 2026 dates format
    dates_2026 = sorted([d for d in unique_dates.keys() if d.startswith('2026')])
    print(f"Number of unique 2026 dates: {len(dates_2026)}")
    if dates_2026:
        print(f"2026 Date range: {dates_2026[0]} to {dates_2026[-1]}")
        print("First 5 dates in 2026:")
        for d in dates_2026[:5]:
            print(f"  - {d}: {unique_dates[d]} records")

if __name__ == "__main__":
    check_historical_dates()
