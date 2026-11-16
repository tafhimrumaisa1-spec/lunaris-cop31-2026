"""Validate a Google Earth Engine neighborhood CSV and save an explicitly reviewed JSON.

Usage: python scripts/import_atlas_evidence.py export.csv --out ../../deploy/evidence/dubai_area_indicators.json \
       --period 2025-01-01/2025-12-31 --reviewer 'Analyst initials' --ack-reviewed

Important: acknowledgement means the human checked observations, masking, and geographic scope.
"""
import argparse, csv, json, math, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from lunaris_api.action_atlas.evidence import ALLOWED_IDS, FIELDS

def parse_csv(path:Path):
    results=[]; seen=set()
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader=csv.DictReader(handle)
        columns=set(reader.fieldnames or [])
        if 'area_id' not in columns or not set(FIELDS).issubset(columns):
            raise ValueError('CSV needs area_id, trees, grass, built, bare, water, ndvi, lst_c columns')
        for row in reader:
            area=row['area_id'].strip()
            if area not in ALLOWED_IDS or area in seen:
                raise ValueError('Unknown or duplicate area_id: '+area)
            seen.add(area); item={'area_id':area}
            for key in FIELDS:
                raw=str(row.get(key,'')).strip()
                if not raw or raw.lower() in {'nan','null'}:
                    item[key]=None
                    continue
                value=float(raw)
                if not math.isfinite(value): raise ValueError('Non-finite '+key)
                if key in {'trees','grass','built','bare','water'} and not (0 <= value <= 1):
                    raise ValueError(key+' must be in [0,1]')
                if key=='ndvi' and not (-1 <= value <= 1): raise ValueError('NDVI out of range')
                if key=='lst_c' and not (-40 <= value <= 85): raise ValueError('LST out of range')
                item[key]=round(value,5)
            if all(item.get(f) is None for f in FIELDS):
                raise ValueError('Missing all indicators for '+area)
            results.append(item)
    if not results: raise ValueError('No data records')
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument('csv', type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--period',required=True,help='Date range of actual export, e.g. 2025-01-01/2025-12-31')
    p.add_argument('--reviewer',required=True);p.add_argument('--ack-reviewed',action='store_true')
    args=p.parse_args()
    if not args.ack_reviewed: p.error('You must explicitly acknowledge human review of exported observations and masking')
    if len(args.reviewer.strip())<2: p.error('Reviewer must be named')
    periods=args.period.split('/')
    if len(periods)!=2 or any(len(p)!=10 for p in periods): p.error('Use YYYY-MM-DD/YYYY-MM-DD')
    for dt in periods: datetime.strptime(dt,'%Y-%m-%d')
    rows=parse_csv(args.csv)
    out={
      'schema_version':'1.0',
      'source':{'type':'Google Earth Engine user-executed export',
                'datasets':['GOOGLE/DYNAMICWORLD/V1','COPERNICUS/S2_SR_HARMONIZED','LANDSAT/LC08/C02/T1_L2'],
                'script':'lunaris_api/action_atlas/export_gee.js',
                'dataset_period':args.period,'reviewed_by':args.reviewer.strip(),
                'imported_at_utc':datetime.now(timezone.utc).isoformat(),
                'scope':'600m illustrative neighborhood circles; NOT planting/volunteer sites',
                'limitations':['Land-surface temperature is not pedestrian air temperature',
                 'Dynamic World probabilities and NDVI do not prove any planting feasibility',
                 'Valid pixel counts and cloud screening require independent review',
                 'No evidence of landowner permission or project outcome']},
      'indicators': rows
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,allow_nan=False),encoding='utf-8')
    print(f'Imported {len(rows)} reviewed neighborhoods into {args.out}')
if __name__=='__main__':main()
