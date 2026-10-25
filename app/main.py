
"""FastAPI application exposing read-only meter portal endpoints."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

from app.client import PortalClient, PortalError



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and close the upstream portal client."""
    portal = PortalClient()
    app.state.portal = portal

    try:
        yield
    finally:
        await portal.close()

app = FastAPI(
    title="Flock Energy Meter API",
    description=(
        "A read-only REST API wrapper for meter, transformer, "
        "and energy-consumption data."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def get_portal() -> PortalClient:
    """Return the portal client stored by the application."""
    return app.state.portal


PortalDependency = Annotated[PortalClient, Depends(get_portal)]


@app.get("/health", tags=["Health"])
async def health_check():
    """Check whether the wrapper application is running."""
    return {
        "status": "ok",
        "service": "flock-energy-api",
    }


@app.get("/api/v1/meters", tags=["Meters"])
async def list_meters(
    portal: PortalDependency,
    page: int = Query(default=1, ge=1),
    q: str = Query(default="", max_length=100),
):
    """Return a page of meters, optionally filtered by search."""
    try:
        return await portal.get_meters(page=page, q=q)
    except PortalError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


@app.get("/api/v1/transformers", tags=["Transformers"])
async def list_transformers(
    portal: PortalDependency,
    page: int = Query(default=1, ge=1),
):
    """Return a page of distribution transformers."""
    try:
        return await portal.get_transformers(page=page)
    except PortalError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


@app.get(
    "/api/v1/meters/{meter_id}/consumption",
    tags=["Consumption"],
)
async def meter_consumption(
    meter_id: str,
    portal: PortalDependency,
):
    """Return energy readings for a specific meter."""
    if not meter_id.strip():
        raise HTTPException(
            status_code=400,
            detail="meter_id is required",
        )

    try:
        return await portal.get_consumption(meter_id)
    except PortalError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

@app.get("/api/v1/meters/{meter_id}", tags=["Meters"])
async def get_meter_details(
    meter_id: str,
    portal: PortalDependency,
):
    """Return details for a single meter."""
    if not meter_id.strip():
        raise HTTPException(
            status_code=400,
            detail="meter_id is required",
        )

    try:
        return await portal.get_meter_details(meter_id)
    except PortalError as exc:
        message = str(exc)

        if "was not found" in message:
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=502,
            detail=message,
        ) from exc
