#!/usr/bin/env python3
"""Reproducible Dubai historical ambient heat case study, with NASA POWER data.

No model is trained. No local heat-island observation is inferred. The baseline
comparison is a hold-out 2025 error check for two simple reference estimators.

Usage:
python research/dubai_heat_case.py --output dist/app/action-atlas/dubai-heat-case/nasa_power_metrics.json

Requires internet access to NASA POWER. Writes measurement data only on success.
"""
import argparse
import json
import math
import statistics
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

LAT = 25.2769
LON = 55.2962
PARAMS = ['T2M_MAX', 'T2M', 'RH2M']
API = 'https://power.larc.nasa.gov/api/temporal/daily/point'
SOURCE_DOC = 'https://power.larc.nasa.gov/docs/services/api/temporal/daily/'


def build_url():
    query = dict(parameters=','.join(PARAMS), community='AG', latitude=str(LAT), longitude=str(LON),
                 start='20240101', end='20251231', format='JSON', **{'time-standard': 'UTC'})
    return API + '?' + urllib.parse.urlencode(query)


def valid_number(value):
    return isinstance(value, (int, float)) and math.isfinite(value) and value != -999


def process(payload):
    values = payload['properties']['parameter']
    rows = []
    start = date(2024, 1, 1)
    end = date(2025, 12, 31)
    current = start
    missing = []
    while current <= end:
        k = current.strftime('%Y%m%d')
        v = {name: values.get(name, {}).get(k) for name in PARAMS}
        if all(valid_number(x) for x in v.values()):
            rows.append(dict(date=current.isoformat(), **{x: round(float(v[x]), 3) for x in PARAMS}))
        else:
            missing.append(k)
        current += timedelta(days=1)
    if len(rows) < 700 or len(missing) > 31:
        raise ValueError(f'Insufficient complete NASA POWER records: {len(rows)} usable days, {len(missing)} missing')
    lookup = {x['date']: x for x in rows}
    summer_2024 = [x['T2M_MAX'] for x in rows if '2024-06-01' <= x['date'] <= '2024-08-31']
    summer_2025 = [x['T2M_MAX'] for x in rows if '2025-06-01' <= x['date'] <= '2025-08-31']
    if len(summer_2024) < 85 or len(summer_2025) < 85:
        raise ValueError('Missing more than 7 days from one of the June–August evaluation windows')
    persistence = []
    prior_year = []
    reference_days = []
    # Holdout 2025 June–August; 2024 reference not used to train any model.
    for day_num in range((date(2025,8,31)-date(2025,6,1)).days + 1):
        d = date(2025,6,1)+timedelta(days=day_num)
        actual = lookup.get(d.isoformat())
        if not actual: continue
        day_before = lookup.get((d-timedelta(days=1)).isoformat())
        year_before = lookup.get(d.replace(year=2024).isoformat())
        if day_before:
            persistence.append(abs(actual['T2M_MAX']-day_before['T2M_MAX']))
        if year_before:
            prior_year.append(abs(actual['T2M_MAX']-year_before['T2M_MAX']))
        reference_days.append(d.isoformat())
    if min(len(persistence), len(prior_year)) < 85:
        raise ValueError('Insufficient matched baseline comparison days')
    return {
      'source':'NASA POWER', 'status':'measured_reanalysis',
      'notes':'NASA POWER gridded/reanalysis-derived 2m atmospheric daily estimates, NOT field station observations, satellite LST or measured neighborhood heat-island contrasts.',
      'coordinates':{'latitude':LAT,'longitude':LON},
      'source_api_url':build_url(), 'documentation_url':SOURCE_DOC,
      'parameters': PARAMS, 'time_standard':'UTC',
      'periods':{
        'range':'2024-01-01 to 2025-12-31',
        'observed_days':len(rows), 'missing_days':len(missing),
        'reference_summer_mean_max_c':round(statistics.mean(summer_2024),4),
        'test_summer_mean_max_c':round(statistics.mean(summer_2025),4),
        'reference_summer_days':len(summer_2024),'test_summer_days':len(summer_2025)
      },
      'evaluation':{
        'period':'2025-06-01 to 2025-08-31',
        'actual':'NASA POWER daily T2M_MAX',
        'persistence_mae_c':round(statistics.mean(persistence),4),
        'prior_year_mae_c':round(statistics.mean(prior_year),4),
        'persistence_n':len(persistence),'prior_year_n':len(prior_year),
        'interpretation':'Descriptive baseline errors for predicting a daily max. Neither is LUNARIS AI; not an urban cooling intervention evaluation.'
      },
      'days':rows,
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',default='dist/app/action-atlas/dubai-heat-case/nasa_power_metrics.json')
    args = cli.parse_args()
    req = urllib.request.Request(build_url(), headers={'User-Agent':'LUNARIS-Research/1.0'})
    print('Fetching NASA POWER daily gridded air temperature (2024–2025)...')
    with urllib.request.urlopen(req, timeout=70) as r:
        raw = r.read()
    payload = json.loads(raw)
    result = process(payload)
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    # Write only after all validation and computation succeed.
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Written',output,'with',result['periods']['observed_days'],'validated daily records')
    print('2025 holdout baselines:',result['evaluation'])

if __name__=='__main__':main()
