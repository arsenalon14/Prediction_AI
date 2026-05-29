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

### Pair Route
The atomic unit of catering decisions: DMK → MLE → DMK. All catering is loaded at DMK hub. No replenishment at MLE. All unsold perishables are disposed of at DMK on the return leg.

### Censored Observation
A historical flight where total pair-route sales equalled or exceeded the quantity loaded (`Y_total >= Q_loaded`). True demand was higher than observed; the Tobit model recovers the latent demand distribution.

### PBM (Pre-Booked Meal)
A hot meal booked by the passenger before the flight through the PSS system. PBM buyers are subtracted from the total passenger count when computing the Net BoB Market.

### Critical Ratio (F*)
The target service level derived from the Newsvendor financial parameters:
`F* = C_u / (C_u + C_o) = (price − cost) / price`
Determines the z-score applied to σ to set the safety stock buffer above μ.
