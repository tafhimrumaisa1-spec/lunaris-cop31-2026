# LUNARIS Consumer Intelligence — Final v3.1 testing handoff

## What has been implemented

- **Explore**: six real Dubai venue entries with source-attributed descriptions from Visit Dubai or Dubai DET. Search by name/area, café/hotel category, map lookup and direct evidence link. No opening hours, star ratings, site-specific indoor temperatures, CO₂e or eco-scores are invented. The verified venue catalogue is small and editorial, *not* an exhaustive or live listings provider. Source-reviewed practices and DST Stamp recognitions have different evidentiary meaning.
- **HeatShield**: duration, daylight/sun setting, daypart filter and ranked candidate starts. The decision summary examines hourly forecast conditions **across the activity duration** (as available), and links to Explore. It does not infer location-level shade, clinical heat stress, verified indoor comfort or safe passage. Optional ML correction is not trained/validated in this release.
- **FoodPrint**: two-barcode identity and ingredient comparison via Open Food Facts, alongside the prior single-barcode lookup and manual product LCA comparison. No brand is ranked by carbon unless the user supplies source-reported product footprints; manual inputs remain *unverified* and cannot substitute for audit.
- **GreenMiles**: specific user-supplied model name, fuel/EV efficiency and comparison to a second efficiency with the same powertrain, per-passenger emissions or electricity. Optional EV grid factor is explicitly **user supplied** (not a Dubai default). Upstream and manufacturing stages are outside the estimate; fuel results are tailpipe CO₂, not full lifecycle CO₂e.
- **WattFlow**: appliance rated/estimated power, count, duration before/after and marginal DEWA electricity-component bill effect using currently entered monthly baseline. Rejected an appliance modeled reduction greater than the supplied household baseline. Actual HVAC compressor cycling and smart-meter readings are not available.
- **Existing app**: original homepage, Dubai Action Atlas, guest preferences and FastAPI endpoints preserved.

## Local test

From the extracted ZIP root:

```bash
cd dist
python -m http.server 5173
```

Open `http://localhost:5173/app/` in Chrome. `dist` is a static preview. For guest accounts, preference sync, Action Atlas join functionality and AI API, also start the FastAPI backend according to `START_HERE.md`.

### QA by page

1. **Explore:** verify six sourced venue cards, search `Marina` yields Crowne Plaza Dubai Marina, switch to Café yields Spill the Bean, click original source and map lookup; treat all hours as unverified.
2. **HeatShield:** wait for live Open-Meteo to load, choose Run/90 minutes/Direct Sun and compare against Walk/15 minutes/Mostly Shaded; select Morning and Evening. Ensure missing forecast shows a clear unavailable state. Click Explore.
3. **FoodPrint:** look up two **different** valid product barcodes; when online, names and ingredients should appear if Open Food Facts knows them. Neither product gets a carbon ranking. Test user-reported published LCA sources separately, and reject missing/invalid HTTPS links.
4. **GreenMiles:** input 7.0 L/100km petrol vs 5.0 L/100km petrol on a 20 km journey. Try EV with 17 kWh/100 km and grid factor empty, then with a *documented user-supplied* example value. Ensure EV without factor does not claim zero emissions.
5. **WattFlow:** set monthly use to 2500 kWh, appliance 1200 W, 6 hours/day versus 4 hours/day, check estimated 72 kWh/month reduction. Try unrealistic power > total monthly baseline, which should reject the scenario.
6. **Action Atlas:** check mapped area cases remain conceptual and only reviewed satellite evidence is labeled measured. Join Interest is an expression of interest only.
7. **Desktop + mobile:** check all tool panels, source links, interactive inputs, navigation, and the browser console.

## Verification in build environment

- `node --check dist/app/app.js`: passed.
- FastAPI pytest suite: **131 passed, 1 skipped** (live network).
- Chromium interactive DOM test using `page.set_content` with inlined local HTML/CSS/JS: 6 Explore cards, search filtering, café filtering, appliance result, petrol + EV calculations, HeatShield daypart, mobile width, and no page errors.
- Browser navigation to localhost was blocked by policy, so this is **not** a verified public deployed site test. Remote network APIs and external sites weren't exercised by the offline Chromium test.

## Still required before production

1. Obtain a real public hostname and deploy frontend, FastAPI and DB with HTTPS, environment secrets and monitoring. Test the hosted experience.
2. Train and evaluate the Dubai ML model on real historical climate observations. Don't call rule-based decisions 'validated AI'.
3. Run and review Google Earth Engine exports before describing Action Atlas candidates as satellite-detected areas.
4. Obtain independently comparable product LCAs and license/permission if building a commercial brand-specific footprint database.
5. Source regional vehicle energy data and electricity grid intensity before using UAE-specific CO₂e; a manufacturer name alone cannot establish fuel economy.
6. Obtain business-provider/partner integrations for live hours, availability, accessibility and more venues; don't infer environmental practices from venue type alone.
7. Test and monitor vendor API usage rights, privacy policy, storage limits, and rate limiting.

### Sources used for the Explore seed
- Dubai DET tourism stamp: https://www.dubaidet.gov.ae/en/about-det/initiatives/dubai-sustainable-tourism/dubai-sustainable-tourism-stamp
- Dubai DET silver list: https://www.dubaidet.gov.ae/en/about-det/initiatives/dubai-sustainable-tourism/dubai-sustainable-tourism-stamp/dst-stamp-silver-tier
- Visit Dubai Spill the Bean: https://www.visitdubai.com/en/restaurants/spill-the-bean
- Open Food Facts API: https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/
- DEWA tariff source: https://www.dewa.gov.ae/en/consumer/billing/slab-tariff
