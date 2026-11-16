"""Offline launch readiness checker. Does not contact the internet or assert live readiness."""
from pathlib import Path
import sys,os,json,re
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def ck(name, success, note=''):
    checks.append((name,success,note));print(f'{"PASS" if success else "ACTION"} {name}'+(f' — {note}' if note else ''))

ck('Homepage entry', (ROOT/'dist/index.html').is_file())
ck('Consumer app entry', (ROOT/'dist/app/index.html').is_file())
ck('Dubai Action Atlas entry',(ROOT/'dist/app/action-atlas/index.html').is_file())
ck('Same-origin gateway config', (ROOT/'deploy/nginx.conf').is_file())
ck('Production compose config', (ROOT/'compose.release.yml').is_file())
ck('Migration exists', any((ROOT/'services/api/alembic/versions').glob('*.py')))
ck('API implementation', (ROOT/'services/api/src/lunaris_api/main.py').is_file())
ck('ML training script', (ROOT/'services/api/ml_training/train.py').is_file())
artifact=ROOT/'deploy/models/model.joblib'
report=ROOT/'deploy/models/evaluation.json'
ck('Real model installed',artifact.is_file() and report.is_file(),'Required for a validated AI launch; baseline-only mode is supported')
if report.is_file():
    try:
        data=json.loads(report.read_text())
        ck('ML evaluation report parses', bool(data.get('test_baseline') and data.get('test_ml')))
    except Exception:ck('ML evaluation report parses',False)
else:ck('ML evaluation report parses',False,'Must train with real archived data')
evidence=ROOT/'deploy/evidence/dubai_area_indicators.json'
ck('Reviewed satellite export installed',evidence.is_file(),'If absent, Atlas remains clearly labeled conceptual')
config=ROOT/'dist/app/config.js'
ck('App uses configurable API origin',config.is_file() and 'LUNARIS_API_BASE' in config.read_text())
ck('Private credentials absent from release zip', not (ROOT/'.env.release').exists() and not (ROOT/'services/api/.env').exists())
print('\nOffline static preflight: '+str(sum(x[1] for x in checks))+'/'+str(len(checks))+' checks satisfied.')
print('This is not a live deployment or a scientific validation. Verify HTTPS, real provider forecasts, CORS, sessions, and UI in a public browser.')
# Mandatory implementation checks are distinct from external launch dependencies.
mandatory={x[0] for x in checks[:8]}
sys.exit(0 if all(ok for name,ok,_ in checks if name in mandatory) else 1)
