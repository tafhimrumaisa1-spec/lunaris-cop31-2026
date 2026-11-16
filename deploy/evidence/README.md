No reviewed Earth Engine data is bundled. Never place example measurements into the production evidence directory.

Run the provided Earth Engine export manually, review its observation counts/cloud masks, then import the CSV using
`services/api/scripts/import_atlas_evidence.py` with `--ack-reviewed` and a reviewer name. The API exposes
`GET /v1/action/atlas/evidence`. It will stay `not_imported` until a real reviewed dataset is installed.
