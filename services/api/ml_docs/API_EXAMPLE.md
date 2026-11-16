# Expected request and response shape

```
POST /v1/heatshield/windows
Content-Type: application/json
```

```json
{
  "preferences": {
    "min_comfort_c": 21,
    "max_comfort_c": 29,
    "prefers_clouds": true,
    "prefers_rain": false,
    "prefer_evenings": true,
    "activity": "walking"
  },
  "days": 3,
  "limit": 6
}
```

Response is assembled from **real provider data**, not fixed sample numbers, and contains:

- `city`: `Dubai`, `country`: `United Arab Emirates`
- `windows`: sorted upcoming time slots, each with actual modeled apparent temperature, preference-match score, caution flags and provider-vs-ML method
- `weather_source`, `weather_url`, `data_kind`, `limitations`
- `prediction_method`, `ml_status`, `ml_evaluation_available`

Before the model is trained, `ml_status` is `not_trained` and `prediction_method` is `third_party_forecast_no_ml`. If provider access is down, HTTP 503 with no fabricated temperature. OpenAPI interactive documentation is available at `/docs` in the standalone service.
