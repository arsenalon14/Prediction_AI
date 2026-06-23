# Domain Glossary — TAA Perishable Demand Forecasting (DMK-MLE-DMK)

## Terms

### Net BoB Market
The number of passengers on a specific upcoming flight who are eligible to buy from the Buy-on-Board cart.
`Net BoB Market = total_pax − pbm_count`
Passengers who have pre-booked a meal (PBM) are excluded because their probability of buying a second hot meal from the cart is near zero.

### Flight-Specific Forecast
A Q* recommendation that is scaled to a specific upcoming flight's **Net BoB Market**. Requires both a passenger manifest and PBM data for that flight. Cannot be produced without these inputs.

### Historical Baseline
The raw Tobit MLE output (μ, σ) estimated from historical pair-route sales. Represents average demand across all historical flights in the dataset, without adjustment for a specific flight's passenger volume or PBM count. **Not a valid operational recommendation on its own.**

### Rotation
The atomic unit of catering decisions. An ordered sequence of flights starting and ending at the same Loading Station. The catering cart is loaded once at the Loading Station, sold throughout all legs, and all unsold inventory is disposed of when the aircraft returns to the Loading Station. Replaces "Pair Route" as the general case.

### Rotation Loading Date
The canonical date of a rotation instance, defined as the calendar `FlightDate` of the first leg (Leg 0) of the rotation departing from the Loading Station. For legs operating on subsequent calendar days (e.g. overnight flights), their rotation instance is mapped back to the Loading Date using schedule-defined day offsets (e.g., a return leg on Day N+1 maps back to Loading Date N). This ensures correct S1+S2 sales and passenger aggregation.

### Loading Station
An airport where the catering cart is physically loaded and reconciled. Confirmed locations include DMK, BKK, CNX, and HKT.

### Rotation Schedule Validity Window
The specific start and end date boundaries during which a flight-to-rotation configuration is active. Because airline flight numbers and rotation schedules are modified during IATA Summer and Winter schedule transitions, each rotation configuration in the Schedule File is mapped to a validity window. The pipeline dynamically selects the correct rotation mapping matching a flight's calendar `FlightDate` to ensure accurate multi-year historical demand aggregation.

### Schedule File
A CSV file containing the active flight-to-rotation mappings, validity windows, day offsets, and loading stations for the entire route network. Instead of hardcoding rotation schedules or building complex form-based web editors, the system dynamically loads this file. The operations team can edit this configuration in Excel and upload a new Schedule File only when a flight schedule change occurs (e.g. at the turn of an IATA season), keeping configuration management extremely simple and robust.

### Route
A logical grouping of rotations departing from the same Loading Station to the same destination market. A Route is defined by a unique Loading Station and a destination, sharing historical data directories, uploads, and a common active menu profile. If the same city-pair has flights catered at both ends (e.g., DMK→CNX and CNX→DMK), they are treated as two distinct Routes (e.g., `DMK-CNX` and `CNX-DMK`) to align with their respective physical Loading Stations. **Onboarding Prerequisite:** To activate a Route and run forecasts, the operations team must upload or copy historical sales, passenger, and wastage CSV files (following the standard PSS schema) into the Route's defined data directory, allowing the Tobit MLE model to learn the true demand rates directly from empirical data.


### Pair Route
A 2-leg rotation departing and returning to the same Loading Station. Special case of Rotation. DMK-MLE remains a Pair Route.




### Censored Observation
A historical flight where total pair-route sales equalled or exceeded the quantity loaded (`Y_total >= Q_loaded`). True demand was higher than observed; the Tobit model recovers the latent demand distribution.

### PBM (Pre-Booked Meal)
A hot meal booked by the passenger before the flight through the PSS system. PBM buyers are subtracted from the total passenger count when computing the Net BoB Market.

### Critical Ratio (F*)
The target service level derived from the Newsvendor financial parameters:
`F* = C_u / (C_u + C_o) = (price − cost) / price`
Determines the z-score applied to σ to set the safety stock buffer above μ.

### Proxy Item
A historical product code linked to a newly introduced seasonal product. Used in Theory 6 (Product Substitution / Cold Start) to provide an initial expected demand baseline ($\mu_{\text{rate}}, \sigma_{\text{rate}}$) based on historical sales of a mathematically or flavor-profile similar product. The proxy item is typically inactive in the current season's menu.

### Weighted Tobit MLE / Recency Weighting
A mechanism inside Theory 2 (Demand Censoring) that assigns a higher sample weight (`RECENCY_WEIGHT_FACTOR = 10.0`) to recent post-flight actuals (May/June 2026) compared to historical data (2024/2025). This forces the Tobit optimization to adapt rapidly to recent structural demand drops and prevent over-catering, while preserving older history as a robust secondary baseline.

### Expected Profitability Override
A margin-maximizing constraint that overrides the standard continuous Newsvendor critical ratio. When the expected financial profit of carrying the optimal rounded-up integer quantity $Q^*$ is non-positive ($E[\text{Profit}(Q^*)] \le 0$), the model overrides the baseline and recommends a zero load ($Q^* = 0$). This occurs when the expected cost of wastage (overage) exceeds the expected sales margin (underage) of the minimum load unit, optimizing overall flight margin to the absolute maximum.

**Exception (Grace Period):** To avoid prematurely discontinuing new products before gathering empirical demand, brand new items with no direct sales history utilizing a Proxy Item (Theory 6) are bypassed from this override and always load a minimum of 1 unit.

### Year-over-Year (YoY) Demand Scaling
A calibration mechanism that adjusts pre-2026 historical demand rates and censoring caps for established items based on their product-specific 2026 vs. 2025 performance. For brand-new 2026 products, the system-wide average YoY shift is applied to their historical proxy baseline. This eliminates 'phantom volatility' caused by year-over-year structural demand drops, preventing the Newsvendor model from overinflating safety stock recommendations.

### Active SKU Registry
A dynamic array of active SKU codes defined on a per-route basis in `routes.json` (under `active_skus`). Instead of modifying individual item booleans in `active_menu.json`, this configuration serves as the canonical list of which products are offered for on-board sale on any given route, separating static SKU metadata from dynamic route-specific configurations.






