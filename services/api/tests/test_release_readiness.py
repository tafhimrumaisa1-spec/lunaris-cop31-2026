"""Regression coverage for the bounded, optional city evidence ingest path."""
from pathlib import Path
import json
import importlib.util
from lunaris_api.action_atlas.evidence import read_indicators


def test_absent_satellite_data_never_claims_detection(tmp_path):
    data=read_indicators(tmp_path/'missing.json')
    assert data['status']=='not_imported'
    assert data['indicators']==[]


def test_invalid_measured_values_not_displayed(tmp_path):
    p=tmp_path/'bad.json'
    p.write_text(json.dumps({'schema_version':'1.0','source':{'dataset_period':'2025'},
         'indicators':[{'area_id':'marina-shade','trees':3.5}]}))
    data=read_indicators(p)
    assert data['status']=='invalid_or_unreviewed'
    assert data['indicators']==[]


def test_valid_reviewed_area_data_retained_without_impact_claims(tmp_path):
    p=tmp_path/'review.json'
    p.write_text(json.dumps({'schema_version':'1.0', 'source':{'dataset_period':'2025-01-01/2025-12-31'},
         'indicators':[{'area_id':'marina-shade','trees':0.23,'ndvi':0.14,'lst_c':41.1}]}))
    data=read_indicators(p)
    assert data['status']=='reviewed_area_indicators'
    assert data['indicators'][0]['trees']==0.23
    assert 'impact' not in data['indicators'][0]


def test_atlas_evidence_endpoint_empty_by_default(client, monkeypatch):
    monkeypatch.delenv('LUNARIS_ATLAS_EVIDENCE_FILE',raising=False)
    r=client.get('/v1/action/atlas/evidence')
    assert r.status_code==200
    assert r.json()['status']=='not_imported'
