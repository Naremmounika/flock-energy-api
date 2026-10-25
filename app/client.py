
"""HTTP client for the upstream Urja Meter Ops portal."""

from typing import Any
from urllib.parse import quote

import httpx

from app.config import get_settings


SESSION_COOKIE = "__Secure-better-auth.session_token"


class PortalError(Exception):
    """Raised when an upstream portal request fails."""


class PortalClient:
    """Reusable HTTP client with automatic login and session retry."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.portal_base_url.rstrip("/")
        self.timeout = settings.request_timeout
        self.email = settings.portal_email
        self.password = settings.portal_password.get_secret_value()

        initial_cookies = {}
        session_cookie = (
            settings.portal_session_cookie.get_secret_value()
        )
        if session_cookie:
            initial_cookies[SESSION_COOKIE] = session_cookie

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            follow_redirects=False,
            headers={
                "Accept": "application/json",
                "Referer": f"{self.base_url}/meters",
            },
            cookies=initial_cookies,
        )

    async def close(self) -> None:
        """Close the reusable HTTP client."""
        await self._client.aclose()

    def _has_session(self) -> bool:
        """Check whether the HTTP client's cookie jar has a session."""
        return any(
            cookie.name == SESSION_COOKIE
            for cookie in self._client.cookies.jar
        )

    async def _login(self) -> None:
        """Log in and retain the session cookie returned by the portal."""
        if not self.email or not self.password:
            raise PortalError(
                "Portal login requires PORTAL_EMAIL and "
                "PORTAL_PASSWORD in your .env file."
            )

        try:
            response = await self._client.post(
                "/login",
                data={
                    "email": self.email,
                    "password": self.password,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": f"{self.base_url}/login",
                },
            )
        except httpx.RequestError as exc:
            raise PortalError(
                "Could not connect to the portal login endpoint."
            ) from exc

        if response.status_code >= 400:
            raise PortalError(
                f"Portal login failed with HTTP "
                f"{response.status_code}. Check your credentials "
                "and the login request format."
            )

        if not self._has_session():
            raise PortalError(
                "The login response did not provide the expected "
                "session cookie. Check the portal login flow."
            )

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """GET JSON from the portal and retry once after re-login."""
        for attempt in range(2):
            try:
                response = await self._client.get(
                    path,
                    params=params,
                )
            except httpx.RequestError as exc:
                raise PortalError(
                    f"Could not connect to the portal for {path}"
                ) from exc

            redirected_to_login = (
                response.is_redirect
                and "/login" in response.headers.get("location", "")
            )
            authentication_failed = response.status_code in (401, 403)

            if authentication_failed or redirected_to_login:
                if attempt == 0:
                    await self._login()
                    continue

                raise PortalError(
                    "Portal authentication failed after retry."
                )

            if response.is_redirect:
                raise PortalError(
                    f"Portal redirected the request for {path}. "
                    "Authentication or the upstream route may have "
                    "changed."
                )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise PortalError(
                    f"Portal returned HTTP "
                    f"{exc.response.status_code} for {path}"
                ) from exc

            content_type = response.headers.get("content-type", "")
            if "json" not in content_type.lower():
                if attempt == 0:
                    await self._login()
                    continue

                raise PortalError(
                    f"Portal returned a non-JSON response for {path} "
                    "even after re-authentication."
                )

            try:
                return response.json()
            except ValueError as exc:
                raise PortalError(
                    f"Portal returned invalid JSON for {path}"
                ) from exc

        raise PortalError(f"Portal request failed for {path}")

    async def get_meters(
        self,
        page: int = 1,
        q: str = "",
    ) -> dict[str, Any]:
        """Retrieve a page of meters, optionally filtered by search."""
        result = await self._get(
            "/portal/meters/search",
            {"q": q, "page": page},
        )

        if not isinstance(result, dict) or not isinstance(
            result.get("data"), list
        ):
            raise PortalError(
                "Unexpected response format from meters endpoint"
            )

        return result

    async def get_meter_details(
        self,
        meter_id: str,
    ) -> dict[str, Any]:
        """Find a single meter using the verified search endpoint."""
        result = await self.get_meters(page=1, q=meter_id)

        for meter in result["data"]:
            if str(meter.get("meterId", "")) == meter_id:
                return meter

        raise PortalError(f"Meter '{meter_id}' was not found")

    async def get_transformers(
        self,
        page: int = 1,
    ) -> dict[str, Any]:
        """Retrieve a page of distribution transformers."""
        result = await self._get(
            "/portal/dts",
            {"page": page},
        )

        if not isinstance(result, dict) or not isinstance(
            result.get("data"), list
        ):
            raise PortalError(
                "Unexpected response format from transformers endpoint"
            )

        return result

    async def get_consumption(
        self,
        meter_id: str,
    ) -> dict[str, Any]:
        """Retrieve energy readings for a specific meter."""
        safe_meter_id = quote(meter_id, safe="")

        result = await self._get(
            f"/portal/meters/{safe_meter_id}/energy"
        )

        if not isinstance(result, dict) or not isinstance(
            result.get("data"), list
        ):
            raise PortalError(
                "Unexpected response format from consumption endpoint"
            )

        return result
