"""Tests for billing API endpoints."""


def test_billing_requires_auth(client):
    resp = client.get('/api/billing/status')
    assert resp.status_code == 401
