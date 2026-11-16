# Source register

| Source | Endpoint | Data kind | Main caveat |
|---|---|---|---|
| Open-Meteo Previous Runs | https://previous-runs-api.open-meteo.com/v1/forecast | Fixed-24-hour-lead historical model forecast | Archived model output, not measured truth |
| Open-Meteo Historical Weather | https://archive-api.open-meteo.com/v1/archive | Historical reanalysis reference | Model-based, may share upstream information |
| Open-Meteo Forecast | https://api.open-meteo.com/v1/forecast | Live forecast | Spatial gridpoint; mixed lead time; provider outage possible |

All requests pinned to Dubai (25.2048 N, 55.2708 E) and Asia/Dubai. The data cache retains timestamp and requested provider URL. Check https://open-meteo.com/en/terms for commercial terms, rate limits and attribution.
