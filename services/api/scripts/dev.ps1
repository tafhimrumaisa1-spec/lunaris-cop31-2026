$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = "src;..\..\packages\contracts;..\..\packages\choices\src;..\..\packages\places\src"
$env:LUNARIS_ENV = 'development'
$env:LUNARIS_DATABASE_URL = 'sqlite:///./.data/lunaris_dev.db'
$env:LUNARIS_CORS_ALLOW_ORIGINS = 'http://localhost:4173,http://localhost:3000'
$env:LUNARIS_AUTO_CREATE_SCHEMA = 'true'
$env:LUNARIS_SEED_DEMO_DATA = 'true'
$env:LUNARIS_WEATHER_PROVIDER = 'lunaris_api.integrations.builtin:OpenMeteoWeatherProvider'
$env:LUNARIS_CLIMATE_ENGINE = 'lunaris_api.integrations.builtin:ComfortWindowEngine'
$env:LUNARIS_CHOICES_ENGINE = 'lunaris_api.integrations.builtin:VerifiedChoicesEngine'
python -m uvicorn lunaris_api.main:app --host 127.0.0.1 --port 8000 --reload
