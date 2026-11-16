"""Read a reviewed, locally supplied Dubai indicator export; never infer unverified sites.

The dataset is *not* downloaded or generated implicitly. Earth Engine exports must be
reviewed and imported with scripts/import_atlas_evidence.py before this can return data.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import os

from .catalog import AREAS

ALLOWED_IDS = {x['id'] for x in AREAS}
FIELDS = ('trees', 'grass', 'built', 'bare', 'water', 'ndvi', 'lst_c')

def evidence_path() -> Path | None:
    raw = os.environ.get('LUNARIS_ATLAS_EVIDENCE_FILE', '').strip()
    return Path(raw) if raw else None

def read_indicators(path: Path | None = None) -> dict:
    path = evidence_path() if path is None else path
    if path is None or not path.is_file():
        return {'status': 'not_imported', 'message': 'No reviewed satellite indicator export is installed.', 'indicators': []}
    try:
        dataset = json.loads(path.read_text(encoding='utf-8'))
        if dataset.get('schema_version') != '1.0' or not isinstance(dataset.get('indicators'), list):
            raise ValueError('Wrong evidence schema')
        if not isinstance(dataset.get('source'), dict) or not dataset['source'].get('dataset_period'):
            raise ValueError('Missing provenance')
        checked=[]
        seen=set()
        for row in dataset['indicators']:
            if not isinstance(row, dict) or row.get('area_id') not in ALLOWED_IDS or row['area_id'] in seen:
                raise ValueError('Unknown or duplicate area ID')
            seen.add(row['area_id'])
            item={'area_id': row['area_id']}
            for key in FIELDS:
                value = row.get(key)
                if value is not None:
                    if not isinstance(value, (float,int)) or not float('-inf') < value < float('inf'):
                        raise ValueError(f'Invalid {key}')
                    if key in ('trees','grass','built','bare','water') and not 0 <= value <= 1:
                        raise ValueError(f'Invalid fraction {key}')
                    if key=='ndvi' and not -1 <= value <= 1:
                        raise ValueError('Invalid NDVI')
                    if key=='lst_c' and not -40 <= value <= 85:
                        raise ValueError('Out-of-range surface temperature')
                item[key]=value
            checked.append(item)
        return {'status':'reviewed_area_indicators', 'message':'Area-level exploratory satellite indicators. Not verified project sites, tree counts, or intervention impact.', 'source':dataset['source'], 'indicators':checked}
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, OSError):
        return {'status':'invalid_or_unreviewed', 'message':'The installed evidence export failed validation. No measurements are displayed.', 'indicators':[]}
