
"""Pydantic models for the public REST API."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base model that ignores extra upstream fields."""

    model_config = ConfigDict(extra="ignore")


class HierarchyNode(APIModel):
    name: str
    code: str


class Hierarchy(APIModel):
    zone: HierarchyNode | None = None
    circle: HierarchyNode | None = None
    division: HierarchyNode | None = None
    subdivision: HierarchyNode | None = None
    substation: HierarchyNode | None = None
    feeder: HierarchyNode | None = None
    dt: HierarchyNode | None = None


class MeterSummary(APIModel):
    meter_id: str
    serial_no: str | None = None
    make: str | None = None
    phase_type: str | None = None
    install_status: str | None = None
    dt_code: str | None = None


class MeterDetail(MeterSummary):
    install_type: str | None = None
    build: str | None = None
    hierarchy: Hierarchy | None = None
    latitude: float | None = None
    longitude: float | None = None


class ConsumptionReading(APIModel):
    timestamp: str
    kwh: float | None = None
    kvah: float | None = None
    volt_r: float | None = None


class ConsumptionResponse(APIModel):
    meter_id: str
    readings: list[ConsumptionReading]
    count: int


class PaginatedMeters(APIModel):
    data: list[MeterSummary]
    total: int
    page: int
    page_size: int


class DistributionTransformer(APIModel):
    code: str
    name: str
    feeder_code: str | None = None
    capacity_kva: float | None = None


class PaginatedTransformers(APIModel):
    data: list[DistributionTransformer]
    total: int
    page: int
    page_size: int


class HierarchyTreeResponse(APIModel):
    tree: dict[str, Any]
    meter_count: int


class MeterExportResponse(APIModel):
    data: list[MeterDetail]
    total: int
