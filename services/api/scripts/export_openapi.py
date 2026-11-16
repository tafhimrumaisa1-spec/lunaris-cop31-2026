"""Write the served OpenAPI to stdout so the lead can diff it against contracts/openapi-target.yaml."""
import json
import sys

from lunaris_api.app import create_app
from lunaris_api.config import Settings

app = create_app(Settings.for_tests(database_url="sqlite://", auto_create_schema=False, seed_demo_data=False))
json.dump(app.openapi(), sys.stdout, indent=2, sort_keys=True)
