"""Tests for auth middleware and error handlers."""


def test_unauthenticated_request_returns_401(client):
    resp = client.get('/api/graph/project/list')
    assert resp.status_code == 401


def test_invalid_token_returns_401(client):
    resp = client.get('/api/graph/project/list', headers={'Authorization': 'Bearer invalid.token.here'})
    assert resp.status_code == 401


def test_authenticated_request_succeeds(client, auth_headers):
    resp = client.get('/api/graph/project/list', headers=auth_headers)
    assert resp.status_code == 200


def test_health_check(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'


def test_security_headers_present(client):
    resp = client.get('/health')
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
    assert resp.headers.get('X-Frame-Options') == 'DENY'
