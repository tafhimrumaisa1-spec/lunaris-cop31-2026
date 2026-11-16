from lunaris_api.action_atlas.catalog import all_areas, POLICIES
from lunaris_api.action_atlas.scenario import estimate, ScenarioError
import pytest

def test_catalog_declares_uncertainty():
    areas = all_areas()
    assert len(areas) >= 10
    assert len({a['id'] for a in areas}) == len(areas)
    assert all(a['status'] == 'concept_only' for a in areas)
    assert all('not satellite' in a['evidence_status'] for a in areas)
    assert all(a['category'] in POLICIES for a in areas)

def test_scenario_canopy_arithmetic():
    r = estimate('greening', 10, unit_benefit=12, adoption=.5)
    assert r['potential_impact'] == 60
    assert r['illustrative_budget_aed'] == 14000
    assert r['scenario_status'] == 'illustrative'

def test_unavailable_or_invalid_assumptions():
    with pytest.raises(ScenarioError): estimate('greening', -2)
    with pytest.raises(ScenarioError): estimate('greening', 10, adoption=1.2)
    with pytest.raises(ScenarioError): estimate('solar', 1000000)
    with pytest.raises(ScenarioError): estimate('greening', float('nan'))

def test_all_category_models_bounded():
    for category in POLICIES:
        val = estimate(category, 1)
        assert val['potential_impact'] >= 0
        assert val['model_kind'].startswith('deterministic')

def test_endpoint_catalog_and_scenario():
    from fastapi import FastAPI
    from lunaris_api.routers.action_atlas import router
    from fastapi.testclient import TestClient
    mini = FastAPI(); mini.include_router(router)
    client = TestClient(mini)
    found = client.get('/v1/action/atlas')
    assert found.status_code == 200
    assert 'conceptual' in found.json()['data_status']
    ok = client.post('/v1/action/atlas/marina-shade/scenario', json={'quantity':10,'unit_benefit':12,'adoption':.5})
    assert ok.status_code == 200
    assert ok.json()['potential_impact'] == 60
    assert client.post('/v1/action/atlas/nope/scenario', json={'quantity':1}).status_code == 404
    assert client.post('/v1/action/atlas/marina-shade/scenario', json={'quantity':-1}).status_code == 422

def test_interest_is_only_a_concept_record(authed):
    client, headers, _ = authed
    url = '/v1/action/atlas/marina-shade/interest'
    assert client.post(url, json={'consent': True}).status_code == 401
    assert client.post(url, json={'consent': False}, headers=headers).status_code == 422
    response = client.post(url, json={'consent': True}, headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data['status'] == 'concept_interest_only'
    assert 'No actual event exists' in data['notice']
    assert client.post(url, json={'consent': True}, headers=headers).status_code == 409
