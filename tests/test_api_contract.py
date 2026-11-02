import asyncio
import uuid

import httpx

from backend.main import app


def request(method: str, path: str, payload=None):
    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=payload)

    return asyncio.run(_run())


def test_health_contract():
    response = request("GET", "/health")
    assert response.status_code == 200

    payload = response.json()
    assert "status" in payload
    assert "service" in payload
    assert "data_loaded" in payload


def test_analyze_contract_fields():
    body = {
        "reference_lat": 13.0062,
        "reference_lon": 80.2433,
        "search_radius_km": 5.0,
        "weights": {
            "rent": 0.25,
            "crowd": 0.25,
            "competition": 0.25,
            "accessibility": 0.25,
        },
        "business_type": "restaurant",
        "limit": 5,
    }

    response = request("POST", "/api/analyze", body)
    assert response.status_code == 200

    payload = response.json()
    assert payload.get("success") is True
    assert isinstance(payload.get("results"), list)

    # Contract: data quality indicator exists for UI confidence rendering
    dq = payload.get("data_quality")
    assert isinstance(dq, dict)
    for key in [
        "coverage_percent",
        "confidence",
        "radius_candidates",
        "poi_coverage_percent",
        "transit_coverage_percent",
        "market_coverage_percent",
        "note",
    ]:
        assert key in dq

    if payload["results"]:
        result = payload["results"][0]
        for key in [
            "id",
            "name",
            "locality_name",
            "lat",
            "lon",
            "display_lat",
            "display_lon",
            "score",
            "score_percent",
            "breakdown",
            "distance_km",
            "features",
            "constraint_details",
        ]:
            assert key in result

        # Use-case semantics: business-specific competition label should reflect strategy mode
        label = result["constraint_details"]["competition"]["label"]
        assert any(token in label for token in ["Opportunity", "Demand Signal", "Market Fit"])


def test_register_accepts_6_char_password():
    unique_email = f"test_{uuid.uuid4().hex[:10]}@example.com"
    payload = {
        "email": unique_email,
        "password": "abc123",
        "full_name": "Test User",
    }

    response = request("POST", "/api/auth/register", payload)
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True


def test_register_rejects_password_longer_than_16():
    unique_email = f"test_{uuid.uuid4().hex[:10]}@example.com"
    payload = {
        "email": unique_email,
        "password": "abcdefghijklmnopq",  # 17 chars
        "full_name": "Test User",
    }

    response = request("POST", "/api/auth/register", payload)
    assert response.status_code in (400, 422)
    body = response.json()
    assert "72 bytes" not in str(body).lower()
