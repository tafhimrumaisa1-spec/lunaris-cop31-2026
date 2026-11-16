# LUNARIS v3 — Consumer Decision Tools

## Updated modules

### FoodPrint / Product Intelligence beta
- Keeps the original category-level food lifecycle calculator.
- Adds barcode-based **product identity** lookup through Open Food Facts API v3, with graceful network failure. The response does **not** establish the product's emissions.
- Adds a manual, source-linked comparison of two *published* product footprints in kg CO2e/kg with an explicitly selected shared boundary. This is **user-reported and unverified** until reviewed. No company emissions or rankings are invented. The analyst must check market, publication year, boundaries, ingredients and verification before communicating a ranking.
- Next: maintain an audited brand/product catalogue, verify data licencing and provenance, add market-specific product LCA evidence and consistent functional units. Product lookup requires internet access.

### HeatShield / Activity planner
- Keeps existing actual Open-Meteo weather and optional validated ML predictions.
- Adds activity duration, direct-sun / shade / indoor context, and actionable cautions. Ranking adjusts for activity intensity, duration and exposed daylight.
- Explains *which hours are a closer preference fit* without issuing a medical safety certification. The indoor setting specifically requires venue verification. Explore alternative link included; **no live cafe inventory** is falsely implied.
- City-grid forecast is not a street-specific microclimate, UV / radiant heat / wet-bulb measurement, or personalized medical fitness assessment. For emergency heat alerts follow official authorities.

### GreenMiles / Your vehicle
- Retains original UK-factor mode comparison.
- Adds an efficiency-based estimate for a **specific model** using published petrol/diesel L/100km or EV kWh/100km. Fuel tailpipe factors are illustrative; upstream and manufacturing impacts excluded. EVs report kWh without an unverified Dubai grid factor. The user must supply the correct model/year specification.
- Next: source production-region-specific vehicle variants and local grid and upstream emission factors; implement comparable well-to-wheel or lifecycle boundaries.

### WattFlow / Savings scenarios
- Retains DEWA electricity slab tariff estimator with published November 2026 fuel surcharge.
- Adds adjustable percentage-reduction savings scenario with marginal progressive slab arithmetic and one-year illustration. This does not infer household appliances or guarantee energy savings.
- Next: appliance-level wattage/duty-cycle models and dynamic official tariff updates.

## Local smoke test
1. Serve `dist` with `python -m http.server 5173`; open `http://localhost:5173/app/`.
2. Open Choices > FoodPrint; lookup a real barcode when online and verify no false footprint is displayed. Enter two sourced footprints to see source-attributed **unverified** comparison.
3. Open Choices > GreenMiles; enter a documented combined cycle efficiency; switch between petrol/diesel/EV.
4. Open Choices > WattFlow; change kWh and reduction target; assess base bill vs savings.
5. Open HeatShield; choose duration and setting, see updated timing explanations after a live forecast loads.
6. Run backend separately if you need API-driven preference sync or ML-enhanced endpoints; without trained model fallback is explicitly labelled.

## Verification completed in packaging environment
- `node --check dist/app/app.js`
- 131 backend tests passed, 1 skipped live network test
- All new DOM controls found in shipped HTML
- Browser navigation blocked by environment policy. **Live browser QA not claimed.**

## Caveats
Product-discovery platform availability and rate limits vary; Open Food Facts licensing and attribution should be checked before commercial deployment. Neither manual product footprints nor estimated savings should be described as achieved environmental reductions.
