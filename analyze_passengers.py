import os
import csv
from collections import Counter, defaultdict

def analyze_csv(file_path):
    print(f"Loading and analyzing: {file_path}")
    
    # Structure to hold monthly data
    # Month (1-12) -> Month Data
    monthly_data = defaultdict(lambda: {
        'total_pax': 0,
        'f175_pax': 0,
        'f176_pax': 0,
        'ages': [],
        'nationalities': [],
        'genders': []
    })
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date_str = row['FlightDate']
                month = int(date_str.split('-')[1]) # Extract MM as int
                
                flight_num = row['FlightNumber'].strip()
                
                # Parse Age (handling empty or invalid ages)
                age_str = row['PaxAge'].strip()
                age = int(age_str) if age_str.isdigit() else None
                
                nationality = row['Country_name'].strip()
                gender = row['gender'].strip()
                
                monthly_data[month]['total_pax'] += 1
                if flight_num == '175':
                    monthly_data[month]['f175_pax'] += 1
                elif flight_num == '176':
                    monthly_data[month]['f176_pax'] += 1
                
                if age is not None:
                    monthly_data[month]['ages'].append(age)
                if nationality:
                    monthly_data[month]['nationalities'].append(nationality)
                if gender:
                    monthly_data[month]['genders'].append(gender)
                    
            except Exception as e:
                # Silently skip malformed rows if any
                continue

    # Generate and print reports
    print("\n" + "="*80)
    print(f"MONTHLY PASSENGER DEMOGRAPHICS REPORT FOR {os.path.basename(file_path)}")
    print("="*80)
    
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        total = data['total_pax']
        f175 = data['f175_pax']
        f176 = data['f176_pax']
        ages = data['ages']
        nats = data['nationalities']
        
        # Calculate age statistics
        avg_age = sum(ages) / len(ages) if ages else 0
        median_age = sorted(ages)[len(ages)//2] if ages else 0
        
        # Age grouping
        kids = sum(1 for a in ages if a <= 12)
        youths = sum(1 for a in ages if 13 <= a <= 25)
        adults = sum(1 for a in ages if 26 <= a <= 50)
        seniors = sum(1 for a in ages if a >= 51)
        
        # Nationality distribution (top 5)
        nat_counts = Counter(nats)
        top_nats = nat_counts.most_common(5)
        top_nats_str = ", ".join([f"{nat}: {count} ({count/len(nats)*100:.1f}%)" for nat, count in top_nats])
        
        print(f"\n--- MONTH {month:02d} ---")
        print(f"  * Total Boarded Passengers: {total} (FD175: {f175}, FD176: {f176})")
        if ages:
            print(f"  * Age Profile: Mean = {avg_age:.1f} years | Median = {median_age} years")
            print(f"    - Kids (0-12): {kids} ({kids/len(ages)*100:.1f}%)")
            print(f"    - Youths (13-25): {youths} ({youths/len(ages)*100:.1f}%)")
            print(f"    - Adults (26-50): {adults} ({adults/len(ages)*100:.1f}%)")
            print(f"    - Seniors (51+): {seniors} ({seniors/len(ages)*100:.1f}%)")
        print(f"  * Top Nationalities: {top_nats_str}")

if __name__ == "__main__":
    analyze_csv(r"C:\Users\Chaiwatwannawit\Desktop\AI\Passenger_Nat_Age_Seat-2025.csv")
