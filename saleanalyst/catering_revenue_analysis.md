# Airline Inflight Catering Inventory & Sales Revenue Deep Analysis

> [!NOTE]
> This analysis is prepared in compliance with the **Data Analyst** guidelines and provides a multi-dimensional look at inflight catering performance, passenger behavior, prebook meal conversion, and revenue optimization.

## Executive Summary
This report analyzes **117,047** transaction records from the **MasterSaleFile**, merged with passenger statistics (**89,959** records in **NationalityFile**) and prebooked service data (**101,535** records in **PBMFile**).

* **Total Onboard Sales Revenue**: **7,778,330.00 THB** (after adjusting Beverage category with negative Combo discounts)
* **Total Passenger Volume**: **1,214,111 Passengers**
* **Average Spend per Passenger (Onboard)**: **6.4066 THB**
* **Total Prebooked Meals (All items)**: **273,524 Units**
* **Total PBM Category Revenue**: **20,139,625.71 THB** (fully inclusive of all prebooked charges)

***

## 1. Category Performance (Main 5 Categories)
Below is the breakdown of sales revenue, product quantities sold, **RPP (Revenue Per Passenger)**, and **TUR (Take Up Rate / Quantity Per Passenger in %)** across the five primary categories.
* **SEAT UPGRADE** has been completely excluded from all calculations (**682** rows removed, representing **436,170.00 THB**).
* **Combo Category** rows (which represent the discount transactions, totaling **-774,490.00 THB**) have been excluded from direct onboard category listings but applied as a subtraction from `Beverage` revenue.
* **Beverage quantity** excludes **31** specific component codes to prevent quantity inflation.
* **PBM Category** revenue captures **all** prebooked service charges, but the quantity excludes pure drink items (`'Water'`, `'Coconut Water'`, and `'Americano'`) to avoid artificial meal count inflation.

| Category | Base NetSales / Charges (THB) | Total Adjusted Revenue (THB) | Quantity Sold (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 3,209,100.00 | 3,209,100.00 | 24,311 | **2.64** | **2.00%** | 132.00 |
| **Non-Perishable** | 1,301,080.00 | 1,301,080.00 | 21,001 | **1.07** | **1.73%** | 61.95 |
| **Beverage** | 3,380,820.00 | 2,606,330.00 | 59,166 | **2.15** | **4.87%** | 44.05 |
| **Merchandise** | 661,820.00 | 661,820.00 | 2,861 | **0.55** | **0.24%** | 231.32 |
| **PBM** | 20,139,625.71 | 20,139,625.71 | 161,636 | **16.59** | **13.31%** | 124.60 |

> [!TIP]
> * **RPP (Revenue per Passenger)** tells us how much revenue each boarded passenger yields in that category.
> * **TUR (Take Up Rate / Units per Passenger)** shows the purchase conversion rate per passenger. For example, a Beverage TUR of **4.87%** means the average passenger buys **4.87%** drinks.

***

## 2. Monthly Trends Analysis
Passenger volumes, prebooking trends, and onboard sales vary by month:

| Month | Flights | Total Passengers | Total Prebooks | Onboard Revenue (THB) | Onboard Spend / Pax (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| May 2026 | 8,614 | 1,214,111 | 273,524 | 7,778,330.00 | 6.4066 |

***

## 3. Top 10 High-Performing Routes
The table below lists the top routes by total onboard revenue, detailing passenger capacity, prebooked meal rates, and average passenger spend.

| Route | Country / Region | Flights | Total Passengers | Prebooked Meals | Onboard Revenue (THB) | Spend / Pax (THB) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **DMKHKT** | THAILAND | 519 | 76,994 | 13,683 | 412,730.00 | 5.3605 |
| **DMKMLE** | MALDIVES | 48 | 7,275 | 4,927 | 373,200.00 | 51.2990 |
| **BKKHKT** | THAILAND | 320 | 44,763 | 5,512 | 322,080.00 | 7.1952 |
| **DMKCNX** | THAILAND | 532 | 89,519 | 19,569 | 257,840.00 | 2.8803 |
| **DMKHDY** | THAILAND | 372 | 68,761 | 21,419 | 234,420.00 | 3.4092 |
| **DMKURT** | THAILAND | 310 | 50,946 | 7,976 | 220,050.00 | 4.3193 |
| **DMKDAD** | VIETNAM | 186 | 24,869 | 8,420 | 208,480.00 | 8.3831 |
| **DMKCKG** | CHINA | 88 | 11,599 | 4,138 | 196,950.00 | 16.9799 |
| **DMKMFM** | MACAU | 66 | 8,013 | 2,548 | 190,010.00 | 23.7127 |
| **DMKJHB** | MALAYSIA | 88 | 13,955 | 4,160 | 186,820.00 | 13.3873 |

***

## 4. Combo Sales & Popularity Analysis
Combo items are identified by `ProductCode` starting with `COMBO` or `CRFT`. Combo menu transactions have their individual parts categorized under physical goods, while the main promo entry (discount) is captured in the `Combo` category.

### Top 10 Most Popular Combo Deals:
| Product Code | Combo Menu Description | Quantity Sold | Total Discounts Saved (THB) |
| :--- | :--- | :---: | :---: |
| `COMBO1004679` | HAPPY COMBO - LAY'S ORIGINAL + BOBA MILK TEA | 3,771 | 150,840.00 |
| `COMBO1006940` | HAPPY COMBO - LAY'S STAX SOUR CREAM & ONION + BOBA MILK TEA | 1,786 | 71,440.00 |
| `COMBO1002911` | PALMYRA GRILLED CHICKEN, STICKY RICE AND SOMTAM + COKE | 757 | 30,280.00 |
| `COMBO1000207` | UNCLE CHIN CHICKEN RICE + COKE | 695 | 27,800.00 |
| `COMBO1000133` | Fried Chicken & Basil + Coke | 620 | 24,800.00 |
| `COMBO1002927` | PALMYRA GRILLED CHICKEN, STICKY RICE AND SOMTAM + JASMINE GREEN TEA | 411 | 24,660.00 |
| `COMBO1002563` | UNCLE CHIN CHICKEN RICE + JASMINE GREEN TEA | 407 | 24,420.00 |
| `COMBO1006889` | PALMYRA GRILLED CHICKEN, STICKY RICE AND SOMTAM + TIPCO COCONUT WATER 200 ML. | 393 | 31,440.00 |
| `COMBO1002454` | UNCLE CHIN CHICKEN RICE + AMERICANO | 330 | 19,800.00 |
| `COMBO1002564` | FRIED CHICKEN WITH BASIL ON RICE + JASMINE GREEN TEA | 324 | 19,440.00 |

***

## 5. Top 10 Prebooked SSR Meal Preferences
Prebooking is a critical tool for minimizing food waste (Newsvendor critical fractile optimization) and securing upfront revenue. The most popular prebooked items are:

| SSR Code | SSR Meal/Beverage Description | Total Prebooked Quantity | Estimated Prebooked Revenue (THB) |
| :--- | :--- | :---: | :---: |
| `BWHL` | Water | 70,633 | 308,734.97 |
| `BWAK` | Water | 31,094 | 0.00 |
| `WAK` | WAK | 26,351 | 1,581,060.00 |
| `CRCB` | Uncle's Chin Chicken Rice | 11,174 | 1,486,131.87 |
| `CTCB` | Chicken Teriyaki with Rice | 10,974 | 1,477,263.02 |
| `WBHL` | Water | 7,853 | 317,729.17 |
| `CBCB` | ML Noi Fried Chicken with Basil on Rice | 7,152 | 976,292.70 |
| `CBCM` | ML Nois basil fried chicken on rice | 6,869 | 959,510.84 |
| `GACM` | Grilled Mackerel With Japanese Sauce and Rice | 5,958 | 834,106.32 |
| `RCCM` | Roasted Chicken with Black Pepper Sauce | 5,880 | 821,731.13 |

***

## Key Strategic Insights & Recommendations

1. **PBM Revenue Engine**: PBM is the second-largest revenue category overall at **{pbm_revenue_total:,.2f} THB**, representing high customer engagement before flights.
2. **Onboard vs. Prebook Synergy**: Since PBM represents a locked-in meal commitment, we should design high-margin onboard dessert and premium beverage menus to capture additional impulse onboard spend from passengers who have already prebooked their main course.
3. **Route Tailoring**: Routes like **DMKICN** (Seoul) and **DMKMAA** (Chennai) display vastly different spend patterns and product preferences. Adjusting the catering stock loading factor (L) for regional palettes will maximize revenue and slash catering waste.

***

## 6. Country-Level Performance Analysis
The table below details category performance grouped by target Country. This helps identify regional taste profiles, prebooking behaviors, and onboard spend variances.

### 📍 CAMBODIA (Total Passengers: 19,524)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 43,340.00 | 289 | **2.22** | **1.48%** | 149.97 |
| **Non-Perishable** | 17,740.00 | 295 | **0.91** | **1.51%** | 60.14 |
| **Beverage** | 42,630.00 | 853 | **2.18** | **4.37%** | 49.98 |
| **Merchandise** | 8,950.00 | 40 | **0.46** | **0.20%** | 223.75 |
| **PBM** | 213,158.02 | 1,491 | **10.92** | **7.64%** | 142.96 |

### 📍 CHINA (Total Passengers: 52,709)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 359,180.00 | 2,367 | **6.81** | **4.49%** | 151.74 |
| **Non-Perishable** | 97,400.00 | 1,616 | **1.85** | **3.07%** | 60.27 |
| **Beverage** | 196,490.00 | 4,867 | **3.73** | **9.23%** | 40.37 |
| **Merchandise** | 64,770.00 | 487 | **1.23** | **0.92%** | 133.00 |
| **PBM** | 781,402.00 | 5,404 | **14.82** | **10.25%** | 144.60 |

### 📍 HONG KONG (Total Passengers: 2,950)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 15,560.00 | 106 | **5.27** | **3.59%** | 146.79 |
| **Non-Perishable** | 3,480.00 | 58 | **1.18** | **1.97%** | 60.00 |
| **Beverage** | 7,630.00 | 177 | **2.59** | **6.00%** | 43.11 |
| **Merchandise** | 150.00 | 1 | **0.05** | **0.03%** | 150.00 |
| **PBM** | 52,130.48 | 391 | **17.67** | **13.25%** | 133.33 |

### 📍 INDIA (Total Passengers: 53,037)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 53,060.00 | 359 | **1.00** | **0.68%** | 147.80 |
| **Non-Perishable** | 171,210.00 | 2,188 | **3.23** | **4.13%** | 78.25 |
| **Beverage** | 356,530.00 | 5,938 | **6.72** | **11.20%** | 60.04 |
| **Merchandise** | 13,590.00 | 90 | **0.26** | **0.17%** | 151.00 |
| **PBM** | 1,138,100.95 | 9,025 | **21.46** | **17.02%** | 126.11 |

### 📍 JAPAN (Total Passengers: 24,755)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 182,970.00 | 1,301 | **7.39** | **5.26%** | 140.64 |
| **Non-Perishable** | 48,450.00 | 820 | **1.96** | **3.31%** | 59.09 |
| **Beverage** | 121,420.00 | 2,832 | **4.90** | **11.44%** | 42.87 |
| **Merchandise** | 13,930.00 | 78 | **0.56** | **0.32%** | 178.59 |
| **PBM** | 877,871.11 | 6,558 | **35.46** | **26.49%** | 133.86 |

### 📍 KOREA S.(REP. OF) (Total Passengers: 6,021)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 60,310.00 | 410 | **10.02** | **6.81%** | 147.10 |
| **Non-Perishable** | 18,360.00 | 306 | **3.05** | **5.08%** | 60.00 |
| **Beverage** | 52,570.00 | 1,208 | **8.73** | **20.06%** | 43.52 |
| **Merchandise** | 6,430.00 | 43 | **1.07** | **0.71%** | 149.53 |
| **PBM** | 145,381.84 | 1,106 | **24.15** | **18.37%** | 131.45 |

### 📍 LAOS (PEOP.DEM.REP.) (Total Passengers: 16,185)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 46,080.00 | 335 | **2.85** | **2.07%** | 137.55 |
| **Non-Perishable** | 14,480.00 | 240 | **0.89** | **1.48%** | 60.33 |
| **Beverage** | 38,690.00 | 820 | **2.39** | **5.07%** | 47.18 |
| **Merchandise** | 10,770.00 | 39 | **0.67** | **0.24%** | 276.15 |
| **PBM** | 262,931.14 | 1,853 | **16.25** | **11.45%** | 141.89 |

### 📍 MACAU (Total Passengers: 8,013)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 105,380.00 | 749 | **13.15** | **9.35%** | 140.69 |
| **Non-Perishable** | 26,300.00 | 439 | **3.28** | **5.48%** | 59.91 |
| **Beverage** | 45,070.00 | 1,228 | **5.62** | **15.33%** | 36.70 |
| **Merchandise** | 13,260.00 | 69 | **1.65** | **0.86%** | 192.17 |
| **PBM** | 209,687.67 | 1,517 | **26.17** | **18.93%** | 138.23 |

### 📍 MALAYSIA (Total Passengers: 40,400)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 224,640.00 | 1,536 | **5.56** | **3.80%** | 146.25 |
| **Non-Perishable** | 50,390.00 | 837 | **1.25** | **2.07%** | 60.20 |
| **Beverage** | 122,580.00 | 2,948 | **3.03** | **7.30%** | 41.58 |
| **Merchandise** | 26,770.00 | 99 | **0.66** | **0.25%** | 270.40 |
| **PBM** | 1,091,381.40 | 7,307 | **27.01** | **18.09%** | 149.36 |

### 📍 MALDIVES (Total Passengers: 7,275)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 210,550.00 | 1,481 | **28.94** | **20.36%** | 142.17 |
| **Non-Perishable** | 54,440.00 | 916 | **7.48** | **12.59%** | 59.43 |
| **Beverage** | 90,010.00 | 2,283 | **12.37** | **31.38%** | 39.43 |
| **Merchandise** | 18,200.00 | 128 | **2.50** | **1.76%** | 142.19 |
| **PBM** | 421,493.62 | 2,922 | **57.94** | **40.16%** | 144.25 |

### 📍 MYANMAR (Total Passengers: 10,173)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 9,640.00 | 64 | **0.95** | **0.63%** | 150.62 |
| **Non-Perishable** | 4,020.00 | 67 | **0.40** | **0.66%** | 60.00 |
| **Beverage** | 12,720.00 | 266 | **1.25** | **2.61%** | 47.82 |
| **Merchandise** | 2,720.00 | 13 | **0.27** | **0.13%** | 209.23 |
| **PBM** | 251,886.76 | 1,770 | **24.76** | **17.40%** | 142.31 |

### 📍 SINGAPORE (Total Passengers: 7,103)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 46,540.00 | 341 | **6.55** | **4.80%** | 136.48 |
| **Non-Perishable** | 15,960.00 | 266 | **2.25** | **3.74%** | 60.00 |
| **Beverage** | 29,690.00 | 695 | **4.18** | **9.78%** | 42.72 |
| **Merchandise** | 2,590.00 | 15 | **0.36** | **0.21%** | 172.67 |
| **PBM** | 141,849.45 | 960 | **19.97** | **13.52%** | 147.76 |

### 📍 SRI LANKA (Total Passengers: 8,145)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 39,880.00 | 253 | **4.90** | **3.11%** | 157.63 |
| **Non-Perishable** | 24,120.00 | 341 | **2.96** | **4.19%** | 70.73 |
| **Beverage** | 58,910.00 | 1,155 | **7.23** | **14.18%** | 51.00 |
| **Merchandise** | 3,200.00 | 33 | **0.39** | **0.41%** | 96.97 |
| **PBM** | 557,250.37 | 3,548 | **68.42** | **43.56%** | 157.06 |

### 📍 TAIWAN (Total Passengers: 26,316)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 190,230.00 | 1,274 | **7.23** | **4.84%** | 149.32 |
| **Non-Perishable** | 60,180.00 | 999 | **2.29** | **3.80%** | 60.24 |
| **Beverage** | 98,220.00 | 2,303 | **3.73** | **8.75%** | 42.65 |
| **Merchandise** | 26,680.00 | 106 | **1.01** | **0.40%** | 251.70 |
| **PBM** | 686,237.94 | 5,148 | **26.08** | **19.56%** | 133.30 |

### 📍 THAILAND (Total Passengers: 832,307)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 1,333,000.00 | 11,351 | **1.60** | **1.36%** | 117.43 |
| **Non-Perishable** | 579,340.00 | 9,693 | **0.70** | **1.16%** | 59.77 |
| **Beverage** | 1,098,160.00 | 26,722 | **1.32** | **3.21%** | 41.10 |
| **Merchandise** | 395,430.00 | 1,393 | **0.48** | **0.17%** | 283.87 |
| **PBM** | 11,480,867.63 | 98,809 | **13.79** | **11.87%** | 116.19 |

### 📍 VIETNAM (Total Passengers: 99,198)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 288,740.00 | 2,095 | **2.91** | **2.11%** | 137.82 |
| **Non-Perishable** | 115,210.00 | 1,920 | **1.16** | **1.94%** | 60.01 |
| **Beverage** | 235,010.00 | 4,871 | **2.37** | **4.91%** | 48.25 |
| **Merchandise** | 54,380.00 | 227 | **0.55** | **0.23%** | 239.56 |
| **PBM** | 1,827,995.34 | 13,827 | **18.43** | **13.94%** | 132.20 |

***

## 7. Route-Level Performance Analysis (Top 15 Routes)
The table below details the performance of our Top 15 highest-revenue flight routes. The complete performance database for all 81 routes has been successfully calculated and exported to:
👉 [Route_Level_Performance.csv](file:///C:/Users/Chaiwatwannawit/Desktop/Sale/Route_Level_Performance.csv)

### ✈️ Route DMKHDY (THAILAND | Total Passengers: 68,761)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 116,940.00 | 1,017 | **1.70** | **1.48%** | 114.99 |
| **Non-Perishable** | 43,760.00 | 732 | **0.64** | **1.06%** | 59.78 |
| **Beverage** | 52,300.00 | 1,639 | **0.76** | **2.38%** | 31.91 |
| **Merchandise** | 21,420.00 | 81 | **0.31** | **0.12%** | 264.44 |
| **PBM** | 1,506,363.15 | 13,692 | **21.91** | **19.91%** | 110.02 |

### ✈️ Route DMKCNX (THAILAND | Total Passengers: 89,519)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 95,960.00 | 829 | **1.07** | **0.93%** | 115.75 |
| **Non-Perishable** | 42,520.00 | 711 | **0.47** | **0.79%** | 59.80 |
| **Beverage** | 83,670.00 | 2,267 | **0.93** | **2.53%** | 36.91 |
| **Merchandise** | 35,690.00 | 110 | **0.40** | **0.12%** | 324.45 |
| **PBM** | 1,378,479.95 | 12,160 | **15.40** | **13.58%** | 113.36 |

### ✈️ Route DMKHKT (THAILAND | Total Passengers: 76,994)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 153,120.00 | 1,198 | **1.99** | **1.56%** | 127.81 |
| **Non-Perishable** | 68,080.00 | 1,137 | **0.88** | **1.48%** | 59.88 |
| **Beverage** | 149,630.00 | 3,270 | **1.94** | **4.25%** | 45.76 |
| **Merchandise** | 41,900.00 | 136 | **0.54** | **0.18%** | 308.09 |
| **PBM** | 975,830.78 | 7,950 | **12.67** | **10.33%** | 122.75 |

### ✈️ Route DMKDAD (VIETNAM | Total Passengers: 24,869)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 98,040.00 | 710 | **3.94** | **2.85%** | 138.08 |
| **Non-Perishable** | 31,380.00 | 523 | **1.26** | **2.10%** | 60.00 |
| **Beverage** | 63,760.00 | 1,389 | **2.56** | **5.59%** | 45.90 |
| **Merchandise** | 15,300.00 | 70 | **0.62** | **0.28%** | 218.57 |
| **PBM** | 613,564.84 | 4,507 | **24.67** | **18.12%** | 136.14 |

### ✈️ Route DMKMLE (MALDIVES | Total Passengers: 7,275)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 210,550.00 | 1,481 | **28.94** | **20.36%** | 142.17 |
| **Non-Perishable** | 54,440.00 | 916 | **7.48** | **12.59%** | 59.43 |
| **Beverage** | 90,010.00 | 2,283 | **12.37** | **31.38%** | 39.43 |
| **Merchandise** | 18,200.00 | 128 | **2.50** | **1.76%** | 142.19 |
| **PBM** | 421,493.62 | 2,922 | **57.94** | **40.16%** | 144.25 |

### ✈️ Route DMKURT (THAILAND | Total Passengers: 50,946)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 98,300.00 | 829 | **1.93** | **1.63%** | 118.58 |
| **Non-Perishable** | 35,480.00 | 593 | **0.70** | **1.16%** | 59.83 |
| **Beverage** | 52,880.00 | 1,443 | **1.04** | **2.83%** | 36.65 |
| **Merchandise** | 33,390.00 | 123 | **0.66** | **0.24%** | 271.46 |
| **PBM** | 574,091.41 | 4,958 | **11.27** | **9.73%** | 115.79 |

### ✈️ Route DMKKKC (THAILAND | Total Passengers: 44,585)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 33,660.00 | 309 | **0.75** | **0.69%** | 108.93 |
| **Non-Perishable** | 15,240.00 | 252 | **0.34** | **0.57%** | 60.48 |
| **Beverage** | 29,110.00 | 810 | **0.65** | **1.82%** | 35.94 |
| **Merchandise** | 19,040.00 | 67 | **0.43** | **0.15%** | 284.18 |
| **PBM** | 673,851.37 | 5,898 | **15.11** | **13.23%** | 114.25 |

### ✈️ Route DMKKBV (THAILAND | Total Passengers: 34,006)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 56,220.00 | 420 | **1.65** | **1.24%** | 133.86 |
| **Non-Perishable** | 20,540.00 | 343 | **0.60** | **1.01%** | 59.88 |
| **Beverage** | 56,880.00 | 1,207 | **1.67** | **3.55%** | 47.13 |
| **Merchandise** | 13,840.00 | 57 | **0.41** | **0.17%** | 242.81 |
| **PBM** | 608,263.11 | 4,693 | **17.89** | **13.80%** | 129.61 |

### ✈️ Route BKKHKT (THAILAND | Total Passengers: 44,763)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 102,560.00 | 786 | **2.29** | **1.76%** | 130.48 |
| **Non-Perishable** | 57,840.00 | 965 | **1.29** | **2.16%** | 59.94 |
| **Beverage** | 144,220.00 | 2,931 | **3.22** | **6.55%** | 49.21 |
| **Merchandise** | 17,460.00 | 63 | **0.39** | **0.14%** | 277.14 |
| **PBM** | 393,639.93 | 2,936 | **8.79** | **6.56%** | 134.07 |

### ✈️ Route DMKPEN (MALAYSIA | Total Passengers: 18,248)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 86,760.00 | 594 | **4.75** | **3.26%** | 146.06 |
| **Non-Perishable** | 20,940.00 | 347 | **1.15** | **1.90%** | 60.35 |
| **Beverage** | 48,800.00 | 1,171 | **2.67** | **6.42%** | 41.67 |
| **Merchandise** | 14,000.00 | 52 | **0.77** | **0.28%** | 269.23 |
| **PBM** | 530,214.14 | 3,575 | **29.06** | **19.59%** | 148.31 |

### ✈️ Route DMKCMB (SRI LANKA | Total Passengers: 8,145)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 39,880.00 | 253 | **4.90** | **3.11%** | 157.63 |
| **Non-Perishable** | 24,120.00 | 341 | **2.96** | **4.19%** | 70.73 |
| **Beverage** | 58,910.00 | 1,155 | **7.23** | **14.18%** | 51.00 |
| **Merchandise** | 3,200.00 | 33 | **0.39** | **0.41%** | 96.97 |
| **PBM** | 557,250.37 | 3,548 | **68.42** | **43.56%** | 157.06 |

### ✈️ Route DMKUTH (THAILAND | Total Passengers: 44,057)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 63,020.00 | 571 | **1.43** | **1.30%** | 110.37 |
| **Non-Perishable** | 27,380.00 | 459 | **0.62** | **1.04%** | 59.65 |
| **Beverage** | 47,230.00 | 1,221 | **1.07** | **2.77%** | 38.68 |
| **Merchandise** | 32,730.00 | 111 | **0.74** | **0.25%** | 294.86 |
| **PBM** | 497,935.83 | 4,463 | **11.30** | **10.13%** | 111.57 |

### ✈️ Route DMKCEI (THAILAND | Total Passengers: 36,294)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 50,920.00 | 442 | **1.40** | **1.22%** | 115.20 |
| **Non-Perishable** | 21,480.00 | 368 | **0.59** | **1.01%** | 58.37 |
| **Beverage** | 28,530.00 | 814 | **0.79** | **2.24%** | 35.05 |
| **Merchandise** | 18,250.00 | 62 | **0.50** | **0.17%** | 294.35 |
| **PBM** | 481,816.62 | 4,361 | **13.28** | **12.02%** | 110.48 |

### ✈️ Route DMKHAN (VIETNAM | Total Passengers: 21,033)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 52,340.00 | 373 | **2.49** | **1.77%** | 140.32 |
| **Non-Perishable** | 22,570.00 | 374 | **1.07** | **1.78%** | 60.35 |
| **Beverage** | 56,170.00 | 1,084 | **2.67** | **5.15%** | 51.82 |
| **Merchandise** | 16,030.00 | 65 | **0.76** | **0.31%** | 246.62 |
| **PBM** | 432,216.53 | 3,322 | **20.55** | **15.79%** | 130.11 |

### ✈️ Route DMKJHB (MALAYSIA | Total Passengers: 13,955)
| Category | Total Revenue (THB) | Quantity (Units) | RPP (THB/Pax) | TUR (%) | Average Unit Price (THB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Perishable** | 98,720.00 | 661 | **7.07** | **4.74%** | 149.35 |
| **Non-Perishable** | 22,190.00 | 369 | **1.59** | **2.64%** | 60.14 |
| **Beverage** | 56,670.00 | 1,336 | **4.06** | **9.57%** | 42.42 |
| **Merchandise** | 9,240.00 | 34 | **0.66** | **0.24%** | 271.76 |
| **PBM** | 352,624.37 | 2,314 | **25.27** | **16.58%** | 152.39 |
