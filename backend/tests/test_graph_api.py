"""Tests for graph API endpoints."""


def test_list_projects_empty(client, auth_headers):
    resp = client.get('/api/graph/project/list', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True


def test_delete_project_requires_auth(client):
    resp = client.delete('/api/graph/project/some-fake-id')
    assert resp.status_code == 401
