
"""Automated API tests using a fake upstream portal."""

import pytest
from fastapi.testclient import TestClient

from app.client import PortalError
from app.main import app, get_portal


class FakePortalClient:
    """Return predictable test data without making network requests."""

    async def get_meters(self, page: int = 1, q: str = ""):
        meters = [
            {
                "meterId": "J100040",
                "serialNo": "AL53485",
                "make": "Secure",
                "phaseType": "single",
                "installStatus": "Installed",
                "dtCode": "DT-001",
            }
        ]

        filtered = [
            meter
            for meter in meters
            if not q or q.lower() in meter["meterId"].lower()
        ]

        return {
            "data": filtered,
            "total": len(filtered),
            "page": page,
            "pageSize": 20,
        }
    
    async def get_meter_details(self, meter_id: str):
        """Return a matching meter or raise an error."""
        meters = await self.get_meters(page=1, q=meter_id)

        for meter in meters["data"]:
            if meter["meterId"] == meter_id:
                return meter

        raise PortalError(f"Meter '{meter_id}' was not found")

    async def get_transformers(self, page: int = 1):
        return {
            "data": [
                {
                    "code": "DT-001",
                    "name": "Malviya Nagar DT 1",
                    "feederCode": "F-001",
                    "capacityKva": 100,
                }
            ],
            "total": 1,
            "page": page,
            "pageSize": 20,
        }

    async def get_consumption(self, meter_id: str):
        if meter_id != "J100040":
            raise PortalError("Meter not found")

        return {
            "data": [
                {
                    "timestamp": "23/06/2026 00:00",
                    "kwh": "5219.83",
                    "kvah": "5637.41",
                    "voltR": "230",
                }
            ]
        }


@pytest.fixture
def client():
    """Provide a test client with the fake portal dependency."""
    app.dependency_overrides[get_portal] = lambda: FakePortalClient()

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_portal, None)


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "flock-energy-api",
    }


def test_list_meters(client):
    response = client.get("/api/v1/meters?page=1")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["data"][0]["meterId"] == "J100040"


def test_search_meters(client):
    response = client.get(
        "/api/v1/meters",
        params={"page": 1, "q": "J100040"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["data"][0]["meterId"] == "J100040"


def test_search_with_no_matches(client):
    response = client.get(
        "/api/v1/meters",
        params={"q": "NO_MATCH"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["total"] == 0


def test_list_transformers(client):
    response = client.get("/api/v1/transformers?page=1")

    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "DT-001"


def test_meter_consumption(client):
    response = client.get(
        "/api/v1/meters/J100040/consumption"
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["kwh"] == "5219.83"


def test_invalid_page(client):
    response = client.get("/api/v1/meters?page=0")

    assert response.status_code == 422


def test_unknown_meter_consumption(client):
    response = client.get(
        "/api/v1/meters/UNKNOWN/consumption"
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Meter not found"


def test_get_meter_details(client):
    response = client.get("/api/v1/meters/J100040")

    assert response.status_code == 200
    assert response.json()["meterId"] == "J100040"
    assert response.json()["serialNo"] == "AL53485"

def test_get_unknown_meter_details(client):
    response = client.get("/api/v1/meters/UNKNOWN")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]
