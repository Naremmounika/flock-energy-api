
"""Opt-in integration tests against the real Urja portal.

These tests use credentials from the local .env file.
They are separate from the regular mock-based test suite.
"""

import asyncio

import pytest

from app.client import PortalClient, PortalError
from app.config import get_settings


def get_live_client():
    """Create a portal client only when a session cookie is configured."""
    settings = get_settings()

    if not settings.portal_session_cookie.get_secret_value():
        pytest.skip("PORTAL_SESSION_COOKIE is not configured in .env")

    return PortalClient()


@pytest.mark.parametrize(
    "meter_id",
    ["J100000"],
)
def test_live_meter_details(meter_id):
    """Verify meter details against the real portal."""
    portal = get_live_client()
    meter = asyncio.run(portal.get_meter_details(meter_id))

    assert meter["meterId"] == meter_id
    assert "serialNo" in meter
    assert "make" in meter
    assert "installStatus" in meter


def test_live_transformers():
    """Verify transformer data against the real portal."""
    portal = get_live_client()
    result = asyncio.run(portal.get_transformers(page=1))

    assert isinstance(result["data"], list)
    assert result["total"] > 0


def test_live_meter_consumption():
    """Verify energy readings against the real portal."""
    portal = get_live_client()
    result = asyncio.run(portal.get_consumption("J100000"))

    assert isinstance(result["data"], list)

    if result["data"]:
        reading = result["data"][0]
        assert "timestamp" in reading
        assert "kwh" in reading
