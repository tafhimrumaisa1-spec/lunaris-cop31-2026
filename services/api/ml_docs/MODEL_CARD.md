# LUNARIS Dubai Climate Intelligence — model card (template)

**Status:** NOT TRAINED / NOT EVALUATED AGAINST ACTUAL DUBAI DATA IN THIS PACKAGE.

## Research target
Experimental bias correction for 24-hour lead apparent-temperature hourly forecasts at one Dubai gridpoint. Prediction reference is Open-Meteo historical reanalysis, **not independent measured heat-stress ground truth**. Evaluation of model-vs-reanalysis agreement is not proof of health/safety accuracy or superior forecasting against weather stations.

## Sources
- Fixed-lead historical forecasts: https://open-meteo.com/en/docs/previous-runs-api
- Archived reanalysis reference: https://open-meteo.com/en/docs/historical-weather-api
- Live forecast integration: https://open-meteo.com/en/docs
- Data access and licenses: https://open-meteo.com/en/terms

## Method
Chronologically split by complete days (70% train, 15% validation, 15% test), two fixed candidate gradient-boosting configurations selected by validation MAE, compare with raw 24-hour forecast baseline; if model doesn't beat raw forecast on validation, deploy raw forecast. Never use test to select deployment. Five worst held-out prediction failures are reported. Feature list in `lunaris_climate/ml.py`.

## Missingness and leakage
Rows missing any feature/target are excluded; dropped-row fractions should be recorded in future reports. Only use forecast columns available ~24 hours before valid time, seasonal calendar features; no future outcomes. Reference archive may share underlying modeled data with forecasts. Beware exact lead-time alignment and missingness. Refits train+validation after validation-gated selection.

## Deployment caveat
Live forecast values have mixed horizons unlike fixed-lead training. A public MVP can use raw third-party forecast + transparent preference scoring, with ML explicitly marked experimental; compare actual vintage and retrain before claiming operational skill. Real independently observed weather station data is needed for stronger claims.

## Intended use
Educational personalized scheduling of outdoor activity, not medical risk classification, no claims of safety, no street-level conditions.

## Limitations
Single location; model-dependent reanalysis; user comfort range self-declared; no measured outcome improvement; weather advice should follow official warning systems.

## Evaluation result
**Not available until `scripts/train.py` executes against real downloaded data.** The generated `artifacts/evaluation.json` will contain the measured results.
